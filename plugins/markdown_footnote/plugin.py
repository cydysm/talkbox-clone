MARKER = "[FOOTNOTE]"
NOTE = "\n<p class=\"plugin-footnote\">本文由 Talkbox Clone 插件处理。</p>"


def transform_html(html: str) -> str:
    return html.replace(MARKER, NOTE) if MARKER in html else html
