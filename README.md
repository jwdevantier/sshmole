# SSH Mole

Wrapper around [sshuttle](https://github.com/sshuttle/sshuttle) supporting management of
multiple endpoints through a YAML config file.

## Motivation
`sshmole` mostly relies on features in [sshuttle](https://github.com/sshuttle/sshuttle) itself - such as the actual traffic forwarding, daemonization and generation of sudoers files allowing passwordless invocation.

The main addition with `sshmole` is a YAML-based configuration file, whose contents are validated as they are read,
and which permit defining several profiles, by associatiating a series of settings to a profile name.

This, in turn, makes `sshmole` able to expose an easy interface for managing profiles, allowing
you to (re-)start or stop profiles, or inquire whether they are presently running by running
`sshmole {start,stop,restart,status} <profile>`.

## How to use

### Install project
```
git clone https://github.com/jwdevantier/sshmole sshmole
cd sshmole
make install
```

Alternatively to `make install`, you can install directory by issuing `pip install --user .`.

Now you should be able to run `sshmole` from a terminal.

### (One-off) install sshuttle
`sshmole` installs [sshuttle](https://github.com/sshuttle/sshuttle) directly into `~/.sshuttle` unless otherwise specified
in the sshmole configuration file (`~/.sshmole.yml`).

This might change, for now, to install `sshuttle`, run `sshmole setup-sshuttle`.

### Create configuration file
The configuration file is expected to be in `$HOME/.sshmole.yml`, though passing `--config path/to/config.yml` to `sshmole.py` can override this.

See `sshmole.sample.yml` for an example and consult [the configuration model](sshmole/model.py) directly to see all available settings. Keep in mind that these simply expose the functionality provided by [sshuttle](https://github.com/sshuttle/sshuttle) itself, see the [sshuttle man page](https://sshuttle.readthedocs.io/en/stable/manpage.html) documentation for an extended explanation of what each setting does.
