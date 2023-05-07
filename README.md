# PyMockoon

## Overview

`PyMockoon` is a Python library that provides an easy way to start, stop, and manage mock servers using Mockoon as a backend. It can leverage the native `mockoon-cli` command or Docker to run the mock server.

The library is inspired by Python's `unittest` mocking system and helps users create extensive test suites by providing the ability to assert and verify HTTP transactions.

### Features

- Start and stop mock servers using Mockoon or Mockoon Docker image
- Provide mock server definition/specification using a Mockoon environment JSON file
- Log all HTTP transactions
- Assert HTTP transactions with the following methods:
  - assert_not_called()
  - assert_called()
  - assert_called_once()
  - assert_called_once_with(request)
  - assert_called_with(request)
  - assert_has_calls(requests, any_order)
  - reset_transactions()

The methods can be used to assert various conditions related to the HTTP transactions made to the mock server.

#### Example Usage

```python
import pathlib
from http import HTTPStatus
import requests
from mockoon import MockoonServer, Request

data_file = "path/to/file.json"

server = MockoonServer(data_file=data_file, use_docker=True)

server.start()

server.assert_not_called()

response = requests.get(f"{server.root_uri}/hello")
assert response.status_code == HTTPStatus.OK

server.wait_for_route_hit("hello")

server.stop()

server.assert_called()
server.assert_called_once()

# Currently the request needs to be checked by hand
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

server.assert_called_once_with(request=expected_request)
server.assert_called_with(request=expected_request)
server.assert_has_calls(requests=[expected_request])

server.reset_transactions()
server.assert_not_called()
```

## Requirements

- Python 3.9+
- Mockoon CLI (required if not using Mockoon Docker image)
- Docker (optional, required if using Mockoon Docker image)
