from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Min, Sum, Subquery, OuterRef, Count
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse
from datetime import date, timedelta
from django.db import transaction, IntegrityError
from django.utils.timezone import now
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
    PlanSuscripcion, Recordatorio, MovimientoStock, Proveedor
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
    Lista de productos del inventario de la empresa actual.
    Si viene ?sku=, precarga el panel "Gestionar" con ese SKU.

    Flags soportadas (Django messages + highlight de fila):
      - ?created=1&created_sku=XXXXXXXX
      - ?updated=1&sku=XXXXXXXX
      - ?deleted=1&sku=XXXXXXXX
      - ?discounted=1&sku=XXXXXXXX
    Además, si viene ?hl=SKU (o si created_sku está presente), se pasa ese SKU
    al template para que el JS resalte la fila.

    También realiza housekeeping de vencimientos:
      - Elimina lotes con fecha < hoy (vencidos) y muestra alerta.
      - En el template, si el próximo vencimiento es dentro de 15 días,
        se pinta en amarillo; si fuera hoy o anterior, sería rojo, pero
        como los lotes vencidos se eliminan aquí, ya no aparecerán.
    """
    # ------------------------------------------------------------------
    # 0) Empresa del usuario
    # ------------------------------------------------------------------
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return render(request, 'inventario/inventario.html', {
            'productos': Producto.objects.none(),
            'sku': '',
            'producto_sel': None,
            'lotes_sel': LoteProducto.objects.none(),
            'query': '',
            'today': date.today(),
            'hoy_mas_15dias': int(time.mktime((date.today() + timedelta(days=15)).timetuple())),
            'highlight_sku': '',
        })

    # ------------------------------------------------------------------
    # 1) Housekeeping de vencidos (rojo): eliminar y alertar
    # ------------------------------------------------------------------
    hoy = now().date()
    lotes_vencidos_qs = (
        LoteProducto.objects
        .select_related('producto', 'producto__producto')
        .filter(producto__empresa=empresa_usuario, fecha_vencimiento__lt=hoy)
    )

    if lotes_vencidos_qs.exists():
        # Guardamos datos para el mensaje ANTES de borrar
        info_lotes = list(
            lotes_vencidos_qs.values(
                'id',
                'fecha_vencimiento',
                'producto__producto__sku',
                'producto__producto__nombre',
            )
        )

        # Borrado en base de datos
        deleted_count, _ = lotes_vencidos_qs.delete()

        # Armamos un mensaje compacto
        # Mostramos hasta 5 ítems y luego "y N más..."
        detalle = []
        for item in info_lotes[:5]:
            detalle.append(
                f"SKU {item['producto__producto__sku']} · «{item['producto__producto__nombre']}» (lote #{item['id']}, {item['fecha_vencimiento']:%d-%m-%Y})"
            )
        extras = max(0, len(info_lotes) - 5)
        detalle_txt = " | ".join(detalle) + (f" … y {extras} más." if extras else "")

        messages.warning(
            request,
            "Se eliminaron lotes vencidos. Retira los productos vencidos de la vitrina. "
            f"Detalle: {detalle_txt}"
        )

    # ------------------------------------------------------------------
    # 2) Flags de retorno (toasts) + highlight
    # ------------------------------------------------------------------
    created = request.GET.get('created') == '1'
    created_sku = (request.GET.get('created_sku') or '').strip()

    updated = request.GET.get('updated') == '1'
    deleted = request.GET.get('deleted') == '1'
    discounted = request.GET.get('discounted') == '1'
    sku_flag = (request.GET.get('sku') or '').strip()

    # Mensajes
    if created:
        nombre_txt = None
        if created_sku:
            try:
                p = Producto.objects.get(sku=created_sku, empresas=empresa_usuario)
                nombre_txt = p.nombre
            except Producto.DoesNotExist:
                pass
        if nombre_txt:
            messages.success(request, f"¡Producto «{nombre_txt}» ingresado correctamente!")
        elif created_sku:
            messages.success(request, f"¡Producto con SKU {created_sku} ingresado correctamente!")
        else:
            messages.success(request, "¡Producto ingresado correctamente!")

    if updated and sku_flag:
        messages.info(request, f"Producto (SKU {sku_flag}) actualizado.")
    if deleted and sku_flag:
        messages.warning(request, f"Producto (SKU {sku_flag}) eliminado del inventario.")
    if discounted and sku_flag:
        messages.success(request, f"Se descontó stock del producto (SKU {sku_flag}).")

    # SKU a resaltar: ?hl=... o, si no viene, usa created_sku
    highlight_sku = (request.GET.get('hl') or '').strip() or created_sku

    # ------------------------------------------------------------------
    # 3) Base de productos + subconsultas (stock, vencimiento, #lotes)
    # ------------------------------------------------------------------
    productos_base = Producto.objects.filter(empresas=empresa_usuario)

    lotes_empresa = LoteProducto.objects.filter(
        producto__producto=OuterRef('pk'),
        producto__empresa=empresa_usuario,
    )

    subquery_stock = Subquery(
        lotes_empresa.values('producto__producto')
        .annotate(total=Sum('cantidad'))
        .values('total')[:1]
    )
    subquery_vencimiento = Subquery(
        lotes_empresa.values('producto__producto')
        .annotate(proximo=Min('fecha_vencimiento'))
        .values('proximo')[:1]
    )
    subquery_cantidad_lotes = Subquery(
        LoteProducto.objects.filter(
            producto__producto=OuterRef('pk'),
            producto__empresa=empresa_usuario,
        ).values('producto__producto')
         .annotate(count=Count('id'))
         .values('count')[:1]
    )

    productos = productos_base.annotate(
        stock_total=subquery_stock,
        proximo_vencimiento=subquery_vencimiento,
        cantidad_lotes=subquery_cantidad_lotes,
    )

    # ------------------------------------------------------------------
    # 4) Buscador
    # ------------------------------------------------------------------
    query = (request.GET.get('q') or '').strip()
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) |
            Q(sku__icontains=query) |
            Q(marca__icontains=query) |
            Q(categoria__icontains=query)
        ).distinct()
        if not productos.exists():
            messages.info(request, f"No se encontraron resultados para «{query}».")

    # ------------------------------------------------------------------
    # 5) Panel "Gestionar" por SKU
    # ------------------------------------------------------------------
    sku = (request.GET.get('sku') or '').strip()
    producto_sel = None
    lotes_sel = LoteProducto.objects.none()

    if sku:
        try:
            producto_sel = get_object_or_404(Producto, sku=sku, empresas=empresa_usuario)
            oferta_producto = get_object_or_404(OfertaProducto, producto=producto_sel, empresa=empresa_usuario)
            lotes_sel = (
                LoteProducto.objects
                .filter(producto=oferta_producto)
                .select_related('proveedor')
                .order_by('-fecha_vencimiento')
            )
        except Exception:
            messages.error(request, "Producto no encontrado o no autorizado.")
            producto_sel = None
            lotes_sel = LoteProducto.objects.none()

    # ------------------------------------------------------------------
    # 6) Render
    # ------------------------------------------------------------------
    context = {
        'productos': productos,
        'query': query,
        'today': hoy,
        'hoy_mas_15dias': int(time.mktime((hoy + timedelta(days=15)).timetuple())),
        'sku': sku,
        'producto_sel': producto_sel,
        'lotes_sel': lotes_sel,
        'highlight_sku': highlight_sku,
    }
    return render(request, 'inventario/inventario.html', context)

# --- CRUD de Productos ---

# Configurar logger
logger = logging.getLogger(__name__)

@login_required
@transaction.atomic
def agregar_producto(request):
    from django.urls import reverse
    
    """
    Agrega un nuevo producto (o asocia uno existente) al inventario de la
    empresa del usuario. Tras guardar, redirige al inventario con:
      ?created=1&created_sku=<SKU>&hl=<SKU>
    para mostrar el toast y destacar la fila del producto.
    """
    # --- Validaciones iniciales: empresa y suscripción --------------------
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Debes estar asociado a una empresa para agregar productos.")
        return redirect('home')

    try:
        suscripcion = SuscripcionUsuario.objects.get(empresa=empresa_usuario, activa=True)
        productos_actuales = Producto.objects.filter(empresas=empresa_usuario).count()
        # Si el plan limita el número de productos (max_productos != 0)
        if suscripcion.plan.max_productos != 0 and productos_actuales >= suscripcion.plan.max_productos:
            messages.error(
                request,
                f"Has alcanzado el límite de productos para tu plan ({suscripcion.plan.max_productos})."
            )
            return redirect('inventario')
    except SuscripcionUsuario.DoesNotExist:
        messages.error(request, "No tienes una suscripción activa.")
        return redirect('home')
    # ---------------------------------------------------------------------

    if request.method == 'POST':
        form_prod = ProductoForm(request.POST, empresa_usuario=empresa_usuario)

        if form_prod.is_valid():
            sku = form_prod.cleaned_data.get('sku')

            try:
                # 1) Crear o recuperar el Producto por SKU
                producto, creado_producto = Producto.objects.get_or_create(
                    sku=sku,
                    defaults={
                        'nombre': form_prod.cleaned_data.get('nombre'),
                        'marca': form_prod.cleaned_data.get('marca'),
                        'categoria': form_prod.cleaned_data.get('categoria'),
                        'gramage': form_prod.cleaned_data.get('gramage'),
                        'unidad_medida': form_prod.cleaned_data.get('unidad_medida'),
                    }
                )

                # 2) Asociar a la empresa vía OfertaProducto (evita duplicados)
                oferta, creada_oferta = OfertaProducto.objects.get_or_create(
                    producto=producto,
                    empresa=empresa_usuario
                )

                # 3) Mensaje + redirect con highlight siempre que se haya agregado/asociado
                if creada_oferta:
                    accion = "agregado" if creado_producto else "asociado"
                    messages.success(request, f"Producto «{producto.nombre}» {accion} a tu inventario.")
                    url = reverse('inventario') + f"?created=1&created_sku={producto.sku}&hl={producto.sku}"
                    return redirect(url)
                else:
                    # Ya estaba en el inventario de esta empresa
                    messages.info(request, f"El producto «{producto.nombre}» ya estaba en tu inventario.")
                    url = reverse('inventario') + f"?hl={producto.sku}"
                    return redirect(url)

            except IntegrityError:
                messages.error(request, "Ocurrió un problema guardando el producto. Intenta nuevamente.")
                return redirect('inventario')

        # Form inválido: enviar errores a messages
        for field, errors in form_prod.errors.items():
            for error in errors:
                messages.error(request, f"Error en {field}: {error}")
        for error in form_prod.non_field_errors():
            messages.error(request, f"Error general en producto: {error}")

    else:
        # GET
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
@transaction.atomic
def agregar_lote_producto(request):
    from django.urls import reverse
    
    """
    Alta de Lote con preselección por ?sku=…
    - Si viene ?sku=, busca el Producto de la empresa y lo setea como initial en el form.
    - Tras guardar, redirige al hub de inventario con ?sku=…#tab-gestionar
    """
    empresa = obtener_empresa_del_usuario(request.user)
    if not empresa:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('inventario')

    sku = (request.GET.get('sku') or '').strip()
    oferta_seleccionada = None

    if sku:
        # Comprueba que ese producto exista y esté ofrecido por la empresa
        producto = Producto.objects.filter(sku=sku, empresas=empresa).first()
        if producto:
            oferta_seleccionada = OfertaProducto.objects.filter(empresa=empresa, producto=producto).first()

    if request.method == 'POST':
        form = LoteProductoForm(request.POST, empresa_usuario=empresa)
        if form.is_valid():
            lote = form.save()
            messages.success(request, f"Lote para '{lote.producto.producto.nombre}' agregado correctamente.")
            # Redirige al hub de gestionar con el SKU
            try:
                sku_ok = lote.producto.producto.sku
            except Exception:
                sku_ok = sku
            inv = reverse('inventario')
            return redirect(f"{inv}?sku={sku_ok}#tab-gestionar" if sku_ok else inv)
        else:
            messages.error(request, "Revisa los errores del formulario.")
    else:
        initial = {}
        if oferta_seleccionada:
            initial['producto'] = oferta_seleccionada
        form = LoteProductoForm(empresa_usuario=empresa, initial=initial)
        # Si hay oferta seleccionada, podrías restringir el queryset del campo 'producto' a esa oferta:
        if oferta_seleccionada and 'producto' in form.fields:
            form.fields['producto'].queryset = OfertaProducto.objects.filter(pk=oferta_seleccionada.pk)

    return render(request, 'inventario/agregar_lote.html', {
        'form': form,
        'sku_prefill': sku,
        'oferta_seleccionada': oferta_seleccionada,
    })

@login_required
def editar_lote(request, lote_id):
    """
    Edita un lote y, al guardar o cancelar, redirige al hub de inventario con el SKU
    del producto seleccionado en la pestaña 'Gestionar'.
    """
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

            # Redirección Plan B: volver al inventario con el SKU y abrir 'Gestionar'
            from django.urls import reverse
            try:
                sku = lote_actualizado.producto.producto.sku
            except Exception:
                # fallback por si cambia la relación
                sku = getattr(getattr(lote, 'producto', None), 'producto', None)
                sku = getattr(sku, 'sku', '') if sku else ''

            inventario_url = reverse('inventario')
            return redirect(f"{inventario_url}?sku={sku}#tab-gestionar" if sku else inventario_url)
        else:
            # Logs de ayuda + mensaje al usuario
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
    from django.urls import reverse
    
    # Mantén validación de empresa si quieres:
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('inventario')

    sku = (request.GET.get('sku') or '').strip()
    if sku:
        return redirect(f"{reverse('inventario')}?sku={sku}#tab-gestionar")
    return redirect(f"{reverse('inventario')}#tab-gestionar")

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
    return redirect('landing:landing')

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

@login_required
def metrics_view(request):
    from datetime import date, datetime, timedelta
    from decimal import Decimal
    from django.db.models import Q, F, Sum, Count, DecimalField, ExpressionWrapper
    from django.db.models.functions import TruncMonth
    from django.core.serializers.json import DjangoJSONEncoder
    
    # --- Helper: 'YYYY-MM-DD' -> date|None
    def _parse_iso_date(value):
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None

    # ===== 1) Contexto de empresa (aislamiento) =====
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        # Usuario sin empresa asociada: muestra estado vacío (o redirige si prefieres)
        return render(
            request,
            "inventario/metrics.html",
            {
                "f": {"q": "", "categoria": "", "proveedor": "", "desde": "", "hasta": ""},
                "proveedores": [],
                "categorias": [],
                "kpis": {
                    "stock_total": 0,
                    "valor_compra": 0.0,
                    "valor_venta": 0.0,
                    "margen_potencial": 0.0,
                    "vencidos": 0,
                    "proximos": 0,
                    "productos_bajos": 0,
                },
                "top_productos_stock": [],
                "lotes_por_vencer": [],
                "top_proveedores": [],
                "chart_payload_json": "{}",
                "today": date.today(),
            },
        )

    # ===== 2) Filtros =====
    q = (request.GET.get("q") or "").strip()
    categoria = (request.GET.get("categoria") or "").strip()
    proveedor_id = (request.GET.get("proveedor") or "").strip()
    desde = _parse_iso_date(request.GET.get("desde"))
    hasta = _parse_iso_date(request.GET.get("hasta"))
    hoy = date.today()

    # Base: LoteProducto -> OfertaProducto (FK: producto) -> Empresa (FK interno en OfertaProducto)
    lotes = (
        LoteProducto.objects.select_related("producto__producto", "producto__empresa", "proveedor")
        .filter(producto__empresa=empresa)  # <- AISLAMIENTO POR EMPRESA
    )

    if q:
        lotes = lotes.filter(
            Q(producto__producto__sku__icontains=q)
            | Q(producto__producto__nombre__icontains=q)
        )
    if categoria:
        lotes = lotes.filter(producto__producto__categoria=categoria)
    if proveedor_id:
        lotes = lotes.filter(proveedor_id=proveedor_id)
    if desde:
        lotes = lotes.filter(fecha_vencimiento__gte=desde)
    if hasta:
        lotes = lotes.filter(fecha_vencimiento__lte=hasta)

    # ===== 3) KPIs =====
    stock_total = lotes.aggregate(total=Sum("cantidad"))["total"] or 0

    valor_compra = lotes.aggregate(
        total=Sum(
            ExpressionWrapper(
                F("cantidad") * F("precio_compra"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )
    )["total"] or Decimal("0")

    valor_venta = lotes.aggregate(
        total=Sum(
            ExpressionWrapper(
                F("cantidad") * F("precio_venta"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )
    )["total"] or Decimal("0")

    margen_potencial = (valor_venta or 0) - (valor_compra or 0)

    vencidos = lotes.filter(fecha_vencimiento__lt=hoy).count()
    proximos = lotes.filter(
        fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=hoy + timedelta(days=15)
    ).count()

    # Stock bajo por producto (SOLO de esta empresa)
    productos_bajos = (
        Producto.objects.filter(ofertaproducto__empresa=empresa)
        .annotate(
            stock=Sum(
                "ofertaproducto__lotes__cantidad",
                filter=Q(ofertaproducto__empresa=empresa),
            )
        )
        .filter(stock__lte=5)
        .count()
    )

    kpis = {
        "stock_total": int(stock_total),
        "valor_compra": float(valor_compra),
        "valor_venta": float(valor_venta),
        "margen_potencial": float(margen_potencial),
        "vencidos": int(vencidos),
        "proximos": int(proximos),
        "productos_bajos": int(productos_bajos),
    }

    # ===== 4) Tablas =====
    # Top productos por stock
    top_qs = (
        lotes.values(
            prod_id=F("producto__producto__id"),
            nombre=F("producto__producto__nombre"),
            sku=F("producto__producto__sku"),
        )
        .annotate(stock=Sum("cantidad"))
        .order_by("-stock")[:10]
    )
    top_productos_stock = [
        {
            # claves simples
            "prod_id": r["prod_id"],
            "nombre": r["nombre"],
            "sku": r["sku"],
            "stock": r["stock"],
            # compat con tu template actual
            "producto__producto__id": r["prod_id"],
            "producto__producto__nombre": r["nombre"],
            "producto__producto__sku": r["sku"],
            "producto__nombre": r["nombre"],
            "producto__sku": r["sku"],
        }
        for r in top_qs
    ]

    # Próximos a vencer (alias que no chocan con campos reales)
    vencer_qs = (
        lotes.filter(fecha_vencimiento__gte=hoy)
        .order_by("fecha_vencimiento")
        .values(
            "id",
            "fecha_vencimiento",
            "cantidad",
            prod_nombre=F("producto__producto__nombre"),
            prov_nombre=F("proveedor__nombre"),
        )[:10]
    )
    lotes_por_vencer = [
        {
            "id": r["id"],
            "producto": r["prod_nombre"],
            "proveedor": r["prov_nombre"],
            "fecha_vencimiento": r["fecha_vencimiento"],
            "cantidad": r["cantidad"],
            # compat con template
            "producto__producto__nombre": r["prod_nombre"],
            "proveedor__nombre": r["prov_nombre"],
            "producto__nombre": r["prod_nombre"],
        }
        for r in vencer_qs
    ]

    # Proveedores con más unidades (solo los que aparecen en estos lotes)
    top_proveedores = list(
        lotes.values("proveedor__id", "proveedor__nombre")
        .annotate(unidades=Sum("cantidad"), lotes=Count("id"))
        .order_by("-unidades")[:10]
    )

    # ===== 5) Datos para gráficos =====
    stock_por_categoria_qs = (
        lotes.values("producto__producto__categoria")
        .annotate(unidades=Sum("cantidad"))
        .order_by("producto__producto__categoria")
    )
    bar_labels = [
        row["producto__producto__categoria"] or "Sin categoría" for row in stock_por_categoria_qs
    ]
    bar_values = [int(row["unidades"] or 0) for row in stock_por_categoria_qs]

    stock_por_proveedor_qs = (
        lotes.values("proveedor__nombre")
        .annotate(unidades=Sum("cantidad"))
        .order_by("-unidades")[:8]
    )
    pie_labels = [row["proveedor__nombre"] or "Sin proveedor" for row in stock_por_proveedor_qs]
    pie_values = [int(row["unidades"] or 0) for row in stock_por_proveedor_qs]

    cad_por_mes_qs = (
        lotes.annotate(mes=TruncMonth("fecha_vencimiento"))
        .values("mes")
        .annotate(total=Count("id"))
        .order_by("mes")
    )
    line_labels = [(row["mes"].strftime("%Y-%m") if row["mes"] else "Sin fecha") for row in cad_por_mes_qs]
    line_values = [int(row["total"] or 0) for row in cad_por_mes_qs]

    chart_data = {
        "bar_stock_categoria": {"labels": bar_labels, "values": bar_values},
        "pie_stock_proveedor": {"labels": pie_labels, "values": pie_values},
        "line_caducidad_mes": {"labels": line_labels, "values": line_values},
    }
    import json
    chart_payload_json = json.dumps(chart_data, cls=DjangoJSONEncoder)

    # ===== 6) Selects (limitados a la empresa) =====
    proveedores = list(
        lotes.values("proveedor__id", "proveedor__nombre")
        .distinct()
        .order_by("proveedor__nombre")
    )
    # normaliza el shape para el template
    proveedores = [
        {"id": p["proveedor__id"], "nombre": p["proveedor__nombre"] or "No especificado"}
        for p in proveedores
    ]

    categorias = list(
        Producto.objects.filter(ofertaproducto__empresa=empresa)
        .values_list("categoria", flat=True)
        .distinct()
        .order_by("categoria")
    )

    # ===== 7) Render =====
    context = {
        "f": {
            "q": q,
            "categoria": categoria,
            "proveedor": proveedor_id,
            "desde": request.GET.get("desde") or "",
            "hasta": request.GET.get("hasta") or "",
        },
        "proveedores": proveedores,
        "categorias": categorias,
        "kpis": kpis,
        "top_productos_stock": top_productos_stock,
        "lotes_por_vencer": lotes_por_vencer,
        "top_proveedores": top_proveedores,
        "chart_payload_json": chart_payload_json,
        "today": hoy,
    }
    return render(request, "inventario/metrics.html", context)