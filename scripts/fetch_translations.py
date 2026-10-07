#!/usr/bin/env python3
"""Fetch Arabic catalogs for CRM, ERPNext, Frappe, and HRMS into sources/v16."""

import argparse
import os
import sys
import tempfile
from pathlib import Path
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import urlopen

import polib

APPS = ("crm", "erpnext", "frappe", "hrms")


def fetch_catalog(app: str, branch: str, timeout: float) -> bytes:
	url = f"https://raw.githubusercontent.com/frappe/{app}/refs/heads/{quote(branch, safe='')}/{app}/locale/ar.po"
	with urlopen(url, timeout=timeout) as response:
		content = response.read()
	catalog = polib.pofile(content.decode("utf-8-sig"), encoding="utf-8")
	language = catalog.metadata.get("Language", "").replace("-", "_").split("_")[0]
	if not catalog or language != "ar":
		raise ValueError(f"{url} did not return a non-empty Arabic PO catalog")
	return content


def save_catalog(path: Path, content: bytes) -> bool:
	if path.exists() and path.read_bytes() == content:
		return False
	path.parent.mkdir(parents=True, exist_ok=True)
	mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
	temporary_path = None
	try:
		with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
			temporary_path = Path(temporary.name)
			temporary.write(content)
		temporary_path.chmod(mode)
		os.replace(temporary_path, path)
	finally:
		if temporary_path is not None:
			temporary_path.unlink(missing_ok=True)
	return True


def positive_timeout(value: str) -> float:
	timeout = float(value)
	if not 0 < timeout < float("inf"):
		raise argparse.ArgumentTypeError("Timeout must be a positive, finite number")
	return timeout


def main(argv: list[str] | None = None) -> int:
	root = Path(__file__).resolve().parents[1]
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--apps", nargs="+", choices=APPS, default=APPS, help="Apps to fetch (default: all)")
	parser.add_argument("--branch", default="develop", help="Upstream branch (default: develop)")
	parser.add_argument("--output-dir", type=Path, default=root / "sources" / "v16")
	parser.add_argument("--timeout", type=positive_timeout, default=30.0, help="Request timeout in seconds")
	args = parser.parse_args(argv)
	failed = 0
	for app in dict.fromkeys(args.apps):
		try:
			content = fetch_catalog(app, args.branch, args.timeout)
			path = args.output_dir / app / "ar.po"
			changed = save_catalog(path, content)
			status = "updated" if changed else "unchanged"
			print(f"{app}: {status} ({len(content):,} bytes) -> {path}")
		except (OSError, URLError, UnicodeError, ValueError) as error:
			failed += 1
			print(f"{app}: failed: {error}", file=sys.stderr)
	return 1 if failed else 0


if __name__ == "__main__":
	raise SystemExit(main())
