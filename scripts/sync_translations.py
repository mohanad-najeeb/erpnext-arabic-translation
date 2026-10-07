#!/usr/bin/env python3
"""Append new upstream v16 PO entries without changing existing translations."""

import argparse
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import polib


@dataclass
class CatalogUpdate:
	path: Path
	content: bytes
	added: int


def active_keys(catalog: polib.POFile, path: Path) -> set[tuple[str | None, str]]:
	keys: set[tuple[str | None, str]] = set()
	for entry in catalog:
		if entry.obsolete:
			continue
		key = (entry.msgctxt or None, entry.msgid)
		if key in keys:
			raise ValueError(f"Duplicate active entry in {path}: {key!r}")
		keys.add(key)
	return keys


def plan_updates(source_dir: Path, target_dir: Path) -> list[CatalogUpdate]:
	sources = sorted(source_dir.glob("*/ar.po"))
	if not sources:
		raise ValueError(f"No source catalogs found in {source_dir}")
	updates = []
	for source in sources:
		app = source.parent.name
		target = target_dir / app / app / "locale" / "ar.po"
		original = target.read_bytes()
		upstream = polib.pofile(str(source), encoding="utf-8")
		local = polib.pofile(str(target), encoding="utf-8")
		active_keys(upstream, source)
		keys = active_keys(local, target)
		missing = [
			entry
			for entry in upstream
			if not entry.obsolete and (entry.msgctxt or None, entry.msgid) not in keys
		]
		content = original
		if missing:
			newline = b"\r\n" if b"\r\n" in original else b"\n"
			if not content.endswith(newline * 2):
				content += newline if content.endswith(newline) else newline * 2
			additions = "\n".join(str(entry) for entry in missing)
			content += additions.replace("\n", newline.decode("ascii")).encode("utf-8")
			merged = polib.pofile(content.decode("utf-8"), encoding="utf-8")
			if active_keys(merged, target) != keys | active_keys(upstream, source):
				raise ValueError(f"Merged catalog failed key validation: {target}")
		updates.append(CatalogUpdate(target, content, len(missing)))
	return updates


def write_update(update: CatalogUpdate) -> None:
	if not update.added:
		return
	mode = update.path.stat().st_mode & 0o777
	temporary_path = None
	try:
		with tempfile.NamedTemporaryFile(dir=update.path.parent, delete=False) as temporary:
			temporary_path = Path(temporary.name)
			temporary.write(update.content)
		temporary_path.chmod(mode)
		os.replace(temporary_path, update.path)
	finally:
		if temporary_path is not None:
			temporary_path.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
	root = Path(__file__).resolve().parents[1]
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--source-dir", type=Path, default=root / "sources" / "v16")
	parser.add_argument(
		"--target-dir", type=Path, default=root / "arabic_translations" / "locale" / "other-apps" / "v16"
	)
	parser.add_argument("--dry-run", action="store_true", help="Report new entries without writing files")
	args = parser.parse_args(argv)
	try:
		updates = plan_updates(args.source_dir, args.target_dir)
		for update in updates:
			if not args.dry_run:
				write_update(update)
			app = update.path.parents[2].name
			action = "would add" if args.dry_run else "added"
			print(f"{app}: {action} {update.added} new entries")
	except (OSError, UnicodeError, ValueError) as error:
		print(f"Error: {error}", file=sys.stderr)
		return 1
	print(f"Total: {sum(update.added for update in updates)} new entries")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
