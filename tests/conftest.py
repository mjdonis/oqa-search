from glob import iglob
from typing import Dict, List, Optional

MOCK_URL = "https://fake.test.url"

MOCK_LOGS_DIR = "tests/fixtures"

MOCK_INCIDENT_GROUPS = {
    "15-SP1": 233,
    "15-SP2": 306,
    "15-SP3": 367,
    "15-SP4": 439,
    "15-SP5": 490,
    "15-SP6": 546,
    "15-SP7": 644,
    "12-SP3": 106,
    "12-SP5": 282,
    "15-SP4-TERADATA": 521,
    "12-SP3-TERADATA": 106,
}

MOCK_AGGREGATED_GROUPS = {"core": 414, "containers": 417, "yast": 421, "security": 429, "cloud": 427}


def mock_incident_settings_json(
    build: str,
    versions: List[str],
    *,
    distri: Optional[str] = "sle",
    settings_kwargs: Optional[Dict[str, str]] = {},
    **kwargs
) -> List[Dict]:
    return [
        {
            "flavor": "TERADATA" if "TERADATA" in v else "",
            "version": v.replace("-TERADATA", "") if "TERADATA" in v else v,
            "settings": {
                "BUILD": "{}".format(build),
                "DISTRI": "{}".format(distri),
                **settings_kwargs,
            },
            **kwargs,
        }
        for v in versions
    ]


def mock_incident_info_json(packages, **kwargs) -> Dict[str, str]:
    return {"packages": packages, **kwargs}


def mock_openqa_job_json(issues: str, **kwargs) -> Dict[str, Dict]:
    return {"job": {"settings": {"BASE_TEST_ISSUES": issues, **kwargs}}}


def mock_openqa_job_results(jobs: int) -> List[Dict[str, str]]:
    return [{"id": i, "name": "somejob-{}".format(i)} for i in range(jobs)]


def mock_openqa_job_group(id: int = 123, name: str = "somename", template: str = "sometemplate"):
    return {"id": id, "name": name, "template": template}


def mock_build_checks_index(package: str) -> str:
    path = "tests/fixtures/{}_build_checks_index.html".format(package)

    return open(path, "r").read()


def _get_mock_log_files(package: str, pattern: str) -> List[str]:
    logs_dir = "{}/{}".format(MOCK_LOGS_DIR, package)
    paths = list(iglob(pattern.format(logs_dir)))
    paths.sort()

    return paths


def get_mock_log_filenames(package: str) -> List[str]:
    paths = _get_mock_log_files(package, "{}/*.log")

    return [path.split("/")[-1] for path in paths]


def mock_log_text(package: str) -> List[str]:
    paths = _get_mock_log_files(package, "{}/*.log")
    logs_text = [open(path, "r").read() for path in paths]

    return logs_text


def get_expected_log_matches(package: str) -> List[List[str]]:
    paths = _get_mock_log_files(package, "{}/*.matches")
    logs_text = [open(path, "r").read().splitlines() for path in paths]

    return logs_text
