# imports - third party imports
import click

# imports - module imports
from forge.utils.cli import (
	MultiCommandGroup,
	print_forge_version,
	use_experimental_feature,
	setup_verbosity,
)


@click.group(cls=MultiCommandGroup)
@click.option(
	"--version",
	is_flag=True,
	is_eager=True,
	callback=print_forge_version,
	expose_value=False,
)
@click.option(
	"--use-feature",
	is_eager=True,
	callback=use_experimental_feature,
	expose_value=False,
)
@click.option(
	"-v",
	"--verbose",
	is_flag=True,
	callback=setup_verbosity,
	expose_value=False,
)
def forge_command(forge_path="."):
	import forge

	forge.set_stylo_version(forge_path=forge_path)


from forge.commands.make import (
	drop,
	exclude_app_for_update,
	get_app,
	include_app_for_update,
	init,
	new_app,
	pip,
	remove_app,
	validate_dependencies,
)

forge_command.add_command(init)
forge_command.add_command(drop)
forge_command.add_command(get_app)
forge_command.add_command(new_app)
forge_command.add_command(remove_app)
forge_command.add_command(exclude_app_for_update)
forge_command.add_command(include_app_for_update)
forge_command.add_command(pip)
forge_command.add_command(validate_dependencies)


from forge.commands.update import (
	retry_upgrade,
	switch_to_branch,
	switch_to_develop,
	update,
)

forge_command.add_command(update)
forge_command.add_command(retry_upgrade)
forge_command.add_command(switch_to_branch)
forge_command.add_command(switch_to_develop)


from forge.commands.utils import (
	app_cache_helper,
	backup_all_sites,
	forge_src,
	disable_production,
	download_translations,
	find_forgees,
	migrate_env,
	renew_lets_encrypt,
	restart,
	set_mariadb_host,
	set_nginx_port,
	set_redis_cache_host,
	set_redis_queue_host,
	set_redis_socketio_host,
	set_ssl_certificate,
	set_ssl_certificate_key,
	set_url_root,
	start,
)

forge_command.add_command(start)
forge_command.add_command(restart)
forge_command.add_command(set_nginx_port)
forge_command.add_command(set_ssl_certificate)
forge_command.add_command(set_ssl_certificate_key)
forge_command.add_command(set_url_root)
forge_command.add_command(set_mariadb_host)
forge_command.add_command(set_redis_cache_host)
forge_command.add_command(set_redis_queue_host)
forge_command.add_command(set_redis_socketio_host)
forge_command.add_command(download_translations)
forge_command.add_command(backup_all_sites)
forge_command.add_command(renew_lets_encrypt)
forge_command.add_command(disable_production)
forge_command.add_command(forge_src)
forge_command.add_command(find_forgees)
forge_command.add_command(migrate_env)
forge_command.add_command(app_cache_helper)

from forge.commands.setup import setup

forge_command.add_command(setup)


from forge.commands.config import config

forge_command.add_command(config)

from forge.commands.git import remote_reset_url, remote_set_url, remote_urls

forge_command.add_command(remote_set_url)
forge_command.add_command(remote_reset_url)
forge_command.add_command(remote_urls)

from forge.commands.install import install

forge_command.add_command(install)
