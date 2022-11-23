import csv
import os.path
import subprocess
from typing import Dict, Iterable, List, Optional

import pytest

import univention.testing.ucr


ucr = univention.testing.ucr.UCSTestConfigRegistry()
ucr.load()
HOSTNAME = ucr.get("hostname")
DOMAIN_NAME = ucr.get("domainname")
DEFAULT_HOST = f"{HOSTNAME}.{DOMAIN_NAME}"


BASE_DIR = "/var/lib/udm-performance-tests/"
VENV = os.path.join(BASE_DIR, "venv")
LOCUST_EXE = os.path.join(VENV, "bin", "locust")

ENV_LOCUST_DEFAULTS: Dict[str, str] = {
    "LOCUST_LOGLEVEL": "INFO",
    "LOCUST_RUN_TIME": "10s",
    "LOCUST_SPAWN_RATE": "1",
    "LOCUST_STOP_TIMEOUT": "10",
    "LOCUST_USERS": "1",
    "LOCUST_WAIT_TIME": "0.05",
}

LOCUST_FILES_DIRNAME = "locustfiles"
RESULT_DIR = os.path.join(BASE_DIR, "results")
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
LOCUST_FILES_DIR = os.path.join(TEST_DIR, LOCUST_FILES_DIRNAME)


def set_locust_environment_vars(locust_env_vars: Dict[str, str]):
    for k, v in locust_env_vars.items():
        if not k.startswith("LOCUST_"):
            raise ValueError(f"Environment variable {k} is not a locust enviroment variable.")
        os.environ[k] = v


@pytest.fixture(scope="session")
def rows():
    def _func(csv_file_name: str) -> Iterable[Dict[str, str]]:
        print("Reading {!r}...".format(csv_file_name))
        with open(csv_file_name) as fp:
            yield from csv.DictReader(fp)

    return _func


@pytest.fixture(scope="session")
def get_one_row(rows):
    def _func(csv_file: str, column_name: str, column_value: str) -> Dict[str, str]:
        for row in rows(csv_file):
            if row[column_name] == column_value:
                return row
        raise ValueError(
            "No row found that had a column {!r} with value {!r}.".format(column_name, column_value)
        )

    return _func


@pytest.fixture(scope="session")
def check_failure_count(rows):
    def _func(result_file_base_path: str) -> None:
        csv_file = f"{result_file_base_path}_stats.csv"
        col = "Failure Count"
        for row in rows(csv_file):
            value = int(row[col])
            assert value == 0

    return _func


@pytest.fixture(scope="session")
def check_rps(get_one_row):
    def _func(result_file_base_path: str, url_name: str, expected_min: float) -> None:
        csv_file = f"{result_file_base_path}_stats.csv"
        row = get_one_row(csv_file, "Name", url_name)
        col_avg_r_time = "Average Response Time"
        avg_r_time = float(row[col_avg_r_time])
        rps = 1000 / avg_r_time
        assert rps > expected_min
    return _func


@pytest.fixture(scope="session")
def check_95_percentile(get_one_row):
    def _func(result_file_base_path: str, url_name: str, expected_max: int) -> None:
        csv_file = f"{result_file_base_path}_stats.csv"
        row = get_one_row(csv_file, "Name", url_name)
        col = "95%"
        value = int(row[col])
        assert value < expected_max

    return _func


@pytest.fixture(scope="session")
def check_95_percentile_multirow(get_one_row):
    def _func(result_file_base_path: str, url_names: List[str], expected_max: int) -> None:
        value = 0
        csv_file = f"{result_file_base_path}_stats.csv"
        for url_name in url_names:
            row = get_one_row(csv_file, "Name", url_name)
            col = "95%"
            value += int(row[col])
        assert value < expected_max

    return _func


@pytest.fixture(scope="session")
def execute_test():
    """
    Execute `Locust`. Configure by setting environment variables (`LOCUST_*`). See
    https://docs.locust.io/en/stable/configuration.html#all-available-configuration-options
    """

    def _func(
        locust_path: str,
        locust_user_class: str,
        result_file_base_path: str,
        host: str,
        loglevel: Optional[str] = None,
    ) -> None:
        for k, v in ENV_LOCUST_DEFAULTS.items():
            if k not in os.environ:
                os.environ[k] = v
        if loglevel:
            os.environ["LOCUST_LOGLEVEL"] = loglevel
        logfile = f"{result_file_base_path}.log"
        envs = {k: v for k, v in os.environ.items() if k.startswith("LOCUST_")}
        cmd = [
            LOCUST_EXE,
            "--locustfile",
            locust_path,
            "--host",
            host,
            "--headless",
            f"--csv={result_file_base_path}",
            f"--html={result_file_base_path}.html",
            "--print-stats",
            locust_user_class,
        ]
        print("Executing {!r}...".format(" ".join(cmd)))
        print(f"Redirecting stdout and stderr for Locust execution to {logfile!r}.")
        msg = f"Running with 'LOCUST_' environment variables: {envs!r}\nExecuting: {cmd!r}\n"
        print(msg)
        with open(f"{result_file_base_path}.log", "w") as fp:
            fp.write(f"{msg}\n")
            fp.flush()
            process = subprocess.Popen(cmd, stdout=fp, stderr=fp)  # nosec
            process.communicate()

    return _func


@pytest.fixture(scope="session")
def verify_test_sent_requests(rows):
    def _func(result_file_base_path: str) -> None:
        csv_file = f"{result_file_base_path}_stats.csv"
        col = "Name"
        for row in rows(csv_file):
            assert row[col] != "Aggregated"  # should be the last row, so no requests were sent
            break  # found a row with request statistics

    return _func
