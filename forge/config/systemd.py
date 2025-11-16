# imports - standard imports
import getpass
import os

# imports - third partyimports
import click

# imports - module imports
import forge
from forge.app import use_rq
from forge.forge import Forge
from forge.config.common_site_config import (
	get_gunicorn_workers,
	update_config,
	get_default_max_requests,
	compute_max_requests_jitter,
)
from forge.utils import exec_cmd, which, get_forge_name


def generate_systemd_config(
	forge_path,
	user=None,
	yes=False,
	stop=False,
	create_symlinks=False,
	delete_symlinks=False,
):

	if not user:
		user = getpass.getuser()

	config = Forge(forge_path).conf

	forge_dir = os.path.abspath(forge_path)
	forge_name = get_forge_name(forge_path)

	if stop:
		exec_cmd(
			f"sudo systemctl stop -- $(systemctl show -p Requires {forge_name}.target | cut -d= -f2)"
		)
		return

	if create_symlinks:
		_create_symlinks(forge_path)
		return

	if delete_symlinks:
		_delete_symlinks(forge_path)
		return

	number_of_workers = config.get("background_workers") or 1
	background_workers = []
	for i in range(number_of_workers):
		background_workers.append(
			get_forge_name(forge_path) + "-stylo-default-worker@" + str(i + 1) + ".service"
		)

	for i in range(number_of_workers):
		background_workers.append(
			get_forge_name(forge_path) + "-stylo-short-worker@" + str(i + 1) + ".service"
		)

	for i in range(number_of_workers):
		background_workers.append(
			get_forge_name(forge_path) + "-stylo-long-worker@" + str(i + 1) + ".service"
		)

	web_worker_count = config.get(
		"gunicorn_workers", get_gunicorn_workers()["gunicorn_workers"]
	)
	max_requests = config.get(
		"gunicorn_max_requests", get_default_max_requests(web_worker_count)
	)

	forge_info = {
		"forge_dir": forge_dir,
		"sites_dir": os.path.join(forge_dir, "sites"),
		"user": user,
		"use_rq": use_rq(forge_path),
		"http_timeout": config.get("http_timeout", 120),
		"redis_server": which("redis-server"),
		"node": which("node") or which("nodejs"),
		"redis_cache_config": os.path.join(forge_dir, "config", "redis_cache.conf"),
		"redis_queue_config": os.path.join(forge_dir, "config", "redis_queue.conf"),
		"webserver_port": config.get("webserver_port", 8000),
		"gunicorn_workers": web_worker_count,
		"gunicorn_max_requests": max_requests,
		"gunicorn_max_requests_jitter": compute_max_requests_jitter(max_requests),
		"forge_name": get_forge_name(forge_path),
		"worker_target_wants": " ".join(background_workers),
		"forge_cmd": which("forge"),
	}

	if not yes:
		click.confirm(
			"current systemd configuration will be overwritten. Do you want to continue?",
			abort=True,
		)

	setup_systemd_directory(forge_path)
	setup_main_config(forge_info, forge_path)
	setup_workers_config(forge_info, forge_path)
	setup_web_config(forge_info, forge_path)
	setup_redis_config(forge_info, forge_path)

	update_config({"restart_systemd_on_update": False}, forge_path=forge_path)
	update_config({"restart_supervisor_on_update": False}, forge_path=forge_path)


def setup_systemd_directory(forge_path):
	if not os.path.exists(os.path.join(forge_path, "config", "systemd")):
		os.makedirs(os.path.join(forge_path, "config", "systemd"))


def setup_main_config(forge_info, forge_path):
	# Main config
	forge_template = forge.config.env().get_template("systemd/stylo-forge.target")
	forge_config = forge_template.render(**forge_info)
	forge_config_path = os.path.join(
		forge_path, "config", "systemd", forge_info.get("forge_name") + ".target"
	)

	with open(forge_config_path, "w") as f:
		f.write(forge_config)


def setup_workers_config(forge_info, forge_path):
	# Worker Group
	forge_workers_target_template = forge.config.env().get_template(
		"systemd/stylo-forge-workers.target"
	)
	forge_default_worker_template = forge.config.env().get_template(
		"systemd/stylo-forge-stylo-default-worker.service"
	)
	forge_short_worker_template = forge.config.env().get_template(
		"systemd/stylo-forge-stylo-short-worker.service"
	)
	forge_long_worker_template = forge.config.env().get_template(
		"systemd/stylo-forge-stylo-long-worker.service"
	)
	forge_schedule_worker_template = forge.config.env().get_template(
		"systemd/stylo-forge-stylo-schedule.service"
	)

	forge_workers_target_config = forge_workers_target_template.render(**forge_info)
	forge_default_worker_config = forge_default_worker_template.render(**forge_info)
	forge_short_worker_config = forge_short_worker_template.render(**forge_info)
	forge_long_worker_config = forge_long_worker_template.render(**forge_info)
	forge_schedule_worker_config = forge_schedule_worker_template.render(**forge_info)

	forge_workers_target_config_path = os.path.join(
		forge_path, "config", "systemd", forge_info.get("forge_name") + "-workers.target"
	)
	forge_default_worker_config_path = os.path.join(
		forge_path,
		"config",
		"systemd",
		forge_info.get("forge_name") + "-stylo-default-worker@.service",
	)
	forge_short_worker_config_path = os.path.join(
		forge_path,
		"config",
		"systemd",
		forge_info.get("forge_name") + "-stylo-short-worker@.service",
	)
	forge_long_worker_config_path = os.path.join(
		forge_path,
		"config",
		"systemd",
		forge_info.get("forge_name") + "-stylo-long-worker@.service",
	)
	forge_schedule_worker_config_path = os.path.join(
		forge_path,
		"config",
		"systemd",
		forge_info.get("forge_name") + "-stylo-schedule.service",
	)

	with open(forge_workers_target_config_path, "w") as f:
		f.write(forge_workers_target_config)

	with open(forge_default_worker_config_path, "w") as f:
		f.write(forge_default_worker_config)

	with open(forge_short_worker_config_path, "w") as f:
		f.write(forge_short_worker_config)

	with open(forge_long_worker_config_path, "w") as f:
		f.write(forge_long_worker_config)

	with open(forge_schedule_worker_config_path, "w") as f:
		f.write(forge_schedule_worker_config)


def setup_web_config(forge_info, forge_path):
	# Web Group
	forge_web_target_template = forge.config.env().get_template(
		"systemd/stylo-forge-web.target"
	)
	forge_web_service_template = forge.config.env().get_template(
		"systemd/stylo-forge-stylo-web.service"
	)
	forge_node_socketio_template = forge.config.env().get_template(
		"systemd/stylo-forge-node-socketio.service"
	)

	forge_web_target_config = forge_web_target_template.render(**forge_info)
	forge_web_service_config = forge_web_service_template.render(**forge_info)
	forge_node_socketio_config = forge_node_socketio_template.render(**forge_info)

	forge_web_target_config_path = os.path.join(
		forge_path, "config", "systemd", forge_info.get("forge_name") + "-web.target"
	)
	forge_web_service_config_path = os.path.join(
		forge_path, "config", "systemd", forge_info.get("forge_name") + "-stylo-web.service"
	)
	forge_node_socketio_config_path = os.path.join(
		forge_path,
		"config",
		"systemd",
		forge_info.get("forge_name") + "-node-socketio.service",
	)

	with open(forge_web_target_config_path, "w") as f:
		f.write(forge_web_target_config)

	with open(forge_web_service_config_path, "w") as f:
		f.write(forge_web_service_config)

	with open(forge_node_socketio_config_path, "w") as f:
		f.write(forge_node_socketio_config)


def setup_redis_config(forge_info, forge_path):
	# Redis Group
	forge_redis_target_template = forge.config.env().get_template(
		"systemd/stylo-forge-redis.target"
	)
	forge_redis_cache_template = forge.config.env().get_template(
		"systemd/stylo-forge-redis-cache.service"
	)
	forge_redis_queue_template = forge.config.env().get_template(
		"systemd/stylo-forge-redis-queue.service"
	)

	forge_redis_target_config = forge_redis_target_template.render(**forge_info)
	forge_redis_cache_config = forge_redis_cache_template.render(**forge_info)
	forge_redis_queue_config = forge_redis_queue_template.render(**forge_info)

	forge_redis_target_config_path = os.path.join(
		forge_path, "config", "systemd", forge_info.get("forge_name") + "-redis.target"
	)
	forge_redis_cache_config_path = os.path.join(
		forge_path, "config", "systemd", forge_info.get("forge_name") + "-redis-cache.service"
	)
	forge_redis_queue_config_path = os.path.join(
		forge_path, "config", "systemd", forge_info.get("forge_name") + "-redis-queue.service"
	)

	with open(forge_redis_target_config_path, "w") as f:
		f.write(forge_redis_target_config)

	with open(forge_redis_cache_config_path, "w") as f:
		f.write(forge_redis_cache_config)

	with open(forge_redis_queue_config_path, "w") as f:
		f.write(forge_redis_queue_config)


def _create_symlinks(forge_path):
	forge_dir = os.path.abspath(forge_path)
	etc_systemd_system = os.path.join("/", "etc", "systemd", "system")
	config_path = os.path.join(forge_dir, "config", "systemd")
	unit_files = get_unit_files(forge_dir)
	for unit_file in unit_files:
		filename = "".join(unit_file)
		exec_cmd(
			f'sudo ln -s {config_path}/{filename} {etc_systemd_system}/{"".join(unit_file)}'
		)
	exec_cmd("sudo systemctl daemon-reload")


def _delete_symlinks(forge_path):
	forge_dir = os.path.abspath(forge_path)
	etc_systemd_system = os.path.join("/", "etc", "systemd", "system")
	unit_files = get_unit_files(forge_dir)
	for unit_file in unit_files:
		exec_cmd(f'sudo rm {etc_systemd_system}/{"".join(unit_file)}')
	exec_cmd("sudo systemctl daemon-reload")


def get_unit_files(forge_path):
	forge_name = get_forge_name(forge_path)
	unit_files = [
		[forge_name, ".target"],
		[forge_name + "-workers", ".target"],
		[forge_name + "-web", ".target"],
		[forge_name + "-redis", ".target"],
		[forge_name + "-stylo-default-worker@", ".service"],
		[forge_name + "-stylo-short-worker@", ".service"],
		[forge_name + "-stylo-long-worker@", ".service"],
		[forge_name + "-stylo-schedule", ".service"],
		[forge_name + "-stylo-web", ".service"],
		[forge_name + "-node-socketio", ".service"],
		[forge_name + "-redis-cache", ".service"],
		[forge_name + "-redis-queue", ".service"],
	]
	return unit_files
