import typer
from typing import Optional
from pathlib import Path
import sys
import signal
import subprocess
import os
import time
from sshmole.model import all_endpoints_names, get_endpoint
from sshmole import setup, model, cliutils

app = typer.Typer()
config_fpath: Path
_config: model.Config


def _profile_pidfile_path(profile: str) -> Path:
    return Path(f"/tmp/sshuttle.pid.{profile}")


def profile_pid(profile: str) -> Optional[int]:
    fpath = _profile_pidfile_path(profile)
    if not fpath.exists():
        return None
    return cliutils.pidfile_read(fpath)


def _start_profile(profile: str) -> subprocess.Popen:
    endpoint = get_endpoint(_config, profile)
    with cliutils.cwd(_config.sshuttle_dir):
        args = endpoint.sshuttle_args
        args.extend(["--daemon", "--pidfile", str(_profile_pidfile_path(profile).absolute())])
        # TODO: check that we're not stuck on sudo
        # TODO: wait for tunnel to start... (check on output method)
        return cliutils.sshuttle_popen(_config, args)


def _stop_profile(profile: str):
    fpath = _profile_pidfile_path(profile)
    if not fpath.exists():
        return
    pid = cliutils.pidfile_read(fpath)
    if not cliutils.is_pid_running(pid):
        return

    print(f"stopping {profile}", end="", flush=True)
    os.kill(pid, signal.SIGTERM)
    while cliutils.is_pid_running(pid):
        # TODO: abort after some time...
        print(".", end="", flush=True)
        time.sleep(1)
    print("", flush=True)

    if fpath.exists():
        fpath.unlink()


@app.command("start")
def start(profile: Optional[str] = typer.Argument(None)):
    """start all or specified profile"""
    print(f"start @ {_config}")
    endpoints = all_endpoints_names(_config) if not profile else [profile]
    for profile in endpoints:
        _start_profile(profile)


@app.command("stop")
def stop(profile: Optional[str] = typer.Argument(None)):
    """stop all or specified profile"""
    endpoints = all_endpoints_names(_config) if not profile else [profile]
    for profile in endpoints:
        _stop_profile(profile)


@app.command("restart")
def restart(profile: Optional[str] = typer.Argument(None)):
    """restart all or specified profile"""
    endpoints = all_endpoints_names(_config) if not profile else [profile]
    for profile in endpoints:
        _stop_profile(profile)
        _start_profile(profile)


@app.command("status")
def status(profile: Optional[str] = typer.Argument(None)):
    """see status of all or specified profile"""
    if profile:
        endpoints = [profile]
    else:
        endpoints = all_endpoints_names(_config)

    for profile in endpoints:
        pid = profile_pid(profile)
        if cliutils.is_pid_running(pid) if pid is not None else False:
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
    _config.python = cliutils.py3_fpath(_config.python)
    if _config.python is None:
        raise ValueError("cannot resolve/find python")


def main():
    # default to showing usage information.
    if len(sys.argv) == 1:
        sys.argv.append("--help")
    app()


if __name__ == "__main__":
    main()
