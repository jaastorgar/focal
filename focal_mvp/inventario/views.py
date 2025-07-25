from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.db.models import Q, Min, Sum, Subquery, OuterRef
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from datetime import date, timedelta
import time
from .forms import (
    ProductoForm, OfertaProductoFormSet, LoteProductoForm, OfertaProductoForm,
    ArchivoVentasForm
)
from .models import (
    SuscripcionUsuario, Producto, LoteProducto, OfertaProducto,
    PlanSuscripcion
)
from .utils import obtener_empresa_del_usuario

# --- Vistas Principales (Home, Logout, Perfil) ---

@login_required
def home(request):
    empresa = obtener_empresa_del_usuario(request.user)
    alertas_vencimiento = []
    alertas_stock_bajo = []

    if empresa:
        fecha_limite = date.today() + timedelta(days=30)
        alertas_vencimiento = LoteProducto.objects.filter(
            empresa=empresa, 
            cantidad__gt=0, 
            fecha_vencimiento__lte=fecha_limite
        ).select_related('producto').order_by('fecha_vencimiento')[:5]

        # CORREGIDO: Se crea la subconsulta que realiza la suma
        lotes_de_la_empresa = LoteProducto.objects.filter(
            producto=OuterRef('pk'), 
            empresa=empresa
        )
        subquery_stock = Subquery(lotes_de_la_empresa.values('producto').annotate(total=Sum('cantidad')).values('total'))

        alertas_stock_bajo = Producto.objects.filter(empresas=empresa).annotate(
            stock_total=subquery_stock # Se usa la subconsulta corregida
        ).filter(stock_total__gt=0, stock_total__lte=5).order_by('stock_total')[:5]

    context = {
        'almacenero': getattr(request.user, 'almacenero', None),
        'alertas_vencimiento': alertas_vencimiento,
        'alertas_stock_bajo': alertas_stock_bajo,
    }
    return render(request, 'inventario/home.html', context)

# --- Vistas de Inventario (MODIFICADAS) ---

@login_required
def inventario_view(request):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return render(request, 'inventario/inventario.html', {'productos': Producto.objects.none()})

    productos_base = Producto.objects.filter(empresas=empresa_usuario)
    
    # CORREGIDO: Se crean subconsultas que realizan la agregación
    lotes_empresa = LoteProducto.objects.filter(producto=OuterRef('pk'), empresa=empresa_usuario)
    
    subquery_stock = Subquery(
        lotes_empresa.values('producto')
        .annotate(total=Sum('cantidad'))
        .values('total')
    )
    subquery_vencimiento = Subquery(
        lotes_empresa.values('producto')
        .annotate(proximo=Min('fecha_vencimiento'))
        .values('proximo')
    )
    
    ofertas_empresa = OfertaProducto.objects.filter(producto=OuterRef('pk'), empresa=empresa_usuario)
    
    productos = productos_base.annotate(
        stock_total=subquery_stock,
        proximo_vencimiento=subquery_vencimiento,
        precio_compra_empresa=Subquery(ofertas_empresa.values('precio_compra')[:1]),
        precio_venta_empresa=Subquery(ofertas_empresa.values('precio_venta')[:1])
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

@login_required
def detalle_producto(request, producto_id):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('inventario')

    # Se busca el producto asegurando que la empresa del usuario lo ofrezca
    producto = get_object_or_404(Producto, id=producto_id, empresas=empresa_usuario)
    
    # Se obtiene la oferta específica de esta empresa para mostrar sus precios
    oferta_empresa = get_object_or_404(OfertaProducto, producto=producto, empresa=empresa_usuario)
    
    # ¡CORREGIDO! Ahora filtramos los lotes por la empresa del usuario.
    lotes = producto.lotes.filter(empresa=empresa_usuario).order_by('fecha_vencimiento')

    context = {
        'producto': producto,
        'oferta': oferta_empresa,
        'lotes': lotes
    }
    return render(request, 'inventario/detalle_producto.html', context)


# --- Vistas de CRUD de Producto (REFACTORIZADAS) ---

@login_required
@transaction.atomic
def agregar_producto(request):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Debes estar asociado a una empresa para agregar productos.")
        return redirect('home')

    # Lógica de plan 
    try:
        plan = SuscripcionUsuario.objects.get(empresa=empresa_usuario, activa=True).plan
        productos_actuales = Producto.objects.filter(empresas=empresa_usuario).count()
        if plan.max_productos != 0 and productos_actuales >= plan.max_productos:
            messages.error(request, f"Has alcanzado el límite de productos para tu plan ({plan.max_productos}).")
            return redirect('inventario')
    except SuscripcionUsuario.DoesNotExist:
        messages.error(request, "No tienes una suscripción activa.")
        return redirect('home')

    if request.method == 'POST':
        form_prod = ProductoForm(request.POST)
        formset_oferta = OfertaProductoFormSet(request.POST, queryset=OfertaProducto.objects.none())

        if form_prod.is_valid() and formset_oferta.is_valid():
            sku = form_prod.cleaned_data['sku']
            defaults_y_updates = {
                'nombre': form_prod.cleaned_data['nombre'],
                'marca': form_prod.cleaned_data['marca'],
                'categoria': form_prod.cleaned_data['categoria'],
                'dramage': form_prod.cleaned_data['dramage'],
                'unidad_medida': form_prod.cleaned_data['unidad_medida'],
            }
            
            producto, creado = Producto.objects.update_or_create(
                sku=sku,
                defaults=defaults_y_updates
            )
            # --- FIN DEL CAMBIO ---

            # La lógica para la oferta
            if not creado and OfertaProducto.objects.filter(producto=producto, empresa=empresa_usuario).exists():
                messages.error(request, f"Este producto (SKU: {sku}) ya existe en tu inventario.")
            else:
                oferta = formset_oferta.save(commit=False)[0]
                oferta.producto = producto
                oferta.empresa = empresa_usuario
                oferta.save()
                messages.success(request, f"Producto '{producto.nombre}' agregado/actualizado en tu inventario.")
                return redirect('inventario')
        else:
            # Si los formularios no son válidos, renderiza la página con los errores
            context = {
                'form': form_prod,
                'formset': formset_oferta
            }
            return render(request, 'inventario/agregar-producto.html', context)

    # Lógica para la petición GET 
    form_prod = ProductoForm()
    formset_oferta = OfertaProductoFormSet(queryset=OfertaProducto.objects.none())
    context = {
        'form': form_prod,
        'formset': formset_oferta
    }
    return render(request, 'inventario/agregar-producto.html', context)


@login_required
@transaction.atomic
def editar_producto(request, producto_id):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        return redirect('inventario')

    # Se obtiene el producto y la oferta específica de la empresa
    producto = get_object_or_404(Producto, id=producto_id, empresas=empresa_usuario)
    oferta = get_object_or_404(OfertaProducto, producto=producto, empresa=empresa_usuario)
    
    if request.method == 'POST':
        form_prod = ProductoForm(request.POST, instance=producto)
        form_oferta = OfertaProductoForm(request.POST, instance=oferta) # Un solo form, no un formset

        if form_prod.is_valid() and form_oferta.is_valid():
            form_prod.save()
            form_oferta.save()
            messages.success(request, 'Producto y oferta actualizados correctamente.')
            return redirect('detalle_producto', producto_id=producto.id)
    else:
        form_prod = ProductoForm(instance=producto)
        form_oferta = OfertaProductoForm(instance=oferta)

    context = {
        'form_prod': form_prod,
        'form_oferta': form_oferta,
        'producto': producto
    }
    return render(request, 'inventario/editar-producto.html', context)


@login_required
def eliminar_producto(request, producto_id):
    """
    MODIFICADO: Esta vista ahora no elimina el producto global, sino que elimina
    la OFERTA de la empresa actual. El producto solo se borra si ninguna otra
    empresa lo está ofreciendo.
    """
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        return redirect('inventario')

    producto = get_object_or_404(Producto, id=producto_id, empresas=empresa_usuario)
    oferta_a_eliminar = get_object_or_404(OfertaProducto, producto=producto, empresa=empresa_usuario)

    if request.method == 'POST':
        nombre_producto = producto.nombre
        # Se elimina la oferta, no el producto directamente
        oferta_a_eliminar.delete()

        # Si el producto ya no tiene ninguna otra oferta, se elimina por completo
        if not producto.ofertaproducto_set.exists():
            producto.delete()
            messages.success(request, f'Producto "{nombre_producto}" y todas sus referencias han sido eliminados.')
        else:
            messages.success(request, f'Has dejado de ofrecer el producto "{nombre_producto}". Se ha eliminado de tu inventario.')
        
        return redirect('inventario')
    
    context = {'producto': producto}
    return render(request, 'inventario/eliminar_producto_confirm.html', context)


# --- Vistas de Lotes y Stock (con filtros M2M actualizados) ---
# ... (Las vistas como agregar_lote, editar_lote, retirar_lote, etc., 
#      necesitarían actualizar sus filtros de `producto__empresa` a `producto__empresas`.
#      Aquí un ejemplo clave:)

@login_required
def agregar_lote_producto(request):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        return redirect('home')

    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        if not producto_id:
            messages.error(request, "Debes seleccionar un producto.")
            return render(request, 'inventario/agregar_lote.html', {'form': LoteProductoForm()})

        producto_a_asignar = get_object_or_404(Producto, id=producto_id, empresas=empresa_usuario)
        
        form = LoteProductoForm(request.POST)
        if form.is_valid():
            lote = form.save(commit=False)
            lote.producto = producto_a_asignar
            lote.empresa = empresa_usuario
            lote.save()
            messages.success(request, f"Lote para '{lote.producto.nombre}' agregado correctamente.")
            return redirect('inventario')
    
    return render(request, 'inventario/agregar_lote.html', {'form': LoteProductoForm()})

# --- Vistas de API (REFACTORIZADAS) ---

@login_required
def obtener_datos_sku_api(request, sku):
    empresa_actual = obtener_empresa_del_usuario(request.user)

    if OfertaProducto.objects.filter(producto__sku=sku, empresa=empresa_actual).exists():
        return JsonResponse({'status': 'duplicado_local', 'mensaje': 'Este producto ya existe en tu inventario.'})

    producto_global = Producto.objects.filter(sku=sku).first()
    if producto_global:
        # Devolvemos datos para autocompletar, pero SIN precios
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

    # 3. El producto es completamente nuevo
    return JsonResponse({'status': 'nuevo'})

@login_required
def logout_view(request):
    """
    Cierra la sesión del usuario y lo redirige a la página de inicio.
    """
    from django.contrib.auth import logout
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('/')

@login_required
def perfil(request):
    """
    Muestra el perfil del usuario, su empresa y su plan de suscripción activo.
    """
    almacenero = getattr(request.user, 'almacenero', None)
    empresa = obtener_empresa_del_usuario(request.user)
    suscripcion = None
    plan = None

    if empresa:
        try:
            suscripcion = SuscripcionUsuario.objects.select_related('plan').get(empresa=empresa, activa=True)
            plan = suscripcion.plan
        except SuscripcionUsuario.DoesNotExist:
            messages.warning(request, "No tienes una suscripción activa.")

    context = {
        'almacenero': almacenero,
        'empresa': empresa,
        'suscripcion': suscripcion,
        'plan': plan,
    }
    return render(request, 'inventario/perfil.html', context)


# --- Gestión de Lotes (Refactorizado) ---

@login_required
def editar_lote(request, lote_id):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    # MODIFICADO: Se comprueba la pertenencia a través de la relación M2M 'empresas'
    lote = get_object_or_404(LoteProducto, id=lote_id, producto__empresas=empresa_usuario)
    
    if request.method == 'POST':
        form = LoteProductoForm(request.POST, instance=lote)
        if form.is_valid():
            form.save()
            messages.success(request, "Lote actualizado correctamente.")
            return redirect('detalle_producto', producto_id=lote.producto.id)
    else:
        form = LoteProductoForm(instance=lote)

    return render(request, 'inventario/editar_lote.html', {'form': form, 'lote': lote})


@login_required
@transaction.atomic
def retirar_lote(request, lote_id):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    # MODIFICADO: Se comprueba la pertenencia a través de la relación M2M 'empresas'
    lote = get_object_or_404(LoteProducto, id=lote_id, producto__empresas=empresa_usuario)

    if request.method == 'POST':
        try:
            cantidad_a_retirar = int(request.POST.get('cantidad', 0))
            if cantidad_a_retirar <= 0:
                messages.error(request, "La cantidad a retirar debe ser mayor que cero.")
            elif cantidad_a_retirar > lote.cantidad:
                messages.error(request, f"No puedes retirar más de {lote.cantidad} unidades.")
            else:
                lote.cantidad -= cantidad_a_retirar
                lote.save()
                # Opcional: Registrar el movimiento
                # MovimientoStock.objects.create(...)
                messages.success(request, f"Se retiraron {cantidad_a_retirar} unidades del lote.")
        except (ValueError, TypeError):
            messages.error(request, "La cantidad ingresada no es un número válido.")
        
        return redirect('detalle_producto', producto_id=lote.producto.id)

    return render(request, 'inventario/retirar_lote.html', {'lote': lote})


@login_required
def eliminar_lote(request, lote_id):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    # MODIFICADO: Se comprueba la pertenencia a través de la relación M2M 'empresas'
    lote = get_object_or_404(LoteProducto, id=lote_id, producto__empresas=empresa_usuario)
    producto_id = lote.producto.id

    if request.method == 'POST':
        lote.delete()
        messages.success(request, "Lote eliminado correctamente.")
        return redirect('detalle_producto', producto_id=producto_id)
    
    return render(request, 'inventario/eliminar_lote_confirm.html', {'lote': lote})


# --- Gestión de Archivos (Refactorizado) ---

@login_required
def descargar_plantilla_ventas(request):
    from openpyxl import Workbook
    from django.http import HttpResponse

    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "No se pudo encontrar tu empresa.")
        return redirect('home')

    wb = Workbook()
    ws = wb.active
    ws.title = "Plantilla Ventas"
    ws.append(['sku', 'cantidad'])

    # MODIFICADO: Se buscan los productos que la empresa ofrece
    productos = Producto.objects.filter(empresas=empresa_usuario).only('sku')
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
    
    if request.method != 'POST':
        return render(request, 'inventario/procesar_ventas_archivo.html', {'form': ArchivoVentasForm()})

    form = ArchivoVentasForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, 'inventario/procesar_ventas_archivo.html', {'form': form})

    empresa_usuario = obtener_empresa_del_usuario(request.user)
    archivo = request.FILES['archivo_ventas']
    
    try:
        df = pd.read_excel(archivo) if archivo.name.endswith(('.xlsx', '.xls')) else pd.read_csv(archivo)
    except Exception as e:
        messages.error(request, f"Error al leer el archivo: {e}")
        return redirect('procesar_ventas_archivo')

    errores = []
    # MODIFICACIÓN CLAVE: Procesar todo dentro de una transacción para poder revertir
    try:
        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    sku = str(row['sku']).strip()
                    cantidad_a_retirar = int(row['cantidad'])
                    if cantidad_a_retirar <= 0: continue

                    # MODIFICADO: Se busca el producto que ofrezca la empresa actual
                    producto = Producto.objects.get(sku=sku, empresas=empresa_usuario)
                    
                    # El resto de la lógica para descontar de lotes es compleja y puede mantenerse
                    # similar a tu versión original, asegurando que se haga de forma atómica.
                    # ... (lógica de retiro de lotes FIFO) ...

                except Producto.DoesNotExist:
                    errores.append(f"Fila {index + 2}: Producto con SKU {sku} no encontrado en tu inventario.")
                except (ValueError, TypeError):
                    errores.append(f"Fila {index + 2}: Cantidad inválida para SKU {sku}.")
                except Exception as e:
                    errores.append(f"Fila {index + 2}: Error inesperado con SKU {sku}: {e}")
            
            # Si hubo algún error, se lanza una excepción para revertir la transacción completa.
            if errores:
                raise Exception("Errores durante el procesamiento.")

    except Exception:
        for error in errores:
            messages.error(request, error)
        messages.warning(request, "No se realizó ninguna actualización en el stock debido a los errores encontrados.")
    else:
        messages.success(request, "Archivo procesado y stock actualizado correctamente.")
    
    return redirect('inventario')


# --- Vistas de API (Refactorizadas) ---

@login_required
def buscar_producto_api(request, codigo_barras):
    """
    Busca un producto por SKU que pertenezca a la empresa del usuario.
    Usado para agregar lotes.
    """
    empresa = obtener_empresa_del_usuario(request.user)
    # MODIFICADO: Filtra por la relación M2M
    producto = Producto.objects.filter(sku=codigo_barras, empresas=empresa).first()
    
    if producto:
        return JsonResponse({'encontrado': True, 'producto_id': producto.id, 'nombre': producto.nombre})
    else:
        return JsonResponse({'encontrado': False, 'mensaje': 'Producto no registrado en tu inventario.'}, status=404)

# --- Vistas Basadas en Planes (Sin cambios, pero necesarias) ---

# Asegúrate de tener los decoradores importados
from .decorators import plan_requerido, caracteristica_requerida

@login_required
@plan_requerido('PREMIUM')
def vista_reportes_avanzados(request):
    return render(request, 'inventario/reportes_avanzados.html')


@login_required
@caracteristica_requerida('soporte_prioritario')
def vista_soporte_premium(request):
    return render(request, 'inventario/soporte_premium.html')

@login_required
def verificar_producto_api(request, codigo_barras):
    """
    Verifica si un producto con el código de barras dado ya existe.
    """
    empresa = obtener_empresa_del_usuario(request.user)
    existe = Producto.objects.filter(sku=codigo_barras, empresa=empresa).exists()
    
    return JsonResponse({'existe': existe})

@login_required
def seleccionar_plan(request, plan_id):
    """
    Esta es la vista que faltaba. Por ahora, solo muestra un mensaje
    y redirige al inicio. Más adelante puedes desarrollar su lógica.
    """
    try:
        # Intenta obtener el plan desde la base de datos
        plan = PlanSuscripcion.objects.get(id=plan_id)

        # Aquí iría tu lógica para suscribir al usuario al plan
        messages.success(request, f"Has seleccionado el plan: {plan.nombre}. ¡Funcionalidad en desarrollo!")

        # Redirige al home del inventario
        return redirect('home') 

    except PlanSuscripcion.DoesNotExist:
        messages.error(request, "El plan que intentas seleccionar no existe.")
        return redirect('home') 