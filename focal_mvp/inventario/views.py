from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.db.models import Q, Min, Sum, Subquery, OuterRef, Count
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse
from datetime import date, timedelta
import time
import logging
from .forms import (
    ProductoForm, 
    LoteProductoForm, 
    OfertaProductoForm,
    ProveedorForm,
    RecordatorioForm
)

# Se importan los modelos correctos
from .models import (
    SuscripcionUsuario, Producto, LoteProducto, OfertaProducto,
    PlanSuscripcion, Recordatorio, MovimientoStock
)
from .utils import obtener_empresa_del_usuario

# --- Vistas del Panel Principal ---

@login_required
def home(request):
    """
    Muestra el panel principal con alertas de vencimiento y stock bajo
    para la empresa del usuario actual.
    """
    empresa = obtener_empresa_del_usuario(request.user)
    alertas_vencimiento = []
    alertas_stock_bajo = []

    if empresa:
        fecha_limite = date.today() + timedelta(days=30)
        alertas_vencimiento = LoteProducto.objects.filter(
            producto__empresa=empresa,
            cantidad__gt=0,
            fecha_vencimiento__lte=fecha_limite
        ).select_related('producto__producto').order_by('fecha_vencimiento')[:5]

        lotes_de_la_empresa = LoteProducto.objects.filter(
            producto__producto=OuterRef('pk'),
            producto__empresa=empresa
        )
        subquery_stock = Subquery(
            lotes_de_la_empresa.values('producto__producto')
            .annotate(total=Sum('cantidad'))
            .values('total')
        )
        alertas_stock_bajo = Producto.objects.filter(empresas=empresa).annotate(
            stock_total=subquery_stock
        ).filter(stock_total__gt=0, stock_total__lte=5).order_by('stock_total')[:5]

    context = {
        'almacenero': request.user,
        'alertas_vencimiento': alertas_vencimiento,
        'alertas_stock_bajo': alertas_stock_bajo,
    }
    return render(request, 'inventario/home.html', context)

@login_required
def inventario_view(request):
    """
    Muestra la lista de productos del inventario de la empresa actual.
    """
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return render(request, 'inventario/inventario.html', {'productos': Producto.objects.none()})

    productos_base = Producto.objects.filter(empresas=empresa_usuario)

    lotes_empresa = LoteProducto.objects.filter(
        producto__producto=OuterRef('pk'),
        producto__empresa=empresa_usuario
    )

    subquery_stock = Subquery(
        lotes_empresa.values('producto__producto').annotate(total=Sum('cantidad')).values('total')
    )

    subquery_vencimiento = Subquery(
        lotes_empresa.values('producto__producto').annotate(proximo=Min('fecha_vencimiento')).values('proximo')
    )

    subquery_cantidad_lotes = Subquery(
        LoteProducto.objects.filter(
            producto__producto=OuterRef('pk'),  
            producto__empresa=empresa_usuario
        ).values('producto__producto') 
         .annotate(count=Count('id'))  
         .values('count')  
    )
    # =============================================================

    # Subconsultas para precios - AHORA USANDO PROPIEDADES DINÁMICAS
    ofertas_empresa = OfertaProducto.objects.filter(producto=OuterRef('pk'), empresa=empresa_usuario)

    productos = productos_base.annotate(
        stock_total=subquery_stock,
        proximo_vencimiento=subquery_vencimiento,
        cantidad_lotes=subquery_cantidad_lotes 
    )

    query = request.GET.get('q')
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) | Q(sku__icontains=query) |
            Q(marca__icontains=query) | Q(categoria__icontains=query)
        ).distinct()

    context = {
        'productos': productos,
        'query': query,
        'today': date.today(),
        'hoy_mas_15dias': int(time.mktime((date.today() + timedelta(days=15)).timetuple())),
    }
    return render(request, 'inventario/inventario.html', context)

# --- CRUD de Productos ---

# Configurar logger
logger = logging.getLogger(__name__)

@login_required
@transaction.atomic
def agregar_producto(request):
    """
    Vista para agregar un nuevo producto al inventario de la empresa del usuario.
    """
    # --- Esta parte inicial de validaciones de empresa y suscripción es correcta y se mantiene ---
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Debes estar asociado a una empresa para agregar productos.")
        return redirect('home')

    try:
        suscripcion = SuscripcionUsuario.objects.get(empresa=empresa_usuario, activa=True)
        productos_actuales = Producto.objects.filter(empresas=empresa_usuario).count()
        if suscripcion.plan.max_productos != 0 and productos_actuales >= suscripcion.plan.max_productos:
            messages.error(request, f"Has alcanzado el límite de productos para tu plan ({suscripcion.plan.max_productos}).")
            return redirect('inventario')
    except SuscripcionUsuario.DoesNotExist:
        messages.error(request, "No tienes una suscripción activa.")
        return redirect('home')
    # --- Fin de las validaciones iniciales ---

    if request.method == 'POST':
        form_prod = ProductoForm(request.POST, empresa_usuario=empresa_usuario)
        
        if form_prod.is_valid():
            
            sku = form_prod.cleaned_data.get('sku')
            
            producto, creado = Producto.objects.get_or_create(
                sku=sku,
                defaults={
                    'nombre': form_prod.cleaned_data.get('nombre'),
                    'marca': form_prod.cleaned_data.get('marca'),
                    'categoria': form_prod.cleaned_data.get('categoria'),
                    'dramage': form_prod.cleaned_data.get('dramage'),
                    'unidad_medida': form_prod.cleaned_data.get('unidad_medida'),
                }
            )
            
            # Finalmente, creamos la relación entre el producto (nuevo o existente) y la empresa.
            OfertaProducto.objects.create(
                producto=producto,
                empresa=empresa_usuario
            )

            accion = "agregado" if creado else "asociado"
            messages.success(request, f"Producto '{producto.nombre}' {accion} a tu inventario.")
            return redirect('inventario')
        else:
            # Mostrar errores en los mensajes de Django
            for field, errors in form_prod.errors.items():
                for error in errors:
                    messages.error(request, f"Error en {field}: {error}")
            
            for error in form_prod.non_field_errors():
                messages.error(request, f"Error general en producto: {error}")

    else: # GET request
        form_prod = ProductoForm(empresa_usuario=empresa_usuario)

    context = {
        'form_prod': form_prod,
    }
    return render(request, 'inventario/agregar-producto.html', context)

@login_required
@transaction.atomic
def editar_producto(request, producto_id):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    producto = get_object_or_404(Producto, id=producto_id, empresas=empresa_usuario)
    oferta = get_object_or_404(OfertaProducto, producto=producto, empresa=empresa_usuario)

    if request.method == 'POST':
        form_prod = ProductoForm(request.POST, instance=producto)
        form_oferta = OfertaProductoForm(request.POST, instance=oferta)
        if form_prod.is_valid() and form_oferta.is_valid():
            form_prod.save()
            form_oferta.save()
            messages.success(request, 'Producto y oferta actualizados correctamente.')
            return redirect('detalle_producto', producto_id=producto.id)
    else:
        form_prod = ProductoForm(instance=producto)
        form_oferta = OfertaProductoForm(instance=oferta)

    context = {'form_prod': form_prod, 'form_oferta': form_oferta, 'producto': producto}
    return render(request, 'inventario/editar-producto.html', context)

@login_required
def eliminar_producto(request, producto_id):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    producto = get_object_or_404(Producto, id=producto_id, empresas=empresa_usuario)

    if request.method == 'POST':
        nombre_producto = producto.nombre
        oferta_a_eliminar = get_object_or_404(OfertaProducto, producto=producto, empresa=empresa_usuario)
        oferta_a_eliminar.delete()

        if not producto.ofertaproducto_set.exists():
            producto.delete()
            messages.success(request, f'Producto "{nombre_producto}" y todas sus referencias han sido eliminados.')
        else:
            messages.success(request, f'Has dejado de ofrecer el producto "{nombre_producto}".')

        return redirect('inventario')

    context = {'producto': producto}
    return render(request, 'inventario/eliminar_producto_confirm.html', context)

# --- CRUD de Lotes ---

@login_required
def detalle_producto(request, producto_id):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    producto = get_object_or_404(Producto, id=producto_id, empresas=empresa_usuario)
    oferta_empresa = get_object_or_404(OfertaProducto, producto=producto, empresa=empresa_usuario)
    lotes = LoteProducto.objects.filter(producto=oferta_empresa).order_by('fecha_vencimiento')

    context = {'producto': producto, 'oferta': oferta_empresa, 'lotes': lotes}
    return render(request, 'inventario/detalle_producto.html', context)

@login_required
def agregar_lote_producto(request):
    """
    Vista para agregar un nuevo lote de producto.
    """
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('inventario')

    if request.method == 'POST':
        # === PASAR empresa_usuario AL FORMULARIO ===
        form = LoteProductoForm(request.POST, empresa_usuario=empresa_usuario)
        # =========================================

        if form.is_valid():
            lote = form.save()
            messages.success(request, f"Lote para '{lote.producto.producto.nombre}' agregado.")
            return redirect('inventario')
        else:
            # Para debugging - puedes remover después
            print("Form errors:", form.errors)
            print("Form data:", request.POST)
    else:
        # === PASAR empresa_usuario AL FORMULARIO PARA GET ===
        form = LoteProductoForm(empresa_usuario=empresa_usuario)
        # ==================================================

    context = {'form': form}
    return render(request, 'inventario/agregar_lote.html', context)

@login_required
def editar_lote(request, lote_id):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    lote = get_object_or_404(
        LoteProducto.objects.select_related('producto__producto', 'proveedor'),
        id=lote_id,
        producto__empresa=empresa_usuario
    )

    if request.method == 'POST':
        form = LoteProductoForm(request.POST, instance=lote, empresa_usuario=empresa_usuario)
        if form.is_valid():
            lote_actualizado = form.save()
            messages.success(request, "Lote actualizado correctamente.")
            return redirect('inventario', producto_id=lote_actualizado.producto.producto.id)
        else:
            print("Form errors (editar_lote):", form.errors)
            print("Form non-field errors:", form.non_field_errors())
            print("Form data:", request.POST)
            messages.error(request, "Por favor, corrige los errores en el formulario.")
    else:
        form = LoteProductoForm(instance=lote, empresa_usuario=empresa_usuario)

    return render(request, 'inventario/editar_lote.html', {'form': form, 'lote': lote})

@login_required
@transaction.atomic
def retirar_lote(request, lote_id):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    lote = get_object_or_404(LoteProducto, id=lote_id, producto__empresa=empresa_usuario)

    if request.method == 'POST':
        try:
            cantidad_a_retirar = int(request.POST.get('cantidad', 0))
            if 0 < cantidad_a_retirar <= lote.cantidad:
                lote.cantidad -= cantidad_a_retirar
                lote.save()
                messages.success(request, f"Se retiraron {cantidad_a_retirar} unidades del lote.")
            else:
                messages.error(request, "La cantidad a retirar es inválida.")
        except (ValueError, TypeError):
            messages.error(request, "La cantidad ingresada no es un número válido.")

        return redirect('detalle_producto', producto_id=lote.producto.producto.id)

    return render(request, 'inventario/retirar_lote.html', {'lote': lote})

@login_required
def eliminar_lote(request, lote_id):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    lote = get_object_or_404(LoteProducto, id=lote_id, producto__empresa=empresa_usuario)
    producto_id = lote.producto.producto.id

    if request.method == 'POST':
        lote.delete()
        messages.success(request, "Lote eliminado correctamente.")
        return redirect('detalle_producto', producto_id=producto_id)

    return render(request, 'inventario/eliminar_lote_confirm.html', {'lote': lote})

@login_required
def gestionar_proveedores_precios(request):
    from django.http import Http404
    
    """
    Muestra la página para gestionar proveedores y precios.
    Puede funcionar sin un producto seleccionado inicialmente.
    """
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('inventario')

    # Obtener el SKU de la solicitud GET
    sku = request.GET.get('sku')
    producto = None
    lotes = LoteProducto.objects.none()

    if sku:
        try:
            # Buscar el producto por SKU
            producto = get_object_or_404(Producto, sku=sku, empresas=empresa_usuario)
            oferta_producto = get_object_or_404(OfertaProducto, producto=producto, empresa=empresa_usuario)
            lotes = LoteProducto.objects.filter(producto=oferta_producto).order_by('-fecha_vencimiento')
        except Http404:
            messages.error(request, "Producto no encontrado o no autorizado.")

    context = {
        'producto': producto,
        'lotes': lotes,
    }
    return render(request, 'inventario/gestionar_proveedores_precios.html', context)

@login_required
def agregar_proveedor(request):
    """
    Vista para agregar un nuevo proveedor.
    """
    
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            proveedor = form.save()
            messages.success(request, f"Proveedor '{proveedor.nombre}' agregado exitosamente.")
            return redirect('gestionar_proveedores_precios')
    else:
        form = ProveedorForm()
    
    context = {
        'form': form,
    }
    return render(request, 'inventario/agregar_proveedor.html', context)

# --- Vistas de Utilidades, Perfil y Sesión ---

@login_required
def perfil(request):
    from .models import Almacenero
    """
    Muestra el perfil del usuario, su empresa y su plan de suscripción activo,
    optimizando la consulta a la base de datos.
    """
    # Usamos select_related para traer la empresa, la suscripción y el plan
    # en una sola consulta eficiente desde el objeto del usuario.
    try:
        almacenero = Almacenero.objects.select_related(
            'empresa',
            'empresa__suscripcion',
            'empresa__suscripcion__plan'
        ).get(id=request.user.id)
        empresa = almacenero.empresa
        suscripcion = getattr(empresa, 'suscripcion', None)
        plan = getattr(suscripcion, 'plan', None)
    except Almacenero.DoesNotExist:
        almacenero = request.user
        empresa = None
        suscripcion = None
        plan = None

    context = {
        'almacenero': almacenero,
        'empresa': empresa,
        'suscripcion': suscripcion,
        'plan': plan
    }
    return render(request, 'inventario/perfil.html', context)


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('landing')

# --- Vistas de API ---

@login_required
def obtener_datos_sku_api(request, sku):
    empresa_actual = obtener_empresa_del_usuario(request.user)
    if OfertaProducto.objects.filter(producto__sku=sku, empresa=empresa_actual).exists():
        return JsonResponse({'status': 'duplicado_local', 'mensaje': 'Este producto ya existe en tu inventario.'})

    producto_global = Producto.objects.filter(sku=sku).first()
    if producto_global:
        data = {
            'status': 'encontrado_global',
            'datos': {
                'nombre': producto_global.nombre,
                'sku': producto_global.sku,
                'marca': producto_global.marca,
                'categoria': producto_global.categoria,
                'dramage': producto_global.dramage,
                'unidad_medida': producto_global.unidad_medida,
            }
        }
        return JsonResponse(data)
    return JsonResponse({'status': 'nuevo'})

@login_required
def buscar_producto_api(request, codigo_barras):
    empresa = obtener_empresa_del_usuario(request.user)
    oferta = OfertaProducto.objects.filter(
        producto__sku=codigo_barras,
        empresa=empresa
    ).select_related('producto').first()
    if oferta:
        data = {
            'encontrado': True,
            'oferta_id': oferta.id,
            'nombre': oferta.producto.nombre
        }
        return JsonResponse(data)
    else:
        return JsonResponse({
            'encontrado': False,
            'mensaje': 'Producto no registrado en tu inventario.'
        }, status=404)


@login_required
def verificar_producto_api(request, codigo_barras):
    """
    Verifica si una oferta para un producto con el SKU dado ya existe para la empresa del usuario.
    """
    empresa = obtener_empresa_del_usuario(request.user)
    existe = OfertaProducto.objects.filter(producto__sku=codigo_barras, empresa=empresa).exists()
    return JsonResponse({'existe': existe})


# --- Vistas de Gestión de Archivos y Planes ---

@login_required
def descargar_plantilla_ventas(request):
    from openpyxl import Workbook
    from django.http import HttpResponse

    wb = Workbook()
    ws = wb.active
    ws.title = "Plantilla Ventas"
    ws.append(['sku', 'cantidad'])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=plantilla_ventas.xlsx'
    wb.save(response)
    return response

@login_required
def seleccionar_plan(request, plan_id):
    empresa = obtener_empresa_del_usuario(request.user)
    plan = get_object_or_404(PlanSuscripcion, id=plan_id)

    if not empresa:
        messages.error(request, "No estás asociado a ninguna empresa para seleccionar un plan.")
        return redirect('planes')

    try:
        with transaction.atomic():
            SuscripcionUsuario.objects.filter(empresa=empresa, activa=True).update(activa=False)
            SuscripcionUsuario.objects.create(empresa=empresa, plan=plan, activa=True)
        messages.success(request, f"Has cambiado exitosamente al plan {plan.nombre}.")
    except Exception as e:
        messages.error(request, f"Ocurrió un error al cambiar de plan: {e}")

    return redirect('home')

@login_required
def lista_recordatorios(request):
    """Muestra la lista de recordatorios de la empresa"""
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('home')
    
    recordatorios = Recordatorio.objects.filter(empresa=empresa_usuario).order_by('proxima_fecha_ejecucion')
    
    # Filtrar por estado
    estado = request.GET.get('estado')
    if estado == 'vencido':
        recordatorios = recordatorios.filter(proxima_fecha_ejecucion__lt=date.today())
    elif estado == 'proxima':
        hoy = date.today()
        limite = hoy + timedelta(days=5)  # 5 días de anticipación por defecto
        recordatorios = recordatorios.filter(
            proxima_fecha_ejecucion__gte=hoy,
            proxima_fecha_ejecucion__lte=limite
        )
    elif estado == 'normal':
        hoy = date.today()
        limite = hoy + timedelta(days=5)
        recordatorios = recordatorios.filter(proxima_fecha_ejecucion__gt=limite)
    
    context = {
        'recordatorios': recordatorios,
        'estado_filtro': estado,
        'today': date.today(),
    }
    return render(request, 'inventario/lista_recordatorios.html', context)

@login_required
def agregar_recordatorio(request):
    """Agrega un nuevo recordatorio"""
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('home')
    
    if request.method == 'POST':
        form = RecordatorioForm(request.POST)
        if form.is_valid():
            recordatorio = form.save(commit=False)
            recordatorio.empresa = empresa_usuario
            recordatorio.save()
            messages.success(request, f"Recordatorio '{recordatorio.nombre}' agregado correctamente.")
            return redirect('lista_recordatorios')
    else:
        form = RecordatorioForm()
    
    context = {'form': form}
    return render(request, 'inventario/agregar_recordatorio.html', context)

@login_required
def editar_recordatorio(request, recordatorio_id):
    """Edita un recordatorio existente"""
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    recordatorio = get_object_or_404(Recordatorio, id=recordatorio_id, empresa=empresa_usuario)
    
    if request.method == 'POST':
        form = RecordatorioForm(request.POST, instance=recordatorio)
        if form.is_valid():
            recordatorio = form.save()
            messages.success(request, f"Recordatorio '{recordatorio.nombre}' actualizado correctamente.")
            return redirect('lista_recordatorios')
    else:
        form = RecordatorioForm(instance=recordatorio)
    
    context = {'form': form, 'recordatorio': recordatorio}
    return render(request, 'inventario/editar_recordatorio.html', context)

@login_required
def eliminar_recordatorio(request, recordatorio_id):
    """Elimina un recordatorio"""
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    recordatorio = get_object_or_404(Recordatorio, id=recordatorio_id, empresa=empresa_usuario)
    
    if request.method == 'POST':
        nombre_recordatorio = recordatorio.nombre
        recordatorio.delete()
        messages.success(request, f"Recordatorio '{nombre_recordatorio}' eliminado correctamente.")
        return redirect('lista_recordatorios')
    
    context = {'recordatorio': recordatorio}
    return render(request, 'inventario/eliminar_recordatorio_confirm.html', context)

@login_required
def completar_recordatorio(request, recordatorio_id):
    """Marca un recordatorio como completado y calcula la próxima fecha"""
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    recordatorio = get_object_or_404(Recordatorio, id=recordatorio_id, empresa=empresa_usuario)
    
    if request.method == 'POST':
        recordatorio.fecha_ultima_ejecucion = date.today()
        recordatorio.proxima_fecha_ejecucion = recordatorio.calcular_proxima_fecha()
        recordatorio.save()
        messages.success(request, f"Recordatorio '{recordatorio.nombre}' marcado como completado.")
        return redirect('lista_recordatorios')
    
    context = {'recordatorio': recordatorio}
    return render(request, 'inventario/completar_recordatorio_confirm.html', context)

@login_required
def descontar_producto_view(request):
    """
    Vista para descontar productos del inventario usando lector de código de barras o entrada manual.
    """
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('home')

    if request.method == 'POST':
        sku = request.POST.get('sku', '').strip()
        cantidad_a_descontar = request.POST.get('cantidad', '').strip()

        if not sku:
            messages.error(request, "Debes ingresar o escanear un código de barras (SKU).")
            return render(request, 'inventario/descontar_producto.html')

        if not cantidad_a_descontar:
            messages.error(request, "Debes ingresar la cantidad a descontar.")
            return render(request, 'inventario/descontar_producto.html')

        try:
            cantidad_a_descontar = int(cantidad_a_descontar)
            if cantidad_a_descontar <= 0:
                raise ValueError("La cantidad debe ser un número positivo.")
        except ValueError:
            messages.error(request, "La cantidad debe ser un número entero positivo.")
            return render(request, 'inventario/descontar_producto.html')

        try:
            with transaction.atomic():
                # 1. Buscar el producto global por SKU
                producto = get_object_or_404(Producto, sku=sku)
                
                # 2. Verificar que el producto esté en el inventario de la empresa
                oferta_producto = get_object_or_404(OfertaProducto, producto=producto, empresa=empresa_usuario)
                
                # 3. Buscar lotes disponibles con stock (FIFO - First In, First Out)
                lotes_disponibles = LoteProducto.objects.filter(
                    producto=oferta_producto,
                    cantidad__gt=0
                ).order_by('fecha_vencimiento')  # Ordenar por fecha de vencimiento ascendente

                if not lotes_disponibles.exists():
                    messages.error(request, f"No hay stock disponible para el producto '{producto.nombre}'.")
                    return render(request, 'inventario/descontar_producto.html')

                # 4. === LÓGICA DE DESCONTEO CON ELIMINACIÓN AUTOMÁTICA ===
                cantidad_restante = cantidad_a_descontar
                lotes_afectados = []
                movimientos_creados = []
                lotes_eliminados = []

                for lote in lotes_disponibles:
                    if cantidad_restante <= 0:
                        break
                    
                    # Determinar cuánto se puede descontar de este lote
                    descuento = min(lote.cantidad, cantidad_restante)
                    
                    # Registrar movimiento de stock ANTES de modificar el lote
                    movimiento = MovimientoStock.objects.create(
                        lote=lote,
                        cantidad=descuento,
                        tipo='SALIDA',
                        descripcion=f"Descontado automáticamente por venta/salida. Solicitado por {request.user.email}"
                    )
                    movimientos_creados.append(movimiento)
                    
                    # Actualizar el lote
                    lote.cantidad -= descuento
                    lote.save()
                    lotes_afectados.append(lote)
                    
                    # === NUEVO: Eliminar lote si la cantidad llega a 0 ===
                    if lote.cantidad == 0:
                        lote_id = lote.id
                        lote.delete() # Elimina el lote automáticamente
                        lotes_eliminados.append(lote_id)
                        messages.info(request, f"Lote #{lote_id} de {producto.nombre} agotado y eliminado.")
                    # ===================================================

                    cantidad_restante -= descuento

                # 5. Verificar si se descontó todo
                if cantidad_restante > 0:
                    messages.warning(
                        request, 
                        f"Stock parcialmente descontado. Solo se pudieron descontar {cantidad_a_descontar - cantidad_restante} de {cantidad_a_descontar} unidades de '{producto.nombre}'."
                    )
                else:
                    mensaje_exito = f"Se han descontado {cantidad_a_descontar} unidades de '{producto.nombre}' correctamente."
                    if lotes_eliminados:
                        mensaje_exito += f" ({len(lotes_eliminados)} lote(s) agotado(s) y eliminado(s))."
                    messages.success(request, mensaje_exito)

                return redirect('inventario')
                
        except Exception as e:
            messages.error(request, f"Error al descontar el producto: {str(e)}")
            return render(request, 'inventario/descontar_producto.html')

    # Para solicitudes GET, mostrar el formulario vacío
    context = {}
    return render(request, 'inventario/descontar_producto.html', context)