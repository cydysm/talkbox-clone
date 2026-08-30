from django.conf import settings

from .models import MarkdownSourceSetting, NavItem, SiteAbout, default_theme

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


def get_switch_mode(request):
    preference = get_theme_preference(request)
    if preference == SYSTEM_THEME:
        return "auto"
    if preference:
        return preference

    default_theme_name = default_theme()
    if default_theme_name.endswith("_light"):
        return "light"
    return "dark"


def get_nav_items(request):
    is_home = request.path == "/"
    items = list(
        NavItem.objects.exclude(visibility="hidden")
        .exclude(visibility="non_home" if is_home else "home")
        .only("title", "url")[: settings.NAV_MAX_ITEMS]
    )
    if items:
        return items
    return [NavItem(title="首页", url="/")]


def theme_context(request):
    theme_name = get_resolved_theme_name(request)
    preference = get_theme_preference(request)
    return {
        "THEME_NAME": theme_name,
        "THEME_STATIC_DIR": f"themes/{theme_name}",
        "THEME_PREFERENCE": preference,
        "THEME_SWITCH_MODE": get_switch_mode(request),
        "SYSTEM_THEME": SYSTEM_THEME,
        "AVAILABLE_THEMES": settings.AVAILABLE_THEMES,
        "SITE_NAME": settings.SITE_NAME,
        "SITE_DESCRIPTION": settings.SITE_DESCRIPTION,
        "NAV_ITEMS": get_nav_items(request),
        "ABOUT_TEXT": SiteAbout.current_text(),
        "MARKDOWN_SOURCE_ENABLED": MarkdownSourceSetting.enabled(),
    }
