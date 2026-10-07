# Arabic Translations

Arabic Translations for Frappe, ERPNext, HRMS and CRM

Arabic translations for Frappe, ERPNext, HRMS, and CRM.

## Supported version

This project currently supports **Frappe Framework v16**. Its Arabic catalogs are
maintained for v16 and are not intended for v15 or other major versions. Use
compatible v16 releases of ERPNext, HRMS, and CRM with these translations.

## What it does

The app copies the bundled Arabic catalogs for Frappe, ERPNext, HRMS, and CRM
into the matching installed apps. It reapplies them during installation and
after app installs or migrations, so updates do not remove the translations.
Frappe v16 catalogs use `.po` files; the app compiles copied catalogs to `.mo`
files so Frappe can load them without rebuilding assets.

## Installation

From your bench directory, install the app and then add it to your site:

```bash
cd "$PATH_TO_YOUR_BENCH"
bench get-app https://github.com/mohanad-najeeb/erpnext-arabic-translation
bench --site <site-name> install-app arabic_translations
```

## Docker / production deployment

For Docker or production deployments that build frontend assets into the image,
copy the translations before running `bench build`. The app's installation
hooks run at site/runtime installation, while assets are compiled during the
image build.

Run the translation command after installing the apps and before building assets:

```dockerfile
# Install the app
RUN bench get-app https://github.com/mohanad-najeeb/erpnext-arabic-translation

# Copy translation files for all apps in the environment
RUN bench install-arabic-translations

# Build assets (will include the updated translations)
RUN bench build
```

## Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/arabic_translations
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

## Checking for empty v16 translations

Install the locale tooling and run the read-only checker from the repository root:

```bash
python -m pip install -e ".[locale]"
python scripts/check_empty_translations.py
```

The checker recursively scans PO catalogs in `arabic_translations/locale/other-apps/v16`
and reports the catalog path, entry line number, source text, context (when present),
and empty translation fields, followed by per-file and overall counts. It parses
multiline strings correctly, treats whitespace-only translations as empty, checks
each existing plural translation field, and skips metadata headers and obsolete entries.
It does not modify translation files.

Use `--target-dir PATH` to scan a different directory. Exit codes are `0` when no
empty translations are found, `1` when any are found, and `2` for errors (including
missing directories, no PO catalogs, or unreadable/malformed catalogs).

## License

mit
