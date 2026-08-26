import json
import importlib.metadata
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path

from django.conf import settings
from packaging.requirements import Requirement

from apps.blog.models import PluginSetting


@dataclass(slots=True)
class Plugin:
    name: str
    version: str = "1.0"
    description: str = ""
    module_name: str = ""
    hooks: dict[str, object] = field(default_factory=dict)


class PluginRegistry:
    def __init__(self):
        self._plugins: dict[str, Plugin] = {}

    def clear(self):
        self._plugins.clear()

    def discover(self):
        self.clear()
        for plugin_dir in settings.PLUGIN_DIRS:
            if not plugin_dir.exists():
                continue
            for manifest_path in sorted(Path(plugin_dir).glob("*/plugin.json")):
                with manifest_path.open(encoding="utf-8") as manifest_file:
                    metadata = json.load(manifest_file)
                name = metadata["name"]
                self._validate_dependencies(manifest_path.parent, metadata.get("dependencies", []))
                module_name = f"{manifest_path.parent.name}.plugin"
                try:
                    module = import_module(module_name)
                except (ImportError, AttributeError):
                    hooks = {}
                else:
                    hooks = {
                        hook_name: getattr(module, hook_name)
                        for hook_name in ("transform_markdown", "transform_html")
                        if hasattr(module, hook_name)
                    }
                self._plugins[name] = Plugin(
                    name=name,
                    version=str(metadata.get("version", "1.0")),
                    description=metadata.get("description", ""),
                    module_name=module_name,
                    hooks=hooks,
                )
        return self.available()

    def _validate_dependencies(self, plugin_path: Path, dependencies) -> None:
        requirements = [str(item).strip() for item in dependencies or [] if str(item).strip()]
        requirements_file = plugin_path / "requirements.txt"
        if requirements_file.exists():
            file_requirements = []
            for raw_line in requirements_file.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if any(token in line for token in ("\n", "; --")):
                    raise ValueError(f"{plugin_path.name}/requirements.txt 包含不受支持的选项")
                file_requirements.append(line)
            requirements.extend(file_requirements)

        missing = []
        for requirement in requirements:
            try:
                parsed = Requirement(requirement)
                importlib.metadata.version(parsed.name)
            except (ValueError, importlib.metadata.PackageNotFoundError):
                missing.append(requirement)
        if missing:
            raise RuntimeError(
                "插件依赖未安装：" + ", ".join(missing)
                + f"。请在当前 Python 环境安装后重启，或删除 {plugin_path.name}/requirements.txt 对应依赖。"
            )

    def available(self) -> list[Plugin]:
        return list(self._plugins.values())

    def enabled(self):
        enabled_names = set(
            PluginSetting.objects.filter(is_enabled=True).values_list("name", flat=True)
        )
        return [plugin for plugin in self._plugins.values() if plugin.name in enabled_names]

    def apply_hook(self, hook_name: str, value: str) -> str:
        for plugin in self.enabled():
            handler = plugin.hooks.get(hook_name)
            if callable(handler):
                result = handler(value)
                if isinstance(result, str):
                    value = result
        return value


registry = PluginRegistry()
