#!/usr/bin/env python3
import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

def main() -> int:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
    try:
        import django

        django.setup()
    except Exception as error:
        print(f"插件依赖检查无法初始化 Django：{error}", file=sys.stderr)
        return 2

    from apps.plugins.registry import registry

    try:
        registry.discover()
    except (OSError, RuntimeError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"已检查 {len(registry.available())} 个插件依赖。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
