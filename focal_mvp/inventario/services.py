# services.py
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.timezone import now

from .models import OfertaProducto, LoteProducto, MovimientoStock

def _round_to_step(grams: int, step: int) -> int:
    if step <= 1:
        return grams
    remainder = grams % step
    if remainder == 0:
        return grams
    down = grams - remainder
    up = down + step
    # redondeo simétrico
    return up if (grams - down) >= (step / 2) else down

def _grams_from_amount(amount_clp: int, price_per_kg: Decimal) -> int:
    if price_per_kg is None or Decimal(price_per_kg) <= 0:
        raise ValidationError("Precio por kg inválido.")
    grams = (Decimal(amount_clp) / Decimal(price_per_kg)) * Decimal(1000)
    return int(grams.quantize(Decimal('1'), rounding=ROUND_HALF_UP))

@transaction.atomic
def venta_cecina_por_monto(oferta_id: int, amount_clp: int, usuario, nota: str = "") -> dict:
    """
    Convierte CLP a gramos con price_per_kg vigente y descuenta (FEFO) en gramos
    desde los lotes del producto (para esta empresa).
    Retorna payload con gramos_finales y lotes afectados.
    """
    if amount_clp is None or int(amount_clp) <= 0:
        raise ValidationError("El monto debe ser un entero positivo en CLP.")

    oferta = OfertaProducto.objects.select_for_update().get(id=oferta_id)

    if not oferta.sell_by_weight:
        raise ValidationError("Este producto no está configurado para venta por peso.")
    if oferta.price_per_kg is None or oferta.price_per_kg <= 0:
        raise ValidationError("Debes definir un precio por kg vigente en la oferta.")

    grams_calc = _grams_from_amount(int(amount_clp), oferta.price_per_kg)
    grams_final = _round_to_step(grams_calc, max(1, oferta.min_step_grams))

    # Lotes con stock (FEFO/fecha de vencimiento asc, luego id)
    lotes_qs = (LoteProducto.objects
                .select_for_update()
                .filter(producto=oferta, cantidad__gt=0)
                .order_by('fecha_vencimiento', 'id'))

    # Verificar stock disponible total (en gramos)
    stock_total_grams = sum(int(l.cantidad or 0) for l in lotes_qs)
    if stock_total_grams < grams_final:
        raise ValidationError(f"Stock insuficiente. Disponible: {stock_total_grams} g, requerido: {grams_final} g.")

    grams_to_deduct = grams_final
    lotes_afectados = []

    for lote in lotes_qs:
        if grams_to_deduct <= 0:
            break
        disponible = int(lote.cantidad or 0)
        if disponible <= 0:
            continue

        tomar = min(disponible, grams_to_deduct)
        # Registrar movimiento
        MovimientoStock.objects.create(
            lote=lote,
            cantidad=tomar,
            tipo='SALIDA',
            descripcion=f"Salida por monto ${amount_clp:,} → {grams_final} g (precio {oferta.price_per_kg}/kg). {nota}".strip()
        )
        # Actualizar lote (cantidad representa gramos cuando sell_by_weight=True)
        lote.cantidad = disponible - tomar
        lote.save(update_fields=['cantidad'])

        if lote.cantidad == 0:
            lote_id = lote.id
            lote.delete()
            lotes_afectados.append({'lote_id': lote_id, 'descontado_g': tomar, 'agotado': True})
        else:
            lotes_afectados.append({'lote_id': lote.id, 'descontado_g': tomar, 'agotado': False})

        grams_to_deduct -= tomar

    if grams_to_deduct != 0:
        raise ValidationError("No fue posible completar el descuento por un desajuste de concurrencia.")

    return {
        'grams_final': grams_final,
        'price_per_kg': float(oferta.price_per_kg),
        'amount_clp': int(amount_clp),
        'lotes_afectados': lotes_afectados,
        'timestamp': now().isoformat(),
    }