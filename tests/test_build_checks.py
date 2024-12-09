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
    ("incident_id", "request_id", "package"),
    [
        (1234, 56789, "automake"),
        (9876, 12345, "python"),
    ],
)
@mock.patch("oqa_search.oqa_search._get_log_text")
@mock.patch("oqa_search.oqa_search.print")
@mock.patch("oqa_search.oqa_search.print_title")
def test_build_checks(mock_print_title, mock_print, mock_get_log_text, incident_id, request_id, package):
    mock_logs_text = mock_log_text(package)
    mock_get_log_text.side_effect = [mock_build_checks_index(package), *mock_logs_text]
    oqa_search.build_checks(incident_id, request_id, ":{}:{}".format(incident_id, package), MOCK_URL)

    mock_logs = get_mock_log_filenames(package)
    mock_urls = [
        "{}/testreports/SUSE:Maintenance:{}:{}/build_checks/{}".format(MOCK_URL, incident_id, request_id, file)
        for file in mock_logs
    ]
    calls = [mock.call(url) for url in mock_urls]

    for log_text in mock_logs_text:
        calls.extend([mock.call("\n".join(matches), "\n") for matches in get_expected_log_matches(log_text)])

    assert mock_print.call_count == len(calls)
    mock_print.assert_has_calls(calls, any_order=True)
