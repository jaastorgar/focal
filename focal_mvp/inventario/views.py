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
    RecordatorioForm,
    AlmaceneroProfileForm,
    PlanSelectForm,
    EmpresaForm
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
    Además, el banner de bienvenida se muestra solo una vez por sesión.
    """
    empresa = obtener_empresa_del_usuario(request.user)
    alertas_vencimiento = []
    alertas_stock_bajo = []

    # --- Banner de bienvenida: solo una vez por sesión ---
    show_welcome = not request.session.get('saw_welcome_banner', False)
    if show_welcome:
        request.session['saw_welcome_banner'] = True

    # Nombre a mostrar
    display_name = (
        getattr(request.user, "nombres", None)
        or request.user.first_name
        or request.user.username
    )

    if empresa:
        fecha_limite = date.today() + timedelta(days=30)
        alertas_vencimiento = (
            LoteProducto.objects
            .filter(producto__empresa=empresa, cantidad__gt=0, fecha_vencimiento__lte=fecha_limite)
            .select_related('producto__producto')
            .order_by('fecha_vencimiento')[:5]
        )

        lotes_de_la_empresa = LoteProducto.objects.filter(
            producto__producto=OuterRef('pk'),
            producto__empresa=empresa
        )
        subquery_stock = Subquery(
            lotes_de_la_empresa.values('producto__producto')
            .annotate(total=Sum('cantidad'))
            .values('total')
        )
        alertas_stock_bajo = (
            Producto.objects.filter(empresas=empresa)
            .annotate(stock_total=subquery_stock)
            .filter(stock_total__gt=0, stock_total__lte=5)
            .order_by('stock_total')[:5]
        )

    context = {
        'almacenero': request.user,
        'display_name': display_name,
        'show_welcome': show_welcome,
        'alertas_vencimiento': alertas_vencimiento,
        'alertas_stock_bajo': alertas_stock_bajo,
    }
    return render(request, 'inventario/home.html', context)

@login_required
def inventario_view(request):
    """
    Lista de productos del inventario de la empresa actual.
    Si viene ?sku=, precarga el panel "Gestionar" con ese SKU.

    - Pinta en amarillo los productos cuyo lote más próximo vence en ≤15 días.
    - Elimina los lotes ya vencidos y muestra alerta.
    - Agrega alerta general si existen productos próximos a vencer.
    - 🧠 Anota en cada producto si su OfertaProducto vende por peso (sell_by_weight),
      más price_per_kg y min_step_grams para lógica de interfaz.
    """
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return render(request, 'inventario/inventario.html', {
            'productos': Producto.objects.none(),
            'query': '',
            'today': now().date(),
            'hoy_mas_15dias': int(time.mktime((now().date() + timedelta(days=15)).timetuple())),
            'highlight_sku': '',
        })

    hoy = now().date()
    hoy_mas_15 = hoy + timedelta(days=15)

    # --- 1) Lotes vencidos: eliminar y alertar ---
    lotes_vencidos = (
        LoteProducto.objects
        .select_related('producto', 'producto__producto')
        .filter(producto__empresa=empresa_usuario, fecha_vencimiento__lt=hoy)
    )
    if lotes_vencidos.exists():
        info_lotes = list(lotes_vencidos.values(
            'id', 'fecha_vencimiento', 'producto__producto__sku', 'producto__producto__nombre'
        ))
        deleted_count, _ = lotes_vencidos.delete()
        detalle = " | ".join([
            f"{l['producto__producto__nombre']} ({l['producto__producto__sku']})"
            for l in info_lotes[:5]
        ])
        extras = max(0, len(info_lotes) - 5)
        if extras:
            detalle += f" … y {extras} más."
        messages.warning(request, f"Se eliminaron {deleted_count} lotes vencidos: {detalle}")

    # --- 2) Subconsultas de lotes (stock, vencimiento, cantidad) ---
    productos_base = Producto.objects.filter(empresas=empresa_usuario)

    lotes_empresa = LoteProducto.objects.filter(
        producto__producto=OuterRef('pk'),
        producto__empresa=empresa_usuario
    )
    subquery_stock = Subquery(
        lotes_empresa.values('producto__producto')
        .annotate(total=Sum('cantidad')).values('total')[:1]
    )
    subquery_vencimiento = Subquery(
        lotes_empresa.values('producto__producto')
        .annotate(proximo=Min('fecha_vencimiento')).values('proximo')[:1]
    )
    subquery_cantidad_lotes = Subquery(
        lotes_empresa.values('producto__producto')
        .annotate(count=Count('id')).values('count')[:1]
    )

    # --- 2.b) Subconsultas de oferta (inteligencia por peso) ---
    oferta_empresa = OfertaProducto.objects.filter(
        empresa=empresa_usuario,
        producto=OuterRef('pk')
    )
    sub_sell_by_weight = Subquery(oferta_empresa.values('sell_by_weight')[:1])
    sub_price_per_kg = Subquery(oferta_empresa.values('price_per_kg')[:1])
    sub_min_step = Subquery(oferta_empresa.values('min_step_grams')[:1])

    productos = productos_base.annotate(
        stock_total=subquery_stock,
        proximo_vencimiento=subquery_vencimiento,
        cantidad_lotes=subquery_cantidad_lotes,
        # 🧠 campos para el template
        sell_by_weight=sub_sell_by_weight,
        price_per_kg=sub_price_per_kg,
        min_step_grams=sub_min_step,
    )

    # --- 3) Buscador ---
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

    # --- 4) Alerta de próximos a vencer ---
    productos_proximos = productos.filter(proximo_vencimiento__lte=hoy_mas_15, proximo_vencimiento__gte=hoy)
    if productos_proximos.exists():
        lista_alerta = ", ".join(p.nombre for p in productos_proximos[:5])
        extras = max(0, productos_proximos.count() - 5)
        if extras:
            lista_alerta += f" … y {extras} más."
        messages.warning(request, f"Tienes productos próximos a vencer: {lista_alerta}")

    # --- 5) Highlight seguro para el template ---
    created_sku = (request.GET.get('created_sku') or '').strip()
    highlight_sku = (request.GET.get('hl') or '').strip() or created_sku

    # --- 6) Render ---
    context = {
        'productos': productos,
        'query': query,
        'today': hoy,
        'hoy_mas_15dias': int(time.mktime(hoy_mas_15.timetuple())),
        'highlight_sku': highlight_sku,
    }
    return render(request, 'inventario/inventario.html', context)

# --- CRUD de Productos ---

# Configurar logger
logger = logging.getLogger(__name__)

from django.urls import reverse

@login_required
@transaction.atomic
def agregar_producto(request):
    from django.template.loader import render_to_string
    
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    # --- Validaciones iniciales: empresa y suscripción --------------------
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        msg = "Debes estar asociado a una empresa para agregar productos."
        if is_ajax:
            return JsonResponse({'ok': False, 'html': f'<p>{msg}</p>'}, status=400)
        messages.error(request, msg)
        return redirect('home')

    try:
        suscripcion = SuscripcionUsuario.objects.get(empresa=empresa_usuario, activa=True)
        productos_actuales = Producto.objects.filter(empresas=empresa_usuario).count()
        if suscripcion.plan.max_productos != 0 and productos_actuales >= suscripcion.plan.max_productos:
            msg = f"Has alcanzado el límite de productos para tu plan ({suscripcion.plan.max_productos})."
            if is_ajax:
                return JsonResponse({'ok': False, 'html': f'<p>{msg}</p>'}, status=403)
            messages.error(request, msg)
            return redirect('inventario')
    except SuscripcionUsuario.DoesNotExist:
        msg = "No tienes una suscripción activa."
        if is_ajax:
            return JsonResponse({'ok': False, 'html': f'<p>{msg}</p>'}, status=403)
        messages.error(request, msg)
        return redirect('home')
    # ---------------------------------------------------------------------

    if request.method == 'POST':
        form_prod = ProductoForm(request.POST, empresa_usuario=empresa_usuario)

        if form_prod.is_valid():
            sku = form_prod.cleaned_data.get('sku')

            # -------- Heurística de venta por peso (nivel 1) --------
            KEYWORDS_PESO = [
                "cecina", "queso", "jamón", "fiambre", "longaniza", "salame",
                "salami", "mortadela", "arrechera", "vacuno", "cerdo", "pavo",
                "pollo", "carne", "pescado", "jamon", "lomo", "entraña", "atun"
            ]
            CATEGORIAS_PESO = [
                "fiambres", "quesos", "carnes", "pescados", "charcutería",
                "charcuteria", "frescos", "granel"
            ]
            # ---------------------------------------------------------

            try:
                # 1) Crear o recuperar el Producto por SKU
                producto, creado_producto = Producto.objects.get_or_create(
                    sku=sku,
                    defaults={
                        'nombre': form_prod.cleaned_data.get('nombre'),
                        'marca': form_prod.cleaned_data.get('marca'),
                        'categoria': form_prod.cleaned_data.get('categoria'),
                        'gramaje': form_prod.cleaned_data.get('gramaje'),
                        'unidad_medida': form_prod.cleaned_data.get('unidad_medida'),
                    }
                )

                # 2) Asociar a la empresa vía OfertaProducto (evita duplicados)
                oferta, creada_oferta = OfertaProducto.objects.get_or_create(
                    producto=producto,
                    empresa=empresa_usuario
                )

                # 3) Detección automática: decidir si es "por peso"
                nombre_lower = (
                    (form_prod.cleaned_data.get('nombre') or producto.nombre or "").lower()
                )
                categoria_val = form_prod.cleaned_data.get('categoria') or getattr(producto, 'categoria', "")
                categoria_lower = str(categoria_val).lower()

                es_por_peso = any(k in nombre_lower for k in KEYWORDS_PESO) or \
                              any(c in categoria_lower for c in CATEGORIAS_PESO)

                campos_actualizar = []
                if es_por_peso and not getattr(oferta, 'sell_by_weight', False):
                    oferta.sell_by_weight = True
                    campos_actualizar.append('sell_by_weight')

                min_step = getattr(oferta, 'min_step_grams', 0) or 0
                if es_por_peso and (min_step <= 0):
                    oferta.min_step_grams = 5
                    campos_actualizar.append('min_step_grams')

                if es_por_peso and (getattr(oferta, 'price_per_kg', 0) or 0) <= 0:
                    oferta.price_per_kg = 0
                    campos_actualizar.append('price_per_kg')

                if campos_actualizar:
                    oferta.save(update_fields=campos_actualizar)
                    messages.info(
                        request,
                        "Detectamos que «{0}» se vende por peso (gramos). "
                        "Redondeo fijado en {1} g. "
                        "Define el precio por kg al cargar el primer lote o en la pantalla de configuración."
                        .format(producto.nombre, oferta.min_step_grams)
                    )

                # 4) Mensajes y preparación de respuesta
                if creada_oferta:
                    accion = "agregado" if creado_producto else "asociado"
                    messages.success(request, f"Producto «{producto.nombre}» {accion} a tu inventario.")
                else:
                    messages.info(request, f"El producto «{producto.nombre}» ya estaba en tu inventario.")

                if is_ajax:
                    # Render de la fila para inserción/actualización en vivo
                    today = date.today()
                    hoy_mas_15dias = int((today + timedelta(days=15)).strftime('%s'))  # epoch como en template

                    row_html = render_to_string(
                        'inventario/_producto_row.html',
                        {
                            'producto': producto,
                            'today': today,
                            'hoy_mas_15dias': hoy_mas_15dias,
                        },
                        request=request,
                    )

                    return JsonResponse({
                        'ok': True,
                        'action': 'create' if creada_oferta else 'update',
                        'sku': producto.sku,
                        'row_html': row_html,
                        # Si quieres forzar el flujo posterior, descomenta:
                        # 'redirect': reverse('post_creacion_producto', kwargs={'producto_id': producto.id}),
                    })

                # Flujo no-AJAX (página completa)
                if creada_oferta:
                    return redirect(reverse('post_creacion_producto', kwargs={'producto_id': producto.id}))
                else:
                    return redirect(reverse('inventario') + f"?hl={producto.sku}")

            except IntegrityError:
                err_msg = "Ocurrió un problema guardando el producto. Intenta nuevamente."
                if is_ajax:
                    return JsonResponse({'ok': False, 'html': f'<p>{err_msg}</p>'}, status=500)
                messages.error(request, err_msg)
                return redirect('inventario')

        # Form inválido
        if is_ajax:
            html = render(request, 'productos/_producto_form.html', {'form': form_prod}).content.decode('utf-8')
            return JsonResponse({'ok': False, 'html': html}, status=422)

        for field, errors in form_prod.errors.items():
            for error in errors:
                messages.error(request, f"Error en {field}: {error}")
        for error in form_prod.non_field_errors():
            messages.error(request, f"Error general en producto: {error}")

    else:
        # GET
        form_prod = ProductoForm(empresa_usuario=empresa_usuario)
        if is_ajax:
            return render(request, 'productos/_producto_form.html', {'form': form_prod})

    # Render de página completa (fallback no-AJAX)
    context = {'form_prod': form_prod}
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
    """
    Alta de Lote con preselección por ?producto_id= o ?sku=.
    - Si viene producto_id, se asocia automáticamente y al guardar redirige a flujo_opciones.
    - Si viene sku, mantiene el comportamiento clásico y redirige al inventario.

    Nivel 2: Detección inteligente de "venta por peso" al guardar el lote:
      - Si la oferta no tenía sell_by_weight=True pero el nombre/categoría lo sugiere,
        se activa automáticamente, fija min_step_grams (5) y, si price_per_kg=0
        y el form trae precio_venta>0, lo usa como precio/kg inicial.
    """
    empresa = obtener_empresa_del_usuario(request.user)
    if not empresa:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('inventario')

    sku = (request.GET.get('sku') or '').strip()
    producto_id = request.GET.get('producto_id')
    oferta_seleccionada = None
    producto = None

    # --- Buscar producto por ID o SKU ---
    if producto_id:
        producto = get_object_or_404(Producto, pk=producto_id, empresas=empresa)
        oferta_seleccionada = OfertaProducto.objects.filter(empresa=empresa, producto=producto).first()
    elif sku:
        producto = Producto.objects.filter(sku=sku, empresas=empresa).first()
        if producto:
            oferta_seleccionada = OfertaProducto.objects.filter(empresa=empresa, producto=producto).first()

    # --- POST: guardar el lote ---
    if request.method == 'POST':
        form = LoteProductoForm(request.POST, empresa_usuario=empresa)

        if form.is_valid():
            # Antes de guardar, aplicamos la detección inteligente sobre la oferta seleccionada
            oferta_form = form.cleaned_data.get('producto')  # suele ser OfertaProducto
            oferta_obj = oferta_form or oferta_seleccionada  # fallback por si viene prefijada

            # Heurística simple por nombre/categoría
            KEYWORDS_PESO = [
                "cecina", "queso", "jamón", "jamon", "fiambre", "longaniza", "salame",
                "salami", "mortadela", "vacuno", "cerdo", "pavo", "pollo", "carne",
                "pescado", "atun", "charcutería", "charcuteria"
            ]
            CATEGORIAS_PESO = [
                "fiambres", "quesos", "carnes", "pescados", "charcutería", "charcuteria", "frescos", "granel"
            ]

            if oferta_obj:
                nombre_lower = (oferta_obj.producto.nombre or "").lower()
                categoria_lower = str(getattr(oferta_obj.producto, 'categoria', "") or "").lower()

                es_por_peso = any(k in nombre_lower for k in KEYWORDS_PESO) or \
                              any(c in categoria_lower for c in CATEGORIAS_PESO)

                campos_update = []
                info_msgs = []

                if es_por_peso and not getattr(oferta_obj, 'sell_by_weight', False):
                    oferta_obj.sell_by_weight = True
                    campos_update.append('sell_by_weight')
                    info_msgs.append("venta por peso activada automáticamente")

                min_step = getattr(oferta_obj, 'min_step_grams', 0) or 0
                if es_por_peso and (min_step <= 0):
                    oferta_obj.min_step_grams = 5
                    campos_update.append('min_step_grams')
                    info_msgs.append("redondeo fijado en 5 g")

                # Si no hay precio/kg y el form trae precio_venta (>0), úsalo como inicial
                precio_venta_lote = form.cleaned_data.get('precio_venta')
                if es_por_peso and (getattr(oferta_obj, 'price_per_kg', 0) or 0) <= 0:
                    try:
                        pv = float(precio_venta_lote or 0)
                    except (TypeError, ValueError):
                        pv = 0.0
                    if pv > 0:
                        oferta_obj.price_per_kg = pv
                        campos_update.append('price_per_kg')
                        info_msgs.append(f"precio/kg inicial = ${int(pv)}")
                # Guardamos cambios en la oferta si corresponde
                if campos_update:
                    oferta_obj.save(update_fields=campos_update)
                    messages.info(
                        request,
                        f"FOCAL detectó {', '.join(info_msgs)} para «{oferta_obj.producto.nombre}». "
                        "Ingrese la cantidad en gramos (ej.: 3000 para 3 kg)."
                    )

            # Guardar el lote
            lote = form.save()
            messages.success(request, f"Lote para '{lote.producto.producto.nombre}' agregado correctamente.")

            # ✅ Si el flujo viene de producto_id, redirige al flujo encadenado
            if producto_id:
                return redirect(reverse('flujo_opciones', kwargs={'producto_id': producto_id}))

            # 🔙 Si no, vuelve al inventario (modo clásico)
            try:
                sku_ok = lote.producto.producto.sku
            except Exception:
                sku_ok = sku
            inv = reverse('inventario')
            return redirect(f"{inv}?sku={sku_ok}#tab-gestionar" if sku_ok else inv)

        else:
            messages.error(request, "Revisa los errores del formulario.")
    else:
        # --- GET: inicialización del formulario ---
        initial = {}
        if oferta_seleccionada:
            initial['producto'] = oferta_seleccionada

        form = LoteProductoForm(empresa_usuario=empresa, initial=initial)

        # Restringir opciones de producto si ya hay selección
        if oferta_seleccionada and 'producto' in form.fields:
            form.fields['producto'].queryset = OfertaProducto.objects.filter(pk=oferta_seleccionada.pk)

    # --- Render final ---
    return render(request, 'inventario/agregar_lote.html', {
        'form': form,
        'sku_prefill': sku,
        'oferta_seleccionada': oferta_seleccionada,
        'producto_id': producto_id,
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
def agregar_proveedor(request):
    """
    Vista para agregar un nuevo proveedor.
    - Si viene ?producto_id=, vuelve al flujo encadenado.
    - Si además viene ?next=add_lote, tras crear el proveedor redirige a agregar_lote.
    - Si no viene producto_id, redirige al inventario.
    """
    from django.urls import reverse

    producto_id = request.GET.get('producto_id')
    next_step = request.GET.get('next')  # soporte para 'add_lote'

    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            proveedor = form.save()
            messages.success(request, f"Proveedor '{proveedor.nombre}' agregado exitosamente.")

            if producto_id and next_step == 'add_lote':
                # Atajo: Proveedor → Lote
                return redirect(f"{reverse('agregar_lote')}?producto_id={producto_id}")
            if producto_id:
                # Flujo normal: volver a las opciones del producto
                return redirect(reverse('flujo_opciones', kwargs={'producto_id': producto_id}))
            # Sin contexto de flujo
            return redirect('inventario')
    else:
        form = ProveedorForm()

    # (Opcional) puedes usar estos valores en el template para ajustar el botón "Cancelar"
    context = {
        'form': form,
        'producto_id': producto_id,
        'next_step': next_step,
    }
    return render(request, 'inventario/agregar_proveedor.html', context)

@login_required
def post_creacion_producto(request, producto_id):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    producto = get_object_or_404(Producto, id=producto_id, empresas=empresa_usuario)

    # Para mostrar info en la vista
    oferta = OfertaProducto.objects.filter(producto=producto, empresa=empresa_usuario).first()

    return render(request, 'inventario/post_creacion_producto.html', {
        'producto': producto,
        'oferta': oferta,
    })

@login_required
def flujo_opciones(request, producto_id):
    """
    Pantalla intermedia que ofrece continuar con el flujo:
    agregar lote, agregar proveedor o finalizar.
    """
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    producto = get_object_or_404(Producto, id=producto_id, empresas=empresa_usuario)
    return render(request, 'inventario/flujo_opciones.html', {'producto': producto})

@login_required
def producto_resumen(request, producto_id):
    """
    Muestra un resumen del producto, sus lotes y sus proveedores asociados.
    """
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    producto = get_object_or_404(Producto, id=producto_id, empresas=empresa_usuario)

    # Buscar oferta de la empresa
    oferta = OfertaProducto.objects.filter(producto=producto, empresa=empresa_usuario).first()
    lotes = LoteProducto.objects.filter(producto=oferta).select_related('proveedor')
    proveedores = Proveedor.objects.filter(lotes__producto=oferta).distinct()

    context = {
        'producto': producto,
        'oferta': oferta,
        'lotes': lotes,
        'proveedores': proveedores,
    }
    return render(request, 'inventario/producto_resumen.html', context)

@login_required
@transaction.atomic
def ajustar_stock(request, producto_id):
    """
    Ajusta +/- 1 (o 'cantidad' enviada) sobre el LOTE más próximo a vencer
    del producto indicado (según la empresa del usuario).
    - POST operacion: 'sumar' | 'restar'
    - POST cantidad: entero >= 1 (default 1)
    """
    if request.method != 'POST':
        return redirect('inventario')

    empresa = obtener_empresa_del_usuario(request.user)
    if not empresa:
        messages.error(request, "No se encontró una empresa válida.")
        return redirect('inventario')

    operacion = (request.POST.get('operacion') or '').strip()
    try:
        cantidad = int(request.POST.get('cantidad') or 1)
        if cantidad < 1:
            cantidad = 1
    except ValueError:
        cantidad = 1

    # Producto y oferta de la empresa
    producto = get_object_or_404(Producto, pk=producto_id, empresas=empresa)
    oferta = OfertaProducto.objects.filter(empresa=empresa, producto=producto).first()
    if not oferta:
        messages.error(request, "Este producto no está asociado a tu inventario.")
        return redirect('inventario')

    # Lote más próximo a vencer
    lotes_qs = (LoteProducto.objects
                .filter(producto=oferta)
                .order_by('fecha_vencimiento', 'id'))

    if operacion == 'restar':
        # Buscar el primer lote con stock disponible
        lote = next((l for l in lotes_qs if l.cantidad and l.cantidad > 0), None)
        if not lote:
            messages.warning(request, f"No hay stock disponible para «{producto.nombre}».")
            return redirect('inventario')

        descontar = min(cantidad, max(lote.cantidad, 0))
        lote.cantidad = max(lote.cantidad - descontar, 0)
        lote.save(update_fields=['cantidad'])
        messages.success(request, f"Se descontaron {descontar} unidad(es) del lote que vence primero de «{producto.nombre}».")

    elif operacion == 'sumar':
        lote = lotes_qs.first()
        if not lote:
            messages.info(request, f"«{producto.nombre}» no tiene lotes. Crea el primero para registrar entrada.")
            # Redirige a crear lote con el producto_id ya listo
            from django.urls import reverse
            return redirect(f"{reverse('agregar_lote')}?producto_id={producto.id}")

        lote.cantidad = (lote.cantidad or 0) + cantidad
        lote.save(update_fields=['cantidad'])
        messages.success(request, f"Se agregaron {cantidad} unidad(es) al lote que vence primero de «{producto.nombre}».")

    else:
        messages.error(request, "Operación inválida.")
        return redirect('inventario')

    return redirect('inventario')

from .services import venta_cecina_por_monto
from django.core.exceptions import ValidationError

@login_required
@transaction.atomic
def salida_cecina_por_monto_view(request):
    """
    GET: permite previsualizar precio/kg y producto al ingresar SKU (querystring ?sku=...)
    POST: confirma la salida por monto (CLP → gramos).
    """
    empresa = obtener_empresa_del_usuario(request.user)
    if not empresa:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('home')

    context = {
        "sku_prefill": (request.GET.get('sku') or '').strip(),
        "producto_nombre": "",
        "precio_por_kg": None,
        "min_step_grams": 5,
    }

    # Si viene ?sku=... por GET, pre-carga datos para el preview
    if context["sku_prefill"]:
        try:
            producto = get_object_or_404(Producto, sku=context["sku_prefill"], empresas=empresa)
            oferta = get_object_or_404(OfertaProducto, producto=producto, empresa=empresa)
            context["producto_nombre"] = producto.nombre
            context["precio_por_kg"] = float(oferta.price_per_kg or 0)
            context["min_step_grams"] = int(oferta.min_step_grams or 5)
        except Exception:
            pass  # si falla, simplemente no hay preview

    if request.method == 'POST':
        sku = (request.POST.get('sku') or '').strip()
        try:
            amount = int(request.POST.get('amount_clp') or '0')
        except ValueError:
            amount = 0
        nota = (request.POST.get('nota') or '').strip()

        if not sku:
            messages.error(request, "Ingresa el SKU (código de barras).")
            return render(request, 'inventario/salida_cecina_monto.html', context)

        if amount <= 0:
            messages.error(request, "Ingresa un monto válido en CLP (entero positivo).")
            context["sku_prefill"] = sku
            return render(request, 'inventario/salida_cecina_monto.html', context)

        producto = get_object_or_404(Producto, sku=sku, empresas=empresa)
        oferta = get_object_or_404(OfertaProducto, producto=producto, empresa=empresa)

        try:
            result = venta_cecina_por_monto(oferta.id, amount, request.user, nota=nota)
            g = result['grams_final']
            p = result['price_per_kg']
            messages.success(
                request,
                f"Salida registrada: ${amount:,} → {g} g de «{producto.nombre}» (a ${p:,.0f}/kg)."
            )
            return redirect('inventario')  # ajusta a tu vista de inventario
        except (ValidationError, Exception) as e:
            messages.error(request, f"No se pudo registrar la salida: {e}")
            # Mantén el preview en el re-render
            context.update({
                "sku_prefill": sku,
                "producto_nombre": producto.nombre,
                "precio_por_kg": float(oferta.price_per_kg or 0),
                "min_step_grams": int(oferta.min_step_grams or 5),
            })
            return render(request, 'inventario/salida_cecina_monto.html', context)

    return render(request, 'inventario/salida_cecina_monto.html', context)

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

from django.views.decorators.cache import never_cache

@never_cache
def logout_view(request):
    """Cierra sesión y muestra mensaje de confirmación."""
    logout(request)
    messages.success(request, "Has cerrado sesión correctamente.")
    return redirect('landing:landing')

# --- Vistas de API ---

@login_required
def obtener_datos_sku_api(request, sku):
    from django.http import HttpResponseBadRequest
    import re

    empresa_actual = obtener_empresa_del_usuario(request.user)

    # Normalizar y validar SKU recibido por URL
    sku = (sku or '').strip()
    if re.search(r'\s', sku) or (not sku.isdigit()) or len(sku) > 30:
        return JsonResponse({
            'status': 'invalido',
            'mensaje': 'SKU inválido: usa solo números, sin espacios, máximo 30 dígitos.'
        }, status=400)

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
                'gramaje': producto_global.gramaje,
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

@login_required
def post_login_router(request):
    """
    Si falta empresa o plan => onboarding.
    Si está todo ok => home.
    """
    user = request.user
    if not getattr(user, "empresa_id", None):
        return redirect('onboarding_inicial')

    tiene_plan = SuscripcionUsuario.objects.filter(
        empresa=user.empresa, activa=True
    ).exists()

    if not tiene_plan:
        return redirect('onboarding_inicial')  # mismo flujo con selección de plan

    # Todo ok
    return redirect('home')

@login_required
@transaction.atomic
def onboarding_inicial(request):
    """
    Permite completar/editar datos del usuario y su empresa
    y seleccionar un plan (si no lo tiene). Se usa al primer login o si falta algo.
    """
    user = request.user

    # Instancias iniciales
    empresa = getattr(user, "empresa", None)
    if not empresa:
        from .models import Empresa
        empresa = Empresa()  # temporal (no guardada aún)

    if request.method == "POST":
        f_user = AlmaceneroProfileForm(request.POST)
        f_emp = EmpresaForm(request.POST, instance=empresa if empresa.pk else None)
        f_plan = PlanSelectForm(request.POST)

        if f_user.is_valid() and f_emp.is_valid() and f_plan.is_valid():
            # 1) Usuario
            cd = f_user.cleaned_data
            changed = []
            for field in ["nombres", "apellidos", "telefono", "direccion", "region", "comuna"]:
                val = cd.get(field)
                if getattr(user, field, None) != val:
                    setattr(user, field, val)
                    changed.append(field)
            if changed:
                user.save(update_fields=changed)

            # 2) Empresa (crea si no existe)
            empresa = f_emp.save(commit=False)
            if not empresa.pk:
                empresa.save()
            else:
                empresa.save()

            # vincular user.empresa si hacía falta
            if getattr(user, "empresa_id", None) != empresa.pk:
                user.empresa = empresa
                user.save(update_fields=["empresa"])

            # 3) Plan (si no existe activo)
            plan = f_plan.cleaned_data["plan"]
            if not SuscripcionUsuario.objects.filter(empresa=empresa, activa=True).exists():
                SuscripcionUsuario.objects.create(empresa=empresa, plan=plan, activa=True)

            messages.success(request, "¡Listo! Tu información y plan quedaron configurados.")
            return redirect('home')
        else:
            messages.error(request, "Revisa los campos del formulario.")
    else:
        initial_user = {
            "nombres": getattr(user, "nombres", ""),
            "apellidos": getattr(user, "apellidos", ""),
            "telefono": getattr(user, "telefono", ""),
            "direccion": getattr(user, "direccion", ""),
            "region": getattr(user, "region", ""),
            "comuna": getattr(user, "comuna", ""),
        }
        f_user = AlmaceneroProfileForm(initial=initial_user)
        f_emp = EmpresaForm(instance=empresa if empresa.pk else None)
        # Preselecciona un plan “free” si existe
        f_plan = PlanSelectForm()
        try:
            from .models import Plan
            free = Plan.objects.filter(codigo__iexact="free", activo=True).first()
            if free:
                f_plan.fields["plan"].initial = free.pk
        except Exception:
            pass

    return render(request, "inventario/onboarding_inicial.html", {
        "f_user": f_user,
        "f_emp": f_emp,
        "f_plan": f_plan,
    })