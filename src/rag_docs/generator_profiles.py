from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
from threading import RLock

from rag_docs.generation import GenerationError, Generator, OllamaGenerator


@dataclass(frozen=True, slots=True)
class GeneratorProfile:
    id: str
    label: str
    endpoint: str
    model: str


GeneratorFactory = Callable[..., Generator]


class GeneratorProfileRegistry:
    def __init__(
        self,
        profiles: list[GeneratorProfile],
        active_profile: str,
        *,
        timeout: float,
        temperature: float,
        seed: int,
        generator_factory: GeneratorFactory = OllamaGenerator,
    ) -> None:
        if not profiles:
            raise ValueError("Debe existir al menos un perfil de generador")
        self._profiles = {profile.id: profile for profile in profiles}
        if len(self._profiles) != len(profiles):
            raise ValueError("Los perfiles de generador no pueden repetir su ID")
        if active_profile not in self._profiles:
            raise ValueError(f"El perfil inicial no está configurado: {active_profile}")
        self._generator_factory = generator_factory
        self._timeout = timeout
        self._temperature = temperature
        self._seed = seed
        self._generators = {
            profile.id: self._build_generator(profile)
            for profile in profiles
        }
        self._active_profile = active_profile
        self._lock = RLock()

    @property
    def active_profile(self) -> str:
        with self._lock:
            return self._active_profile

    @property
    def active_generator(self) -> Generator:
        with self._lock:
            return self._generators[self._active_profile]

    def state(self) -> dict:
        with self._lock:
            return {
                "active_profile": self._active_profile,
                "profiles": [
                    {
                        **asdict(profile),
                        "active": profile.id == self._active_profile,
                    }
                    for profile in self._profiles.values()
                ],
            }

    def check(self, profile_id: str) -> dict:
        with self._lock:
            profile = self._require_profile(profile_id)
            generator = self._generators[profile_id]
        health = generator.health()
        capabilities = generator.capabilities
        return {
            **asdict(profile),
            "active": profile_id == self.active_profile,
            "ready": health.ready,
            "available_models": list(health.available_models),
            "capabilities": asdict(capabilities),
        }

    def activate(self, profile_id: str, model_name: str | None = None) -> dict:
        checked = self.check(profile_id)
        selected_model = model_name or checked["model"]
        available_models = checked["available_models"]
        if selected_model not in available_models:
            available = ", ".join(available_models) or "ninguno"
            raise GenerationError(
                f"El endpoint responde, pero no contiene el modelo {selected_model}. "
                f"Modelos disponibles: {available}."
            )

        with self._lock:
            current_profile = self._require_profile(profile_id)
        selected_profile = GeneratorProfile(
            id=current_profile.id,
            label=current_profile.label,
            endpoint=current_profile.endpoint,
            model=selected_model,
        )
        selected_generator = self._build_generator(selected_profile)

        with self._lock:
            self._profiles[profile_id] = selected_profile
            self._generators[profile_id] = selected_generator
            self._active_profile = profile_id
        return {
            **asdict(selected_profile),
            "active": True,
            "ready": True,
            "available_models": available_models,
            "capabilities": asdict(selected_generator.capabilities),
        }

    def _build_generator(self, profile: GeneratorProfile) -> Generator:
        return self._generator_factory(
            profile.endpoint,
            profile.model,
            self._timeout,
            self._temperature,
            self._seed,
        )

    def _require_profile(self, profile_id: str) -> GeneratorProfile:
        try:
            return self._profiles[profile_id]
        except KeyError as exc:
            raise ValueError(f"Perfil de generador no configurado: {profile_id}") from exc
