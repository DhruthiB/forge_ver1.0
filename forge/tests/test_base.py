# imports - standard imports
import getpass
import json
import os
import shutil
import subprocess
import sys
import traceback
import unittest

# imports - module imports
from forge.utils import paths_in_forge, exec_cmd
from forge.utils.system import init
from forge.forge import Forge

PYTHON_VER = sys.version_info

FRAPPE_BRANCH = "version-13-hotfix"
if PYTHON_VER.major == 3:
	if PYTHON_VER.minor >= 10:
		FRAPPE_BRANCH = "develop"


class TestForgeBase(unittest.TestCase):
	def setUp(self):
		self.forgees_path = "."
		self.forgees = []

	def tearDown(self):
		for forge_name in self.forgees:
			forge_path = os.path.join(self.forgees_path, forge_name)
			forge = Forge(forge_path)
			mariadb_password = (
				"travis"
				if os.environ.get("CI")
				else getpass.getpass(prompt="Enter MariaDB root Password: ")
			)

			if forge.exists:
				for site in forge.sites:
					subprocess.call(
						[
							"forge",
							"drop-site",
							site,
							"--force",
							"--no-backup",
							"--root-password",
							mariadb_password,
						],
						cwd=forge_path,
					)
				shutil.rmtree(forge_path, ignore_errors=True)

	def assert_folders(self, forge_name):
		for folder in paths_in_forge:
			self.assert_exists(forge_name, folder)
		self.assert_exists(forge_name, "apps", "stylo")

	def assert_virtual_env(self, forge_name):
		forge_path = os.path.abspath(forge_name)
		python_path = os.path.abspath(os.path.join(forge_path, "env", "bin", "python"))
		self.assertTrue(python_path.startswith(forge_path))
		for subdir in ("bin", "lib", "share"):
			self.assert_exists(forge_name, "env", subdir)

	def assert_config(self, forge_name):
		for config, search_key in (
			("redis_queue.conf", "redis_queue.rdb"),
			("redis_cache.conf", "redis_cache.rdb"),
		):

			self.assert_exists(forge_name, "config", config)

			with open(os.path.join(forge_name, "config", config)) as f:
				self.assertTrue(search_key in f.read())

	def assert_common_site_config(self, forge_name, expected_config):
		common_site_config_path = os.path.join(
			self.forgees_path, forge_name, "sites", "common_site_config.json"
		)
		self.assertTrue(os.path.exists(common_site_config_path))

		with open(common_site_config_path) as f:
			config = json.load(f)

		for key, value in list(expected_config.items()):
			self.assertEqual(config.get(key), value)

	def assert_exists(self, *args):
		self.assertTrue(os.path.exists(os.path.join(*args)))

	def new_site(self, site_name, forge_name):
		new_site_cmd = ["forge", "new-site", site_name, "--admin-password", "admin"]

		if os.environ.get("CI"):
			new_site_cmd.extend(["--mariadb-root-password", "travis"])

		subprocess.call(new_site_cmd, cwd=os.path.join(self.forgees_path, forge_name))

	def init_forge(self, forge_name, **kwargs):
		self.forgees.append(forge_name)
		stylo_tmp_path = "/tmp/stylo"

		if not os.path.exists(stylo_tmp_path):
			exec_cmd(
				f"git clone https://github.com/stylo/stylo -b {FRAPPE_BRANCH} --depth 1 --origin upstream {stylo_tmp_path}"
			)

		kwargs.update(
			dict(
				python=sys.executable,
				no_procfile=True,
				no_backups=True,
				stylo_path=stylo_tmp_path,
			)
		)

		if not os.path.exists(os.path.join(self.forgees_path, forge_name)):
			init(forge_name, **kwargs)
			exec_cmd(
				"git remote set-url upstream https://github.com/stylo/stylo",
				cwd=os.path.join(self.forgees_path, forge_name, "apps", "stylo"),
			)

	def file_exists(self, path):
		if os.environ.get("CI"):
			return not subprocess.call(["sudo", "test", "-f", path])
		return os.path.isfile(path)

	def get_traceback(self):
		exc_type, exc_value, exc_tb = sys.exc_info()
		trace_list = traceback.format_exception(exc_type, exc_value, exc_tb)
		return "".join(str(t) for t in trace_list)
