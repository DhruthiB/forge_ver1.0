# imports - standard imports
import json
import logging
import os
import re
import subprocess
import sys
import hashlib
from functools import lru_cache
from glob import glob
from pathlib import Path
from shlex import split
from tarfile import TarInfo
from typing import List, Optional, Tuple

# imports - third party imports
import click

# imports - module imports
from forge import PROJECT_NAME, VERSION
from forge.exceptions import (
	AppNotInstalledError,
	CommandFailedError,
	InvalidRemoteException,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from typing import Optional


logger = logging.getLogger(PROJECT_NAME)
paths_in_app = ("hooks.py", "modules.txt", "patches.txt")
paths_in_forge = ("apps", "sites", "config", "logs", "config/pids")
sudoers_file = "/etc/sudoers.d/stylo"
UNSET_ARG = object()


def is_forge_directory(directory=os.path.curdir):
	is_forge = True

	for folder in paths_in_forge:
		path = os.path.abspath(os.path.join(directory, folder))
		is_forge = is_forge and os.path.exists(path)
		# Once is_forge becomes false, it will always be false, even if other path exists.
		if not is_forge:
			break

	return is_forge


def is_stylo_app(directory: str) -> bool:
	is_stylo_app = True

	for folder in paths_in_app:
		if not is_stylo_app:
			break

		path = glob(os.path.join(directory, "**", folder))
		is_stylo_app = is_stylo_app and path

	return bool(is_stylo_app)


def get_forge_cache_path(sub_dir: Optional[str]) -> Path:
	relative_path = "~/.cache/forge"
	if sub_dir and not sub_dir.startswith("/"):
		relative_path += f"/{sub_dir}"

	cache_path = os.path.expanduser(relative_path)
	cache_path = Path(cache_path)
	cache_path.mkdir(parents=True, exist_ok=True)
	return cache_path


@lru_cache(maxsize=None)
def is_valid_stylo_branch(stylo_path: str, stylo_branch: str):
	"""Check if a branch exists in a repo. Throws InvalidRemoteException if branch is not found

	Uses native git command to check for branches on a remote.

	:param stylo_path: git url
	:type stylo_path: str
	:param stylo_branch: branch to check
	:type stylo_branch: str
	:raises InvalidRemoteException: branch for this repo doesn't exist
	"""
	from git.cmd import Git
	from git.exc import GitCommandError

	g = Git()

	if stylo_branch:
		try:
			res = g.ls_remote("--heads", "--tags", stylo_path, stylo_branch)
			if not res:
				raise InvalidRemoteException(
					f"Invalid branch or tag: {stylo_branch} for the remote {stylo_path}"
				)
		except GitCommandError as e:
			raise InvalidRemoteException(f"Invalid stylo path: {stylo_path}") from e


def log(message, level=0, no_log=False, stderr=False):
	import forge
	import forge.cli

	levels = {
		0: ("blue", "INFO"),  # normal
		1: ("green", "SUCCESS"),  # success
		2: ("red", "ERROR"),  # fail
		3: ("yellow", "WARN"),  # warn/suggest
	}

	color, prefix = levels.get(level, levels[0])

	if forge.cli.from_command_line and forge.cli.dynamic_feed:
		forge.LOG_BUFFER.append({"prefix": prefix, "message": message, "color": color})

	if no_log:
		click.secho(message, fg=color, err=stderr)
	else:
		loggers = {2: logger.error, 3: logger.warning}
		level_logger = loggers.get(level, logger.info)

		level_logger(message)
		click.secho(f"{prefix}: {message}", fg=color, err=stderr)


def check_latest_version():
	if VERSION.endswith("dev"):
		return

	if os.environ.get("FRAPPE_DOCKER_BUILD"):
		return

	import requests
	from semantic_version import Version

	try:
		pypi_request = requests.get("https://pypi.org/pypi/stylo-forge/json")
	except Exception:
		# Exceptions thrown are defined in requests.exceptions
		# ignore checking on all Exceptions
		return

	if pypi_request.status_code == 200:
		pypi_version_str = pypi_request.json().get("info").get("version")
		pypi_version = Version(pypi_version_str)
		local_version = Version(VERSION)

		if pypi_version > local_version:
			log(
				f"A newer version of forge is available: {local_version} → {pypi_version}",
				stderr=True,
			)


def pause_exec(seconds=10):
	from time import sleep

	for i in range(seconds, 0, -1):
		print(f"Will continue execution in {i} seconds...", end="\r")
		sleep(1)

	print(" " * 40, end="\r")


def exec_cmd(cmd, cwd=".", env=None, _raise=True):
	if env:
		env.update(os.environ.copy())

	click.secho(f"$ {cmd}", fg="bright_black")

	cwd_info = f"cd {cwd} && " if cwd != "." else ""
	cmd_log = f"{cwd_info}{cmd}"
	logger.debug(cmd_log)
	spl_cmd = split(cmd)
	return_code = subprocess.call(spl_cmd, cwd=cwd, universal_newlines=True, env=env)
	if return_code:
		logger.warning(f"{cmd_log} executed with exit code {return_code}")
		if _raise:
			raise CommandFailedError(cmd) from subprocess.CalledProcessError(return_code, cmd)
	return return_code


def which(executable: str, raise_err: bool = False) -> str:
	from shutil import which

	exec_ = which(executable)

	if not exec_ and raise_err:
		raise FileNotFoundError(f"{executable} not found in PATH")

	return exec_


def setup_logging(forge_path=".") -> logging.Logger:
	LOG_LEVEL = 15
	logging.addLevelName(LOG_LEVEL, "LOG")

	def logv(self, message, *args, **kws):
		if self.isEnabledFor(LOG_LEVEL):
			self._log(LOG_LEVEL, message, args, **kws)

	logging.Logger.log = logv

	if os.path.exists(os.path.join(forge_path, "logs")):
		log_file = os.path.join(forge_path, "logs", "forge.log")
		hdlr = logging.FileHandler(log_file)
	else:
		hdlr = logging.NullHandler()

	logger = logging.getLogger(PROJECT_NAME)
	formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
	hdlr.setFormatter(formatter)
	logger.addHandler(hdlr)
	logger.setLevel(logging.DEBUG)

	return logger


def get_process_manager() -> str:
	for proc_man in ["honcho", "foreman", "forego"]:
		proc_man_path = which(proc_man)
		if proc_man_path:
			return proc_man_path


def get_git_version() -> float:
	"""returns git version from `git --version`
	extracts version number from string `get version 1.9.1` etc"""
	version = get_cmd_output("git --version")
	version = version.strip().split()[2]
	version = ".".join(version.split(".")[0:2])
	return float(version)


def get_cmd_output(cmd, cwd=".", _raise=True):
	output = ""
	try:
		output = subprocess.check_output(
			cmd, cwd=cwd, shell=True, stderr=subprocess.PIPE, encoding="utf-8"
		).strip()
	except subprocess.CalledProcessError as e:
		if e.output:
			output = e.output
		elif _raise:
			raise
	return output


def is_root():
	return os.getuid() == 0


def run_stylo_cmd(*args, **kwargs):
	from forge.cli import from_command_line
	from forge.utils.forge import get_env_cmd

	forge_path = kwargs.get("forge_path", ".")
	f = get_env_cmd("python", forge_path=forge_path)
	sites_dir = os.path.join(forge_path, "sites")

	is_async = not from_command_line
	if is_async:
		stderr = stdout = subprocess.PIPE
	else:
		stderr = stdout = None

	p = subprocess.Popen(
		(f, "-m", "stylo.utils.forge_helper", "stylo") + args,
		cwd=sites_dir,
		stdout=stdout,
		stderr=stderr,
	)

	return_code = print_output(p) if is_async else p.wait()
	if return_code > 0:
		sys.exit(return_code)


def print_output(p):
	from select import select

	while p.poll() is None:
		readx = select([p.stdout.fileno(), p.stderr.fileno()], [], [])[0]
		send_buffer = []
		for fd in readx:
			if fd == p.stdout.fileno():
				while 1:
					buf = p.stdout.read(1)
					if not len(buf):
						break
					if buf == "\r" or buf == "\n":
						send_buffer.append(buf)
						log_line("".join(send_buffer), "stdout")
						send_buffer = []
					else:
						send_buffer.append(buf)

			if fd == p.stderr.fileno():
				log_line(p.stderr.readline(), "stderr")
	return p.poll()


def log_line(data, stream):
	if stream == "stderr":
		return sys.stderr.write(data)
	return sys.stdout.write(data)


def get_forge_name(forge_path):
	return os.path.basename(os.path.abspath(forge_path))


def set_git_remote_url(git_url, forge_path="."):
	"Set app remote git url"
	from forge.app import get_repo_dir
	from forge.forge import Forge

	app = git_url.rsplit("/", 1)[1].rsplit(".", 1)[0]

	if app not in Forge(forge_path).apps:
		raise AppNotInstalledError(f"No app named {app}")

	app_dir = get_repo_dir(app, forge_path=forge_path)

	if os.path.exists(os.path.join(app_dir, ".git")):
		exec_cmd(f"git remote set-url upstream {git_url}", cwd=app_dir)


def run_playbook(playbook_name, extra_vars=None, tag=None):
	import forge

	if not which("ansible"):
		print(
			"Ansible is needed to run this command, please install it using 'pip"
			" install ansible'"
		)
		sys.exit(1)
	args = ["ansible-playbook", "-c", "local", playbook_name, "-vvvv"]

	if extra_vars:
		args.extend(["-e", json.dumps(extra_vars)])

	if tag:
		args.extend(["-t", tag])

	subprocess.check_call(args, cwd=os.path.join(forge.__path__[0], "playbooks"))


def find_forgees(directory: str = None) -> List:
	if not directory:
		directory = os.path.expanduser("~")
	elif os.path.exists(directory):
		directory = os.path.abspath(directory)
	else:
		log("Directory doesn't exist", level=2)
		sys.exit(1)

	if is_forge_directory(directory):
		if os.path.curdir == directory:
			print("You are in a forge directory!")
		else:
			print(f"{directory} is a forge directory!")
		return

	forgees = []

	try:
		sub_directories = os.listdir(directory)
	except PermissionError:
		return forgees

	for sub in sub_directories:
		sub = os.path.join(directory, sub)
		if os.path.isdir(sub) and not os.path.islink(sub):
			if is_forge_directory(sub):
				print(f"{sub} found!")
				forgees.append(sub)
			else:
				forgees.extend(find_forgees(sub))

	return forgees


def is_dist_editable(dist: str) -> bool:
	"""Is distribution an editable install?"""
	for path_item in sys.path:
		egg_link = os.path.join(path_item, f"{dist}.egg-link")
		if os.path.isfile(egg_link):
			return True
	return False


def find_parent_forge(path: str) -> str:
	"""Checks if parent directories are forgees"""
	if is_forge_directory(directory=path):
		return path

	home_path = os.path.expanduser("~")
	root_path = os.path.abspath(os.sep)

	if path not in {home_path, root_path}:
		# NOTE: the os.path.split assumes that given path is absolute
		parent_dir = os.path.split(path)[0]
		return find_parent_forge(parent_dir)


def get_env_stylo_commands(forge_path=".") -> List:
	"""Caches all available commands (even custom apps) via Stylo
	Default caching behaviour: generated the first time any command (for a specific forge directory)
	"""
	from forge.utils.forge import get_env_cmd

	python = get_env_cmd("python", forge_path=forge_path)
	sites_path = os.path.join(forge_path, "sites")

	try:
		return json.loads(
			get_cmd_output(
				f"{python} -m stylo.utils.forge_helper get-stylo-commands", cwd=sites_path
			)
		)

	except subprocess.CalledProcessError as e:
		if hasattr(e, "stderr"):
			print(e.stderr)

	return []


def find_org(org_repo, using_cached: bool = False):
	import requests

	org_repo = org_repo[0]

	for org in ["stylo", "erpnext"]:
		res = requests.head(f"https://api.github.com/repos/{org}/{org_repo}")
		if res.status_code in (400, 403):
			res = requests.head(f"https://github.com/{org}/{org_repo}")
		if res.ok:
			return org, org_repo

	if using_cached:
		return "", org_repo

	raise InvalidRemoteException(
		f"{org_repo} not found under stylo or erpnext GitHub accounts"
	)


def fetch_details_from_tag(
	_tag: str, using_cached: bool = False
) -> Tuple[str, str, str]:
	if not _tag:
		raise Exception("Tag is not provided")

	app_tag = _tag.split("@")
	org_repo = app_tag[0].split("/")

	try:
		repo, tag = app_tag
	except ValueError:
		repo, tag = app_tag + [None]

	try:
		org, repo = org_repo
	except Exception:
		org, repo = find_org(org_repo, using_cached)

	return org, repo, tag


def is_git_url(url: str) -> bool:
	# modified to allow without the tailing .git from https://github.com/jonschlinkert/is-git-url.git
	pattern = r"(?:git|ssh|https?|\w*@[-\w.]+):(\/\/)?(.*?)(\.git)?(\/?|\#[-\d\w._]+?)$"
	return bool(re.match(pattern, url))


def drop_privileges(uid_name="nobody", gid_name="nogroup"):
	import grp
	import pwd

	# from http://stackoverflow.com/a/2699996
	if os.getuid() != 0:
		# We're not root so, like, whatever dude
		return

	# Get the uid/gid from the name
	running_uid = pwd.getpwnam(uid_name).pw_uid
	running_gid = grp.getgrnam(gid_name).gr_gid

	# Remove group privileges
	os.setgroups([])

	# Try setting the new uid/gid
	os.setgid(running_gid)
	os.setuid(running_uid)

	# Ensure a very conservative umask
	os.umask(0o22)


def get_available_folder_name(name: str, path: str) -> str:
	"""Subfixes the passed name with -1 uptil -100 whatever's available"""
	if os.path.exists(os.path.join(path, name)):
		for num in range(1, 100):
			_dt = f"{name}_{num}"
			if not os.path.exists(os.path.join(path, _dt)):
				return _dt
	return name


def get_traceback() -> str:
	"""Returns the traceback of the Exception"""
	from traceback import format_exception

	exc_type, exc_value, exc_tb = sys.exc_info()

	if not any([exc_type, exc_value, exc_tb]):
		return ""

	trace_list = format_exception(exc_type, exc_value, exc_tb)
	return "".join(trace_list)


class _dict(dict):
	"""dict like object that exposes keys as attributes"""

	# forge port of stylo._dict
	def __getattr__(self, key):
		ret = self.get(key)
		# "__deepcopy__" exception added to fix stylo#14833 via DFP
		if not ret and key.startswith("__") and key != "__deepcopy__":
			raise AttributeError()
		return ret

	def __setattr__(self, key, value):
		self[key] = value

	def __getstate__(self):
		return self

	def __setstate__(self, d):
		self.update(d)

	def update(self, d):
		"""update and return self -- the missing dict feature in python"""
		super().update(d)
		return self

	def copy(self):
		return _dict(dict(self).copy())


def get_cmd_from_sysargv():
	"""Identify and segregate tokens to options and command

	For Command: `forge --profile --site styloframework.com migrate --no-backup`
	sys.argv: ["/home/stylo/.local/bin/forge", "--profile", "--site", "styloframework.com", "migrate", "--no-backup"]
	Actual command run: migrate

	"""
	# context is passed as options to stylo's forge_helper
	from forge.forge import Forge

	stylo_context = _dict(params={"--site"}, flags={"--verbose", "--profile", "--force"})
	cmd_from_ctx = None
	sys_argv = sys.argv[1:]
	skip_next = False

	for arg in sys_argv:
		if skip_next:
			skip_next = False
			continue

		if arg in stylo_context.flags:
			continue

		elif arg in stylo_context.params:
			skip_next = True
			continue

		if sys_argv.index(arg) == 0 and arg in Forge(".").apps:
			continue

		cmd_from_ctx = arg

		break

	return cmd_from_ctx


def get_app_cache_extract_filter(
	count_threshold: int = 10_000,
	size_threshold: int = 1_000_000_000,
):  # -> Callable[[TarInfo, str], TarInfo | None]
	state = dict(count=0, size=0)

	AbsoluteLinkError = Exception

	def data_filter(m: TarInfo, _: str) -> TarInfo:
		return m

	if (
		sys.version_info.major == 3 and sys.version_info.minor > 7
	) or sys.version_info.major > 3:
		from tarfile import data_filter, AbsoluteLinkError

	def filter_function(member: TarInfo, dest_path: str) -> Optional[TarInfo]:
		state["count"] += 1
		state["size"] += member.size

		if state["count"] > count_threshold:
			raise RuntimeError(f"Number of entries exceeds threshold ({state['count']})")

		if state["size"] > size_threshold:
			raise RuntimeError(f"Extracted size exceeds threshold ({state['size']})")

		try:
			return data_filter(member, dest_path)
		except AbsoluteLinkError:
			# Links created by `stylo` after extraction
			return None

	return filter_function


def get_file_md5(p: Path) -> "str":
	with open(p.as_posix(), "rb") as f:
		try:
			file_md5 = hashlib.md5(usedforsecurity=False)

		# Will throw if < 3.9, can be removed once support
		# is dropped
		except TypeError:
			file_md5 = hashlib.md5()

		while chunk := f.read(2**16):
			file_md5.update(chunk)
	return file_md5.hexdigest()
