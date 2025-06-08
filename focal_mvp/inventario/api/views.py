from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from inventario.models import LoteProducto, MovimientoStock
from .serializers import DescontarStockSerializer

class DescontarStockView(APIView):
    """
    API que descuenta stock por lote y continúa con otros si no alcanza.
    Registra cada retiro en el historial MovimientoStock.
    """

    def post(self, request):
        serializer = DescontarStockSerializer(data=request.data)
        if serializer.is_valid():
            cantidad = serializer.validated_data['cantidad']
            lotes = serializer.validated_data['lotes_ordenados']

            cantidad_restante = cantidad
            movimientos = []

            for lote in lotes:
                if cantidad_restante == 0:
                    break

                retirar = min(lote.cantidad, cantidad_restante)
                lote.cantidad -= retirar
                lote.save()

                # Registro del movimiento
                MovimientoStock.objects.create(
                    lote=lote,
                    producto=lote.producto,
                    cantidad_retirada=retirar,
                    usuario=request.user if request.user.is_authenticated else None,
                    nota="Retiro automático por API"
                )

                movimientos.append({
                    "lote_id": lote.id,
                    "producto": lote.producto.nombre,
                    "retirado": retirar,
                    "stock_restante_en_lote": lote.cantidad
                })

                cantidad_restante -= retirar

            return Response({
                "success": True,
                "mensaje": f"Se retiraron {cantidad} unidades del producto '{lotes[0].producto.nombre}'.",
                "lotes_afectados": movimientos
            }, status=status.HTTP_200_OK)

        # Si hay errores de validación
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)