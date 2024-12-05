from argparse import Namespace

import mock
import pytest

from oqa_search import oqa_search


@pytest.mark.parametrize(
    ("update_id", "versions", "no_aggregated"),
    [
        ("SUSE:Maintenance:12345:67890", ["15-SP5"], False),
        ("S:M:9876:123456", ["12-SP3-TERADATA", "12-SP5"], True),
        ("S:M:12345:65478", [], False),
    ],
)
@mock.patch("oqa_search.oqa_search._get_incident_info")
@mock.patch("oqa_search.oqa_search.build_checks")
@mock.patch("oqa_search.oqa_search.aggregated_updates")
@mock.patch("oqa_search.oqa_search.single_incidents")
@mock.patch("oqa_search.oqa_search._parser")
def test_main(
    mock_parser,
    mock_single_incidents,
    mock_aggregated_updates,
    mock_build_checks,
    mock_get_incident_info,
    update_id,
    versions,
    no_aggregated,
):
    mock_parser.return_value = Namespace(
        update_id=update_id,
        url_dashboard_qam="http://dashboard.qam.suse.de",
        url_openqa="https://openqa.suse.de",
        url_qam="https://qam.suse.de",
        no_aggregated=no_aggregated,
        days=5,
        aggregated_groups=["core"],
    )
    mock_get_incident_info.return_value = (":12345:foo", versions)

    oqa_search.main()

    if versions:
        mock_single_incidents.assert_called_once()
        if not no_aggregated:
            mock_aggregated_updates.assert_called_once()
        else:
            mock_aggregated_updates.assert_not_called()
    else:
        mock_single_incidents.assert_not_called()
        mock_aggregated_updates.assert_not_called()

    mock_get_incident_info.assert_called_once()
    mock_build_checks.assert_called_once()
