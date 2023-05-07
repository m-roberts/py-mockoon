from dataclasses import dataclass

from .key_value import list_of_dicts_to_dict


@dataclass
class Request:
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
