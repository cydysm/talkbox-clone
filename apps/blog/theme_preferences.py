from django.conf import settings

from .models import NavItem, SiteMeta, default_theme

THEME_COOKIE_NAME = "visitor_theme"
SYSTEM_THEME = "system"
THEME_PREFERENCES = ("dark", "light", SYSTEM_THEME)


def get_theme_preference(request):
    preference = request.COOKIES.get(THEME_COOKIE_NAME)
    return preference if preference in THEME_PREFERENCES else None


def get_resolved_theme_name(request, active_theme=None):
    preference = get_theme_preference(request)
    if preference in {"dark", "light"}:
        matching_themes = [t for t in settings.AVAILABLE_THEMES if t.endswith(f"_{preference}")]
        if matching_themes:
            return matching_themes[0]
    return active_theme or default_theme()


def get_switch_mode(request, active_theme=None):
    preference = get_theme_preference(request)
    if preference == SYSTEM_THEME:
        return "auto"
    if preference:
        return preference

    theme = active_theme or default_theme()
    if theme.endswith("_light"):
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


def get_site_meta_context(request, meta=None, active_theme=None):
    if meta is None:
        meta = SiteMeta.objects.first()
    favicon_url = ""
    if meta and meta.favicon:
        try:
            favicon_url = meta.favicon.url
        except ValueError:
            favicon_url = ""
    if not favicon_url:
        # 未上传 favicon 时，回退到主题自带的仙人掌 logo
        theme_name = active_theme or get_resolved_theme_name(request)
        favicon_url = f"/static/themes/{theme_name}/img/logo.png"
    return {
        "SITE_NAME": SiteMeta.current_name(meta),
        "SITE_TITLE": SiteMeta.current_title(meta),
        "META_DESCRIPTION": SiteMeta.current_description(meta),
        "FAVICON_URL": favicon_url,
    }


def theme_context(request):
    # 每个请求只查一次主题与站点设置行，向下传递复用
    active_theme = default_theme()
    meta = SiteMeta.objects.first()
    preference = get_theme_preference(request)
    theme_name = get_resolved_theme_name(request, active_theme)
    nav_items = get_nav_items(request)
    return {
        "THEME_NAME": theme_name,
        "THEME_STATIC_DIR": f"themes/{theme_name}",
        "THEME_PREFERENCE": preference,
        "THEME_SWITCH_MODE": get_switch_mode(request, active_theme),
        "SYSTEM_THEME": SYSTEM_THEME,
        "AVAILABLE_THEMES": settings.AVAILABLE_THEMES,
        "SITE_DESCRIPTION": settings.SITE_DESCRIPTION,
        **get_site_meta_context(request, meta, theme_name),
        "NAV_ITEMS": nav_items,
        "POST_NAV_ITEMS": get_post_header_nav_items(nav_items),
        "ABOUT_TEXT": SiteMeta.current_about(meta),
        "MARKDOWN_SOURCE_ENABLED": SiteMeta.current_show_markdown_source(meta),
    }
