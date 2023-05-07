import pathlib
from http import HTTPStatus

import pytest
import requests

from mockoon import MockoonServer, Request  # , Response


@pytest.fixture(scope="module", params=[True, False])
def demo_mock_server(request):
    with MockoonServer(
        data_file=f"{pathlib.Path(__file__).parent.resolve()}/data/demo.json",
        use_docker=request.param,
    ) as server:
        yield server


def test_mockoon_demo(demo_mock_server):
    demo_mock_server.assert_not_called()

    response = requests.get(f"{demo_mock_server.root_uri}/hello", timeout=5.0)

    assert response.status_code == HTTPStatus.OK

    demo_mock_server.wait_for_route_hit("hello")

    demo_mock_server.assert_called()
    demo_mock_server.assert_called_once()

    # TODO: add support for partial definitions
    # e.g. don't worry about headers
    expected_request = Request(
        body="",
        headers={
            "accept": "*/*",
            "accept-encoding": "gzip, deflate",
            "connection": "keep-alive",
            "host": "localhost:3000",
            "user-agent": "python-requests/2.30.0",
        },
        method="GET",
        params={},
        query="",
        queryParams={},
        route="/hello",
        urlPath="/hello",
    )

    demo_mock_server.assert_called_once_with_properties(method="GET", route="/hello")
    demo_mock_server.assert_called_with_properties(method="GET", route="/hello")
    demo_mock_server.assert_has_calls_with_properties(
        [{"method": "GET", "route": "/hello"}],
        any_order=True,
    )

    demo_mock_server.assert_called_once_with(
        request=expected_request,
    )
    demo_mock_server.assert_called_with(
        request=expected_request,
    )
    demo_mock_server.assert_has_calls(
        requests=[expected_request],
    )

    demo_mock_server.reset_transactions()

    demo_mock_server.assert_not_called()
