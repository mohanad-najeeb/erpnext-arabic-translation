import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import polib

from scripts.check_empty_translations import empty_fields, main


class CheckEmptyTranslationsTests(unittest.TestCase):
	def test_singular_empty_and_whitespace(self):
		for translation in ("", " \t\n"):
			with self.subTest(translation=translation):
				self.assertEqual(empty_fields(polib.POEntry(msgid="Empty", msgstr=translation)), ["msgstr"])

	def test_translated_header_and_obsolete_entries_are_skipped(self):
		for entry in (
			polib.POEntry(msgid="Translated", msgstr="Translation"),
			polib.POEntry(msgid="", msgstr=""),
			polib.POEntry(msgid="  \t\n", msgstr=""),
			polib.POEntry(msgid="Removed", msgstr="", obsolete=True),
			polib.POEntry(msgid="Multiline", msgstr="\nTranslation\n"),
		):
			with self.subTest(entry=entry):
				self.assertEqual(empty_fields(entry), [])

	def test_plural_fields_are_checked_individually(self):
		entry = polib.POEntry(
			msgid="Item",
			msgid_plural="Items",
			msgstr_plural={0: "", 1: "Translated", 2: " ", 3: "Translated", 4: "Translated", 5: ""},
		)
		self.assertEqual(empty_fields(entry), ["msgstr[0]", "msgstr[2]", "msgstr[5]"])

	def test_recursive_report_includes_context_and_does_not_write(self):
		with tempfile.TemporaryDirectory() as directory:
			root = Path(directory)
			path = root / "app" / "app" / "locale" / "ar.po"
			path.parent.mkdir(parents=True)
			catalog = polib.POFile()
			catalog.append(polib.POEntry(msgid="Open", msgctxt="Button", msgstr=""))
			catalog.append(polib.POEntry(msgid="Multiline", msgstr="\nTranslation\n"))
			catalog.save(str(path))
			original = path.read_bytes()
			with contextlib.redirect_stdout(io.StringIO()) as output:
				result = main(["--target-dir", str(root)])
			self.assertEqual(result, 1)
			report = output.getvalue()
			entry = polib.pofile(str(path))[0]
			self.assertIn(f"{path}:{entry.linenum}: msgstr: 'Open' (context: 'Button')", report)
			self.assertIn("1 entries with 1 empty translation fields", report)
			self.assertIn("Total: 1 entries with 1 empty translation fields in 1 catalogs", report)
			self.assertEqual(path.read_bytes(), original)

	def test_summary_only_reports_counts_without_entry_details(self):
		with tempfile.TemporaryDirectory() as directory:
			path = Path(directory) / "ar.po"
			catalog = polib.POFile()
			catalog.append(polib.POEntry(msgid="  ", msgstr=""))
			catalog.append(polib.POEntry(msgid="Needs translation", msgstr=""))
			catalog.save(str(path))
			with contextlib.redirect_stdout(io.StringIO()) as output:
				self.assertEqual(main(["--target-dir", directory, "--summary-only"]), 1)
			self.assertEqual(
				output.getvalue(),
				f"{path}: 1 entries with 1 empty translation fields\n"
				"Total: 1 entries with 1 empty translation fields in 1 catalogs\n",
			)

	def test_clean_catalog_returns_zero(self):
		with tempfile.TemporaryDirectory() as directory:
			path = Path(directory) / "ar.po"
			path.write_text('msgid "Translated"\nmsgstr ""\n"Valid "\n"translation"\n', encoding="utf-8")
			with contextlib.redirect_stdout(io.StringIO()) as output:
				self.assertEqual(main(["--target-dir", directory]), 0)
			self.assertIn("Total: 0 entries with 0 empty translation fields in 1 catalogs", output.getvalue())

	def test_missing_empty_or_malformed_catalogs_return_error(self):
		with tempfile.TemporaryDirectory() as directory:
			root = Path(directory)
			for target in (root / "missing", root):
				with self.subTest(target=target), contextlib.redirect_stderr(io.StringIO()) as output:
					self.assertEqual(main(["--target-dir", str(target)]), 2)
				self.assertIn("Error:", output.getvalue())
			(root / "ar.po").write_text("invalid PO syntax\n", encoding="utf-8")
			with contextlib.redirect_stderr(io.StringIO()) as output:
				self.assertEqual(main(["--target-dir", directory]), 2)
			self.assertIn("Error:", output.getvalue())


if __name__ == "__main__":
	unittest.main()
