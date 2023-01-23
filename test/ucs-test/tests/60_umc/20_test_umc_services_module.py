#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test the UMC service module autostart behavior
## bugs: [34506]
## exposure: dangerous

import subprocess

import pytest

from univention.config_registry.frontend import ucr_update

from umc import UMCBase


SERVICE_NAME = "nscd"
AUTOSTART_VAR = f'{SERVICE_NAME}/autostart'


@pytest.mark.exposure('dangerous')
class Test_UMCServiceAutostart:
    service = None

    @pytest.fixture(scope='class', autouse=True)
    def restore_initial_configuration(self):
        """
        Restores the autostart configuration as saved in the global var
        for provided 'SERVICE_NAME'
        """
        Test_UMCServiceAutostart.service = ServiceModule()
        self.service.create_connection_authenticate()
        self.service.check_service_presence(self.service.query(), SERVICE_NAME)
        initial_service_config = self.get_service_current_configuration(AUTOSTART_VAR)
        yield
        ucr_update(self.service.ucr, {AUTOSTART_VAR: initial_service_config})

    def get_service_current_configuration(self, service_name_value):
        """
        Get the current UCR configuration for provided 'service_name_value' var
        Reloads the UCR before proceeding.
        """
        self.service.ucr.load()
        return self.service.ucr.get(service_name_value)

    def set_service_configuration(self, service_names, setting):
        """Set the 'setting' for list of 'service_names' via UMC request"""
        request_result = self.service.client.umc_command('services/' + setting, service_names).result
        assert request_result
        assert request_result['success']

    def test_autostart_yes_to_no(self):
        assert self.get_service_current_configuration(AUTOSTART_VAR) == 'yes'
        self.set_service_configuration([SERVICE_NAME], 'start_never')
        assert self.get_service_current_configuration(AUTOSTART_VAR) == "no"

    def test_autostart_no_to_manually(self):
        assert self.get_service_current_configuration(AUTOSTART_VAR) == 'no'
        self.set_service_configuration([SERVICE_NAME], 'start_manual')
        assert self.get_service_current_configuration(AUTOSTART_VAR) == "manually"

    def test_autostart_manually_to_no(self):
        assert self.get_service_current_configuration(AUTOSTART_VAR) == 'manually'
        self.set_service_configuration([SERVICE_NAME], 'start_never')
        assert self.get_service_current_configuration(AUTOSTART_VAR) == "no"

    def test_autostart_no_to_yes(self):
        assert self.get_service_current_configuration(AUTOSTART_VAR) == 'no'
        self.set_service_configuration([SERVICE_NAME], 'start_auto')
        assert self.get_service_current_configuration(AUTOSTART_VAR) == "yes"

    def test_autostart_yes_to_manually(self):
        assert self.get_service_current_configuration(AUTOSTART_VAR) == 'yes'
        self.set_service_configuration([SERVICE_NAME], 'start_manual')
        assert self.get_service_current_configuration(AUTOSTART_VAR) == "manually"

    def test_autostart_manually_to_yes(self):
        assert self.get_service_current_configuration(AUTOSTART_VAR) == 'manually'
        self.set_service_configuration([SERVICE_NAME], 'start_auto')
        assert self.get_service_current_configuration(AUTOSTART_VAR) == "yes"


@pytest.mark.exposure('dangerous')
class Test_UMCServiceProcessHandling:

    @pytest.fixture(autouse=True)
    def service_module(self):
        if not hasattr(self, "service"):
            self.service = ServiceModule()
            self.service.create_connection_authenticate()

            initial_state = self.service.query()
            self.service.check_service_presence(initial_state, SERVICE_NAME)
            for result in initial_state:
                if result['service'] == SERVICE_NAME and result['autostart'] in ('no', 'false'):
                    print("Skipped due to: %s/autostart=%s" % (SERVICE_NAME, result['autostart']))
                    self.service.return_code_result_skip()

    @pytest.fixture()
    def save_initial_state(self, service_module):
        self.initial_service_state_running = self.query_service_is_running(SERVICE_NAME)

        if self.initial_service_state_running:
            assert self.get_service_current_pid(SERVICE_NAME)
        else:
            assert not self.get_service_current_pid(SERVICE_NAME)

    @pytest.fixture(autouse=True)
    def restore_initial_state(self, service_module, save_initial_state):
        yield
        if self.initial_service_state_running:
            print("Trying to restore the '%s' service to initially "
                  "running state" % SERVICE_NAME)
            self.do_service_action([SERVICE_NAME], 'start')
            assert self.query_service_is_running(SERVICE_NAME)
            assert self.get_service_current_pid(SERVICE_NAME)
        elif self.initial_service_state_running is False:
            print("Trying to restore the '%s' to initially stopped state"
                  % SERVICE_NAME)
            self.do_service_action([SERVICE_NAME], 'stop')
            assert not self.query_service_is_running()
            assert self.get_service_current_pid()

    def query_service_is_running(self, service_name):
        """
        Get the current state for provided 'service_name' by making
        'services/query' UMC request and returning 'isRunning' field value
        """
        request_result = self.service.query()
        for result in request_result:
            if result['service'] == service_name:
                return result['isRunning']
        raise AssertionError("Couldn't find service %s: %s" % (service_name, request_result))

    def get_service_current_pid(self, service_name):
        """
        Get the process id for the provided 'service_name' by using pgrep.
        Returns pid as a string.
        """
        proc = subprocess.Popen(("pgrep", service_name),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        if not stderr:
            return stdout.rstrip()

    def do_service_action(self, service_names, action):
        """
        Applies an 'action' for provided 'service_names' list via UMC request.
        Possible options for actions are: start/stop/restart.
        """
        request_result = self.service.client.umc_command(f'services/{action}', service_names).result
        assert request_result
        assert request_result['success']

    def save_initial_service_state(self):
        """
        Saves the initial state of the process (Running == True ;
        Stopped == False).
        Makes a check if pid is not empty when process is running
        and v.v. - that pid is empty when 'SERVICE_NAME' is stopped.
        """
        self.initial_service_state_running = self.query_service_is_running(SERVICE_NAME)

        if self.initial_service_state_running:
            assert self.get_service_current_pid(SERVICE_NAME)
        else:
            assert not self.get_service_current_pid(SERVICE_NAME)

    def test_response_structure(self):
        """Check the response general structure for obligatory keys"""
        request_result = self.service.query()
        assert request_result
        for result in request_result:
            assert all(x in result for x in ('service', 'isRunning', 'description', 'autostart'))

    def test_directory_listener(self):
        """Check if the 'Univention Directory Listener' was listed in the response"""
        request_result = self.service.query()
        assert request_result
        assert any("univention-directory-listener" in x['service'] for x in request_result)

    def test_service_process_states(self):
        self.do_service_action([SERVICE_NAME], 'start')

        assert self.query_service_is_running(SERVICE_NAME)
        assert self.get_service_current_pid(SERVICE_NAME)

    def test_service_restart_already_running(self):
        last_service_pid = self.get_service_current_pid(SERVICE_NAME)
        self.do_service_action([SERVICE_NAME], 'restart')
        assert self.query_service_is_running(SERVICE_NAME)

        current_service_pid = self.get_service_current_pid(SERVICE_NAME)
        assert current_service_pid
        assert current_service_pid != last_service_pid

    def test_stop_running_service(self):
        self.do_service_action([SERVICE_NAME], 'stop')

        assert not self.query_service_is_running(SERVICE_NAME)
        assert not self.get_service_current_pid(SERVICE_NAME)

    def test_restart_not_running_service(self):
        self.do_service_action([SERVICE_NAME], 'restart')

        assert self.query_service_is_running(SERVICE_NAME)
        assert self.get_service_current_pid(SERVICE_NAME)

    def test_starting_already_started_service(self):
        last_service_pid = self.get_service_current_pid(SERVICE_NAME)
        self.do_service_action([SERVICE_NAME], 'start')

        assert self.query_service_is_running(SERVICE_NAME)
        current_service_pid = self.get_service_current_pid(SERVICE_NAME)
        assert current_service_pid
        assert current_service_pid == last_service_pid


class ServiceModule(UMCBase):

    def query(self):
        return self.request('services/query')

    def check_service_presence(self, request_result, service_name):
        """
        Check if the service with 'service_name' was listed in the response
        'request_result'. Returns 'missing software' code 137 when missing.
        """
        assert any(request['service'] == service_name for request in request_result)
