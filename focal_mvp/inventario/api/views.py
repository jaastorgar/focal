from django.db import models, transaction
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from inventario.forms import ArchivoVentasForm
from inventario.models import Producto, MovimientoStock
from inventario.utils import obtener_empresa_del_usuario
import pandas as pd

@login_required
@transaction.atomic
def procesar_ventas_archivo(request):
    if request.method == 'POST':
        form = ArchivoVentasForm(request.POST, request.FILES)
        if form.is_valid():
            empresa_usuario = obtener_empresa_del_usuario(request.user)
            if not empresa_usuario:
                messages.error(request, "Tu cuenta no está asociada a una empresa.")
                return redirect('procesar_ventas_archivo')

            archivo = form.cleaned_data['archivo']
            try:
                if archivo.name.endswith('.csv'):
                    df = pd.read_csv(archivo)
                elif archivo.name.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(archivo)
                else:
                    messages.error(request, "Formato no válido. Usa .csv o .xlsx")
                    return redirect('procesar_ventas_archivo')
            except Exception as e:
                messages.error(request, f"Error al leer el archivo: {e}")
                return redirect('procesar_ventas_archivo')

            errores = []
            # Usamos un punto de guardado para poder revertir si algo sale mal.
            sid = transaction.savepoint()

            for idx, fila in df.iterrows():
                try:
                    sku = str(fila.get('sku')).strip()
                    cantidad = int(fila.get('cantidad', 0))

                    # OPTIMIZACIÓN DE SEGURIDAD: Buscamos el producto que coincida con el SKU Y la empresa del usuario.
                    producto = Producto.objects.get(sku=sku, empresa=empresa_usuario)

                    lotes = producto.lotes.filter(cantidad__gt=0).order_by('fecha_vencimiento')
                    cantidad_restante = cantidad

                    for lote in lotes:
                        if cantidad_restante <= 0:
                            break
                        
                        retirar = min(lote.cantidad, cantidad_restante)
                        # Usamos F() expressions para evitar race conditions
                        lote.cantidad = models.F('cantidad') - retirar
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
                
                except Producto.DoesNotExist:
                    errores.append(f"Fila {idx+2}: Producto con SKU {sku} no encontrado en tu empresa.")
                except Exception as e:
                    errores.append(f"Fila {idx+2}: Error inesperado procesando SKU {sku}: {e}")

            if errores:
                # Si hubo algún error, revertimos todos los cambios en la base de datos.
                transaction.savepoint_rollback(sid)
                for err in errores:
                    messages.error(request, err)
            else:
                # Si no hubo errores, confirmamos todos los cambios.
                transaction.savepoint_commit(sid)
                messages.success(request, "Descuento de productos completado correctamente.")

            return redirect('inventario')
    else:
        form = ArchivoVentasForm()

    return render(request, 'inventario/procesar_ventas_archivo.html', {'form': form})