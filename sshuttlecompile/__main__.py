from sshuttlecompile import model
import os
from pathlib import Path
import sys
from typing import Optional
import signal
import subprocess
import time

# start each sshuttle in daemon mode
# record PID in /tmp/sshuttle.pid.<profile>


def _get_config_fpath() -> str:
    fpath = os.environ.get("SSHUTTLE_CONFIG", None)
    if not fpath:
        return str(Path.home() / ".sshuttle_conf.yml")
    return fpath


config_fpath = _get_config_fpath()
config: model.Config


def _usage_msg():
    print(f"USAGE: {sys.argv[0]} COMMAND [profile]")
    print("")
    print("COMMAND: start|restart|stop|status")
    print("")
    print("if `profile` is omitted, the command is applied to all profiles in order of definition")


def _parse_args(cfg: model.Config):
    profile = None

    print(sys.argv)
    if len(sys.argv) not in [1, 2]:
        _usage_msg()
        sys.exit(1)

    sys.argv[1] = sys.argv[1].lower()
    if sys.argv[1] not in {"start" "restart" "stop" "status"}:
        print(f"invalid command '{sys.argv[1]}'")
        _usage_msg()
        sys.exit(1)

    if len(sys.argv) == 2:
        profile = sys.argv[2]
        profiles = [endpoint.name for endpoint in cfg.endpoints]
        if not profile in profiles:
            print("profile '{profile}' not found")
            print(f"""available profiles: {", ".join(profiles)}""")
            _usage_msg()
            sys.exit(1)

    return sys.argv[1], sys.argv[2]


def read_config() -> model.Config:
    return model.read_yaml_config(model.Config, config_fpath)


def _profile_pidfile_path(profile: str) -> Path:
    return Path(f"/tmp/sshuttle.pid.{profile}")


def _pidfile_read(fpath: Path) -> int:
    with open(fpath, "r") as fp:
        return int(fp.readline())


def _profile_pid(profile: str) -> Optional[int]:
    fpath = _profile_pidfile_path(profile)
    if not fpath.exists():
        return None
    return _pidfile_read(fpath)


def _is_pid_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def _start_profile(config: model.Config, profile: str) -> subprocess.Popen:
    profile_endpoints = [
        endpoint
        for endpoint in config.endpoints
        if endpoint.name == profile
    ]
    # TODO: maybe panic if there's multiple / zero entries
    endpoint = profile_endpoints[0]
    # TODO: shuttle binary location
    cmd = ["sshuttle"]
    cmd.extend(endpoint.sshuttle_args)
    cmd.extend(["--daemon", "--pidfile", _profile_pidfile_path(profile)])
    return subprocess.Popen(cmd)


def start(config: model.Config, profile: Optional[str] = None):
    if profile:
        _start_profile(config, profile)
    else:
        for profile in (endpoint.name for endpoint in config.endpoints):
            _start_profile(config, profile)


def _stop_profile(profile: str):
    fpath = _profile_pidfile_path(profile)
    if not fpath.exists():
        return
    pid = _pidfile_read(fpath)
    if not _is_pid_running(pid):
        return

    print(f"stopping {profile}", end="", flush=True)
    os.kill(pid, signal.SIGTERM)
    while _is_pid_running(pid):
        # TODO: abort after some time...
        print(".", end="", flush=True)
        time.sleep(1)
    print("", flush=True)

    fpath.unlink(missing_ok=True)


def stop(config: model.Config, profile: Optional[str] = None):
    if profile:
        _stop_profile(profile)
    else:
        for profile in (endpoint.name for endpoint in config.endpoints):
            _stop_profile(profile)


def _restart_profile(config: model.Config, profile: str):
    pid = _profile_pid(profile)
    if _is_pid_running(pid) if pid is not None else False:
        _stop_profile(profile)
    _start_profile(config, profile)


def restart(config: model.Config, profile: Optional[str] = None):
    if profile:
        _restart_profile(config, profile)
    else:
        for profile in (endpoint.name for endpoint in config.endpoints):
            _restart_profile(config, profile)


def status(config: model.Config, profile: Optional[str] = None):
    if profile:
        profiles = [profile]
    else:
        profiles = [endpoint.name for endpoint in config.endpoints]

    for profile in profiles:
        pid = _profile_pid(profile)
        if _is_pid_running(pid) if pid is not None else False:
            profile_status = "ON"
        else:
            profile_status = "OFF"
        print(f"{profile}: {profile_status}")


if __name__ == "__main__":
    # cfg = model.read_yaml_config(model.Config, "/home/pseud/sshuttle.yml")
    # for endpoint in cfg.endpoints:
    #     print(endpoint)
    #     print(endpoint.sshuttle_args)
    config = read_config()
    cmd, profile = _parse_args(config)

    if cmd == "start":
        start(config, profile)
    elif cmd == "restart":
        restart(config, profile)
    elif cmd == "stop":
        stop(config, profile)
    elif cmd == "status":
        status(config, profile)
