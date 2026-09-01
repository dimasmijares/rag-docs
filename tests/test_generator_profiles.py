from rag_docs.generation import (
    GeneratedResponse,
    GenerationError,
    GeneratorCapabilities,
    GeneratorHealth,
)
from rag_docs.generator_profiles import GeneratorProfile, GeneratorProfileRegistry


class StubGenerator:
    def __init__(
        self,
        base_url: str,
        model_name: str,
        timeout: float,
        temperature: float,
        seed: int,
    ) -> None:
        self.base_url = base_url
        self.model_name = model_name
        self.options = (timeout, temperature, seed)

    @property
    def capabilities(self) -> GeneratorCapabilities:
        return GeneratorCapabilities(True, False, False)

    def health(self) -> GeneratorHealth:
        if "offline" in self.base_url:
            raise GenerationError("Endpoint no disponible")
        available = ("model-new",) if "missing" in self.base_url else (self.model_name,)
        return GeneratorHealth(
            ready=self.model_name in available,
            endpoint=self.base_url,
            selected_model=self.model_name,
            available_models=available,
        )

    def generate(self, *args, **kwargs) -> GeneratedResponse:
        raise AssertionError("Este fake no debe generar respuestas")


def registry(remote_endpoint: str = "http://remote:11434") -> GeneratorProfileRegistry:
    return GeneratorProfileRegistry(
        [
            GeneratorProfile("local", "Local", "http://local:11434", "model-a"),
            GeneratorProfile("remote", "Remoto", remote_endpoint, "model-b"),
        ],
        "local",
        timeout=30,
        temperature=0,
        seed=7,
        generator_factory=StubGenerator,
    )


def test_profile_can_be_checked_and_activated() -> None:
    profiles = registry()

    checked = profiles.check("remote")
    activated = profiles.activate("remote")

    assert checked["ready"] is True
    assert checked["model"] == "model-b"
    assert checked["capabilities"]["structured_output"] is True
    assert activated["active"] is True
    assert profiles.active_profile == "remote"
    assert profiles.active_generator.model_name == "model-b"


def test_missing_model_does_not_replace_previous_profile() -> None:
    profiles = registry("http://missing:11434")

    try:
        profiles.activate("remote")
    except GenerationError as exc:
        assert "no contiene el modelo model-b" in str(exc)
    else:
        raise AssertionError("La activación debía fallar")

    assert profiles.active_profile == "local"


def test_discovered_model_can_replace_configured_model() -> None:
    profiles = registry("http://missing:11434")

    checked = profiles.check("remote")
    activated = profiles.activate("remote", "model-new")

    assert checked["ready"] is False
    assert checked["available_models"] == ["model-new"]
    assert activated["model"] == "model-new"
    assert profiles.active_profile == "remote"
    assert profiles.active_generator.model_name == "model-new"
    assert profiles.state()["profiles"][1]["model"] == "model-new"


def test_unknown_discovered_model_is_rejected_atomically() -> None:
    profiles = registry()

    try:
        profiles.activate("remote", "invented-model")
    except GenerationError as exc:
        assert "no contiene el modelo invented-model" in str(exc)
    else:
        raise AssertionError("La activación debía fallar")

    assert profiles.active_profile == "local"
    assert profiles.state()["profiles"][1]["model"] == "model-b"


def test_offline_profile_reports_explicit_error() -> None:
    profiles = registry("http://offline:11434")

    try:
        profiles.check("remote")
    except GenerationError as exc:
        assert str(exc) == "Endpoint no disponible"
    else:
        raise AssertionError("La comprobación debía fallar")
