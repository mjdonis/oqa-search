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


@pytest.mark.parametrize(
    "package",
    [
        "AppStream",
        "automake",
        "iniparser",
        "python",
    ],
)
def test_extract_test_results(package):
    mock_logs_text = mock_log_text(package)
    mock_results = get_expected_log_matches(package)

    for log_text, expected_value in zip(mock_logs_text, mock_results):
        value = oqa_search.extract_test_results(log_text)

        assert value == expected_value


@pytest.mark.parametrize(
    ("incident_id", "request_id", "package"),
    [
        (1234, 56789, "automake"),
        (9876, 12345, "python"),
    ],
)
@mock.patch("oqa_search.oqa_search._get_log_text")
@mock.patch("oqa_search.oqa_search.print")
@mock.patch("oqa_search.oqa_search.print_title")
@mock.patch("oqa_search.oqa_search.extract_test_results")
def test_build_checks(
    mock_extract_test_results, mock_print_title, mock_print, mock_get_log_text, incident_id, request_id, package
):
    mock_logs_text = mock_log_text(package)
    mock_get_log_text.side_effect = [mock_build_checks_index(package), *mock_logs_text]
    expected_log_matches = get_expected_log_matches(package)
    mock_extract_test_results.side_effect = expected_log_matches
    oqa_search.build_checks(incident_id, request_id, ":{}:{}".format(incident_id, package), MOCK_URL)

    mock_logs = get_mock_log_filenames(package)
    mock_urls = [
        "{}/testreports/SUSE:Maintenance:{}:{}/build_checks/{}".format(MOCK_URL, incident_id, request_id, file)
        for file in mock_logs
    ]
    calls = [mock.call(url) for url in mock_urls]
    calls.extend([mock.call("\n".join(matches), "\n") for matches in expected_log_matches])

    assert mock_print.call_count == len(calls)
    assert mock_extract_test_results.call_count == len(mock_logs)
    mock_print.assert_has_calls(calls, any_order=True)
