#!/usr/bin/python3

import argparse
import re
from datetime import datetime, timedelta
from sys import argv
from typing import Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse

import requests

DEFAULT_DASHBOARD_URL = "http://dashboard.qam.suse.de"
DEFAULT_OPENQA_URL = "https://openqa.suse.de"
DEFAULT_QAM_URL = "https://qam.suse.de"


INCIDENT_GROUPS: Dict[str, int] = {
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
    "12-SP3-TERADATA": 191,
}

AGGREGATED_GROUPS: Dict[str, int] = {"core": 414, "containers": 417, "yast": 421, "security": 429}

OQA_QUERY_STRINGS: Dict[str, str] = {
    "failed": "&result=failed&result=incomplete&result=timeout_exceeded",
    "running": "&state=scheduled&state=running",
    "all": "",
}


TESTSUITE_REGEX_PATTERNS: List[str] = [
    "^.*] # [A-Z]+: [ 0-9]+.*$",
    "^.*] [=Tests ]*[Rr]esult: [A-Za-z]+.*$",
    "^.*[0-9]+ examples, [0-9]+ failures.*",
    "^.*] [A-Za-z#: ]*All [0-9 ]*tests [A-Za-z]+.*$",
    "^.*[0-9][%]? [tests ]*passed[,| in].*$",
    "^.*] [0-9]+ tests OK[.].*$",
    "^.*] Tests [a-z ]+: [ 0-9]+.*$",
    "^.*] [ ]*[Ok Passed Expectedly Failed]+[ ]*: [ 0-9]+.*$",
    "^.*] [ ]*OK[ ]*[(][ 0-9A-Za-z]+[)].*$",
]

LOGFILE_REGEX_PATTERN: str = "[A-Za-z-0-9]*[.]SUSE_SLE-[0-9]+[-SP0-9]*_Update[%3A-Za-z_-]*[.][a-z_0-9]+[.]log"


def _check_url(url: str) -> str:
    try:
        result = urlparse(url)
        all([result.scheme, result.netloc])
        return url
    except ValueError:
        raise argparse.ArgumentError("Not a valid URL")


def _parser(args) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="""For a given update, search inside the Single Incidents - Core Incidents and Aggregated updates
        job groups for openQA builds related to the update.  It searches by default within the last 5 days in the
        "Aggregated updates" section.""",
    )
    parser.add_argument(
        "update_id", type=str, help="Update ID, format SUSE:Maintenance:xxxxx:xxxxxx or S:M:xxxxx:xxxxxx"
    )
    parser.add_argument("--url-dashboard-qam", type=_check_url, default=DEFAULT_DASHBOARD_URL, help="QAM dashboard URL")
    parser.add_argument("--url-openqa", type=_check_url, default=DEFAULT_OPENQA_URL, help="OpenQA URL")
    parser.add_argument("--url-qam", type=_check_url, default=DEFAULT_QAM_URL, help="QAM URL")
    parser.add_argument(
        "--no-aggregated", action="store_true", help="Don't search for jobs in the Aggregated Updates section"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=5,
        choices=range(1, 31),
        help="How many days to search back for in the Aggregated Updates section",
    )
    parser.add_argument(
        "--aggregated-groups",
        type=str,
        default=["core"],
        choices=AGGREGATED_GROUPS.keys(),
        nargs="+",
        help="Job groups to look into inside the Aggregated Updates section",
    )

    return parser.parse_args(args)


def print_ok(text: str) -> None:
    """
    Print text in green using ANSI escape sequences

    :param text: text to print
    """
    print("\033[01;32m{}\033[0m".format(text))


def print_ko(text: str) -> None:
    """
    Print text in red using ANSI escape sequences

    :param text: text to print
    """
    print("\033[01;31m{}\033[0m".format(text))


def print_warn(text: str) -> None:
    """
    Print text in red using ANSI escape sequences

    :param text: text to print
    """
    print("\033[01;33m{}\033[0m".format(text))


def print_title(text: str) -> None:
    """
    Print text in cyan using ANSI escape sequences

    :param text: text to print
    """
    print("\033[01;36m{}\033[0m".format(text))


def _get_json(url: str) -> List[Dict]:
    """
    Fetch json data from a given url

    :param url: url to fetch json from
    :return: json data
    """
    response = requests.get(url)
    response.raise_for_status()

    return response.json()


def _get_log_text(url: str) -> str:
    """
    Fetch log text from a given url

    :param url: url to fetch log text from
    :return: log text
    """
    response = requests.get(url)
    response.raise_for_status()

    return response.text


def _parse_update_id(update_id: str) -> Tuple[int, int]:
    """
    Given an update ID, return its incident ID and request ID

    :param update_id: update ID
    :return: incident ID and request ID
    """
    _, _, incident_id, request_id = update_id.split(":")

    # check that the ids are numbers
    try:
        return int(incident_id), int(request_id)
    except ValueError as e:
        raise ValueError("Invalid update ID") from e


def _get_incident_info(url_dashboard_qam: str, incident_id: int) -> Tuple[str, Optional[List[str]]]:
    """
    Get incident build name and affected versions

    :param url_dashboard_qam: qam dashboard URL
    :param incident_id: incident ID
    :return: build name and versions
    """
    url = "{}/api/incident_settings/{}".format(url_dashboard_qam, incident_id)
    incident_settings = _get_json(url)

    try:
        # get build name
        build = incident_settings[0]["settings"]["BUILD"]

        # get all SLE versions
        versions = list(
            set(
                "{}-TERADATA".format(i["version"]) if "TERADATA" in i["flavor"] else i["version"]
                for i in incident_settings
                if i["settings"]["DISTRI"] == "sle"
            )
        )
        versions.sort()

        return build, versions
    except IndexError:
        # no builds yet
        url = "{}/api/incidents/{}".format(url_dashboard_qam, incident_id)
        incident_info = _get_json(url)
        build = ":{}:{}".format(incident_id, incident_info["packages"][0])
        return build, None


def _get_group_id(key: str) -> int:
    """
    Get the group ID for a given key

    :param key: SLE version for single incidents and job group for aggregated updates
    :return: group ID
    """
    try:
        # single incidents
        return INCIDENT_GROUPS[key]
    except KeyError:
        try:
            # aggregated updates
            return AGGREGATED_GROUPS[key]
        except KeyError as e:
            raise ValueError(
                "Not a valid version (single incident) or group (aggregated updates): {}".format(key)
            ) from e


def _get_openqa_print_url(url_openqa: str, version: str, build: str, group_id: int) -> str:
    """
    Get printable openQA url (not the API endpoint)

    :param url_openqa: openQA URL
    :param version: SLE version
    :param build: build name
    :param group_id: group ID
    :return: printable openQA URL
    """
    return "{}/tests/overview?distri=sle&version={}&build={}&groupid={}".format(url_openqa, version, build, group_id)


def _get_openqa_build_url(state: str, url_openqa: str, version: str, build: str, group_id: int) -> str:
    """
    Get the openQA build URL for a given version and build

    :param state: job state (all, running, failed)
    :param url_openqa: openQA URL
    :param version: SLE version
    :param build: build name
    :param group_id: group ID
    :return: job URL
    """
    if group_id not in [*AGGREGATED_GROUPS.values(), *INCIDENT_GROUPS.values()]:
        raise ValueError("Invalid openQA group ID")

    base_url = "{}/api/v1/jobs/overview?distri=sle&version={}&build={}&groupid={}".format(
        url_openqa, version, build, group_id
    )

    try:
        return base_url + OQA_QUERY_STRINGS[state]
    except KeyError as e:
        raise ValueError("Invalid openQA job state") from e


def _get_openqa_job_issues(url_openqa: str, job_id: int) -> Set[int]:
    """
    Get all the test issues that are being tested in an openQA job

    :param url_openqa: openQA URL
    :param job_id: openQA job ID
    :return: set of issues tested in the openQA job
    """
    issues_url = "{}/api/v1/jobs/{}".format(url_openqa, job_id)
    issues_response = _get_json(issues_url)

    # check if the job is testing the incident for this MU
    issues = []
    for k, v in issues_response["job"]["settings"].items():
        if "_TEST_ISSUES" in k.upper():
            issues.extend([int(i) for i in v.split(",")])

    # remove duplicates
    return set(issues)


def _print_openqa_job_results(url_openqa: str, version: str, build: str, group_id: int) -> None:
    """
    Print the openQA job results for a given version and build

    :param url_openqa: openQA URL
    :param version: SLE version
    :param build: build name
    :param group_id: group ID
    """
    # print version and oQA build url
    print("{} -> {}".format(version, _get_openqa_print_url(url_openqa, version, build, group_id)))

    # query oQA build for any failed or running/scheduled jobs
    running_url = _get_openqa_build_url("running", url_openqa, version, build, group_id)
    failed_url = _get_openqa_build_url("failed", url_openqa, version, build, group_id)

    running_results = _get_json(running_url)
    failed_results = _get_json(failed_url)

    # print oQA build results
    if failed_results:
        print_ko("FAILED ({} jobs)".format(len(failed_results)))
    elif running_results:
        print_warn("RUNNING/SCHEDULED ({} jobs)".format(len(running_results)))
    else:
        print_ok("PASSED")


def single_incidents(build: str, versions: List[str], url_openqa: str) -> None:
    """
    Print the openQA job results under the Single Incidents - Core Incidents section for an update

    :param build: build name
    :param versions: SLE versions
    :param url_openqa: openQA URL
    """
    print_title("Single incidents - Core")

    for version in versions:
        # version check is already done in _get_group_id
        _print_openqa_job_results(url_openqa, version, build, _get_group_id(version))


def aggregated_updates(
    incident_id: int, versions: List[str], days: int, aggregated_groups: Union[str, List], url_openqa: str
) -> None:
    """
    Print the openQA job results under the Aggregated Updates section for an update

    :param incident_id: incident ID
    :param versions: SLE versions
    :param days: how many days to search back for
    :param aggregated_groups: groups under aggregated updates to search for builds in
    :param url_openqa: openQA URL
    """
    # no teradata builds under aggregated updates
    versions = [v for v in versions if "TERADATA" not in v]

    for group in aggregated_groups:
        print_title("\nAggregated updates - {}".format(group.title()))
        for version in versions:
            for i in range(days):
                # check if there's a build for this date
                build = "{}-1".format((datetime.now() - timedelta(i)).strftime("%Y%m%d"))
                job_url = _get_openqa_build_url("all", url_openqa, version, build, _get_group_id(group))

                try:
                    # build for this date available
                    # check if it's testing the incident for this MU
                    job_id = _get_json(job_url)[0]["id"]
                    issues = _get_openqa_job_issues(url_openqa, job_id)

                    if incident_id in issues:
                        _print_openqa_job_results(url_openqa, version, build, _get_group_id(group))
                        break
                    else:
                        # this build does not test the incident for this MU
                        continue
                except IndexError:
                    # no build for this date yet
                    continue
            else:
                print_warn(
                    "{} -> No aggregated updates build for this incident in the last {} days".format(version, days)
                )


def build_checks(incident_id: int, request_id: int, build: str, url_qam: str) -> None:
    """
    Print the link and results of any build checks available for the update

    :param incident_id: incident ID
    :param request_id: request ID
    :param build: build name
    :param url_qam: qam url
    """
    print_title("\nBuild checks:\n#############")
    package_name = build.split(":")[2]
    base_url = "{}/testreports/SUSE:Maintenance:{}:{}/build_checks".format(url_qam, incident_id, request_id)

    # check if any build checks were run by looking for logs
    text = _get_log_text(base_url)
    logfiles = set(re.findall("{}{}".format(package_name, LOGFILE_REGEX_PATTERN), text, re.MULTILINE))

    if logfiles:
        for log in logfiles:
            # print log url
            log_url = "{}/{}".format(base_url, log)
            log_text = _get_log_text(log_url)
            print(log_url)

            # check for testsuite results
            for regex in TESTSUITE_REGEX_PATTERNS:
                matches = re.findall(regex, log_text, re.MULTILINE)
                if matches:
                    print("\n".join(matches), "\n")
    else:
        print("No build checks for this incident")


def main():
    # parser = _parser()
    # args = parser.parse_args()
    args = _parser(argv[1:])

    # get RR and II
    incident_id, request_id = _parse_update_id(args.update_id)
    print_title("OpenQA:\n#######")
    # get build name and versions
    build, versions = _get_incident_info(args.url_dashboard_qam, incident_id)
    if versions:
        single_incidents(build, versions, args.url_openqa)
        if not args.no_aggregated:
            print("-------")
            aggregated_updates(incident_id, versions, args.days, args.aggregated_groups, args.url_openqa)
    else:
        print_warn("No openQA builds for this incident yet")

    print("-------")
    build_checks(incident_id, request_id, build, args.url_qam)


if __name__ == "__main__":
    main()
