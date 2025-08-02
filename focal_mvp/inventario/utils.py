from .models import LoteProducto, MovimientoStock, Almacenero, Empresa

def descontar_stock_por_lotes(producto, cantidad, usuario=None, nota="Venta automática"):
    # Esta función parece correcta, la mantenemos igual.
    lotes = (
        LoteProducto.objects
        .filter(producto=producto, cantidad__gt=0)
        .order_by('fecha_vencimiento')
    )
    restante = cantidad
    for lote in lotes:
        if restante <= 0:
            break
        a_retirar = min(lote.cantidad, restante)
        lote.cantidad -= a_retirar
        lote.save()
        MovimientoStock.objects.create(
            lote=lote,
            producto=producto,
            cantidad_retirada=a_retirar,
            usuario=usuario,
            nota=nota
        )
        restante -= a_retirar
    if restante > 0:
        raise Exception(f"No hay stock suficiente para el producto '{producto.nombre}'")

# ▼▼▼ ESTA ES LA FUNCIÓN CORREGIDA ▼▼▼
def obtener_empresa_del_usuario(user):
    """
    Obtiene la empresa asociada directamente al perfil del usuario.
    """
    if user.is_authenticated and hasattr(user, 'empresa'):
        return user.empresa
    return None