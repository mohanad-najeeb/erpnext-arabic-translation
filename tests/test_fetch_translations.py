import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from scripts.fetch_translations import fetch_catalog, main, save_catalog

CATALOG = (
	b'msgid ""\nmsgstr ""\n'
	b'"Language: ar_SA\\n"\n'
	b'"Content-Type: text/plain; charset=UTF-8\\n"\n\n'
	b'msgid "Hello"\nmsgstr "Translation"\n'
)


class FetchTranslationsTests(unittest.TestCase):
	def setUp(self):
		self.temporary = tempfile.TemporaryDirectory()
		self.addCleanup(self.temporary.cleanup)
		self.root = Path(self.temporary.name)

	def test_fetch_validates_catalog_and_preserves_downloaded_bytes(self):
		with patch("scripts.fetch_translations.urlopen", return_value=io.BytesIO(CATALOG)) as request:
			self.assertEqual(fetch_catalog("crm", "develop", 12), CATALOG)
		request.assert_called_once_with(
			"https://raw.githubusercontent.com/frappe/crm/refs/heads/develop/crm/locale/ar.po", timeout=12
		)

	def test_invalid_downloads_are_rejected(self):
		for content in (b"", b"<html>Not a catalog</html>", CATALOG.replace(b"ar_SA", b"en_US"), b"\xff"):
			with self.subTest(content=content):
				with patch("scripts.fetch_translations.urlopen", return_value=io.BytesIO(content)):
					with self.assertRaises((OSError, ValueError, UnicodeError)):
						fetch_catalog("crm", "develop", 30)

	def test_save_creates_directories_and_refreshes_without_numbered_files(self):
		path = self.root / "crm" / "ar.po"
		self.assertTrue(save_catalog(path, CATALOG))
		path.chmod(0o640)
		before = path.stat().st_mtime_ns
		self.assertFalse(save_catalog(path, CATALOG))
		self.assertEqual(path.stat().st_mtime_ns, before)
		updated = CATALOG.replace(b"Hello", b"Goodbye")
		self.assertTrue(save_catalog(path, updated))
		self.assertEqual(path.read_bytes(), updated)
		self.assertEqual(path.stat().st_mode & 0o777, 0o640)
		self.assertEqual(list(path.parent.iterdir()), [path])

	def test_failed_replace_preserves_old_file_and_cleans_temporary_file(self):
		path = self.root / "ar.po"
		path.write_bytes(b"old content")
		with patch("scripts.fetch_translations.os.replace", side_effect=OSError("Cannot replace")):
			with self.assertRaises(OSError):
				save_catalog(path, CATALOG)
		self.assertEqual(path.read_bytes(), b"old content")
		self.assertEqual(list(self.root.iterdir()), [path])

	def test_failed_download_preserves_old_file_and_continues_other_apps(self):
		path = self.root / "crm" / "ar.po"
		path.parent.mkdir()
		path.write_bytes(b"old content")
		with (
			patch("scripts.fetch_translations.urlopen", side_effect=[URLError("Offline"), io.BytesIO(CATALOG)]),
			contextlib.redirect_stdout(io.StringIO()) as output,
			contextlib.redirect_stderr(io.StringIO()) as errors,
		):
			result = main(["--apps", "crm", "hrms", "--output-dir", str(self.root)])
		self.assertEqual(result, 1)
		self.assertEqual(path.read_bytes(), b"old content")
		self.assertEqual((self.root / "hrms" / "ar.po").read_bytes(), CATALOG)
		self.assertIn("crm: failed", errors.getvalue())
		self.assertIn("hrms: updated", output.getvalue())

	def test_invalid_catalog_does_not_replace_existing_file(self):
		path = self.root / "crm" / "ar.po"
		path.parent.mkdir()
		path.write_bytes(b"old content")
		with (
			patch("scripts.fetch_translations.urlopen", return_value=io.BytesIO(b"")),
			contextlib.redirect_stderr(io.StringIO()),
		):
			self.assertEqual(main(["--apps", "crm", "--output-dir", str(self.root)]), 1)
		self.assertEqual(path.read_bytes(), b"old content")

	def test_rejects_non_positive_or_non_finite_timeout(self):
		for timeout in ("0", "-1", "nan", "inf"):
			with self.subTest(timeout=timeout), contextlib.redirect_stderr(io.StringIO()):
				with self.assertRaises(SystemExit) as error:
					main(["--timeout", timeout])
				self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
	unittest.main()
