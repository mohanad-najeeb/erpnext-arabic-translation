### Arabic Translations

Arabic Translations for Frappe, ERPNext, HR and CRM

### What it does

- Provides Arabic translations for Frappe, ERPNext, and HRMS.
- On install, auto-detects the Frappe major version (v15 or v16) and copies the matching Arabic locale bundle for each installed app from `arabic_translations/locale/other-apps/{version}` into the app’s `locale/` or `translations/` folder (`ar.po` or `ar.csv`). Existing files are overwritten to ensure fresh strings.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/ibrahim317/erpnext-arabic-full-translation 
bench install-app arabic_translations
```

### Docker / Production Deployment

If you are using Docker or deploying in a production environment where frontend assets are pre-compiled:

Standard installation hooks only run when installing the app on a site (runtime). However, frontend assets (JS/CSS) are compiled during the image build process. To ensure translations are applied to these assets, you must copy the translation files *before* building the assets.

Add the following step to your custom Dockerfile after installing apps but before running `bench build`:

```dockerfile
# Install the app
RUN bench get-app https://github.com/ibrahim317/erpnext-arabic-full-translation

# Copy translation files for all apps in the environment
RUN bench install-arabic-translations

# Build assets (will include the updated translations)
RUN bench build
```

### Contributing

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

### License

mit
