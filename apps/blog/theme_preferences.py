from django.conf import settings

from .models import default_theme

THEME_COOKIE_NAME = "visitor_theme"
SYSTEM_THEME = "system"
THEME_PREFERENCES = ("dark", "light", SYSTEM_THEME)


def get_theme_preference(request):
    preference = request.COOKIES.get(THEME_COOKIE_NAME)
    return preference if preference in THEME_PREFERENCES else None


def get_resolved_theme_name(request):
    preference = get_theme_preference(request)
    available = set(settings.AVAILABLE_THEMES)
    matching_themes = [theme for theme in available if theme.endswith(f"_{preference}")]
    if preference in {"dark", "light"} and matching_themes:
        return matching_themes[0]
    return default_theme()


def theme_context(request):
    theme_name = get_resolved_theme_name(request)
    preference = get_theme_preference(request)
    return {
        "THEME_NAME": theme_name,
        "THEME_STATIC_DIR": f"themes/{theme_name}",
        "THEME_PREFERENCE": preference,
        "SYSTEM_THEME": SYSTEM_THEME,
        "AVAILABLE_THEMES": settings.AVAILABLE_THEMES,
        "SITE_NAME": settings.SITE_NAME,
    }
