from pathlib import Path

from django.conf import settings
from django.template import Origin, TemplateDoesNotExist
from django.template.loaders.base import Loader as BaseLoader
from django.template.loaders.cached import Loader as CachedLoader


class ActiveThemeFilesystemLoader(BaseLoader):
    def get_template_sources(self, template_name, template=None):
        from .models import default_theme

        theme_dir = Path(settings.BASE_DIR) / "themes" / default_theme() / "templates"
        yield Origin(
            name=str(theme_dir / template_name),
            template_name=template_name,
            loader=self,
        )

    def get_contents(self, origin):
        try:
            with open(origin.name, encoding="utf-8") as template_file:
                return template_file.read()
        except FileNotFoundError as error:
            raise TemplateDoesNotExist(origin.template_name) from error


class ActiveThemeCachedLoader(CachedLoader):
    def cache_key(self, template_name, skip=None):
        from .models import default_theme

        key = super().cache_key(template_name, skip)
        return f"{default_theme()}:{key}"
