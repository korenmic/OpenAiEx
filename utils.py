
def slice_dict(d: dict, keys: list) -> dict:
    return {k: d[k] for k in keys if k in d}
