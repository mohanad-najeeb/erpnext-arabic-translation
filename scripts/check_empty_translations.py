#!/usr/bin/env python3
"""Report empty translations in the bundled v16 Arabic PO catalogs without modifying them."""

import argparse
import sys
from pathlib import Path

import polib


def empty_fields(entry: polib.POEntry) -> list[str]:
	if entry.obsolete or not entry.msgid.strip():
		return []
	if entry.msgid_plural:
		return [
			f"msgstr[{index}]"
			for index, translation in sorted(entry.msgstr_plural.items())
			if not translation.strip()
		]
	return ["msgstr"] if not entry.msgstr.strip() else []


def main(argv: list[str] | None = None) -> int:
	root = Path(__file__).resolve().parents[1]
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument(
		"--target-dir", type=Path, default=root / "arabic_translations" / "locale" / "other-apps" / "v16"
	)
	parser.add_argument("--summary-only", action="store_true", help="Omit per-entry details")
	args = parser.parse_args(argv)
	total_fields = 0
	total_entries = 0
	try:
		if not args.target_dir.is_dir():
			raise ValueError(f"Target directory does not exist or is not a directory: {args.target_dir}")
		paths = sorted(args.target_dir.rglob("*.po"))
		if not paths:
			raise ValueError(f"No PO catalogs found in {args.target_dir}")
		for path in paths:
			catalog = polib.pofile(str(path), encoding="utf-8")
			entry_count = 0
			field_count = 0
			for entry in catalog:
				fields = empty_fields(entry)
				if not fields:
					continue
				if not args.summary_only:
					context = f" (context: {entry.msgctxt!r})" if entry.msgctxt is not None else ""
					print(f"{path}:{entry.linenum}: {', '.join(fields)}: {entry.msgid!r}{context}")
				entry_count += 1
				field_count += len(fields)
			print(f"{path}: {entry_count} entries with {field_count} empty translation fields")
			total_entries += entry_count
			total_fields += field_count
	except (OSError, UnicodeError, ValueError) as error:
		print(f"Error: {error}", file=sys.stderr)
		return 2
	print(
		f"Total: {total_entries} entries with {total_fields} empty translation fields "
		f"in {len(paths)} catalogs"
	)
	return 1 if total_fields else 0


if __name__ == "__main__":
	raise SystemExit(main())
