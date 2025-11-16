## How are Stylo Framework commands available via forge?

forge utilizes `stylo.utils.forge_manager` to get the framework's as well as those of any custom commands written in application installed in the Stylo environment. Currently, with *version 12* there are commands related to the scheduler, sites, translations and other utils in Stylo inherited by forge.


## Can I add CLI commands in my custom app and call them via forge?

Along with the framework commands, Stylo's `forge_manager` module also searches for any commands in your custom applications. Thereby, forge communicates with the respective forge's Stylo which in turn checks for available commands in all of the applications.

To make your custom command available to forge, just create a `commands` module under your parent module and write the command with a click wrapper and a variable commands which contains a list of click functions, which are your own commands. The directory structure may be visualized as:

```
stylo-forge
|──apps
    |── stylo
    ├── custom_app
    │   ├── README.md
    │   ├── custom_app
    │   │   ├── commands    <------ commands module
    │   ├── license.txt
    │   ├── requirements.txt
    │   └── setup.py
```

The commands module maybe a single file such as `commands.py` or a directory with an `__init__.py` file. For a custom application of name 'flags', example may be given as

```python
# file_path: stylo-forge/apps/flags/flags/commands.py
import click

@click.command('set-flags')
@click.argument('state', type=click.Choice(['on', 'off']))
def set_flags(state):
    from flags.utils import set_flags
    set_flags(state=state)

commands = [
    set_flags
]
```

and with context of the current forge, this command maybe executed simply as

```zsh
➜ forge set-flags
Flags are set to state: 'on'
```

