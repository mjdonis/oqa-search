import mock
import pytest

from oqa_search import oqa_search
from tests.conftest import (
    MOCK_URL,
    mock_incident_info_json,
    mock_incident_settings_json,
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
    ("key", "expected_value"),
    [
        ("15-SP1", oqa_search.INCIDENT_GROUPS["15-SP1"]),
        ("15-SP4-TERADATA", oqa_search.INCIDENT_GROUPS["15-SP4-TERADATA"]),
        ("core", oqa_search.AGGREGATED_GROUPS["core"]),
        ("security", oqa_search.AGGREGATED_GROUPS["security"]),
    ],
)
def test_get_group_id(key, expected_value):
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
def test_get_openqa_build_url(state, version, build, group_id):
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
