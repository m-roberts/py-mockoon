from pydantic import BaseModel


def list_of_dicts_to_dict(input_list: list[dict[str, str]]) -> dict[str, str]:
    output_dict = {}
    for item in input_list:
        if "key" in item and "value" in item:
            output_dict[item["key"]] = item["value"]
    return output_dict


class Request(BaseModel):
    body: str
    headers: dict[str, str]
    method: str
    params: dict[str, str]
    query: str
    queryParams: dict[str, str]  # noqa: N815
    route: str
    urlPath: str  # noqa: N815

    @classmethod
    def from_log_entry(cls, log_entry):
        _headers_list = log_entry["headers"]
        del log_entry["headers"]

        headers = list_of_dicts_to_dict(_headers_list)

        _params_list = log_entry["params"]
        del log_entry["params"]

        params = list_of_dicts_to_dict(_params_list)

        _query_params_list = log_entry["queryParams"]
        del log_entry["queryParams"]

        query_params = list_of_dicts_to_dict(_query_params_list)

        return cls(
            headers=headers,
            params=params,
            queryParams=query_params,
            **log_entry,
        )


class Response(BaseModel):
    body: str
    headers: dict[str, str]
    statusCode: int  # noqa: N815
    statusMessage: str | None = None  # noqa: N815

    @classmethod
    def from_log_entry(cls, log_entry):
        _headers_list = log_entry["headers"]
        del log_entry["headers"]

        headers = list_of_dicts_to_dict(_headers_list)

        return cls(headers=headers, **log_entry)


class Transaction(BaseModel):
    proxied: bool
    request: Request
    response: Response
    routeResponseUUID: str | None  # noqa: N815
    routeUUID: str | None  # noqa: N815

    @classmethod
    def from_log_entry(cls, log_entry):
        _request_dict = log_entry["request"]
        del log_entry["request"]

        request = Request.from_log_entry(_request_dict)

        _response_dict = log_entry["response"]
        del log_entry["response"]
        response = Response.from_log_entry(_response_dict)

        # If route is proxied, UUIDs are not created
        if "routeResponseUUID" not in log_entry:
            log_entry["routeResponseUUID"] = None

        if "routeUUID" not in log_entry:
            log_entry["routeUUID"] = None

        return cls(request=request, response=response, **log_entry)
