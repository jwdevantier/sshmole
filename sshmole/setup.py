from sshmole.model import Config
from sshmole.cli import md5sum, cwd, py3_fpath, py_has_venv
import shutil
import subprocess
import getpass


def do_setup(config: Config):
    """setup sshuttle software

    installs `sshuttle` from official git repo."""
    # download sshuttle software (if missing)
    bash = shutil.which("bash")
    if not bash:
        raise Exception("cannot find bash shell, cannot run commands within venv environment")

    if not config.sshuttle_dir.exists():
        git = shutil.which("git")
        if git is None:
            raise Exception("installation failed, cannot clone sshuttle software because 'git' cannot be found")
        subprocess.run([git, "clone", "https://github.com/sshuttle/sshuttle.git", config.sshuttle_dir], check=True)
        with cwd(config.sshuttle_dir):
            subprocess.run([git, "checkout", "tags/v1.0.5"], check=True)
        pass

    # create venv (if missing)
    venv = config.sshuttle_dir / ".venv"
    if not venv.exists():
        with cwd(config.sshuttle_dir):
            if not py_has_venv(config.python):
                raise Exception("python installation lacks 'venv' module - install through your system's package manager and re-try")
            subprocess.run([config.python, "-m", "venv", ".venv"], check=True)

    sshuttle_requirements = config.sshuttle_dir / "requirements.txt"
    if not sshuttle_requirements.exists():
        raise Exception(f"could not find sshuttle software's requirements.txt file in {sshuttle_requirements}")
    req_installed = venv / ".requirements.installed.txt"
    if not req_installed.exists() or md5sum(req_installed) != md5sum(sshuttle_requirements):
        # install/update requirements
        with cwd(config.sshuttle_dir):
            subprocess.run([
                bash, "-c", "source .venv/bin/activate && pip install -r requirements.txt"
            ], check=True)
            # record what we just installed
            shutil.copy(sshuttle_requirements, req_installed)

            subprocess.run([bash, "-c", "source .venv/bin/activate && pip install ."], check=True)

    # install sudoer's file (if missing)
    with cwd(config.sshuttle_dir):
        subprocess.run([bash, "-c", f"source .venv/bin/activate && sshuttle --sudoers --sudoers-filename sshmole_{getpass.getuser()}"])