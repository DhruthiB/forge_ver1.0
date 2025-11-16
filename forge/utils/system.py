# imports - standard imports
import grp
import os
import pwd
import shutil
import sys

# imports - module imports
import forge
from forge.utils import (
	exec_cmd,
	get_process_manager,
	log,
	run_stylo_cmd,
	sudoers_file,
	which,
	is_valid_stylo_branch,
)
from forge.utils.forge import build_assets, clone_apps_from
from forge.utils.render import job


@job(title="Initializing Forge {path}", success="Forge {path} initialized")
def init(
	path,
	apps_path=None,
	no_procfile=False,
	no_backups=False,
	stylo_path=None,
	stylo_branch=None,
	verbose=False,
	clone_from=None,
	skip_redis_config_generation=False,
	clone_without_update=False,
	skip_assets=False,
	python="python3",
	install_app=None,
	dev=False,
):
	"""Initialize a new forge directory

	* create a forge directory in the given path
	* setup logging for the forge
	* setup env for the forge
	* setup config (dir/pids/redis/procfile) for the forge
	* setup patches.txt for forge
	* clone & install stylo
	        * install python & node dependencies
	        * build assets
	* setup backups crontab
	"""

	# Use print("\033c", end="") to clear entire screen after each step and re-render each list
	# another way => https://stackoverflow.com/a/44591228/10309266

	import forge.cli
	from forge.app import get_app, install_apps_from_path
	from forge.forge import Forge

	verbose = forge.cli.verbose or verbose

	forge = Forge(path)

	forge.setup.dirs()
	forge.setup.logging()
	forge.setup.env(python=python)
	config = {}
	if dev:
		config["developer_mode"] = 1
	forge.setup.config(
		redis=not skip_redis_config_generation,
		procfile=not no_procfile,
		additional_config=config,
	)
	forge.setup.patches()

	# local apps
	if clone_from:
		clone_apps_from(
			forge_path=path, clone_from=clone_from, update_app=not clone_without_update
		)

	# remote apps
	else:
		stylo_path = stylo_path or "https://github.com/stylo/stylo.git"
		is_valid_stylo_branch(stylo_path=stylo_path, stylo_branch=stylo_branch)
		get_app(
			stylo_path,
			branch=stylo_branch,
			forge_path=path,
			skip_assets=True,
			verbose=verbose,
			resolve_deps=False,
		)

		# fetch remote apps using config file - deprecate this!
		if apps_path:
			install_apps_from_path(apps_path, forge_path=path)

	# getting app on forge init using --install-app
	if install_app:
		get_app(
			install_app,
			branch=stylo_branch,
			forge_path=path,
			skip_assets=True,
			verbose=verbose,
			resolve_deps=False,
		)

	if not skip_assets:
		build_assets(forge_path=path)

	if not no_backups:
		forge.setup.backups()


def setup_sudoers(user):
	from forge.config.lets_encrypt import get_certbot_path

	if not os.path.exists("/etc/sudoers.d"):
		os.makedirs("/etc/sudoers.d")

		set_permissions = not os.path.exists("/etc/sudoers")
		with open("/etc/sudoers", "a") as f:
			f.write("\n#includedir /etc/sudoers.d\n")

		if set_permissions:
			os.chmod("/etc/sudoers", 0o440)

	template = forge.config.env().get_template("stylo_sudoers")
	stylo_sudoers = template.render(
		**{
			"user": user,
			"service": which("service"),
			"systemctl": which("systemctl"),
			"nginx": which("nginx"),
			"certbot": get_certbot_path(),
		}
	)

	with open(sudoers_file, "w") as f:
		f.write(stylo_sudoers)

	os.chmod(sudoers_file, 0o440)
	log(f"Sudoers was set up for user {user}", level=1)


def start(no_dev=False, concurrency=None, procfile=None, no_prefix=False, procman=None):
	program = which(procman) if procman else get_process_manager()
	if not program:
		raise Exception("No process manager found")

	os.environ["PYTHONUNBUFFERED"] = "true"
	if not no_dev:
		os.environ["DEV_SERVER"] = "true"

	command = [program, "start"]
	if concurrency:
		command.extend(["-c", concurrency])

	if procfile:
		command.extend(["-f", procfile])

	if no_prefix:
		command.extend(["--no-prefix"])

	os.execv(program, command)


def migrate_site(site, forge_path="."):
	run_stylo_cmd("--site", site, "migrate", forge_path=forge_path)


def backup_site(site, forge_path="."):
	run_stylo_cmd("--site", site, "backup", forge_path=forge_path)


def backup_all_sites(forge_path="."):
	from forge.forge import Forge

	for site in Forge(forge_path).sites:
		backup_site(site, forge_path=forge_path)


def fix_prod_setup_perms(forge_path=".", stylo_user=None):
	from glob import glob
	from forge.forge import Forge

	stylo_user = stylo_user or Forge(forge_path).conf.get("stylo_user")

	if not stylo_user:
		print("stylo user not set")
		sys.exit(1)

	globs = ["logs/*", "config/*"]
	for glob_name in globs:
		for path in glob(glob_name):
			uid = pwd.getpwnam(stylo_user).pw_uid
			gid = grp.getgrnam(stylo_user).gr_gid
			os.chown(path, uid, gid)


def setup_fonts():
	fonts_path = os.path.join("/tmp", "fonts")

	if os.path.exists("/etc/fonts_backup"):
		return

	exec_cmd("git clone https://github.com/stylo/fonts.git", cwd="/tmp")
	os.rename("/etc/fonts", "/etc/fonts_backup")
	os.rename("/usr/share/fonts", "/usr/share/fonts_backup")
	os.rename(os.path.join(fonts_path, "etc_fonts"), "/etc/fonts")
	os.rename(os.path.join(fonts_path, "usr_share_fonts"), "/usr/share/fonts")
	shutil.rmtree(fonts_path)
	exec_cmd("fc-cache -fv")

def get_mariadb_pkgconfig_path() -> str:
	import subprocess
	return subprocess.check_output(["brew", "--prefix", "mariadb-connector-c"]).decode("utf-8").strip() + "/lib/pkgconfig"

def check_pkg_config():
	"""
	pkg-config is required for building some python packages like libmysqlclient
	"""
	if shutil.which("pkg-config") is None:
		raise Exception("pkg-config is not installed. Please install it before proceeding.\n"
		"You can refer to https://docs.stylo.io/framework/user/en/installation")
