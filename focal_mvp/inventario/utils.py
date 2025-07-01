from inventario.models import LoteProducto, MovimientoStock, Almacenero, Empresa

def descontar_stock_por_lotes(producto, cantidad, usuario=None, nota="Venta automática"):
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
    
def obtener_empresa_del_usuario(user):
    """
    Obtiene la empresa asociada a un usuario de forma eficiente.
    
    Usa select_related para evitar consultas adicionales a la base de datos.
    Devuelve la instancia de la Empresa o None si no se encuentra.
    """
    try:
        # 1 consulta para obtener Almacenero y Empresa
        almacenero = Almacenero.objects.select_related('empresa').get(usuario=user)
        return almacenero.empresa
    except Almacenero.DoesNotExist:
        # Si el usuario no tiene un perfil de almacenero, no tiene empresa.
        return None