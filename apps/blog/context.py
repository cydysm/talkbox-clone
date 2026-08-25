from django.conf import settings

from .models import default_theme


def theme_context(request):
    theme_name = default_theme()
    return {
        "THEME_NAME": theme_name,
        "THEME_STATIC_DIR": f"themes/{theme_name}",
        "SITE_NAME": settings.SITE_NAME,
    }
