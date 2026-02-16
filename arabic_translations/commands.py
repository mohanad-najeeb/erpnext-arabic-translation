import click
import frappe

from arabic_translations.utils import copy_locale_files


@click.command("install-arabic-translations")
@click.option("--site", help="Site name")
def install_arabic_translations(site=None):
	"""
	Copy Arabic locale files to apps.
	If --site is provided, copies only for installed apps on that site.
	If no site is provided, copies for all apps available in the environment (useful for Docker builds).
	"""
	if site:
		click.echo(f"Copying Arabic translations for site: {site}")
		frappe.init(site=site)
		frappe.connect()
		try:
			copy_locale_files()
		finally:
			frappe.destroy()
	else:
		click.echo("No site provided. Copying Arabic translations for all apps in the environment.")
		# We need to initialize frappe enough to use get_all_apps and get_app_path
		# frappe.init('') usually works for basic path resolution
		frappe.init("")
		try:
			apps = frappe.get_all_apps(with_internal=True)
			click.echo(f"Found apps: {', '.join(apps)}")
			copy_locale_files(apps=apps)
		except Exception as e:
			click.echo(f"Error copying translations: {e}")
			raise e


commands = [install_arabic_translations]
