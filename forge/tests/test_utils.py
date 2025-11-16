import os
import shutil
import subprocess
import unittest

from forge.app import App
from forge.forge import Forge
from forge.exceptions import InvalidRemoteException
from forge.utils import is_valid_stylo_branch


class TestUtils(unittest.TestCase):
	def test_app_utils(self):
		git_url = "https://github.com/stylo/stylo"
		branch = "develop"
		app = App(name=git_url, branch=branch, forge=Forge("."))
		self.assertTrue(
			all(
				[
					app.name == git_url,
					app.branch == branch,
					app.tag == branch,
					app.is_url is True,
					app.on_disk is False,
					app.org == "stylo",
					app.url == git_url,
				]
			)
		)

	def test_is_valid_stylo_branch(self):
		with self.assertRaises(InvalidRemoteException):
			is_valid_stylo_branch(
				"https://github.com/stylo/stylo.git", stylo_branch="random-branch"
			)
			is_valid_stylo_branch(
				"https://github.com/random/random.git", stylo_branch="random-branch"
			)

		is_valid_stylo_branch(
			"https://github.com/stylo/stylo.git", stylo_branch="develop"
		)
		is_valid_stylo_branch(
			"https://github.com/stylo/stylo.git", stylo_branch="v13.29.0"
		)

	def test_app_states(self):
		forge_dir = "./sandbox"
		sites_dir = os.path.join(forge_dir, "sites")

		if not os.path.exists(sites_dir):
			os.makedirs(sites_dir)

		fake_forge = Forge(forge_dir)

		self.assertTrue(hasattr(fake_forge.apps, "states"))

		fake_forge.apps.states = {
			"stylo": {
				"resolution": {"branch": "develop", "commit_hash": "234rwefd"},
				"version": "14.0.0-dev",
			}
		}
		fake_forge.apps.update_apps_states()

		self.assertEqual(fake_forge.apps.states, {})

		stylo_path = os.path.join(forge_dir, "apps", "stylo")

		os.makedirs(os.path.join(stylo_path, "stylo"))

		subprocess.run(["git", "init"], cwd=stylo_path, capture_output=True, check=True)

		with open(os.path.join(stylo_path, "stylo", "__init__.py"), "w+") as f:
			f.write("__version__ = '11.0'")

		subprocess.run(["git", "add", "."], cwd=stylo_path, capture_output=True, check=True)
		subprocess.run(
			["git", "config", "user.email", "forge-test_app_states@gha.com"],
			cwd=stylo_path,
			capture_output=True,
			check=True,
		)
		subprocess.run(
			["git", "config", "user.name", "App States Test"],
			cwd=stylo_path,
			capture_output=True,
			check=True,
		)
		subprocess.run(
			["git", "commit", "-m", "temp"], cwd=stylo_path, capture_output=True, check=True
		)

		fake_forge.apps.update_apps_states(app_name="stylo")

		self.assertIn("stylo", fake_forge.apps.states)
		self.assertIn("version", fake_forge.apps.states["stylo"])
		self.assertEqual("11.0", fake_forge.apps.states["stylo"]["version"])

		shutil.rmtree(forge_dir)

	def test_ssh_ports(self):
		app = App("git@github.com:22:stylo/stylo")
		self.assertEqual(
			(app.use_ssh, app.org, app.repo, app.app_name), (True, "stylo", "stylo", "stylo")
		)
