# forge CLI Usage

This may not be known to a lot of people but half the forge commands we're used to, exist in the Stylo Framework and not in forge directly. Those commands generally are the `--site` commands. This page is concerned only with the commands in the forge project. Any framework commands won't be a part of this consolidation.


# forge CLI Commands

Under Click's structure, `forge` is the main command group, under which there are three main groups of commands in forge currently, namely

 - **install**: The install command group deals with commands used to install system dependencies for setting up Stylo environment

 - **setup**: This command group for consists of commands used to maipulate the requirements and environments required by your Stylo environment

 - **config**: The config command group deals with making changes in the current forge (not the CLI tool) configuration


## Using the forge command line

```zsh
➜ forge
Usage: forge [OPTIONS] COMMAND [ARGS]...

  Forge manager for Stylo

Options:
  --version
  --help     Show this message and exit.

Commands:
  backup                   Backup single site
  backup-all-sites         Backup all sites in current forge
  config                   Change forge configuration
  disable-production       Disables production environment for the forge.
  download-translations    Download latest translations
  exclude-app              Exclude app from updating
  find                     Finds forgees recursively from location
  get-app                  Clone an app from the internet or filesystem and...
```

Similarly, all available flags and options can be checked for commands individually by executing them with the `--help` flag. The `init` command for instance:

```zsh
➜ forge init --help
Usage: forge init [OPTIONS] PATH

  Initialize a new forge instance in the specified path

Options:
  --python TEXT                   Path to Python Executable.
  --ignore-exist                  Ignore if Forge instance exists.
  --apps_path TEXT                path to json files with apps to install
                                  after init
```



## forge and sudo

Some forge commands may require sudo, such as some `setup` commands and everything else under the `install` commands group. For these commands, you may not be asked for your root password if sudoers setup has been done. The security implications, well we'll talk about those soon.



## General Commands

These commands belong directly to the forge group so they can be invoked directly prefixing each with `forge` in your shell. Therefore, the usage for these commands is as

```zsh
    forge COMMAND [ARGS]...
```

### The usual commands

 - **init**: Initialize a new forge instance in the specified path. This sets up a complete forge folder with an `apps` folder which contains all the Stylo apps available in the current forge, `sites` folder that stores all site data seperated by individual site folders, `config` folder that contains your redis, NGINX and supervisor configuration files. The `env` folder consists of all python dependencies the current forge and installed Stylo applications have.
 - **restart**: Restart web, supervisor, systemd processes units. Used in production setup.
 - **update**: If executed in a forge directory, without any flags will backup, pull, setup requirements, build, run patches and restart forge. Using specific flags will only do certain tasks instead of all.
 - **migrate-env**: Migrate Virtual Environment to desired Python version. This regenerates the `env` folder with the specified Python version.
 - **retry-upgrade**: Retry a failed upgrade
 - **disable-production**: Disables production environment for the forge.
 - **renew-lets-encrypt**: Renew Let's Encrypt certificate for site SSL.
 - **backup**: Backup single site data. Can be used to backup files as well.
 - **backup-all-sites**: Backup all sites in current forge.

 - **get-app**: Download an app from the internet or filesystem and set it up in your forge. This clones the git repo of the Stylo project and installs it in the forge environment.
 - **remove-app**: Completely remove app from forge and re-build assets if not installed on any site.
 - **exclude-app**: Exclude app from updating during a `forge update`
 - **include-app**: Include app for updating. All Stylo applications are included by default when installed.
 - **remote-set-url**: Set app remote url
 - **remote-reset-url**: Reset app remote url to stylo official
 - **remote-urls**: Show apps remote url
 - **switch-to-branch**: Switch all apps to specified branch, or specify apps separated by space
 - **switch-to-develop**: Switch Stylo and ERPNext to develop branch


### A little advanced

 - **set-nginx-port**: Set NGINX port for site
 - **set-ssl-certificate**: Set SSL certificate path for site
 - **set-ssl-key**: Set SSL certificate private key path for site
 - **set-url-root**: Set URL root for site
 - **set-mariadb-host**: Set MariaDB host for forge
 - **set-redis-cache-host**: Set Redis cache host for forge
 - **set-redis-queue-host**: Set Redis queue host for forge
 - **set-redis-socketio-host**: Set Redis socketio host for forge
 - **use**: Set default site for forge
 - **download-translations**: Download latest translations


### Developer's commands

 - **start**: Start Stylo development processes. Uses the Procfile to start the Stylo development environment.
 - **src**: Prints forge source folder path, which can be used to cd into the forge installation repository by `cd $(forge src)`.
 - **find**: Finds forgees recursively from location or specified path.
 - **pip**: Use the current forge's pip to manage Python packages. For help about pip usage: `forge pip help [COMMAND]` or `forge pip [COMMAND] -h`.
 - **new-app**: Create a new Stylo application under apps folder.


### Release forge
 - **release**: Create a release of a Stylo application
 - **prepare-beta-release**: Prepare major beta release from develop branch



## Setup commands

The setup commands used for setting up the Stylo environment in context of the current forge need to be executed using `forge setup` as the prefix. So, the general usage of these commands is as

```zsh
    forge setup COMMAND [ARGS]...
```

 - **sudoers**: Add commands to sudoers list for allowing forge commands execution without root password

 - **env**: Setup Python virtual environment for forge. This sets up a `env` folder under the root of the forge directory.
 - **redis**: Generates configuration for Redis
 - **fonts**: Add Stylo fonts to system
 - **config**: Generate or over-write sites/common_site_config.json
 - **backups**: Add cronjob for forge backups
 - **socketio**: Setup node dependencies for socketio server
 - **requirements**: Setup Python and Node dependencies

 - **manager**: Setup `forge-manager.local` site with the [Forge Manager](https://github.com/stylo/forge_manager) app, a GUI for forge installed on it.

 - **procfile**: Generate Procfile for forge start

 - **production**: Setup Stylo production environment for specific user. This installs ansible, NGINX, supervisor, fail2ban and generates the respective configuration files.
 - **nginx**: Generate configuration files for NGINX
 - **fail2ban**: Setup fail2ban, an intrusion prevention software framework that protects computer servers from brute-force attacks
 - **systemd**: Generate configuration for systemd
 - **firewall**: Setup firewall for system
 - **ssh-port**: Set SSH Port for system
 - **reload-nginx**: Checks NGINX config file and reloads service
 - **supervisor**: Generate configuration for supervisor
 - **lets-encrypt**: Setup lets-encrypt SSL for site
 - **wildcard-ssl**: Setup wildcard SSL certificate for multi-tenant forge

 - **add-domain**: Add a custom domain to a particular site
 - **remove-domain**: Remove custom domain from a site
 - **sync-domains**: Check if there is a change in domains. If yes, updates the domains list.

 - **role**: Install dependencies via ansible roles



## Config commands

The config group commands are used for manipulating configurations in the current forge context. The usage for these commands is as

```zsh
    forge config COMMAND [ARGS]...
```

 - **set-common-config**: Set value in common config
 - **remove-common-config**: Remove specific keys from current forge's common config

 - **update_forge_on_update**: Enable/Disable forge updates on running forge update
 - **restart_supervisor_on_update**: Enable/Disable auto restart of supervisor processes
 - **restart_systemd_on_update**: Enable/Disable auto restart of systemd units
 - **dns_multitenant**: Enable/Disable forge multitenancy on running forge update
 - **serve_default_site**: Configure nginx to serve the default site on port 80
 - **http_timeout**: Set HTTP timeout



## Install commands

The install group commands are used for manipulating system level dependencies. The usage for these commands is as

```zsh
    forge install COMMAND [ARGS]...
```

 - **prerequisites**: Installs pre-requisite libraries, essential tools like b2zip, htop, screen, vim, x11-fonts, python libs, cups and Redis
 - **nodejs**: Installs Node.js v8
 - **nginx**: Installs NGINX. If user is specified, sudoers is setup for that user
 - **packer**: Installs Oracle virtualbox and packer 1.2.1
 - **psutil**: Installs psutil via pip
 - **mariadb**: Install and setup MariaDB of specified version and root password
 - **wkhtmltopdf**: Installs wkhtmltopdf v0.12.3 for linux
 - **supervisor**: Installs supervisor. If user is specified, sudoers is setup for that user
 - **fail2ban**: Install fail2ban, an intrusion prevention software framework that protects computer servers from brute-force attacks
 - **virtualbox**: Installs supervisor
