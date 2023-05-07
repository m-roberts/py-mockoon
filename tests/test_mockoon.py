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

    response = requests.get(f"{demo_mock_server.root_uri}/hello")

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

    # expected_response = Response(
    #   body='{"Hello": "World"}',
    #   headers={
    #       'content-length': '18',
    #       'content-type': 'application/json; charset=utf-8'
    #   },
    #   statusCode=HTTPStatus.OK,
    #   statusMessage='OK'
    # )

    # LogMessage(
    #   level='info',
    #   message='GET /hello | 200',
    #   timestamp='2023-05-05T22:57:38.664Z',
    #   mockName='mockoon-demo-mockoon-server',
    #   transaction=Transaction(
    #     proxied=False,
    #     routeResponseUUID='53791854-64c9-4af9-99b5-e9fd1dfcbcdf',
    #     routeUUID='9202536a-7c19-492d-a5cd-e7d1b9526bed'
    #   )
    # )

    demo_mock_server.transactions[-1].request

    demo_mock_server.assert_called_once_with(
        request=expected_request,
        # response=expected_response
    )
    demo_mock_server.assert_called_with(
        request=expected_request,
        # response=expected_response
    )
    demo_mock_server.assert_has_calls(
        requests=[expected_request],
        # responses=[expected_response]
    )

    demo_mock_server.reset_transactions()

    demo_mock_server.assert_not_called()
