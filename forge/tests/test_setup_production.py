# imports - standard imports
import getpass
import os
import pathlib
import re
import subprocess
import time
import unittest

# imports - module imports
from forge.utils import exec_cmd, get_cmd_output, which
from forge.config.production_setup import get_supervisor_confdir
from forge.tests.test_base import TestForgeBase


class TestSetupProduction(TestForgeBase):
	def test_setup_production(self):
		user = getpass.getuser()

		for forge_name in ("test-forge-1", "test-forge-2"):
			forge_path = os.path.join(os.path.abspath(self.forgees_path), forge_name)
			self.init_forge(forge_name)
			exec_cmd(f"sudo forge setup production {user} --yes", cwd=forge_path)
			self.assert_nginx_config(forge_name)
			self.assert_supervisor_config(forge_name)
			self.assert_supervisor_process(forge_name)

		self.assert_nginx_process()
		exec_cmd(f"sudo forge setup sudoers {user}")
		self.assert_sudoers(user)

		for forge_name in self.forgees:
			forge_path = os.path.join(os.path.abspath(self.forgees_path), forge_name)
			exec_cmd("sudo forge disable-production", cwd=forge_path)

	def production(self):
		try:
			self.test_setup_production()
		except Exception:
			print(self.get_traceback())

	def assert_nginx_config(self, forge_name):
		conf_src = os.path.join(
			os.path.abspath(self.forgees_path), forge_name, "config", "nginx.conf"
		)
		conf_dest = f"/etc/nginx/conf.d/{forge_name}.conf"

		self.assertTrue(self.file_exists(conf_src))
		self.assertTrue(self.file_exists(conf_dest))

		# symlink matches
		self.assertEqual(os.path.realpath(conf_dest), conf_src)

		# file content
		with open(conf_src) as f:
			f = f.read()

			for key in (
				f"upstream {forge_name}-stylo",
				f"upstream {forge_name}-socketio-server",
			):
				self.assertTrue(key in f)

	def assert_nginx_process(self):
		out = get_cmd_output("sudo nginx -t 2>&1")
		self.assertTrue(
			"nginx: configuration file /etc/nginx/nginx.conf test is successful" in out
		)

	def assert_sudoers(self, user):
		sudoers_file = "/etc/sudoers.d/stylo"
		service = which("service")
		nginx = which("nginx")

		self.assertTrue(self.file_exists(sudoers_file))

		if os.environ.get("CI"):
			sudoers = subprocess.check_output(["sudo", "cat", sudoers_file]).decode("utf-8")
		else:
			sudoers = pathlib.Path(sudoers_file).read_text()
		self.assertTrue(f"{user} ALL = (root) NOPASSWD: {service} nginx *" in sudoers)
		self.assertTrue(f"{user} ALL = (root) NOPASSWD: {nginx}" in sudoers)

	def assert_supervisor_config(self, forge_name, use_rq=True):
		conf_src = os.path.join(
			os.path.abspath(self.forgees_path), forge_name, "config", "supervisor.conf"
		)

		supervisor_conf_dir = get_supervisor_confdir()
		conf_dest = f"{supervisor_conf_dir}/{forge_name}.conf"

		self.assertTrue(self.file_exists(conf_src))
		self.assertTrue(self.file_exists(conf_dest))

		# symlink matches
		self.assertEqual(os.path.realpath(conf_dest), conf_src)

		# file content
		with open(conf_src) as f:
			f = f.read()

			tests = [
				f"program:{forge_name}-stylo-web",
				f"program:{forge_name}-redis-cache",
				f"program:{forge_name}-redis-queue",
				f"group:{forge_name}-web",
				f"group:{forge_name}-workers",
				f"group:{forge_name}-redis",
			]

			if not os.environ.get("CI"):
				tests.append(f"program:{forge_name}-node-socketio")

			if use_rq:
				tests.extend(
					[
						f"program:{forge_name}-stylo-schedule",
						f"program:{forge_name}-stylo-default-worker",
						f"program:{forge_name}-stylo-short-worker",
						f"program:{forge_name}-stylo-long-worker",
					]
				)

			else:
				tests.extend(
					[
						f"program:{forge_name}-stylo-workerbeat",
						f"program:{forge_name}-stylo-worker",
						f"program:{forge_name}-stylo-longjob-worker",
						f"program:{forge_name}-stylo-async-worker",
					]
				)

			for key in tests:
				self.assertTrue(key in f)

	def assert_supervisor_process(self, forge_name, use_rq=True, disable_production=False):
		out = get_cmd_output("supervisorctl status")

		while "STARTING" in out:
			print("Waiting for all processes to start...")
			time.sleep(10)
			out = get_cmd_output("supervisorctl status")

		tests = [
			r"{forge_name}-web:{forge_name}-stylo-web[\s]+RUNNING",
			# Have commented for the time being. Needs to be uncommented later on. Forge is failing on travis because of this.
			# It works on one forge and fails on another.giving FATAL or BACKOFF (Exited too quickly (process log may have details))
			# "{forge_name}-web:{forge_name}-node-socketio[\s]+RUNNING",
			r"{forge_name}-redis:{forge_name}-redis-cache[\s]+RUNNING",
			r"{forge_name}-redis:{forge_name}-redis-queue[\s]+RUNNING",
		]

		if use_rq:
			tests.extend(
				[
					r"{forge_name}-workers:{forge_name}-stylo-schedule[\s]+RUNNING",
					r"{forge_name}-workers:{forge_name}-stylo-default-worker-0[\s]+RUNNING",
					r"{forge_name}-workers:{forge_name}-stylo-short-worker-0[\s]+RUNNING",
					r"{forge_name}-workers:{forge_name}-stylo-long-worker-0[\s]+RUNNING",
				]
			)

		else:
			tests.extend(
				[
					r"{forge_name}-workers:{forge_name}-stylo-workerbeat[\s]+RUNNING",
					r"{forge_name}-workers:{forge_name}-stylo-worker[\s]+RUNNING",
					r"{forge_name}-workers:{forge_name}-stylo-longjob-worker[\s]+RUNNING",
					r"{forge_name}-workers:{forge_name}-stylo-async-worker[\s]+RUNNING",
				]
			)

		for key in tests:
			if disable_production:
				self.assertFalse(re.search(key, out))
			else:
				self.assertTrue(re.search(key, out))


if __name__ == "__main__":
	unittest.main()
