import re
from glob import iglob
from typing import Dict, List, Optional

from oqa_search import oqa_search

MOCK_URL = "https://fake.test.url"


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


def mock_build_checks_index(package: str) -> str:
    path = "tests/fixtures/{}_build_checks_index.html".format(package)

    return open(path, "r").read()


def get_expected_log_matches(log_text: str) -> List[List[str]]:
    all_matches = []
    for regex in oqa_search.TESTSUITE_REGEX_PATTERNS:
        matches = re.findall(regex, log_text, re.MULTILINE)
        if matches:
            all_matches.append(matches)

    return all_matches


def get_mock_log_filenames(package: str) -> List[str]:
    logs_dir = "tests/fixtures/{}".format(package)
    paths = iglob("{}/*.log".format(logs_dir))

    return [path.split("/")[-1] for path in paths]


def mock_log_text(package: str) -> List[str]:
    logs_dir = "tests/fixtures/{}".format(package)
    paths = iglob("{}/*.log".format(logs_dir))
    logs_text = [open(path, "r").read() for path in paths]

    return logs_text
