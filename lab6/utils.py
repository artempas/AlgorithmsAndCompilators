import re


def parse_params(string: str) -> tuple[str, dict[str, str]]:
    # Parses signature string, returns element name and params
    found=re.match('<([a-z]+) ?([^>]*)>', string, flags=re.IGNORECASE)
    name=found.group(1)
    params=found.group(2)
    param_dict={}
    if params:
        params_iter=re.finditer(r'([a-z]+)\s*=\s*([^ >]+)', params, flags=re.IGNORECASE)
        param_dict=dict((m.group(1), m.group(2)) for m in params_iter)
    return name, param_dict
