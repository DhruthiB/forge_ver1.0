from forge.config.common_site_config import update_config


def execute(forge_path):
	update_config({"live_reload": True}, forge_path)
