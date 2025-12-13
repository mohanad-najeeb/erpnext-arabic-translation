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
