from typing import Dict, Any

class FeatureRegistry:
    """Registry for features and their providers."""
    _exchange_providers: Dict[str, Any] = {}

    @classmethod
    def register_exchange(cls, name: str, provider: Any) -> None:
        """Register an exchange provider."""
        cls._exchange_providers[name] = provider

    @classmethod
    def get_exchange(cls, name: str) -> Any:
        """Get an exchange provider by name."""
        return cls._exchange_providers.get(name)

    @classmethod
    def list_exchanges(cls) -> list[str]:
        """List all registered exchanges."""
        return list(cls._exchange_providers.keys())
