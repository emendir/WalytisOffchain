"""Run all tests in all variations."""

from emtest import ensure_dir_exists
from datetime import datetime
from time import sleep
import os
import sys

from emtest import set_env_var, env_vars

WORKDIR = os.path.dirname(__file__)

pytest_args = sys.argv[1:]


TEST_FUNC_TIMEOUT_SEC = 300
REPORTS_DIR_PREF = env_vars.str(
    "WALY_TEST_REPORTS_DIR", default=os.path.join("reports", "report-")
)


def run_tests() -> None:
    """Run each test file with pytest."""
    pytest_args = sys.argv[1:]
    timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    html_path = os.path.join(REPORTS_DIR_PREF + timestamp, "report.html")
    json_path = os.path.join(REPORTS_DIR_PREF + timestamp, "report.json")
    ensure_dir_exists(os.path.dirname(html_path))
    ensure_dir_exists(os.path.dirname(json_path))

    test_files = [
        os.path.join(WORKDIR, file)
        for file in os.listdir(WORKDIR)
        if (file.startswith("test_") and file.endswith(".py"))
    ]
    test_files.sort()
    for test_file in test_files:
        os.system(
            f"{sys.executable} -m pytest {test_file} "
            f"--html={html_path} "
            f"--json={json_path} "
            f"--timeout={TEST_FUNC_TIMEOUT_SEC} "
            f"{' '.join(pytest_args)} "
        )


print("Starting Brenthy...")
os.system("sudo systemctl start ipfs brenthy")
sleep(5)
if True:
    os.chdir(WORKDIR)
    import conftest  # noqa
    from waloff_docker.build_docker import build_docker_image
    from prebuilt_group_did_managers import create_did_managers


if env_vars.bool("TESTS_REBUILD_DOCKER", default=True):
    create_did_managers()
    build_docker_image(verbose=False)

set_env_var("TESTS_REBUILD_DOCKER", False)

# Test Procedure (Post-Prep)

set_env_var("WALYTIS_TEST_MODE", "RUN_BRENTHY")
print("Running tests with Brenthy...")
run_tests()

set_env_var("WALYTIS_TEST_MODE", "EMBEDDED")
print("Running tests with Walytis Embedded...")
run_tests()


os.system(
    "docker ps --filter 'ancestor=brenthy_testing' - aq | docker rm - f || true"
)
os._exit(0)
