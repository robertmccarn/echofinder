from __future__ import annotations

from backend.app import main


def test_hybrid_runtime_is_lazy(monkeypatch) -> None:
    calls = {"config": 0, "runtime": 0}

    class FakeRuntime:
        @classmethod
        def from_config(cls, config):
            calls["runtime"] += 1
            return {"config": config}

    def fake_load_config():
        calls["config"] += 1
        return object()

    monkeypatch.setattr(main, "_RECO_CONFIG", None)
    monkeypatch.setattr(main, "_HYBRID_RUNTIME", None)
    monkeypatch.setattr(main, "load_reco_config", fake_load_config)
    monkeypatch.setattr(main, "HybridRuntime", FakeRuntime)

    config_a = main._get_reco_config()
    config_b = main._get_reco_config()
    runtime_a = main._get_hybrid_runtime()
    runtime_b = main._get_hybrid_runtime()

    assert config_a is config_b
    assert runtime_a is runtime_b
    assert calls["config"] == 1
    assert calls["runtime"] == 1


def test_hybrid_runtime_falls_back_when_initialization_fails(monkeypatch) -> None:
    class FakeRuntime:
        def __init__(self, config, store):
            self.config = config
            self.store = store

        @classmethod
        def from_config(cls, config):
            raise RuntimeError("db unavailable")

    def fake_load_config():
        return object()

    monkeypatch.setattr(main, "_RECO_CONFIG", None)
    monkeypatch.setattr(main, "_HYBRID_RUNTIME", None)
    monkeypatch.setattr(main, "load_reco_config", fake_load_config)
    monkeypatch.setattr(main, "HybridRuntime", FakeRuntime)

    runtime = main._get_hybrid_runtime()

    assert runtime.store is None
