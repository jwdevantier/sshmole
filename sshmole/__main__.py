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
from sshmole.log import get_logger, LogLevel, loggers_set_log_level

app = typer.Typer()
config_fpath: Path
_config: model.Config


logger = get_logger(__name__, LogLevel.INFO)


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
        pidfile = _profile_pidfile_path(profile).absolute()
        try:
            with open(pidfile, "w") as fp:
                fp.write(f"{os.getpid()}")
            return cliutils.sshuttle_popen(_config, args)
        finally:
            if pidfile.exists():
                pidfile.unlink()


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
def start(profile: str = typer.Argument(..., help="profile to start")):
    """start specified profile"""
    _start_profile(profile)


@app.command("stop")
def stop(profile: str = typer.Argument(..., help="profile to stop")):
    """stop specified profile"""
    _stop_profile(profile)


@app.command("restart")
def restart(profile: str = typer.Argument(..., help="profile to restart")):
    """restart specified profile"""
    _stop_profile(profile)
    _start_profile(profile)


@app.command("status")
def status(profile: Optional[str] = typer.Argument(None, help="profile to query")):
    """see status of all or specified profile"""
    if profile:
        endpoints = [profile]
    else:
        endpoints = all_endpoints_names(_config)

    for profile in endpoints:
        logger.debug(f"querying for status on profile {profile!r}")
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
def _pre_command(
        log_level: Optional[str] = typer.Option("info", help="set log level"),
        config: Path = Path.home() / ".sshmole.yml"):
    if log_level:
        log_level = log_level.upper()
        opts = LogLevel.__members__.keys()
        if log_level not in opts:
            str_opts = ", ".join(opts)
            print(f"{log_level!r} not in {str_opts}")
            sys.exit(1)
        loggers_set_log_level(LogLevel[log_level])
        logger.info(f"log-level set to {log_level!r}")
    global _config
    logger.debug(f"reading config {config!r}")
    _config = model.read_yaml_config(model.Config, config)
    logger.debug("finding python binary")
    _config.python = cliutils.py3_fpath(_config.python)
    if _config.python is None:
        raise ValueError("cannot resolve/find python")


def main():
    # default to showing usage information.
    app()


if __name__ == "__main__":
    main()
