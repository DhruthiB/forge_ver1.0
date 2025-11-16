"""Module for setting up system and respective forge configurations"""


def env():
	from jinja2 import Environment, PackageLoader

	return Environment(loader=PackageLoader("forge.config"))
