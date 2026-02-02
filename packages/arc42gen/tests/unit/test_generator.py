"""
Unit tests for Arc42Generator.
"""

from unittest.mock import Mock, patch, MagicMock

import pytest

from packages.arc42gen.core.generator import Arc42Generator
from packages.arc42gen.models.analysis import (
    AnalysisResult,
    Module,
    ModuleTree,
    DependencyGraph,
    CodeStatistics,
)
from packages.arc42gen.models.documentation import (
    Section5,
    Level1Whitebox,
    Level2Whitebox,
    ComponentDescription,
)


class TestArc42Generator:
    """Tests for Arc42Generator class."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Anthropic client."""
        with patch('packages.arc42gen.core.generator.anthropic.Anthropic') as mock:
            client = Mock()
            mock.return_value = client
            yield client

    @pytest.fixture
    def generator(self, mock_client):
        """Create generator with mocked client."""
        return Arc42Generator(api_key="test_key")

    @pytest.fixture
    def sample_analysis(self):
        """Create sample analysis result."""
        root = Module(
            name="sample_repo",
            path="/path/to/repo",
            type="package",
            children=[
                Module(
                    name="core",
                    path="/path/to/repo/core",
                    type="package",
                    children=[],
                    size_loc=500,
                    interfaces=["class Engine", "def process"],
                    dependencies=["utils"],
                ),
                Module(
                    name="utils",
                    path="/path/to/repo/utils",
                    type="package",
                    children=[],
                    size_loc=200,
                    interfaces=["def helper", "class Logger"],
                    dependencies=[],
                ),
            ],
            size_loc=700,
        )

        return AnalysisResult(
            repo_name="sample_repo",
            repo_path="/path/to/repo",
            language="python",
            module_tree=ModuleTree(root=root),
            dependency_graph=DependencyGraph(
                nodes=["core", "utils"],
                edges=[]
            ),
            statistics=CodeStatistics(
                total_loc=700,
                total_files=10,
                total_modules=3,
                total_classes=5,
                total_functions=15,
            ),
        )

    def test_generate_section_5_calls_claude(self, generator, mock_client, sample_analysis):
        """Test that generate_section_5 calls Claude API."""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = [Mock(text="""OVERVIEW:
This is a sample system.

COMPONENTS:
- core: Main processing engine
- utils: Utility functions

INTERFACES:
Components communicate via function calls.

RATIONALE:
Simple architecture for demo purposes.""")]
        mock_client.messages.create.return_value = mock_response

        result = generator.generate_section_5(sample_analysis)

        # Verify API was called
        assert mock_client.messages.create.called
        assert isinstance(result, Section5)

    def test_generate_section_5_returns_valid_structure(self, generator, mock_client, sample_analysis):
        """Test that generated Section5 has valid structure."""
        mock_response = Mock()
        mock_response.content = [Mock(text="""OVERVIEW:
A sample system for testing.

COMPONENTS:
- core: Processing logic
- utils: Helper functions

INTERFACES:
Direct function calls between modules.

RATIONALE:
Modular design for maintainability.""")]
        mock_client.messages.create.return_value = mock_response

        result = generator.generate_section_5(sample_analysis)

        assert result.level_1 is not None
        assert isinstance(result.level_1.overview, str)
        assert len(result.level_1.overview) > 0
        assert isinstance(result.statistics, dict)

    def test_generate_section_5_includes_statistics(self, generator, mock_client, sample_analysis):
        """Test that generated Section5 includes statistics."""
        mock_response = Mock()
        mock_response.content = [Mock(text="""OVERVIEW:
Test system.

COMPONENTS:
- core: Core logic

INTERFACES:
None.

RATIONALE:
Simple.""")]
        mock_client.messages.create.return_value = mock_response

        result = generator.generate_section_5(sample_analysis)

        assert "total_loc" in result.statistics
        assert result.statistics["total_loc"] == 700
        assert result.statistics["total_classes"] == 5

    def test_generate_diagram_produces_mermaid(self, generator, mock_client, sample_analysis):
        """Test that diagram generation produces Mermaid code."""
        mock_response = Mock()
        mock_response.content = [Mock(text="""```mermaid
flowchart TB
    subgraph System["sample_repo"]
        core["core"]
        utils["utils"]
        core --> utils
    end
```""")]
        mock_client.messages.create.return_value = mock_response

        diagram = generator._generate_diagram(sample_analysis)

        assert "mermaid" in diagram
        assert "flowchart" in diagram or "graph" in diagram

    def test_parse_level_1_response(self, generator, sample_analysis):
        """Test parsing Level 1 response."""
        response = """OVERVIEW:
This is a test system that processes data.

COMPONENTS:
- core: Main processing engine
- utils: Utility helpers
- api: REST API layer

INTERFACES:
The API layer calls core for processing. Core uses utils for helpers.

RATIONALE:
Layered architecture separates concerns."""

        result = generator._parse_level_1_response(response, sample_analysis)

        assert isinstance(result, Level1Whitebox)
        assert "test system" in result.overview
        assert len(result.components) >= 3
        assert "API layer" in result.important_interfaces
        assert "Layered" in result.rationale

    def test_parse_level_2_response(self, generator, sample_analysis):
        """Test parsing Level 2 response."""
        module = sample_analysis.module_tree.root.children[0]  # core module
        response = """PURPOSE:
The core module provides main processing logic.

INTERNAL_STRUCTURE:
- engine: Main processing engine
- handlers: Request handlers

DEPENDENCIES:
- utils.Logger
- config.Settings"""

        result = generator._parse_level_2_response(response, module)

        assert isinstance(result, Level2Whitebox)
        assert result.component_name == "core"
        assert "processing logic" in result.purpose
        assert len(result.internal_structure) >= 2
        assert len(result.dependencies) >= 2

    def test_fallback_diagram_generation(self, generator, sample_analysis):
        """Test fallback diagram when Claude returns invalid response."""
        diagram = generator._generate_fallback_diagram(sample_analysis)

        assert "mermaid" in diagram
        assert "flowchart" in diagram
        assert "core" in diagram or "sample_repo" in diagram

    def test_format_module_tree(self, generator, sample_analysis):
        """Test module tree formatting for prompt."""
        formatted = generator._format_module_tree(sample_analysis.module_tree.root)

        assert "sample_repo" in formatted
        assert "core" in formatted
        assert "utils" in formatted
        assert "LOC" in formatted

    def test_format_dependencies(self, generator, sample_analysis):
        """Test dependency formatting for prompt."""
        # Add some edges
        sample_analysis.dependency_graph.edges = []
        sample_analysis.dependency_graph.add_dependency("core", "utils", "import")

        formatted = generator._format_dependencies(sample_analysis.dependency_graph)

        assert "core" in formatted
        assert "utils" in formatted

    def test_extract_mermaid_code(self, generator):
        """Test extracting mermaid code block from response."""
        response = """Here's the diagram:

```mermaid
flowchart TB
    A --> B
```

That's the diagram."""

        result = generator._extract_mermaid_code(response)

        assert result is not None
        assert "flowchart TB" in result
        assert "A --> B" in result

    def test_extract_mermaid_code_not_found(self, generator):
        """Test extracting mermaid when not present."""
        response = "No diagram here."

        result = generator._extract_mermaid_code(response)

        assert result is None

    def test_api_error_handling(self, generator, mock_client, sample_analysis):
        """Test handling of API errors."""
        import anthropic

        mock_client.messages.create.side_effect = anthropic.APIError(
            message="Test error",
            body=None,
            request=Mock()
        )

        with pytest.raises(anthropic.APIError):
            generator.generate_section_5(sample_analysis)
