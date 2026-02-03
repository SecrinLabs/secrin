"""
Tests for LLM providers.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from ...providers.base import BaseLLMProvider, LLMMessage, LLMResponse
from ...providers.factory import create_llm_provider, get_default_model, get_api_key_env_var
from ...models.config import LLMConfig


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""

    def test_response_creation(self):
        """Test creating an LLM response."""
        response = LLMResponse(
            content="Hello, world!",
            model="test-model",
            usage={"input_tokens": 10, "output_tokens": 20},
            stop_reason="end_turn",
        )
        assert response.content == "Hello, world!"
        assert response.model == "test-model"
        assert response.usage["input_tokens"] == 10
        assert response.stop_reason == "end_turn"

    def test_response_without_optional_fields(self):
        """Test response without optional fields."""
        response = LLMResponse(content="Test", model="model")
        assert response.usage is None
        assert response.stop_reason is None


class TestLLMMessage:
    """Tests for LLMMessage dataclass."""

    def test_message_creation(self):
        """Test creating an LLM message."""
        msg = LLMMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"


class TestProviderFactory:
    """Tests for provider factory functions."""

    def test_get_default_model_anthropic(self):
        """Test getting default model for Anthropic."""
        model = get_default_model("anthropic")
        assert "claude" in model.lower()

    def test_get_default_model_gemini(self):
        """Test getting default model for Gemini."""
        model = get_default_model("gemini")
        assert "gemini" in model.lower()

    def test_get_default_model_unknown(self):
        """Test getting default model for unknown provider."""
        model = get_default_model("unknown")
        assert model == ""

    def test_get_api_key_env_var_anthropic(self):
        """Test getting API key env var for Anthropic."""
        env_var = get_api_key_env_var("anthropic")
        assert env_var == "ANTHROPIC_API_KEY"

    def test_get_api_key_env_var_gemini(self):
        """Test getting API key env var for Gemini."""
        env_var = get_api_key_env_var("gemini")
        assert env_var == "GEMINI_API_KEY"

    @patch('packages.arc42gen.providers.anthropic_provider.anthropic')
    def test_create_anthropic_provider(self, mock_anthropic):
        """Test creating Anthropic provider."""
        config = LLMConfig(
            provider="anthropic",
            model="claude-sonnet-4-5-20250929",
            api_key="test-key",
        )
        provider = create_llm_provider(config)
        assert provider.provider_name == "anthropic"

    def test_create_unsupported_provider(self):
        """Test creating unsupported provider raises error."""
        config = LLMConfig(
            provider="unsupported",
            model="test",
            api_key="key",
        )
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            create_llm_provider(config)


class TestAnthropicProvider:
    """Tests for Anthropic provider."""

    @patch('packages.arc42gen.providers.anthropic_provider.anthropic')
    def test_provider_initialization(self, mock_anthropic):
        """Test provider initialization."""
        from ...providers.anthropic_provider import AnthropicProvider

        provider = AnthropicProvider(api_key="test-key")
        assert provider.provider_name == "anthropic"
        assert provider.api_key == "test-key"

    @patch('packages.arc42gen.providers.anthropic_provider.anthropic')
    def test_model_alias_resolution(self, mock_anthropic):
        """Test model alias resolution."""
        from ...providers.anthropic_provider import AnthropicProvider

        provider = AnthropicProvider(api_key="key", model="claude-sonnet")
        assert "claude-sonnet" in provider.model

    @patch('packages.arc42gen.providers.anthropic_provider.anthropic')
    def test_generate_call(self, mock_anthropic):
        """Test generate method."""
        from ...providers.anthropic_provider import AnthropicProvider

        # Mock the response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Generated text")]
        mock_response.model = "claude-sonnet-4-5-20250929"
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        mock_response.stop_reason = "end_turn"

        mock_anthropic.Anthropic.return_value.messages.create.return_value = mock_response

        provider = AnthropicProvider(api_key="test-key")
        response = provider.generate("Test prompt")

        assert response.content == "Generated text"
        assert response.model == "claude-sonnet-4-5-20250929"

    @patch('packages.arc42gen.providers.anthropic_provider.anthropic')
    def test_validate_api_key(self, mock_anthropic):
        """Test API key validation."""
        from ...providers.anthropic_provider import AnthropicProvider

        provider = AnthropicProvider(api_key="test-key")
        assert provider.validate_api_key() is True

        provider_empty = AnthropicProvider(api_key="")
        assert provider_empty.validate_api_key() is False


class TestGeminiProvider:
    """Tests for Gemini provider."""

    @pytest.fixture
    def mock_genai(self):
        """Mock the genai module."""
        mock_module = MagicMock()
        mock_model = MagicMock()
        mock_module.GenerativeModel.return_value = mock_model
        mock_module.GenerationConfig = MagicMock()

        with patch.dict('sys.modules', {'google.generativeai': mock_module, 'google': MagicMock()}):
            # Reload the module to pick up the mock
            import importlib
            import packages.arc42gen.providers.gemini_provider as gp
            # Manually set GEMINI_AVAILABLE to True for testing
            gp.GEMINI_AVAILABLE = True
            gp.genai = mock_module
            yield mock_module

    def test_provider_initialization(self, mock_genai):
        """Test provider initialization."""
        from ...providers.gemini_provider import GeminiProvider

        provider = GeminiProvider(api_key="test-key")
        assert provider.provider_name == "gemini"

    def test_model_alias_resolution(self, mock_genai):
        """Test model alias resolution."""
        from ...providers.gemini_provider import GeminiProvider

        provider = GeminiProvider(api_key="key", model="gemini-flash")
        assert "gemini" in provider.model

    def test_generate_call(self, mock_genai):
        """Test generate method."""
        from ...providers.gemini_provider import GeminiProvider

        # Mock the response
        mock_response = MagicMock()
        mock_response.text = "Generated text"
        mock_response.usage_metadata = None
        mock_response.candidates = []

        mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response

        provider = GeminiProvider(api_key="test-key")
        response = provider.generate("Test prompt")

        assert response.content == "Generated text"

    def test_generate_with_system_prompt(self, mock_genai):
        """Test generate with system prompt."""
        from ...providers.gemini_provider import GeminiProvider

        mock_response = MagicMock()
        mock_response.text = "Response"
        mock_response.usage_metadata = None
        mock_response.candidates = []

        mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response

        provider = GeminiProvider(api_key="test-key")
        response = provider.generate(
            "Test prompt",
            system_prompt="You are a helpful assistant"
        )

        # Should return the response
        assert response.content == "Response"
