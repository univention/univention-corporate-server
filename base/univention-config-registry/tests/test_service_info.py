#!/usr/bin/python3
"""Unit test for univention.service_into."""
# pylint: disable-msg=C0103,E0611,R0904

from argparse import Namespace

import pytest

import univention.service_info as usi


@pytest.fixture
def service():
	"""Empty service info."""
	return usi.Service()


@pytest.fixture
def mins(service):
	"""Minimum service info."""
	for key in service.REQUIRED:
		service[key] = key
	return service


@pytest.fixture
def maxs(mins):
	"""Maximum service info."""
	for key in mins.OPTIONAL:
		mins[key] = key
	return mins


class TestService(object):

	@pytest.fixture
	def popen(self, mocker):
		"""Fake subprocess.Popen() call."""
		mock = mocker.patch("subprocess.Popen")
		mock.return_value.communicate.return_value = (b"", b"")
		mock.return_value.returncode = 0
		return mock

	def test_incomplete(self, service):
		assert set(service.check()) == {"description", "programs"}

	def test_min(self, mins):
		assert mins.check() == []

	def test_max(self, maxs):
		assert maxs.check() == []

	def test_extra(self, mins):
		mins["extra"] = "extra"
		assert mins.check() == ["extra"]

	def test_repr(self, service):
		assert repr(service) == "Service({})"

	@pytest.mark.parametrize("running", [False, True])
	def test_update_status(self, running, mins, mocker):
		pidof = mocker.patch("univention.service_info.pidof")
		pidof.return_value = running
		mins._update_status()
		assert mins.running == running
		pidof.assert_called_once_with("programs")

	def test_start(self, maxs, popen):
		assert maxs.start()
		popen.assert_called_once()

	def test_stop(self, maxs, popen):
		assert maxs.stop()
		popen.assert_called_once()

	def test_restart(self, maxs, popen):
		assert maxs.restart()
		popen.assert_called_once()

	def test_status(self, maxs, popen):
		assert maxs.status() == ""
		popen.assert_called_once()

	def test_status_error(self, maxs, popen):
		popen.side_effect = EnvironmentError
		assert maxs.status() == u""

	@pytest.mark.parametrize("field", ["systemd", "name"])
	@pytest.mark.parametrize("name", ["name", "name.service"])
	def test_serivce_systemd_service(self, field, name, mins):
		mins[field] = name
		assert mins._service_name() == "name"

	@pytest.mark.parametrize("field", ["init_script", "systemd", "name"])
	def test_change_state(self, field, mins, popen):
		mins[field] = "name"
		assert mins._change_state("action")
		popen.assert_called_once()

	def test_change_state_error(self, mins, popen):
		mins["name"] = "name"
		popen.return_value.returncode = 1
		with pytest.raises(usi.ServiceError):
			mins._change_state("action")


class TestPidOf(object):

	def test_basic(self, mocker, tmpdir):
		docker_pid = tmpdir.join("docker.pid")
		docker_pid.write("42")
		mocker.patch("os.listdir").return_value = []
		assert usi.pidof("XXX", str(docker_pid)) == []

	def test_nodocker(self, mocker):
		mocker.patch("os.listdir").return_value = []
		assert usi.pidof("XXX", 0) == []

	def test_docker(self, mocker):
		mocker.patch("os.listdir").return_value = []
		assert usi.pidof("XXX", 42) == []


class TestServiceInfo(object):

	@pytest.fixture(autouse=True)
	def setup0(self, tmpdir, monkeypatch):
		"""Fake empty service info files."""
		base = tmpdir.mkdir("service.info")
		monkeypatch.setattr(usi.ServiceInfo, "BASE_DIR", str(base))
		services = base.join(usi.ServiceInfo.SERVICES)
		return Namespace(base=base, services=services)

	@pytest.fixture
	def setup(self, setup0):
		"""Fake populated service info files."""
		setup0.services.mkdir()
		setup0.services.join("a.cfg").write("[a]\ndescription=a\nprograms=programs\n")
		setup0.services.join("b.cfg").write("[b]\ndescription=b\nprograms=b\n")
		# setup0.services.join("c.cfg").write("[b]\ndescription=b\n")  # BUG: __init__() -> update_services() -> _update_status() -> KeyError("programs")
		setup0.services.join("c.cfg").write("[c]\nprograms=c")
		setup0.services.join("d.invallid").write("[c]\ndescription=c")
		setup0.services.join(usi.ServiceInfo.CUSTOMIZED).write("[b]\ndescription=B\nprograms=B\n")
		return setup0

	@pytest.fixture
	def services0(self, setup0):
		"""Empty service info instance."""
		return usi.ServiceInfo(install_mode=True)

	@pytest.fixture
	def services(self, setup):
		"""Service info instance."""
		return usi.ServiceInfo()

	def test_load_install(self, services0):
		assert services0.services == {}

	def test_load(self, services):
		assert services.services

	def test_read_servics_error(self, services0):
		with pytest.raises(AttributeError):
			services0.read_services()

	def test_read_servics_explicit(self, services0, setup):
		services0.read_services(package="a")
		assert services0.services["a"]

	@pytest.mark.parametrize("override", [False, True])
	def test_read_servics_override(self, override, services, setup):
		over = setup.services.join("x.cfg")
		over.write("[a]\ndescription=other\n")
		services.read_services(str(over), override=override)
		assert services.services["a"]["description"] == "other" if override else "a"

	def test_read_servics_missing(self, services0, tmpdir):
		tmp = tmpdir.join("x.cfg")
		tmp.write("[x]\ndescription=x\nprograms=/does-not-exist param,other\n")
		services0.read_services(filename=str(tmp))
		assert not services0.services

	def test_check_services(self, services):
		assert services.check_services() == {"c": ["description"]}

	def test_write_customized(self, services, setup):
		assert services.write_customized()
		assert setup.services.join(usi.ServiceInfo.CUSTOMIZED).check(file=1)

	def test_write_customized_error(self, services0):
		assert not services0.write_customized()

	def test_get_services(self, services):
		assert sorted(services.get_services()) == ["a", "b", "c"]

	def test_get_service(self, services):
		assert services.get_service("a")["name"] == "a"

	def test_get_service_None(self, services):
		assert services.get_service("x") is None

	def test_add_service(self, services0, mins):
		services0.add_service("a", mins)
		assert services0.services == {"a": mins}

	def test_add_service_invalid(self, services0, service):
		services0.add_service("a", service)
		assert services0.services == {}
