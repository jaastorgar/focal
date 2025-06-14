from django.http import JsonResponse
from inventario.models import MovimientoStock, Producto, LoteProducto
from django.db import models
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from inventario.forms import ArchivoVentasForm
from inventario.models import Producto, MovimientoStock
import pandas as pd

@login_required
def procesar_ventas_archivo(request):
    if request.method == 'POST':
        form = ArchivoVentasForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = form.cleaned_data['archivo']
            extension = archivo.name.split('.')[-1]

            # Leer archivo
            try:
                if extension == 'csv':
                    df = pd.read_csv(archivo)
                elif extension in ['xlsx', 'xls']:
                    df = pd.read_excel(archivo)
                else:
                    messages.error(request, "Formato no válido. Usa .csv o .xlsx")
                    return redirect('procesar_ventas_archivo')
            except Exception as e:
                messages.error(request, f"Error al leer el archivo: {e}")
                return redirect('procesar_ventas_archivo')

            errores = []

            for idx, fila in df.iterrows():
                sku = str(fila.get('sku')).strip()
                cantidad = int(fila.get('cantidad', 0))

                try:
                    producto = Producto.objects.get(sku=sku)
                except Producto.DoesNotExist:
                    errores.append(f"Fila {idx+2}: Producto con SKU {sku} no encontrado.")
                    continue

                # 👉 Añadir nombre del producto al DataFrame (en memoria)
                df.at[idx, 'nombre_producto'] = producto.nombre

                lotes = producto.lotes.filter(cantidad__gt=0).order_by('fecha_vencimiento')
                cantidad_restante = cantidad

                for lote in lotes:
                    if cantidad_restante <= 0:
                        break

                    retirar = min(lote.cantidad, cantidad_restante)
                    lote.cantidad -= retirar
                    lote.save()

                    MovimientoStock.objects.create(
                        lote=lote,
                        producto=producto,
                        cantidad_retirada=retirar,
                        usuario=request.user,
                        nota="Descuento automático por carga de archivo"
                    )

                    cantidad_restante -= retirar

                if cantidad_restante > 0:
                    errores.append(f"Fila {idx+2}: Stock insuficiente para SKU {sku}. Faltaron {cantidad_restante} unidades.")

            if errores:
                for err in errores:
                    messages.warning(request, err)
            else:
                messages.success(request, "Descuento de productos completado correctamente.")

            return redirect('inventario')
    else:
        form = ArchivoVentasForm()

    return render(request, 'inventario/procesar_ventas_archivo.html', {'form': form})

@login_required
def dashboard_metrics_api(request):
    productos = Producto.objects.all()
    data = []

    for producto in productos:
        stock = producto.lotes.aggregate(total=models.Sum('cantidad'))['total'] or 0
        data.append({
            'nombre': producto.nombre,
            'stock': stock
        })

    total_productos = productos.count()
    total_stock = sum(item['stock'] for item in data)
    total_lotes = LoteProducto.objects.count()

    return JsonResponse({
        'data': data,
        'totales': {
            'productos': total_productos,
            'stock': total_stock,
            'lotes': total_lotes
        }
    })