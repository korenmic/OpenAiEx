from typing import List

from utils.model_negotiator import load_price_map, pick_cheapest_supported_model


class _FakeModel(object):
    def __init__(self, model_id: str) -> None:
        self.id = model_id


class _FakeModelsList(object):
    def __init__(self, ids: List[str]) -> None:
        self.data = [_FakeModel(model_id) for model_id in ids]


class _FakeModelsAPI(object):
    def __init__(self, ids: List[str]) -> None:
        self._ids = ids

    def list(self) -> _FakeModelsList:
        return _FakeModelsList(self._ids)


class _FakeClient(object):
    def __init__(self, ids: List[str]) -> None:
        self.models = _FakeModelsAPI(ids)


def test_load_price_map_not_empty() -> None:
    price_map = load_price_map()
    assert isinstance(price_map, dict)
    assert price_map, 'Expected non-empty price map from chat_models.json'
    # Prices should all be non-None
    assert all(value is not None for value in price_map.values())


def test_pick_cheapest_supported_model_happy_path() -> None:
    # Two priced models, with one clearly cheaper.
    price_map = {
        'alpha-model': 0.002,
        'beta-model': 0.0005,
        'gamma-model': 0.01,
    }
    client = _FakeClient(['alpha-model', 'beta-model'])

    model_id, price = pick_cheapest_supported_model(client, price_map)

    assert model_id == 'beta-model'
    assert price == 0.0005


def test_pick_cheapest_supported_model_raises_on_empty_intersection() -> None:
    price_map = {
        'alpha-model': 0.002,
        'beta-model': 0.0005,
    }
    client = _FakeClient(['unrelated-1', 'unrelated-2'])

    raised = False
    result = None
    try:
        result = pick_cheapest_supported_model(client, price_map)
    except RuntimeError as exc:
        raised = True
    assert not result, 'Got some intersection despite expected empty result'
    assert raised, 'Missing exception upon expected empty intersection'
