from dataclasses import dataclass

from .key_value import list_of_dicts_to_dict


@dataclass
class Response:
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
