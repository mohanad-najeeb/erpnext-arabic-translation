import os
import shutil
from typing import Optional

import frappe 

_LOGGER = frappe.logger("arabic_translations")


def before_install(app_name: Optional[str] = None, *args, **kwargs) -> None:
    """Hook: copy Arabic locale files into installed apps during install."""
    try:
        copy_locale_files()
    except Exception:
        # Log and swallow to avoid breaking installs; details go to the log file.
        _LOGGER.exception("Failed to copy Arabic locale files during install")


def copy_locale_files() -> None:
    """Detect Frappe version/apps and copy ar.po/ar.csv bundles into place."""
    major = _get_frappe_major_version()
    if major not in (15, 16):
        _LOGGER.warning(
            "Unsupported Frappe version %s; skipping Arabic locale copy", major
        )
        return

    source_root = os.path.join(
        os.path.dirname(__file__), "locale", "other-apps", f"v{major}"
    )
    if not os.path.isdir(source_root):
        _LOGGER.warning("Locale source path missing: %s", source_root)
        return

    installed_apps = frappe.get_installed_apps() or []
    for app in installed_apps:
        _copy_for_app(app, source_root)


def _get_frappe_major_version() -> Optional[int]:
    raw_version = getattr(frappe, "__version__", "") or ""
    for sep in ("-", "+"):
        if sep in raw_version:
            raw_version = raw_version.split(sep, 1)[0]
            break

    parts = raw_version.split(".")
    try:
        return int(parts[0])
    except Exception:
        return None


def _copy_for_app(app: str, source_root: str) -> None:
    app_source_dir = os.path.join(source_root, app)
    if not os.path.isdir(app_source_dir):
        _LOGGER.info("No Arabic locale bundle for app %s at %s", app, app_source_dir)
        return

    try:
        app_dest_root = frappe.get_app_path(app)
    except Exception:
        _LOGGER.warning("Could not resolve app path for %s; skipping", app)
        return

    for dirpath, _, files in os.walk(app_source_dir):
        for filename in files:
            if filename not in {"ar.po", "ar.csv"}:
                continue

            source_file = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(source_file, app_source_dir)

            # Drop leading "<app>/" folder from the source bundle so we copy into
            # the actual app root rather than nesting (source layout includes the
            # app name).
            prefix = f"{app}{os.sep}"
            if rel_path.startswith(prefix):
                rel_path = rel_path[len(prefix) :]

            dest_path = os.path.join(app_dest_root, rel_path)

            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(source_file, dest_path)
            _LOGGER.info("Copied %s for app %s to %s", filename, app, dest_path)

