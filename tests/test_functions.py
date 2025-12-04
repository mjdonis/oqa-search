import copy

import mock
import pytest

from oqa_search import oqa_search
from tests.conftest import (
    MOCK_AGGREGATED_GROUPS,
    MOCK_INCIDENT_GROUPS,
    MOCK_URL,
    mock_incident_info_json,
    mock_incident_settings_json,
    mock_openqa_job_group,
    mock_openqa_job_json,
    mock_openqa_job_results,
)


@pytest.mark.parametrize(
    ("update_id", "expected_values"),
    [
        ("SUSE:Maintenance:36413:353665", (36413, 353665)),
        ("SUSE:Maintenance:36419:353574", (36419, 353574)),
        ("SUSE:Maintenance:26894:15345", (26894, 15345)),
    ],
)
def test_parse_update_id(update_id, expected_values):
    actual_values = oqa_search._parse_update_id(update_id)

    assert actual_values == expected_values

    with pytest.raises(ValueError):
        oqa_search._parse_update_id("SUSE:Maintenance:not:numbers")


@pytest.mark.parametrize(
    ("incident_id", "package_name", "versions"),
    [
        (36413, "some_package", ["15-SP2"]),
        (
            36419,
            "bar",
            ["15-SP5", "15-SP6"],
        ),
        (26894, "foo", ["12-SP3-TERADATA", "12-SP5"]),
    ],
)
@mock.patch("oqa_search.oqa_search._get_json")
def test_get_incident_info(mock_get_json, incident_id, package_name, versions):
    mock_get_json.return_value = mock_incident_settings_json(":{}:{}".format(incident_id, package_name), versions)
    actual_values = oqa_search._get_incident_info("https://fake.dashboard.url", incident_id)
    expected_build = ":{}:{}".format(incident_id, package_name)
    expected_values = (expected_build, versions)

    assert actual_values == expected_values

    # test for case when there's no build yet
    mock_get_json.side_effect = [[], mock_incident_info_json([package_name, "baz"])]
    actual_values = oqa_search._get_incident_info("https://fake.dashboard.url", incident_id)
    expected_values = (expected_build, None)

    assert actual_values == expected_values


@pytest.mark.parametrize(
    ("template", "expected_value"), [("sle-micro-2", False), (None, False), ("sle-15", True), ("sometext", True)]
)
def test_is_valid_template(template, expected_value):
    actual_value = oqa_search._is_valid_template(mock_openqa_job_group(template=template))

    assert actual_value == expected_value


@pytest.mark.parametrize(
    ("name", "expected_value"),
    [
        ("Maintenance: SLE 15 SP6 Core Incidents - DEV", False),
        ("Maintenance: Leap 15.6 Core Incidents", False),
        ("Maintenance: SLE 12 SP5 Core Incidents", True),
        ("Maintenance: SLEM 5.4 Incidents", False),
    ],
)
def test_is_name_matching_single_incidents(name, expected_value):
    actual_value = oqa_search._is_name_matching(
        mock_openqa_job_group(name=name), "Core Incidents", oqa_search.EXCLUDED_GROUPS
    )

    assert actual_value == expected_value


@pytest.mark.parametrize(
    ("name", "expected_value"),
    [
        ("YaST Maintenance Updates - Development", False),
        ("Maintenance: SLE Micro / Public Cloud Maintenance Updates", False),
        ("Core Wicked Maintenance Updates", False),
        ("Helm Chart required Images", False),
    ],
)
def test_is_name_matching_aggregated_updates(name, expected_value):
    actual_value = oqa_search._is_name_matching(
        mock_openqa_job_group(name=name), "Maintenance Updates", oqa_search.EXCLUDED_GROUPS
    )

    assert actual_value == expected_value


@pytest.mark.parametrize(
    ("match_text", "name_extractor", "bad_groups", "valid_groups", "expected_value"),
    [
        (
            "Core Incidents",
            oqa_search._extract_version,
            [
                mock_openqa_job_group(123, "Whatever Core Incidents", "sle-micro-testing"),
                mock_openqa_job_group(321, "Wicked Core Incidents From Space"),
            ],
            [
                mock_openqa_job_group(111, "Maintenance: SLE 12 SP5 Core Incidents"),
            ],
            {"12-SP5": 111},
        ),
        (
            "Core Incidents",
            oqa_search._extract_version,
            [
                mock_openqa_job_group(456, "Foobar Group Core Incidents - DEV"),
                mock_openqa_job_group(654, "Maintenance: 12-SP3-TERADATA Core Incidents", "sle-micro-2"),
                mock_openqa_job_group(564, "Containers Maintenance Updates"),
            ],
            [
                mock_openqa_job_group(444, "Maintenance: SLE 15 SP4 TERADATA Core Incidents"),
                mock_openqa_job_group(555, "Maintenance: SLE 15 SP2 Core Incidents"),
            ],
            {"15-SP4-TERADATA": 444, "15-SP2": 555},
        ),
        (
            "Maintenance Updates",
            oqa_search._extract_aggregated_name,
            [
                mock_openqa_job_group(789, "Maintenance: SLE 12 SP5 Core Incidents"),
                mock_openqa_job_group(987, "Yast & Migration Maintenance Updates", "sle-micro"),
            ],
            [
                mock_openqa_job_group(777, "SAP/HA Maintenance Updates"),
            ],
            {"sap": 777},
        ),
        (
            "Maintenance Updates",
            oqa_search._extract_aggregated_name,
            [
                mock_openqa_job_group(123, "FOO Maintenance Updates", template="tests-sle-micro"),
                mock_openqa_job_group(321, "Kernel Maintenance Updates"),
                mock_openqa_job_group(213, "Micro Geeko Maintenance Updates"),
            ],
            [
                mock_openqa_job_group(222, "Public Cloud Maintenance Updates"),
                mock_openqa_job_group(333, "Core Maintenance Updates"),
            ],
            {"cloud": 222, "core": 333},
        ),
    ],
)
@mock.patch("oqa_search.oqa_search._fetch_openqa_groups")
def test_filter_openqa_groups(
    mock_fetch_openqa_groups, match_text, name_extractor, bad_groups, valid_groups, expected_value
):
    groups = copy.deepcopy(bad_groups + valid_groups)
    mock_fetch_openqa_groups.return_value = groups

    actual_value = oqa_search._filter_openqa_groups(match_text, oqa_search.EXCLUDED_GROUPS, name_extractor)

    assert actual_value == expected_value


@pytest.mark.parametrize(
    ("name", "expected_value"),
    [
        ("Maintenance: SLE 12 SP5 Core Incidents", "12-SP5"),
        ("Maintenance: SLE 15 SP4 TERADATA Core Incidents", "15-SP4-TERADATA"),
        ("Maintenance: 12-SP3-TERADATA Core Incidents", "12-SP3-TERADATA"),
        ("Maintenance: SLE 15 SP2 Core Incidents", "15-SP2"),
    ],
)
def test_extract_version(name, expected_value):
    actual_value = oqa_search._extract_version(name)

    assert actual_value == expected_value


@pytest.mark.parametrize(
    ("name", "expected_value"),
    [
        ("Public Cloud Maintenance Updates", "cloud"),
        ("Containers Maintenance Updates", "containers"),
        ("JeOS Maintenance Updates", "jeos"),
        ("SAP/HA Maintenance Updates", "sap"),
    ],
)
def test_extract_aggregated_name(name, expected_value):
    actual_value = oqa_search._extract_aggregated_name(name)

    assert actual_value == expected_value


@pytest.mark.parametrize(
    ("key", "expected_value"),
    [
        ("15-SP1", MOCK_INCIDENT_GROUPS["15-SP1"]),
        ("15-SP4-TERADATA", MOCK_INCIDENT_GROUPS["15-SP4-TERADATA"]),
        ("core", MOCK_AGGREGATED_GROUPS["core"]),
        ("security", MOCK_AGGREGATED_GROUPS["security"]),
    ],
)
@mock.patch("oqa_search.oqa_search.get_incident_groups")
@mock.patch("oqa_search.oqa_search.get_aggregated_groups")
def test_get_group_id(mock_get_incident_groups, mock_get_aggregated_groups, key, expected_value):
    mock_get_incident_groups.return_value = MOCK_INCIDENT_GROUPS
    mock_get_aggregated_groups.return_value = MOCK_AGGREGATED_GROUPS
    actual_value = oqa_search._get_group_id(key)

    assert actual_value == expected_value

    with pytest.raises(ValueError):
        oqa_search._get_group_id("foo")


@pytest.mark.parametrize(
    ("state", "version", "build", "group_id"),
    [
        ("all", "15-SP5", ":12345:foo", 490),
        ("running", "12-SP5", ":98765:bar", 282),
        ("failed", "12-SP3-TERADATA", ":6543:baz", 417),
    ],
)
@mock.patch("oqa_search.oqa_search.get_incident_groups")
@mock.patch("oqa_search.oqa_search.get_aggregated_groups")
def test_get_openqa_build_url(mock_get_incident_groups, mock_get_aggregated_groups, state, version, build, group_id):
    mock_get_incident_groups.return_value = MOCK_INCIDENT_GROUPS
    mock_get_aggregated_groups.return_value = MOCK_AGGREGATED_GROUPS
    expected_value = (
        "{}/api/v1/jobs/overview?distri=sle&version={}&build={}&groupid={}".format(MOCK_URL, version, build, group_id)
        + oqa_search.OQA_QUERY_STRINGS[state]
    )
    actual_value = oqa_search._get_openqa_build_url(state, MOCK_URL, version, build, group_id)

    assert actual_value == expected_value

    with pytest.raises(ValueError):
        oqa_search._get_openqa_build_url(state, MOCK_URL, version, build, 000)
        oqa_search._get_openqa_build_url("foo", MOCK_URL, version, build, group_id)


@pytest.mark.parametrize(
    ("base_issues", "ltss_issues"),
    [
        ([12345, 67890], [2468, 12345]),
        ([2345], [1379]),
        ([6543], [6543]),
    ],
)
@mock.patch("oqa_search.oqa_search._get_json")
def test_openqa_job_issues(mock_get_json, base_issues, ltss_issues):
    mock_base_issue_list = ",".join([str(i) for i in base_issues])
    mock_ltss_issue_list = ",".join([str(i) for i in ltss_issues])

    mock_get_json.return_value = mock_openqa_job_json(mock_base_issue_list, LTSS_TEST_ISSUES=mock_ltss_issue_list)
    expected_values = {*base_issues, *ltss_issues}
    actual_values = oqa_search._get_openqa_job_issues(MOCK_URL, 123)

    assert actual_values == expected_values


@pytest.mark.parametrize(("running_jobs", "failed_jobs"), [(0, 0), (0, 2), (1, 2), (3, 0)])
@mock.patch("oqa_search.oqa_search._get_openqa_print_url")
@mock.patch("oqa_search.oqa_search._get_openqa_build_url")
@mock.patch("oqa_search.oqa_search._get_json")
@mock.patch("oqa_search.oqa_search.print_ko")
@mock.patch("oqa_search.oqa_search.print_warn")
@mock.patch("oqa_search.oqa_search.print_ok")
def test_openqa_job_results(
    mock_print_ok,
    mock_print_warn,
    mock_print_ko,
    mock_get_json,
    mock_get_openqa_build_url,
    mock_get_openqa_print_url,
    running_jobs,
    failed_jobs,
):
    mock_get_openqa_print_url.return_value = MOCK_URL
    mock_get_openqa_build_url.return_value = MOCK_URL
    mock_get_json.side_effect = [mock_openqa_job_results(running_jobs), mock_openqa_job_results(failed_jobs)]

    oqa_search._print_openqa_job_results(MOCK_URL, "15-SP4", ":12345:foo", 439)

    if failed_jobs > 0:
        mock_print_ko.assert_called_once()
        mock_print_ko.assert_has_calls([mock.call("FAILED ({} jobs)".format(failed_jobs))])
    elif running_jobs > 0:
        mock_print_warn.assert_called_once()
        mock_print_warn.assert_has_calls([mock.call("RUNNING/SCHEDULED ({} jobs)".format(running_jobs))])
    else:
        mock_print_ok.assert_called_once()
        mock_print_ok.assert_has_calls([mock.call("PASSED")])


def test_parser():
    mock_update_id = "S:M:12345:56789"
    with pytest.raises(SystemExit):
        oqa_search._parser([mock_update_id, "--url-qam", "not.an.url"])
        oqa_search._parser([mock_update_id, "--url-openqa", "not.an.url"])
        oqa_search._parser([mock_update_id, "--url-openqa", "not.an.url"])
        oqa_search._parser([mock_update_id, "--url-dashboard-qam", "not.an.url"])
        oqa_search._parser([mock_update_id, "--days", "1000"])
        oqa_search._parser([mock_update_id, "--days", "0"])
        oqa_search._parser([mock_update_id, "--days", "-8"])
        oqa_search._parser([mock_update_id, "--aggregated-groups", "core", "foo"])
        oqa_search._parser([mock_update_id, "--aggregated-groups", "bar", "baz"])
        oqa_search._parser([mock_update_id, "--aggregated-groups", "foobar", "yast"])
