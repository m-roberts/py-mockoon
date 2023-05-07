from dataclasses import dataclass

from .request import Request
from .response import Response


@dataclass
class Transaction:
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
