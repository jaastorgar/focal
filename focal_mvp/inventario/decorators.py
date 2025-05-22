# inventario/decorators.py

from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from .models import SuscripcionUsuario, Empresa

def plan_requerido(plan_name):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, "Debes iniciar sesión para acceder a esta función.")
                return redirect('login') # Redirige al login

            try:
                empresa = request.user.almacenero.empresa
                suscripcion = SuscripcionUsuario.objects.get(empresa=empresa, activa=True)
                if suscripcion.plan.nombre == plan_name or \
                   (plan_name == 'BASIC' and suscripcion.plan.nombre in ['BASIC', 'PREMIUM']) or \
                   (plan_name == 'PREMIUM' and suscripcion.plan.nombre == 'PREMIUM'):
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, f"Necesitas el plan {plan_name} para acceder a esta función. Tu plan actual es {suscripcion.plan.get_nombre_display()}.")
                    return redirect('vista_planes') # O a una página de "acceso denegado"
            except (AttributeError, SuscripcionUsuario.DoesNotExist, Empresa.DoesNotExist):
                messages.error(request, "No se encontró una suscripción activa para tu empresa. Por favor, selecciona un plan.")
                return redirect('vista_planes') # O redirige a la página de planes para que elija uno
        return _wrapped_view
    return decorator

def caracteristica_requerida(feature_name):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, "Debes iniciar sesión para acceder a esta función.")
                return redirect('login')

            try:
                empresa = request.user.almacenero.empresa
                suscripcion = SuscripcionUsuario.objects.get(empresa=empresa, activa=True)
                plan = suscripcion.plan

                # Lógica para verificar la característica
                if feature_name == 'max_productos':
                    # Podrías pasar el número de productos actuales del usuario y compararlo con plan.max_productos
                    # Por ahora, solo verificamos si el plan permite más de 0 productos (es decir, no es ilimitado por precio 0)
                    # La lógica real sería: si el usuario tiene X productos, y su plan.max_productos es Y, y X >= Y, entonces denegar.
                    # Esto requiere contar los productos del usuario.
                    messages.error(request, "Esta característica requiere un análisis de uso que no se implementa en este decorador simple.")
                    return redirect('/home/') # O una página de error

                elif feature_name == 'max_almacenes':
                    # Similar a max_productos, necesitarías contar almacenes.
                    messages.error(request, "Esta característica requiere un análisis de uso que no se implementa en este decorador simple.")
                    return redirect('/home/')

                elif feature_name == 'soporte_prioritario':
                    if plan.soporte_prioritario:
                        return view_func(request, *args, **kwargs)
                    else:
                        messages.error(request, "Tu plan actual no incluye soporte prioritario. ¡Considera actualizar!")
                        return redirect('vista_planes')

                else:
                    messages.error(request, f"Característica desconocida: {feature_name}")
                    return redirect('/home/')

            except (AttributeError, SuscripcionUsuario.DoesNotExist, Empresa.DoesNotExist):
                messages.error(request, "No se encontró una suscripción activa para tu empresa. Por favor, selecciona un plan.")
                return redirect('vista_planes')
        return _wrapped_view
    return decorator