# Working with locale files (gettext CLI)

Use the official **GNU gettext** tools.

## Fetch upstream catalogs

Refresh the four source catalogs using the Python fetcher:

```bash
uv run --no-project --with polib python scripts/fetch_translations.py

# Fetch selected apps only.
uv run --no-project --with polib python scripts/fetch_translations.py --apps erpnext frappe
```

Downloads are saved to `sources/v16/<app>/ar.po`. The default paths are resolved
relative to the script, so the working directory does not matter. `--output-dir`
overrides the destination, and `--timeout` sets the request timeout in seconds
(default: 30).

Like the original shell script, this fetches the upstream `develop` branches.
The `v16` directory name does not pin an upstream release. Use `--branch` to
select a different branch that exists in each selected app's repository.

The fetcher validates that each download is a non-empty Arabic PO catalog before
replacing the previous file atomically. Identical files are left untouched; no
`ar.po.1` files are created. A failed download leaves that app's existing catalog
intact, reports an error, and continues with the other apps. Any failure gives a
nonzero exit status. Reviewed translation files are never changed by fetching.

If the optional `locale` dependency is installed, use
`python3 scripts/fetch_translations.py` directly. To fetch and preview new strings
in one command:

```bash
uv run --no-project --with polib python scripts/fetch_translations.py && \
uv run --no-project --with polib python scripts/sync_translations.py --dry-run
```

## Append new upstream v16 strings

After fetching fresh catalogs into `sources/v16/<app>/ar.po`, run the sync
script from any working directory. From the repository root, with `uv`:

```bash
# Preview additions without changing files.
uv run --no-project --with polib python scripts/sync_translations.py --dry-run

# Append missing entries.
uv run --no-project --with polib python scripts/sync_translations.py
```

Alternatively, install the optional dependency once and use Python directly:

```bash
python3 -m pip install -e '.[locale]'
python3 scripts/sync_translations.py --dry-run
python3 scripts/sync_translations.py
```

The script discovers each app with a source catalog and updates
`arabic_translations/locale/other-apps/v16/<app>/<app>/locale/ar.po`.
`--source-dir` and `--target-dir` override those two directory roots.

Entries are compared by `msgid` and `msgctxt`. Existing entries, including empty
translations, headers, comments, and formatting, are left byte-for-byte intact.
Only missing active entries are appended, including their upstream translation
(or empty translation), plural forms, comments, references, and flags. Obsolete
upstream entries are skipped. Local-only entries are never deleted. Appended
machine translations still need contextual review.

All input catalogs are parsed and checked for duplicate active entries before
writing starts. A missing target or invalid input fails without applying the
planned updates. Each changed file is replaced atomically; a write failure can
still leave earlier apps updated. Re-running is safe and adds no duplicates.

Run the focused regression tests with:

```bash
uv run --no-project --with polib python -m unittest discover -s tests -p test_sync_translations.py -v
```

## Prerequisites

```bash
# Ubuntu/Debian
sudo apt install gettext

# Verify
msgmerge --version
msgattrib --version
msgcat --version
```

## 1. Extract entries to translate (untranslated only)

From a `.po` file that is already in sync with the template:

```bash
cd arabic_translations/locale/other-apps/v16/frappe/frappe/locale

# Optional: update ar.po with any new strings from main.pot (run from repo root)
msgmerge -U ar.po main.pot

# Extract only untranslated entries → to_translate.po
msgattrib --no-obsolete --untranslated ar.po -o to_translate.po
```

Translate the `msgstr` fields in `to_translate.po` (e.g. save as `translated.po`).

## 2. Merge your translations back into ar.po

After filling in `translated.po`, merge it into `ar.po` (first file wins for duplicate msgids):

```bash
msgcat --use-first translated.po ar.po -o ar_new.po
mv ar_new.po ar.po
```

## One-liner (frappe v16 locale dir)

```bash
LOCALE="arabic_translations/locale/other-apps/v16/frappe/frappe/locale"
msgmerge -U "$LOCALE/ar.po" "$LOCALE/main.pot"
msgattrib --no-obsolete --untranslated "$LOCALE/ar.po" -o "$LOCALE/to_translate.po"
# ... translate to_translate.po → translated.po ...
msgcat --use-first "$LOCALE/translated.po" "$LOCALE/ar.po" -o "$LOCALE/ar_new.po"
mv "$LOCALE/ar_new.po" "$LOCALE/ar.po"
```

Same idea works for `erpnext` or `hrms` by changing the path (e.g. `.../v16/erpnext/erpnext/locale`).

## Contextual Arabic review (v16)

A populated `msgstr` is not evidence that an entry has been reviewed. Review
related workflows together, using the DocType/field comments, source references,
and `msgctxt` to distinguish labels, commands, statuses, and descriptions.
Check every referenced use of a shared entry before choosing its wording. If
these clues are insufficient, inspect the matching v16 source or UI rather than
guessing or doing a catalog-wide word replacement.

Use clear Modern Standard Arabic and keep domain distinctions intact:

- Leave means time off or a leave balance, not sheets of paper.
- Employee advance means a financial advance, not progress or a training level.
- Employee benefits mean compensation benefits, not interest or profits.
- CTC means cost to company; KRA means key result area, not KPI.
- In accounting, AR means accounts receivable, not augmented reality. Debit and
	credit are accounting balance directions, not debt and credit facilities.
- An account manager manages a customer relationship, not a login account.
- A permission role is not a rule; a tree child is a subordinate node.
- CRM "report to" describes a reporting manager, not sending a report.
- A submitted DocType is finalized, not merely emailed or approved by a reviewer.
	Keep document submission separate from workflow approval and job applications.

Preserve `msgid`, `msgctxt`, plural forms, flags, references, placeholders, URLs,
HTML attributes, mentions, and executable examples. Keep formula symbols such
as B, NB, and T consistent between headings and descriptions. Translate the
surrounding explanation without altering field names, enum values in code,
Jinja expressions, or password patterns. Do not reformat entire catalogs.

Validate each edited catalog with gettext when available:

```bash
msgfmt --check --check-format -o /dev/null path/to/ar.po
```

Also compare edited entries with their original versions to check message keys,
placeholder multiplicity, HTML structure, and embedded code. Record pre-existing
validation failures separately. A successful compilation does not establish
linguistic correctness; verify important workflows in the Arabic v16 UI.

### First review batch (2026-10-07)

This is a partial review, not certification of any complete catalog:

- HRMS: selected early entries covering leave, advances, attendance, recruitment,
	appraisal, benefits, CTC, and payroll help examples.
- ERPNext: selected accounting, accepted-stock, and demand-planning entries.
- Frappe: selected permissions, actions, hierarchy, and API credential entries.
- CRM: selected early hierarchy, assignment, invitation, and credential entries.

The remaining entries, cross-catalog terminology consistency, plural wording,
and live UI rendering still need review. Ambiguous labels such as `Bimonthly`,
`Allocate on Day`, and shift "break" actions require source-level confirmation.
POS Awesome and all v15 catalogs are outside this batch.
