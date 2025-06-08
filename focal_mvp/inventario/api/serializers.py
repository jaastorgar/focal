from rest_framework import serializers
from inventario.models import LoteProducto

class DescontarStockSerializer(serializers.Serializer):
    lote_id = serializers.IntegerField()
    cantidad = serializers.IntegerField(min_value=1)

    def validate(self, data):
        lote_id = data.get("lote_id")
        cantidad = data.get("cantidad")

        try:
            lote = LoteProducto.objects.get(id=lote_id)
        except LoteProducto.DoesNotExist:
            raise serializers.ValidationError({"lote_id": "El lote no existe."})

        producto = lote.producto
        lotes_disponibles = (
            LoteProducto.objects
            .filter(producto=producto, cantidad__gt=0)
            .order_by('fecha_vencimiento')
        )

        stock_total = sum(l.cantidad for l in lotes_disponibles)

        if stock_total < cantidad:
            raise serializers.ValidationError(
                f"No hay stock suficiente en todos los lotes. Stock total disponible: {stock_total}"
            )

        data["producto"] = producto
        data["lotes_ordenados"] = lotes_disponibles
        return data