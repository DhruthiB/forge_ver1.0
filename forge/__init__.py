VERSION = "1.0.0-dev"
PROJECT_NAME = "stylo-forge"
FRAPPE_VERSION = None
current_path = None
updated_path = None
LOG_BUFFER = []


def set_stylo_version(forge_path="."):
	from .utils.app import get_current_stylo_version

	global FRAPPE_VERSION
	if not FRAPPE_VERSION:
		FRAPPE_VERSION = get_current_stylo_version(forge_path=forge_path)
