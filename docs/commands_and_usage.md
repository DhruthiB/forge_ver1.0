## Usage

* Updating

To update the forge CLI tool, depending on your method of installation, you may use 

	pip3 install -U stylo-forge


To backup, update all apps and sites on your forge, you may use

	forge update


To manually update the forge, run `forge update` to update all the apps, run
patches, build JS and CSS files and restart supervisor (if configured to).

You can also run the parts of the forge selectively.

`forge update --pull` will only pull changes in the apps

`forge update --patch` will only run database migrations in the apps

`forge update --build` will only build JS and CSS files for the forge

`forge update --forge` will only update the forge utility (this project)

`forge update --requirements` will only update all dependencies (Python + Node) for the apps available in current forge


* Create a new forge

	The init command will create a forge directory with stylo framework installed. It will be setup for periodic backups and auto updates once a day.

		forge init stylo-forge && cd stylo-forge

* Add a site

	Stylo apps are run by stylo sites and you will have to create at least one site. The new-site command allows you to do that.

		forge new-site site1.local

* Add apps

	The get-app command gets remote stylo apps from a remote git repository and installs them. Example: [erpnext](https://github.com/stylo/erpnext)

		forge get-app erpnext https://github.com/stylo/erpnext

* Install apps

	To install an app on your new site, use the forge `install-app` command.

		forge --site site1.local install-app erpnext

* Start forge

	To start using the forge, use the `forge start` command

		forge start

	To login to Stylo / ERPNext, open your browser and go to `[your-external-ip]:8000`, probably `localhost:8000`

	The default username is "Administrator" and password is what you set when you created the new site.

* Setup Manager

## What it does

		forge setup manager

1. Create new site forge-manager.local
2. Gets the `forge_manager` app from https://github.com/stylo/forge_manager if it doesn't exist already
3. Installs the forge_manager app on the site forge-manager.local

