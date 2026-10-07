import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import polib

from scripts.sync_translations import main, plan_updates, write_update


class SyncTranslationsTests(unittest.TestCase):
	def setUp(self):
		self.temporary = tempfile.TemporaryDirectory()
		self.addCleanup(self.temporary.cleanup)
		self.root = Path(self.temporary.name)
		self.source_dir = self.root / "sources"
		self.target_dir = self.root / "targets"
		self.source = self.source_dir / "hrms" / "ar.po"
		self.target = self.target_dir / "hrms" / "hrms" / "locale" / "ar.po"
		self.source.parent.mkdir(parents=True)
		self.target.parent.mkdir(parents=True)

	def save_catalog(self, path, entries):
		catalog = polib.POFile()
		catalog.metadata = {
			"Language": "ar",
			"Content-Type": "text/plain; charset=UTF-8",
			"Plural-Forms": "nplurals=6; plural=(n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n%100>=3 && n%100<=10 ? 3 : n%100>=11 && n%100<=99 ? 4 : 5);",
		}
		catalog.extend(entries)
		catalog.save(str(path))

	def test_preserves_existing_bytes_and_adds_contexts_and_plurals(self):
		self.save_catalog(
			self.target,
			[
				polib.POEntry(msgid="Existing", msgstr="Reviewed"),
				polib.POEntry(msgid="Empty", msgstr=""),
				polib.POEntry(msgid="Open", msgctxt="Status", msgstr="Reviewed status"),
			],
		)
		new_entry = polib.POEntry(
			msgid="New {0}",
			msgstr="Upstream {0}",
			comment="Field description",
			tcomment="Translator note",
			occurrences=[("view.js", "12")],
			flags=["fuzzy"],
		)
		plural = polib.POEntry(
			msgid="{0} item", msgid_plural="{0} items", msgstr_plural={index: "" for index in range(6)}
		)
		self.save_catalog(
			self.source,
			[
				polib.POEntry(msgid="Existing", msgstr="Machine"),
				polib.POEntry(msgid="Empty", msgstr="Machine"),
				polib.POEntry(msgid="Open", msgctxt="Status", msgstr="Machine"),
				polib.POEntry(msgid="Open", msgctxt="Button", msgstr="New button"),
				new_entry,
				plural,
				polib.POEntry(msgid="Removed", msgstr="Old", obsolete=True),
			],
		)
		original = self.target.read_bytes()
		updates = plan_updates(self.source_dir, self.target_dir)
		self.assertEqual(updates[0].added, 3)
		write_update(updates[0])
		self.assertTrue(self.target.read_bytes().startswith(original))
		catalog = polib.pofile(str(self.target))
		self.assertEqual(catalog.find("Existing").msgstr, "Reviewed")
		self.assertEqual(catalog.find("Empty").msgstr, "")
		self.assertEqual(catalog.find("Open", msgctxt="Status").msgstr, "Reviewed status")
		self.assertEqual(catalog.find("Open", msgctxt="Button").msgstr, "New button")
		self.assertEqual(str(catalog.find("New {0}")), str(new_entry))
		self.assertEqual(catalog.find("{0} item").msgstr_plural, plural.msgstr_plural)
		self.assertIsNone(catalog.find("Removed"))
		self.assertEqual(plan_updates(self.source_dir, self.target_dir)[0].added, 0)

	def test_dry_run_does_not_write(self):
		self.save_catalog(self.target, [polib.POEntry(msgid="Existing", msgstr="Reviewed")])
		self.save_catalog(self.source, [polib.POEntry(msgid="New", msgstr="")])
		original = self.target.read_bytes()
		with contextlib.redirect_stdout(io.StringIO()) as output:
			result = main(["--source-dir", str(self.source_dir), "--target-dir", str(self.target_dir), "--dry-run"])
		self.assertEqual(result, 0)
		self.assertIn("would add 1", output.getvalue())
		self.assertEqual(self.target.read_bytes(), original)

	def test_missing_target_fails_before_any_write(self):
		self.save_catalog(self.target, [polib.POEntry(msgid="Existing", msgstr="Reviewed")])
		self.save_catalog(self.source, [polib.POEntry(msgid="New", msgstr="")])
		other_source = self.source_dir / "zz_missing" / "ar.po"
		other_source.parent.mkdir()
		self.save_catalog(other_source, [polib.POEntry(msgid="Other", msgstr="")])
		original = self.target.read_bytes()
		with contextlib.redirect_stderr(io.StringIO()):
			result = main(["--source-dir", str(self.source_dir), "--target-dir", str(self.target_dir)])
		self.assertEqual(result, 1)
		self.assertEqual(self.target.read_bytes(), original)

	def test_duplicate_active_source_entries_are_rejected(self):
		self.save_catalog(self.target, [polib.POEntry(msgid="Existing", msgstr="")])
		self.save_catalog(self.source, [polib.POEntry(msgid="New"), polib.POEntry(msgid="New")])
		with self.assertRaisesRegex(ValueError, "Duplicate active entry"):
			plan_updates(self.source_dir, self.target_dir)

	def test_active_entry_is_added_when_only_obsolete_entry_exists(self):
		self.save_catalog(self.target, [polib.POEntry(msgid="Restored", msgstr="Old", obsolete=True)])
		self.save_catalog(self.source, [polib.POEntry(msgid="Restored", msgstr="New")])
		update = plan_updates(self.source_dir, self.target_dir)[0]
		self.assertEqual(update.added, 1)
		write_update(update)
		self.assertEqual(polib.pofile(str(self.target)).find("Restored").msgstr, "New")

	def test_preserves_crlf_and_missing_final_newline(self):
		self.save_catalog(self.target, [polib.POEntry(msgid="Existing", msgstr="Reviewed")])
		self.save_catalog(self.source, [polib.POEntry(msgid="New", msgstr="")])
		original = self.target.read_bytes().replace(b"\n", b"\r\n").rstrip(b"\r\n")
		self.target.write_bytes(original)
		write_update(plan_updates(self.source_dir, self.target_dir)[0])
		content = self.target.read_bytes()
		self.assertTrue(content.startswith(original))
		self.assertNotIn(b"\n", content.replace(b"\r\n", b""))

	def test_noop_does_not_write_and_no_sources_is_an_error(self):
		self.save_catalog(self.target, [polib.POEntry(msgid="Existing", msgstr="Reviewed")])
		self.save_catalog(self.source, [polib.POEntry(msgid="Existing", msgstr="Machine")])
		update = plan_updates(self.source_dir, self.target_dir)[0]
		before = self.target.stat().st_mtime_ns
		write_update(update)
		self.assertEqual(self.target.stat().st_mtime_ns, before)
		self.source.unlink()
		with self.assertRaisesRegex(ValueError, "No source catalogs"):
			plan_updates(self.source_dir, self.target_dir)


if __name__ == "__main__":
	unittest.main()
