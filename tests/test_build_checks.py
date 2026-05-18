from urllib.parse import quote

import mock
import pytest

from oqa_search import oqa_search
from tests.conftest import (
    MOCK_URL,
    get_expected_log_matches,
    get_mock_log_filenames,
    mock_build_checks_index,
    mock_log_text,
)


class BuildChecksMockData:
    """container for build checks mock data"""

    def __init__(self, package):
        self.package = package
        self.mock_logs_text = mock_log_text(package)
        self.expected_log_matches = get_expected_log_matches(package)
        self.mock_index = mock_build_checks_index(package)
        self.mock_log_filenames = get_mock_log_filenames(package)


@pytest.fixture
def build_checks_test_data(request):
    """
    Fixture to set up common mock data for build checks tests
    """
    return BuildChecksMockData(request.param)


@pytest.mark.parametrize(
    "package",
    [
        "AppStream",
        "automake",
        "frr",
        "gtk-vnc",
        "iniparser",
        "python",
        "rust",
    ],
)
def test_extract_test_results(package):
    mock_logs_text = mock_log_text(package)
    mock_results = get_expected_log_matches(package)

    for log_text, expected_value in zip(mock_logs_text, mock_results):
        value = oqa_search.extract_test_results(log_text)

        assert value == expected_value


@pytest.mark.parametrize(
    (
        "build_checks_test_data",
        "product",
        "incident_id",
        "request_id",
        "expected_passed",
        "expected_failed",
        "expected_hidden_lines",
    ),
    [
        ("automake", "Maintenance", 1234, 56789, None, None, None),
        ("python", "Maintenance", 9876, 12345, None, None, None),
        ("rust", "Maintenance", 44131, 408430, 758, 0, 5),
        ("gtk-vnc", "SLFO", "1.2", 2069, None, None, None),
        ("frr", "SLFO", "1.2", 3941, 0, 0, 6),
    ],
    indirect=["build_checks_test_data"],  # package names go to the fixture, test gets a BuildChecksMockData obj
)
@mock.patch("oqa_search.oqa_search._fetch_url_content")
@mock.patch("oqa_search.oqa_search.print")
@mock.patch("oqa_search.oqa_search.print_title")
@mock.patch("oqa_search.oqa_search.extract_test_results")
def test_build_checks(
    mock_extract_test_results,
    mock_print_title,
    mock_print,
    mock_fetch_url_content,
    build_checks_test_data,
    product,
    incident_id,
    request_id,
    expected_passed,
    expected_failed,
    expected_hidden_lines,
):
    """Test build_checks prints URLs and test results, with summary when >4 lines"""
    mock_data = build_checks_test_data

    mock_fetch_url_content.side_effect = [mock_data.mock_index, *mock_data.mock_logs_text]
    mock_extract_test_results.side_effect = mock_data.expected_log_matches
    oqa_search.build_checks(
        product, incident_id, request_id, ":smelt:{}:{}".format(incident_id, mock_data.package), MOCK_URL, None
    )

    mock_urls = [
        "{}/testreports/SUSE:{}:{}:{}/build_checks/{}".format(MOCK_URL, product, incident_id, request_id, quote(file))
        for file in mock_data.mock_log_filenames
    ]
    calls = [mock.call(url) for url in mock_urls]

    for matches in mock_data.expected_log_matches:
        if matches:
            if len(matches) > 4:
                calls.append(mock.call(matches[0]))
                calls.append(mock.call(matches[-1], "\n"))
            else:
                calls.append(mock.call("\n".join(matches), "\n"))

    assert mock_extract_test_results.call_count == len(mock_data.mock_log_filenames)

    for call in calls:
        assert call in mock_print.call_args_list

    if expected_passed is not None:
        summary_calls = [str(call) for call in mock_print.call_args_list if "more results" in str(call)]
        large_matches = [m for m in mock_data.expected_log_matches if len(m) > 4]

        assert len(summary_calls) == len(
            large_matches
        ), f"Expected {len(large_matches)} summary lines, found {len(summary_calls)}"

        for summary_line in summary_calls:
            assert f"{expected_hidden_lines} more results" in summary_line
            assert f"{expected_passed} passed" in summary_line
            assert f"{expected_failed} failed" in summary_line


@pytest.mark.parametrize(
    ("lines", "expected_summary"),
    [
        (
            [
                "First line",
                "100 passed",
                "50 failed",
                "Last line",
            ],
            "(2 more results, 100 passed, 50 failed)",
        ),
        (
            [
                "First line",
                "10 pass",
                "5 fail",
                "20 pass",
                "3 fail",
                "Last line",
            ],
            "(4 more results, 30 passed, 8 failed)",
        ),
        (
            [
                "[  204s] ======================= 437 passed, 5 skipped in 22.51s ========================",
                "[  204s] # TOTAL: 0",
                "[  204s] # PASS:  0",
                "[  204s] # SKIP:  0",
                "[  204s] # XFAIL: 0",
                "[  204s] # FAIL:  0",
                "[  204s] # XPASS: 0",
                "[  204s] # ERROR: 0",
            ],
            "(6 more results, 0 passed, 0 failed)",
        ),
    ],
)
def test_summarize_test_results(lines, expected_summary):
    summary = oqa_search.summarize_test_results(lines)

    assert summary == expected_summary
