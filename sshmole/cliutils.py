from contextlib import contextmanager
from pathlib import Path
import os
import hashlib
from typing import Union, Optional, List
import shutil
import subprocess
from sshmole.model import Config
import shlex


@contextmanager
def cwd(path: Path):
    """temporarily operate within `path` as current working directory."""
    origin = Path().absolute()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(origin)


def md5sum(fpath: Union[str, Path]) -> str:
    try:
        with open(fpath, "rb") as fp:
            return hashlib.md5(fp.read()).hexdigest()
    except FileNotFoundError:
        return ""


def _is_python_3(py_fpath: Path) -> bool:
    if not py_fpath.exists():
        return False
    try:
        subprocess.run([py_fpath, "-c", "import sys; sys.exit(sys.version_info[0] != 3)"], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def py3_fpath(val: Optional[str] = None) -> Optional[str]:
    if val:
        pval = Path(val)
        if not pval.is_absolute():
            val = shutil.which(val)
        if val is None:
            return None
        return val if _is_python_3(Path(val)) else None

    for val in ["python3", "python"]:
        py_path = shutil.which(val)
        if not py_path:
            continue
        if _is_python_3(Path(py_path)):
            return val

    return None


def py_has_venv(py_fpath: Union[Path, str]) -> bool:
    out = subprocess.run([py_fpath, "-c", "import venv"])
    if out.returncode == 0:
        return True
    if b"No module named 'venv'" in out.stderr:
        return False
    raise Exception("unspecified error while running command")


def pidfile_read(fpath: Path) -> int:
    with open(fpath, "r") as fp:
        return int(fp.readline())


def is_pid_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def sshuttle_popen(config: Config, args: List[str], **kwargs) -> subprocess.Popen:
    bash = shutil.which("bash")
    if not bash:
        raise Exception("cannot find 'bash' shell, needed to run commands in context of sshuttle's virtual environment")

    if shutil.which("sshuttle"):
        shell_args = [shlex.quote(arg) for arg in args]
        cmd = [bash, "-c", f"""sshuttle {" ".join(shell_args)}"""]
        print(" ".join(cmd))
        proc = subprocess.Popen(cmd, **kwargs)
        proc.wait()
        return proc

    if not config.sshuttle_dir.exists():
        raise Exception("sshuttle is not installed, run setup-sshuttle command first, then re-try")
    venv_dir = config.sshuttle_dir / ".venv"
    if not venv_dir.exists():
        raise Exception(f"sshuttle virtual environment dir ({venv_dir}) does not exist, re-run setup, then re-try")
    activate_fpath = (venv_dir / "bin" / "activate").absolute()
    with cwd(config.sshuttle_dir):
        shell_args = [shlex.quote(arg) for arg in args]
        cmd = [bash, "-c", f"""source {activate_fpath}; sshuttle {" ".join(shell_args)}"""]
        print(" ".join(cmd))
        proc = subprocess.Popen(cmd, **kwargs)
        proc.wait()
        return proc
