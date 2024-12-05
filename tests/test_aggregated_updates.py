from datetime import datetime, timedelta

import mock
import pytest

from oqa_search import oqa_search
from tests.conftest import MOCK_URL, mock_openqa_job_results


@pytest.mark.parametrize(
    ("versions", "days", "aggregated_groups"),
    [
        (["15-SP2"], 5, ["core"]),
        (["12-SP3-TERADATA", "15-SP5", "15-SP6"], 2, ["containers", "yast"]),
        (["12-SP5", "15-SP4"], 3, ["security"]),
    ],
)
@mock.patch("oqa_search.oqa_search._print_openqa_job_results")
@mock.patch("oqa_search.oqa_search._get_openqa_job_issues")
@mock.patch("oqa_search.oqa_search._get_json")
def test_aggregated_updates(
    mock_get_json,
    mock_get_openqa_job_issues,
    mock_print_openqa_job_results,
    versions,
    days,
    aggregated_groups,
):
    actual_versions = [v for v in versions if "TERADATA" not in v]
    mock_get_json.return_value = mock_openqa_job_results(1)
    mock_issues = []
    for _ in range(len(aggregated_groups) * len(actual_versions)):
        for i in range(days - 1):
            mock_issues.append([i])
        mock_issues.append([12345])
    mock_get_openqa_job_issues.side_effect = mock_issues

    oqa_search.aggregated_updates(12345, versions, days, aggregated_groups, MOCK_URL)

    calls = [
        mock.call(
            MOCK_URL,
            version,
            "{}-1".format((datetime.now() - timedelta(days - 1)).strftime("%Y%m%d")),
            oqa_search.AGGREGATED_GROUPS[group],
        )
        for version in actual_versions
        for group in aggregated_groups
    ]
    mock_print_openqa_job_results.assert_has_calls(calls, any_order=True)
    expected_call_count = len(aggregated_groups) * len(actual_versions)
    assert mock_print_openqa_job_results.call_count == expected_call_count


@mock.patch("oqa_search.oqa_search._print_openqa_job_results")
def test_aggregated_updates_teradata_versions_only(mock_print_openqa_job_results):
    oqa_search.aggregated_updates(12345, ["12-SP3-TERADATA", "15-SP4-TERADATA"], 5, ["core"], MOCK_URL)
    mock_print_openqa_job_results.assert_not_called()


@mock.patch("oqa_search.oqa_search.print_warn")
@mock.patch("oqa_search.oqa_search._print_openqa_job_results")
@mock.patch("oqa_search.oqa_search._get_openqa_job_issues")
@mock.patch("oqa_search.oqa_search._get_json")
def test_aggregated_updates_no_builds(
    mock_get_json,
    mock_get_openqa_job_issues,
    mock_print_openqa_job_results,
    mock_print_warn,
):
    mock_get_json.return_value = mock_openqa_job_results(1)
    mock_get_openqa_job_issues.side_effect = [[i] for i in range(5)]
    oqa_search.aggregated_updates(12345, ["15-SP4"], 5, ["core"], MOCK_URL)

    mock_print_openqa_job_results.assert_not_called()
    mock_print_warn.assert_called_once()
    mock_print_warn.assert_has_calls(
        [mock.call("15-SP4 -> No aggregated updates build for this incident in the last 5 days")]
    )
