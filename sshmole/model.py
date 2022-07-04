from pydantic import BaseModel, Field, validator
from typing import List, Type, TypeVar, Union
from pathlib import Path
import ipaddress
import socket
import yaml
from sshconf import read_ssh_config
from sshmole.log import get_logger


logger = get_logger(__name__)


class InvalidRemoteError(Exception):
    def __init__(self, remote: str):
        self.remote = remote
        super().__init__(f"warning: invalid remote '{remote}', it is neither a valid DNS hostname nor an alias for a config entry in ~/.ssh/config")


def get_hostname(remote: str) -> str:
    try:
        return socket.gethostbyname(remote)
    except socket.gaierror as e:
        # may be because the remote is not a legitimate domain name.
        # try reading aliases from ssh config instead.
        pass

    c = read_ssh_config(Path.home() / ".ssh" / "config")
    if not remote in c.hosts():
        raise InvalidRemoteError(remote)

    return get_hostname(c.host(remote)["hostname"])


class Endpoint(BaseModel):
    # name to assign this entry, used mostly for debugging
    name: str
    # hostname or alias for entry in ~/.ssh/config
    remote: str
    # supply additional arguments here (if necessary)
    ssh_cmd: str = Field(default="ssh")
    # whether to intercept and forward DNS requests or not
    forward_dns_requests: bool = False
    # if enabled, sacrifice latency to improve bandwidth
    latency_control: bool = True
    seed_hosts: List[str] = Field(default_factory=list)
    # scan for hostname entries and add them to the local /etc/hosts file for
    # the duration of the tunnel being open.
    # (unlike `forward_dns_requests` this works with multiple open tunnels)
    auto_hosts: bool = False
    # consult remote's routing table and automatically provide access to these
    # through the tunnel.
    auto_nets: bool = False
    # subnets for which requests should be routed through the remote
    subnets: List[str] = Field(default_factory=list)
    # exclude requests for addresses in these subnets from being forwarded
    # specify with multiple -x flags
    exclude_subnets: List[str] = Field(default_factory=list)

    @validator("ssh_cmd")
    def trim_cmd(cls, v):
        return v.strip()

    @validator("seed_hosts", each_item=True)
    def trim_seed_hosts(cls, v):
        v = v.strip()
        if v == "":
            raise ValueError("empty host entry not supported")
        return v

    @validator("auto_hosts", always=True)
    def validate_auto_hosts(cls, v, values):
        seed_hosts = values.get("seed_hosts", [])
        if len(seed_hosts) != 0:
            # seed_hosts has to be positive, then
            return True
        return v

    @validator("subnets", each_item=True)
    def validate_subnet_entries(cls, v):
        return str(ipaddress.ip_network(v.strip()))

    @validator("exclude_subnets", each_item=True)
    def validate_exclude_subnet_entries(cls, v):
        return str(ipaddress.ip_network(v.strip()))

    @validator("exclude_subnets", always=True)
    def ensure_exclude_own_addr(cls, v, values):
        try:
            # determine address of remote itself...
            rhost_addr = get_hostname(values["remote"])

            # if address of remote is not in exclude list, add it.
            if len({rhost_addr, f"{rhost_addr}/32"}.intersection(v)) == 0:
                v.append(f"{rhost_addr}/32")
        except InvalidRemoteError as e:
            print(e, end="\n\n")
        return v

    @property
    def sshuttle_args(self) -> List[str]:
        # caller should prefix with sshuttle binary path
        args = []

        args.extend(["-r", self.remote])
        if self.ssh_cmd != "ssh":
            args.extend(["--ssh-cmd", self.ssh_cmd])
        if self.forward_dns_requests:
            args.append("--dns")
        if not self.latency_control:
            args.append("--no-latency-control")
        if self.seed_hosts:
            args.extend([
                "--seed-hosts",
                ",".join(self.seed_hosts)
            ])
        if self.auto_hosts:
            args.append("--auto-hosts")
        if self.auto_nets:
            args.append("--auto-nets")
        if self.exclude_subnets:
            for subnet in self.exclude_subnets:
                args.append("-x")
                args.append(subnet)
        for subnet in self.subnets:
            args.append(subnet)

        return args


class Config(BaseModel):
    python: str = Field(default="python3")
    sshuttle_dir: Path = Field(default_factory=lambda: Path.home() / ".sshuttle")
    endpoints: List[Endpoint]

    @validator("sshuttle_dir", always=True)
    def if_exists_is_directory(cls, v):
        if v.exists() and not v.is_dir():
            raise ValueError("path exists, but is not a directory")
        return v


ModelType = TypeVar("ModelType", bound=BaseModel)


def read_yaml_config(model: Type[ModelType], fpath: Union[Path, str]) -> ModelType:
    with open(fpath, "r") as fp:
        raw_yaml = yaml.safe_load(fp)
        logger.debug("reading yaml into model")
        return model(**raw_yaml)


def all_endpoints_names(config: Config) -> List[str]:
    return [endpoint.name for endpoint in config.endpoints]


def get_endpoint(config: Config, profile: str) -> Endpoint:
    for endpoint in config.endpoints:
        if endpoint.name == profile:
            return endpoint
    raise Exception(f"No endpoint by name '{profile}'")
