from django.conf import settings

from .models import MarkdownSourceSetting, NavItem, SiteMeta, default_theme

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
        .only("title", "url", "show_in_post_header")[: settings.NAV_MAX_ITEMS]
    )
    if items:
        return items
    return [NavItem(title="首页", url="/")]


def get_post_header_nav_items(nav_items):
    return [item for item in nav_items if getattr(item, "show_in_post_header", True)]


def get_site_meta_context():
    meta = SiteMeta.objects.first()
    favicon_url = ""
    if meta and meta.favicon:
        try:
            favicon_url = meta.favicon.url
        except ValueError:
            favicon_url = ""
    return {
        "SITE_NAME": SiteMeta.current_name(),
        "SITE_TITLE": SiteMeta.current_title(),
        "META_DESCRIPTION": SiteMeta.current_description(),
        "FAVICON_URL": favicon_url,
    }


def theme_context(request):
    theme_name = get_resolved_theme_name(request)
    preference = get_theme_preference(request)
    nav_items = get_nav_items(request)
    return {
        "THEME_NAME": theme_name,
        "THEME_STATIC_DIR": f"themes/{theme_name}",
        "THEME_PREFERENCE": preference,
        "THEME_SWITCH_MODE": get_switch_mode(request),
        "SYSTEM_THEME": SYSTEM_THEME,
        "AVAILABLE_THEMES": settings.AVAILABLE_THEMES,
        "SITE_DESCRIPTION": settings.SITE_DESCRIPTION,
        **get_site_meta_context(),
        "NAV_ITEMS": nav_items,
        "POST_NAV_ITEMS": get_post_header_nav_items(nav_items),
        "ABOUT_TEXT": SiteMeta.current_about(),
        "MARKDOWN_SOURCE_ENABLED": MarkdownSourceSetting.enabled(),
    }
