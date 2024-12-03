import pytest
from core.testing import test_db, auth_headers

# Re-export the fixtures from core.testing
pytest_plugins = ["core.testing"]
