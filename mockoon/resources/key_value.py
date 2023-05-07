def list_of_dicts_to_dict(input_list: list[dict[str, str]]) -> dict[str, str]:
    output_dict = {}
    for item in input_list:
        if "key" in item and "value" in item:
            output_dict[item["key"]] = item["value"]
    return output_dict
