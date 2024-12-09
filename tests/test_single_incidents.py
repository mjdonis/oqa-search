import mock
import pytest

from oqa_search import oqa_search
from tests.conftest import MOCK_URL


@pytest.mark.parametrize(
    "versions",
    [
        ["15-SP2", "15-SP3"],
        ["12-SP3-TERADATA"],
    ],
)
@mock.patch("oqa_search.oqa_search._print_openqa_job_results")
def test_single_incidents(mock_print_openqa_job_results, versions):
    build = ":12345:foo"
    oqa_search.single_incidents(build, versions, MOCK_URL)

    expected_calls = [mock.call(MOCK_URL, v, build, oqa_search.INCIDENT_GROUPS[v]) for v in versions]

    assert mock_print_openqa_job_results.call_count == len(versions)
    mock_print_openqa_job_results.assert_has_calls(expected_calls)

    with pytest.raises(ValueError):
        oqa_search.single_incidents(build, ["12-SP9", "15-SP5"], MOCK_URL)
