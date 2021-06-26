import functools
import logging.config
import socket
from typing import Any
from typing import Dict
from typing import Tuple


__all__ = ["HostInformation", "DockerComposeInformation", "DockerInformation"]


@functools.lru_cache()
def _get_container_attributes(hostname: str) -> Dict[str, Any]:
    import docker

    try:
        client = docker.from_env()
        return client.containers.get(hostname).attrs
    except Exception:
        return dict()


class HostInformation(logging.Filter):
    """
    Add information about the flask app and configuration
    """

    def __init__(self) -> None:
        self.hostname = socket.gethostname()

    def filter(self, log_record: logging.LogRecord) -> bool:
        log_record.hostname = self.hostname  # type: ignore
        return True


class DockerInformation(logging.Filter):
    """
    Add information about the flask app and configuration
    """

    SCHEMA: Dict[Tuple[str, ...], Tuple[str, ...]] = {
        ("docker", "id"): ("Id",),
        ("docker", "name"): ("Name",),
        ("docker", "platform"): ("Platform",),
    }

    def __init__(self) -> None:

        docker_attributes = _get_container_attributes(socket.gethostname())

        filter_info: Dict[str, Any] = {}

        for target, source in self.SCHEMA.items():
            attrs = docker_attributes
            *parents, source_key = source
            for parent in parents:
                attrs = attrs.get(parent, {})

            if source_key not in attrs:
                continue

            value = attrs.get(source_key, None)

            attrs = filter_info
            *parents, target_key = target
            for parent in parents:
                attrs = filter_info.setdefault(parent, {})
            attrs[target_key] = value

        self.docker_attributes = filter_info

    def filter(self, log_record: logging.LogRecord) -> bool:
        for key, value in self.docker_attributes.items():
            setattr(log_record, key, value)
        return True


class DockerComposeInformation(DockerInformation):
    """
    Add information about the flask app and configuration
    """

    SCHEMA: Dict[Tuple[str, ...], Tuple[str, ...]] = {
        ("compose", "project"): ("Config", "Labels", "com.docker.compose.project"),
        ("compose", "service"): ("Config", "Labels", "com.docker.compose.service"),
        ("compose", "container-number"): ("Config", "Labels", "com.docker.compose.container-number"),
        ("compose", "config_files"): ("Config", "Labels", "com.docker.compose.project.config_files"),
    }
