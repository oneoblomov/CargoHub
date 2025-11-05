import pytest
import os
from unittest.mock import MagicMock

# Set environment variables to disable GPU and problematic imports
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["TOKENIZERS_PARALLELISM"] = "false"

@pytest.fixture(scope="session", autouse=True)
def mock_external_dependencies():
    """Mock external dependencies before any test runs"""
    import sys

    # Mock transformers and related modules before they are imported
    mock_transformers = MagicMock()
    mock_pipeline = MagicMock()
    mock_transformers.pipeline = MagicMock(return_value=mock_pipeline)

    mock_hf_hub = MagicMock()
    mock_hf_hub.login = MagicMock()

    sys.modules["transformers"] = mock_transformers
    sys.modules["transformers.pipeline"] = mock_pipeline
    sys.modules["huggingface_hub"] = mock_hf_hub
    sys.modules["huggingface_hub.login"] = mock_hf_hub.login
    sys.modules["streamlit"] = MagicMock()

    yield