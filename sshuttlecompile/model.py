from pydantic import BaseModel, Field, validator
from typing import List, Type, TypeVar, Union
from pathlib import Path
import ipaddress
import socket
import yaml


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
        print(f"EXCL ITEM ({v.strip()})")
        return str(ipaddress.ip_network(v.strip()))

    @validator("exclude_subnets", always=True)
    def ensure_exclude_own_addr(cls, v, values):
        # determine address of remote itself...
        rhost_addr = socket.gethostbyname(values["remote"])

        # if address of remote is not in exclude list, add it.
        if len({rhost_addr, f"{rhost_addr}/32"}.intersection(v)) == 0:
            v.append(f"{rhost_addr}/32")
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
    python: str = Field(default="python")
    endpoints: List[Endpoint]


ModelType = TypeVar("ModelType", bound=BaseModel)


def read_yaml_config(model: Type[ModelType], fpath: Union[Path, str]) -> ModelType:
    with open(fpath, "r") as fp:
        return model(**yaml.safe_load(fp))
