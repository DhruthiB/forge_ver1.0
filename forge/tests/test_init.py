# imports - standard imports
import json
import os
import subprocess
import unittest

# imports - third paty imports
import git

# imports - module imports
from forge.utils import exec_cmd
from forge.app import App
from forge.tests.test_base import FRAPPE_BRANCH, TestForgeBase
from forge.forge import Forge


# changed from stylo_theme because it wasn't maintained and incompatible,
# chat app & wiki was breaking too. hopefully stylo_docs will be maintained
# for longer since docs.erpnext.com is powered by it ;)
TEST_FRAPPE_APP = "stylo_docs"


class TestForgeInit(TestForgeBase):
	def test_utils(self):
		self.assertEqual(subprocess.call("forge"), 0)

	def test_init(self, forge_name="test-forge", **kwargs):
		self.init_forge(forge_name, **kwargs)
		app = App("file:///tmp/stylo")
		self.assertTupleEqual(
			(app.mount_path, app.url, app.repo, app.app_name, app.org),
			("/tmp/stylo", "file:///tmp/stylo", "stylo", "stylo", "stylo"),
		)
		self.assert_folders(forge_name)
		self.assert_virtual_env(forge_name)
		self.assert_config(forge_name)
		test_forge = Forge(forge_name)
		app = App("stylo", forge=test_forge)
		self.assertEqual(app.from_apps, True)

	def basic(self):
		try:
			self.test_init()
		except Exception:
			print(self.get_traceback())

	def test_multiple_forgees(self):
		for forge_name in ("test-forge-1", "test-forge-2"):
			self.init_forge(forge_name, skip_assets=True)

		self.assert_common_site_config(
			"test-forge-1",
			{
				"webserver_port": 8000,
				"socketio_port": 9000,
				"file_watcher_port": 6787,
				"redis_queue": "redis://127.0.0.1:11000",
				"redis_socketio": "redis://127.0.0.1:13000",
				"redis_cache": "redis://127.0.0.1:13000",
			},
		)

		self.assert_common_site_config(
			"test-forge-2",
			{
				"webserver_port": 8001,
				"socketio_port": 9001,
				"file_watcher_port": 6788,
				"redis_queue": "redis://127.0.0.1:11001",
				"redis_socketio": "redis://127.0.0.1:13001",
				"redis_cache": "redis://127.0.0.1:13001",
			},
		)

	def test_new_site(self):
		forge_name = "test-forge"
		site_name = "test-site.local"
		forge_path = os.path.join(self.forgees_path, forge_name)
		site_path = os.path.join(forge_path, "sites", site_name)
		site_config_path = os.path.join(site_path, "site_config.json")

		self.init_forge(forge_name)
		self.new_site(site_name, forge_name)

		self.assertTrue(os.path.exists(site_path))
		self.assertTrue(os.path.exists(os.path.join(site_path, "private", "backups")))
		self.assertTrue(os.path.exists(os.path.join(site_path, "private", "files")))
		self.assertTrue(os.path.exists(os.path.join(site_path, "public", "files")))
		self.assertTrue(os.path.exists(site_config_path))

		with open(site_config_path) as f:
			site_config = json.loads(f.read())

			for key in ("db_name", "db_password"):
				self.assertTrue(key in site_config)
				self.assertTrue(site_config[key])

	def test_get_app(self):
		self.init_forge("test-forge", skip_assets=True)
		forge_path = os.path.join(self.forgees_path, "test-forge")
		exec_cmd(f"forge get-app {TEST_FRAPPE_APP} --skip-assets", cwd=forge_path)
		self.assertTrue(os.path.exists(os.path.join(forge_path, "apps", TEST_FRAPPE_APP)))
		app_installed_in_env = TEST_FRAPPE_APP in subprocess.check_output(
			["forge", "pip", "freeze"], cwd=forge_path
		).decode("utf8")
		self.assertTrue(app_installed_in_env)

	@unittest.skipIf(FRAPPE_BRANCH != "develop", "only for develop branch")
	def test_get_app_resolve_deps(self):
		FRAPPE_APP = "healthcare"
		self.init_forge("test-forge", skip_assets=True)
		forge_path = os.path.join(self.forgees_path, "test-forge")
		exec_cmd(f"forge get-app {FRAPPE_APP} --resolve-deps --skip-assets", cwd=forge_path)
		self.assertTrue(os.path.exists(os.path.join(forge_path, "apps", FRAPPE_APP)))

		states_path = os.path.join(forge_path, "sites", "apps.json")
		self.assertTrue(os.path.exists(states_path))

		with open(states_path) as f:
			states = json.load(f)

		self.assertTrue(FRAPPE_APP in states)

	def test_install_app_from_setup(self):
		app_name = "test-app"
		setup_file_contents = f"""
from setuptools import setup, findpackages
setup(name='{app_name}', version='0.1.0', packages=find_packages())
				"""
		
		from forge.utils.app import get_app_name_from_setup

		parsed_app_name = get_app_name_from_setup(setup_file_contents)

		self.assertEqual(parsed_app_name, app_name)

	def test_install_app(self):
		forge_name = "test-forge"
		site_name = "install-app.test"
		forge_path = os.path.join(self.forgees_path, "test-forge")

		self.init_forge(forge_name, skip_assets=True)
		exec_cmd(
			f"forge get-app {TEST_FRAPPE_APP} --branch master --skip-assets", cwd=forge_path
		)

		self.assertTrue(os.path.exists(os.path.join(forge_path, "apps", TEST_FRAPPE_APP)))

		# check if app is installed
		app_installed_in_env = TEST_FRAPPE_APP in subprocess.check_output(
			["forge", "pip", "freeze"], cwd=forge_path
		).decode("utf8")
		self.assertTrue(app_installed_in_env)

		# create and install app on site
		self.new_site(site_name, forge_name)
		installed_app = not exec_cmd(
			f"forge --site {site_name} install-app {TEST_FRAPPE_APP}",
			cwd=forge_path,
			_raise=False,
		)

		if installed_app:
			app_installed_on_site = subprocess.check_output(
				["forge", "--site", site_name, "list-apps"], cwd=forge_path
			).decode("utf8")
			self.assertTrue(TEST_FRAPPE_APP in app_installed_on_site)

	def test_remove_app(self):
		self.init_forge("test-forge", skip_assets=True)
		forge_path = os.path.join(self.forgees_path, "test-forge")

		exec_cmd(
			f"forge get-app {TEST_FRAPPE_APP} --branch master --overwrite --skip-assets",
			cwd=forge_path,
		)
		exec_cmd(f"forge remove-app {TEST_FRAPPE_APP}", cwd=forge_path)

		with open(os.path.join(forge_path, "sites", "apps.txt")) as f:
			self.assertFalse(TEST_FRAPPE_APP in f.read())
		self.assertFalse(
			TEST_FRAPPE_APP
			in subprocess.check_output(["forge", "pip", "freeze"], cwd=forge_path).decode("utf8")
		)
		self.assertFalse(os.path.exists(os.path.join(forge_path, "apps", TEST_FRAPPE_APP)))

	def test_switch_to_branch(self):
		self.init_forge("test-forge", skip_assets=True)
		forge_path = os.path.join(self.forgees_path, "test-forge")
		app_path = os.path.join(forge_path, "apps", "stylo")

		# * chore: change to 14 when avalible
		prevoius_branch = "version-13"
		if FRAPPE_BRANCH != "develop":
			# assuming we follow `version-#`
			prevoius_branch = f"version-{int(FRAPPE_BRANCH.split('-')[1]) - 1}"

		successful_switch = not exec_cmd(
			f"forge switch-to-branch {prevoius_branch} stylo --upgrade",
			cwd=forge_path,
			_raise=False,
		)
		if successful_switch:
			app_branch_after_switch = str(git.Repo(path=app_path).active_branch)
			self.assertEqual(prevoius_branch, app_branch_after_switch)

		successful_switch = not exec_cmd(
			f"forge switch-to-branch {FRAPPE_BRANCH} stylo --upgrade",
			cwd=forge_path,
			_raise=False,
		)
		if successful_switch:
			app_branch_after_second_switch = str(git.Repo(path=app_path).active_branch)
			self.assertEqual(FRAPPE_BRANCH, app_branch_after_second_switch)


if __name__ == "__main__":
	unittest.main()
