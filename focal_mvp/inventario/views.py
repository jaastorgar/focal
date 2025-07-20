from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from .forms import ProductoForm, LoteProductoForm, ArchivoVentasForm
from .models import Almacenero, Empresa, PlanSuscripcion, SuscripcionUsuario, Producto, LoteProducto, MovimientoStock
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .decorators import plan_requerido, caracteristica_requerida
from .utils import obtener_empresa_del_usuario
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie

@login_required
def home(request):
    from datetime import date, timedelta
    from django.db.models import Sum
    
    try:
        almacenero = Almacenero.objects.get(usuario=request.user)
    except Almacenero.DoesNotExist:
        almacenero = None

    empresa = obtener_empresa_del_usuario(request.user)
    
    alertas_vencimiento = []
    alertas_stock_bajo = []

    if empresa:
        fecha_limite_vencimiento = date.today() + timedelta(days=30)
        alertas_vencimiento = (
            LoteProducto.objects
            .filter(
                producto__empresa=empresa, 
                cantidad__gt=0, 
                fecha_vencimiento__gte=date.today(),
                fecha_vencimiento__lte=fecha_limite_vencimiento
            )
            .order_by('fecha_vencimiento')
            .select_related('producto')[:5]
        )

        alertas_stock_bajo = (
            Producto.objects
            .filter(empresa=empresa)
            .annotate(stock_total=Sum('lotes__cantidad'))
            .filter(stock_total__lte=5, stock_total__gt=0)
            .order_by('stock_total')[:5] 
        )

    context = {
        'almacenero': almacenero,
        'alertas_vencimiento': alertas_vencimiento,
        'alertas_stock_bajo': alertas_stock_bajo,
    }
    
    return render(request, 'inventario/home.html', context)

@login_required
def logout_view(request):
    from django.contrib.auth import logout
    
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('/')

@cache_page(60 * 5)
@vary_on_cookie
@login_required
def perfil(request):
    try:
        suscripcion = SuscripcionUsuario.objects.select_related(
            'empresa__almacenero__usuario', 
            'plan'
        ).get(empresa__almacenero__usuario=request.user, activa=True)

        empresa = suscripcion.empresa
        almacenero = empresa.almacenero
        plan = suscripcion.plan

    except SuscripcionUsuario.DoesNotExist:
        almacenero = getattr(request.user, 'almacenero', None)
        empresa = almacenero.empresa if almacenero else None
        plan = None
        suscripcion = None
        messages.warning(request, "No tienes una suscripción activa.")

    context = {
        'almacenero': almacenero,
        'empresa': empresa,
        'plan': plan,
    }

    return render(request, 'inventario/perfil.html', context)

@login_required
def inventario_view(request):
    from datetime import date, timedelta
    from django.db.models import Q, Min, Sum
    import time
    
    query = request.GET.get('q')
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        productos = Producto.objects.none() 
    else:
        productos = (
            Producto.objects
            .filter(empresa=empresa_usuario)
            .annotate(
                stock_total=Sum('lotes__cantidad'),
                proximo_vencimiento=Min('lotes__fecha_vencimiento')
            )
        )

    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) |
            Q(sku__icontains=query) |
            Q(marca__icontains=query) |
            Q(categoria__icontains=query)
        ).distinct()

        if not productos.exists():
            messages.info(request, f"No se encontraron productos que coincidan con '{query}'.")
        else:
            messages.success(request, f"Mostrando resultados para '{query}'.")

    hoy = date.today()
    hoy_mas_15dias = hoy + timedelta(days=15)

    context = {
        'productos': productos,
        'query': query,
        'today': hoy,
        'hoy_mas_15dias': int(time.mktime(hoy_mas_15dias.timetuple())), 
    }
    
    return render(request, 'inventario/inventario.html', context)

@login_required
def agregar_producto(request):
    try:
        suscripcion = SuscripcionUsuario.objects.select_related('plan', 'empresa').get(
            empresa__almacenero__usuario=request.user, 
            activa=True
        )
        empresa_usuario = suscripcion.empresa
        plan = suscripcion.plan
    except SuscripcionUsuario.DoesNotExist:
        messages.error(request, "Tu cuenta no tiene una suscripción activa. No puedes agregar productos.")
        return redirect('home')

    productos_actuales = Producto.objects.filter(empresa=empresa_usuario).count()
    if plan.max_productos != 0 and productos_actuales >= plan.max_productos:
        messages.error(request, f"Has alcanzado el límite de productos para el plan '{plan.get_nombre_display()}' ({plan.max_productos} productos).")
        return redirect('inventario')

    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.empresa = empresa_usuario
            producto.save()
            messages.success(request, 'Producto agregado correctamente.')
            return redirect('inventario')
    else:
        form = ProductoForm()

    return render(request, 'inventario/agregar-producto.html', {'form': form})

@login_required
def editar_producto(request, producto_id):
    try:
        empresa_usuario = request.user.almacenero.empresa
    except (Almacenero.DoesNotExist, Empresa.DoesNotExist):
        messages.error(request, "Tu cuenta no está asociada a una empresa válida. No puedes editar productos.")
        return redirect('inventario')

    producto = get_object_or_404(Producto, id=producto_id, empresa=empresa_usuario)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado correctamente.')
            return redirect('inventario') 
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'inventario/editar-producto.html', {'form': form, 'producto': producto})

login_required
def editar_lote(request, lote_id):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('inventario')

    lote = get_object_or_404(LoteProducto, id=lote_id, producto__empresa=empresa_usuario)
    
    if request.method == 'POST':
        form = LoteProductoForm(request.POST, instance=lote)
        if form.is_valid():
            form.save()
            messages.success(request, "Lote actualizado correctamente.")
            return redirect('detalle_producto', producto_id=lote.producto.id)
    else:
        form = LoteProductoForm(instance=lote, empresa=empresa_usuario)

    return render(request, 'inventario/editar_lote.html', {'form': form, 'lote': lote})

@login_required
def retirar_lote(request, lote_id):
    from django.db.models import F
    
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('inventario')

    lote = get_object_or_404(LoteProducto, id=lote_id, producto__empresa=empresa_usuario)

    if request.method == 'POST':
        try:
            cantidad_a_retirar = int(request.POST.get('cantidad', 0))
        except (ValueError, TypeError):
            messages.error(request, "La cantidad ingresada no es un número válido.")
            return redirect('detalle_producto', producto_id=lote.producto.id)

        if cantidad_a_retirar <= 0:
            messages.error(request, "La cantidad a retirar debe ser mayor que cero.")
            return redirect('detalle_producto', producto_id=lote.producto.id)

        try:
            with transaction.atomic():
                lote_para_actualizar = LoteProducto.objects.select_for_update().get(id=lote_id)

                if cantidad_a_retirar > lote_para_actualizar.cantidad:
                    messages.error(request, f"No puedes retirar más de {lote_para_actualizar.cantidad} unidades.")
                else:
                    lote_para_actualizar.cantidad = F('cantidad') - cantidad_a_retirar
                    lote_para_actualizar.save()
                    messages.success(request, f"Se retiraron {cantidad_a_retirar} unidades del lote.")
            
            return redirect('detalle_producto', producto_id=lote.producto.id)
            
        except LoteProducto.DoesNotExist:
            messages.error(request, "El lote que intentas modificar ya no existe.")
            return redirect('inventario')

    return render(request, 'inventario/retirar_lote.html', {'lote': lote})

@login_required
def eliminar_producto(request, producto_id):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('inventario')

    producto = get_object_or_404(Producto, id=producto_id, empresa=empresa_usuario)

    if request.method == 'POST':
        nombre_producto = producto.nombre
        producto.delete()
        messages.success(request, f'El producto "{nombre_producto}" ha sido eliminado exitosamente.')
        return redirect('inventario')
    
    lote_proximo = producto.lotes.order_by('fecha_vencimiento').first()

    context = {
        'producto': producto,
        'lote': lote_proximo
    }
    
    return render(request, 'inventario/eliminar_producto_confirm.html', context)

@login_required
def agregar_lote_producto(request):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('inventario')

    if request.method == 'POST':
        form = LoteProductoForm(request.POST, empresa=empresa_usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Lote registrado correctamente.")
            return redirect('inventario')
    else:
        form = LoteProductoForm(empresa=empresa_usuario)

    return render(request, 'inventario/agregar_lote.html', {'form': form})

@login_required
def eliminar_lote(request, lote_id):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('inventario')

    lote = get_object_or_404(
        LoteProducto.objects.select_related('producto'), 
        id=lote_id, 
        producto__empresa=empresa_usuario
    )
    producto_id = lote.producto.id

    if request.method == 'POST':
        lote.delete()
        messages.success(request, "Lote eliminado correctamente.")
        return redirect('detalle_producto', producto_id=producto_id)
    
    return render(request, 'inventario/eliminar_lote_confirm.html', {'lote': lote})

@login_required
def detalle_producto(request, producto_id):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('inventario')

    producto = get_object_or_404(
        Producto.objects.prefetch_related('lotes'), 
        id=producto_id, 
        empresa=empresa_usuario
    )
    
    lotes = sorted(producto.lotes.all(), key=lambda lote: lote.fecha_vencimiento)

    return render(request, 'inventario/detalle_producto.html', {
        'producto': producto,
        'lotes': lotes
    })

@login_required
def seleccionar_plan(request, plan_id):
    from datetime import date, timedelta
    
    plan = get_object_or_404(PlanSuscripcion, id=plan_id)
    
    empresa_usuario = obtener_empresa_del_usuario(request.user)

    if not empresa_usuario:
        messages.error(request, "No se pudo procesar tu solicitud al no encontrar una empresa asociada.")
        return redirect('vista_planes')

    if request.method == 'POST':
        if plan.nombre == 'FREE':
            messages.warning(request, "No es posible seleccionar el plan gratuito directamente.")
            return redirect('vista_planes')

        try:
            with transaction.atomic():
                SuscripcionUsuario.objects.filter(empresa=empresa_usuario, activa=True).update(activa=False)

                SuscripcionUsuario.objects.create(
                    empresa=empresa_usuario,
                    plan=plan,
                    fecha_inicio=date.today(),
                    fecha_fin=date.today() + timedelta(days=30), 
                    activa=True
                )
            
            messages.success(request, f"¡Has seleccionado exitosamente el plan {plan.get_nombre_display()}!")
            return redirect('home') 
        
        except Exception as e:
            messages.error(request, f"Ocurrió un error al cambiar de plan: {e}")
            return redirect('vista_planes')

    return redirect('vista_planes')

@cache_page(60 * 15)
@login_required
@plan_requerido('PREMIUM')
def vista_reportes_avanzados(request):
    return render(request, 'inventario/reportes_avanzados.html')

@cache_page(60 * 15)
@login_required
@caracteristica_requerida('soporte_prioritario')
def vista_soporte_premium(request):
    return render(request, 'inventario/soporte_premium.html')

@login_required
def descargar_plantilla_ventas(request):
    from openpyxl import Workbook
    from django.http import HttpResponse
    
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "No se pudo encontrar la empresa asociada a tu cuenta.")
        return redirect('home')

    wb = Workbook()
    ws = wb.active
    ws.title = "Plantilla Ventas"
    ws.append(['sku', 'cantidad'])

    productos = Producto.objects.filter(empresa=empresa_usuario).only('sku')

    for producto in productos:
        ws.append([producto.sku, ''])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=plantilla_ventas.xlsx'
    wb.save(response)
    return response

@login_required
@transaction.atomic
def procesar_ventas_archivo(request):
    import pandas as pd
    from django.db import models
    
    if request.method == 'POST':
        form = ArchivoVentasForm(request.POST, request.FILES)
        if form.is_valid():
            empresa_usuario = obtener_empresa_del_usuario(request.user)
            if not empresa_usuario:
                messages.error(request, "Tu cuenta no está asociada a una empresa.")
                return redirect('procesar_ventas_archivo')

            archivo = request.FILES['archivo_ventas']
            try:
                if archivo.name.endswith('.csv'):
                    df = pd.read_csv(archivo)
                else:
                    df = pd.read_excel(archivo)
            except Exception as e:
                messages.error(request, f"Error al leer el archivo: {e}")
                return redirect('procesar_ventas_archivo')

            errores = []
            sid = transaction.savepoint() 

            for index, row in df.iterrows():
                try:
                    sku = str(row['sku']).strip()
                    cantidad_a_retirar = int(row['cantidad'])

                    if cantidad_a_retirar <= 0:
                        continue

                    producto = Producto.objects.get(sku=sku, empresa=empresa_usuario)
                    
                    lotes_disponibles = LoteProducto.objects.filter(
                        producto=producto, cantidad__gt=0
                    ).order_by('fecha_vencimiento')

                    cantidad_restante = cantidad_a_retirar
                    for lote in lotes_disponibles:
                        if cantidad_restante <= 0:
                            break
                        
                        retiro = min(lote.cantidad, cantidad_restante)
                        lote.cantidad = models.F('cantidad') - retiro
                        lote.save()

                        MovimientoStock.objects.create(
                            lote=lote,
                            producto=producto,
                            cantidad_retirada=retiro,
                            usuario=request.user,
                            nota=f"Descuento por archivo: {archivo.name}"
                        )
                        cantidad_restante -= retiro
                    
                    if cantidad_restante > 0:
                        errores.append(f"Fila {index + 2}: Stock insuficiente para SKU {sku}. Faltaron {cantidad_restante} unidades.")

                except Producto.DoesNotExist:
                    errores.append(f"Fila {index + 2}: Producto con SKU {sku} no encontrado.")
                except Exception as e:
                    errores.append(f"Fila {index + 2}: Error procesando SKU {sku}: {e}")

            if errores:
                transaction.savepoint_rollback(sid)
                for error in errores:
                    messages.error(request, error)
            else:
                transaction.savepoint_commit(sid)
                messages.success(request, "Archivo procesado y stock actualizado correctamente.")
            
            return redirect('inventario')
    else:
        form = ArchivoVentasForm()

    return render(request, 'inventario/procesar_ventas_archivo.html', {'form': form})