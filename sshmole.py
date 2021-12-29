import typer
from typing import Optional, List
from pathlib import Path
import sys
from sshmole import model, cli, setup
import os
import signal
import time
import subprocess

# start each sshuttle in daemon mode
# record PID in /tmp/sshuttle.pid.<profile>


app = typer.Typer()
config_fpath: Path
_config: model.Config


def _profile_pidfile_path(profile: str) -> Path:
    return Path(f"/tmp/sshuttle.pid.{profile}")


def profile_pid(profile: str) -> Optional[int]:
    fpath = _profile_pidfile_path(profile)
    if not fpath.exists():
        return None
    return cli.pidfile_read(fpath)


def all_profiles(config: model.Config) -> List[str]:
    return [endpoint.name for endpoint in config.endpoints]


def get_endpoint(config: model.Config, profile: str) -> model.Endpoint:
    for endpoint in config.endpoints:
        if endpoint.name == profile:
            return endpoint
    raise Exception(f"No endpoint by name '{profile}'")


def _start_profile(profile: str) -> subprocess.Popen:
    endpoint = get_endpoint(_config, profile)
    with cli.cwd(_config.sshuttle_dir):
        args = endpoint.sshuttle_args
        args.extend(["--daemon", "--pidfile", str(_profile_pidfile_path(profile).absolute())])
        # TODO: check that we're not stuck on sudo
        # TODO: wait for tunnel to start... (check on output method)
        return cli.sshuttle_popen(_config, args)


def _stop_profile(profile: str):
    fpath = _profile_pidfile_path(profile)
    if not fpath.exists():
        return
    pid = cli.pidfile_read(fpath)
    if not cli.is_pid_running(pid):
        return

    print(f"stopping {profile}", end="", flush=True)
    os.kill(pid, signal.SIGTERM)
    while cli.is_pid_running(pid):
        # TODO: abort after some time...
        print(".", end="", flush=True)
        time.sleep(1)
    print("", flush=True)

    fpath.unlink(missing_ok=True)


@app.command("start")
def start(profile: Optional[str] = typer.Argument(None)):
    """start all or specified profile"""
    print(f"start @ {_config}")
    profiles = all_profiles(_config) if not profile else [profile]
    for profile in profiles:
        _start_profile(profile)


@app.command("stop")
def stop(profile: Optional[str] = typer.Argument(None)):
    """stop all or specified profile"""
    profiles = all_profiles(_config) if not profile else [profile]
    for profile in profiles:
        _stop_profile(profile)


@app.command("restart")
def restart(profile: Optional[str] = typer.Argument(None)):
    """restart all or specified profile"""
    profiles = all_profiles(_config) if not profile else [profile]
    for profile in profiles:
        _stop_profile(profile)
        _start_profile(profile)


@app.command("status")
def status(profile: Optional[str] = typer.Argument(None)):
    """see status of all or specified profile"""
    if profile:
        profiles = [profile]
    else:
        profiles = [endpoint.name for endpoint in _config.endpoints]

    for profile in profiles:
        pid = profile_pid(profile)
        if cli.is_pid_running(pid) if pid is not None else False:
            profile_status = "ON"
        else:
            profile_status = "OFF"
        print(f"{profile}: {profile_status}")


@app.command("setup-sshuttle")
def setup_sshuttle():
    """Install `sshuttle` and NOPASSWD sudoer's entry"""
    setup.do_setup(_config)


@app.callback()
def _pre_command(verbose: bool = False, config: Path = Path.home() / ".sshmole.yml"):
    global _config
    _config = model.read_yaml_config(model.Config, config)
    _config.python = cli.py3_fpath(_config.python)
    if _config.python is None:
        raise ValueError("cannot resolve/find python")


if __name__ == "__main__":
    # default to showing usage information.
    if len(sys.argv) == 1:
        sys.argv.append("--help")
    app()
