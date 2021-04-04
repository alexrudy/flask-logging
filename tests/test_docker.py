import logging
import socket
from typing import Any
from typing import Dict

import flask_logging.docker
import pytest
from flask_logging.docker import DockerComposeInformation
from flask_logging.docker import DockerInformation
from flask_logging.docker import HostInformation


@pytest.fixture
def hostname(monkeypatch):
    hostname = "test-hostname"

    def _gethostname() -> str:
        return hostname

    monkeypatch.setattr(socket, "gethostname", _gethostname)
    return hostname


@pytest.fixture
def docker_attributes(monkeypatch):
    attrs = {
        "Labels": {
            "com.docker.compose.config-hash": "b58ebad169e9a9d391977ee308067dbf4e1793d0e9497be3680fdc324ebf8320",
            "com.docker.compose.container-number": "1",
            "com.docker.compose.oneoff": "False",
            "com.docker.compose.project": "flask-test-project",
            "com.docker.compose.project.config_files": "docker-compose.yml,docker-compose.dev.yml",
            "com.docker.compose.project.working_dir": "/path/to/working/directory",
            "com.docker.compose.service": "flask-test-service",
            "com.docker.compose.version": "1.28.5",
        },
        "Id": "3bb7926f50475bd50084c156da269f3a4763f530d6f38c2310fc41d68b7a8d45",
        "Name": "/flask-test-project_flask-test-service_1",
        "Platform": "linux",
    }

    def _get_docker_attributes(hostname: str) -> Dict[str, Any]:
        return attrs

    monkeypatch.setattr(flask_logging.docker, "_get_container_attributes", _get_docker_attributes)
    return attrs


def test_hostname_logging(watchlog, hostname):

    logger = logging.getLogger("test-docker")
    logger.addFilter(HostInformation())

    logger.info("A message here for testing")
    record = watchlog.last("test-docker")

    assert record.hostname == hostname


def test_docker_logging(watchlog, docker_attributes):

    logger = logging.getLogger("test-docker")
    logger.addFilter(DockerInformation())

    logger.info("A message here for testing")
    record = watchlog.last("test-docker")

    assert record.docker["name"] == "/flask-test-project_flask-test-service_1"
    assert record.docker["id"] == "3bb7926f50475bd50084c156da269f3a4763f530d6f38c2310fc41d68b7a8d45"
    assert record.docker["platform"] == "linux"


def test_docker_compose_logging(watchlog, docker_attributes):

    logger = logging.getLogger("test-docker")
    logger.addFilter(DockerComposeInformation())

    logger.info("A message here for testing")
    record = watchlog.last("test-docker")

    assert record.compose["project"] == "flask-test-project"
    assert record.compose["service"] == "flask-test-service"
    assert record.compose["container-number"] == "1"
