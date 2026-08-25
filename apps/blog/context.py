from django.conf import settings


def theme_context(request):
    return {
        "THEME_NAME": settings.THEME,
        "THEME_STATIC_DIR": f"themes/{settings.THEME}",
        "SITE_NAME": settings.SITE_NAME,
    }
