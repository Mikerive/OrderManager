from core.features import FeatureRegistry
from .provider import AlpacaExchangeProvider

def initialize_alpaca(api_key: str, api_secret: str, paper: bool = True):
    """Initialize Alpaca feature."""
    # Create Alpaca provider
    provider = AlpacaExchangeProvider(
        api_key=api_key,
        api_secret=api_secret,
        paper=paper
    )
    
    # Register provider
    FeatureRegistry.register_exchange("alpaca", provider)
    
    return provider
