"""
Unit tests for Python parser.
"""

import pytest

from packages.arc42gen.parsers.python_parser import PythonParser


class TestPythonParser:
    """Tests for PythonParser class."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return PythonParser()

    def test_extract_simple_class(self, parser):
        """Test extracting a simple class definition."""
        source = '''
class UserService:
    """Service for user operations."""

    def __init__(self):
        pass

    def get_user(self, user_id):
        pass
'''
        parser.parse(source)
        classes = parser.extract_classes()

        assert len(classes) == 1
        assert classes[0].name == "UserService"
        assert "__init__" in classes[0].methods
        assert "get_user" in classes[0].methods
        assert classes[0].docstring == "Service for user operations."

    def test_extract_class_with_inheritance(self, parser):
        """Test extracting class with base classes."""
        source = '''
class AdminUser(User, Serializable):
    pass
'''
        parser.parse(source)
        classes = parser.extract_classes()

        assert len(classes) == 1
        assert classes[0].name == "AdminUser"
        assert "User" in classes[0].bases
        assert "Serializable" in classes[0].bases

    def test_extract_decorated_class(self, parser):
        """Test extracting decorated class."""
        source = '''
@dataclass
class Config:
    name: str
    value: int
'''
        parser.parse(source)
        classes = parser.extract_classes()

        assert len(classes) == 1
        assert classes[0].name == "Config"
        assert "dataclass" in classes[0].decorators

    def test_extract_multiple_classes(self, parser):
        """Test extracting multiple classes."""
        source = '''
class First:
    pass

class Second:
    pass

class Third:
    pass
'''
        parser.parse(source)
        classes = parser.extract_classes()

        assert len(classes) == 3
        names = [c.name for c in classes]
        assert "First" in names
        assert "Second" in names
        assert "Third" in names

    def test_extract_simple_function(self, parser):
        """Test extracting simple function."""
        source = '''
def calculate_total(items, tax_rate):
    """Calculate total with tax."""
    return sum(items) * (1 + tax_rate)
'''
        parser.parse(source)
        functions = parser.extract_functions()

        assert len(functions) == 1
        assert functions[0].name == "calculate_total"
        assert "items" in functions[0].parameters
        assert "tax_rate" in functions[0].parameters
        assert functions[0].docstring == "Calculate total with tax."

    def test_extract_async_function(self, parser):
        """Test extracting async function."""
        source = '''
async def fetch_data(url):
    pass
'''
        parser.parse(source)
        functions = parser.extract_functions()

        assert len(functions) == 1
        assert functions[0].name == "fetch_data"
        # Note: async detection depends on tree-sitter version

    def test_extract_decorated_function(self, parser):
        """Test extracting decorated function."""
        source = '''
@app.route("/api")
@require_auth
def api_handler():
    pass
'''
        parser.parse(source)
        functions = parser.extract_functions()

        assert len(functions) == 1
        assert functions[0].name == "api_handler"

    def test_extract_import_statement(self, parser):
        """Test extracting import statements."""
        source = '''
import os
import sys
'''
        parser.parse(source)
        imports = parser.extract_imports()

        assert len(imports) == 2
        modules = [i.module for i in imports]
        assert "os" in modules
        assert "sys" in modules

    def test_extract_from_import(self, parser):
        """Test extracting from...import statements."""
        source = '''
from typing import List, Dict, Optional
from pathlib import Path
'''
        parser.parse(source)
        imports = parser.extract_imports()

        assert len(imports) == 2

        typing_import = next(i for i in imports if i.module == "typing")
        assert typing_import.is_from_import
        assert "List" in typing_import.names
        assert "Dict" in typing_import.names

    def test_extract_aliased_import(self, parser):
        """Test extracting aliased imports."""
        source = '''
import numpy as np
import pandas as pd
'''
        parser.parse(source)
        imports = parser.extract_imports()

        assert len(imports) == 2
        np_import = next(i for i in imports if i.module == "numpy")
        assert np_import.alias == "np"

    def test_extract_module_docstring(self, parser):
        """Test extracting module-level docstring."""
        source = '''"""
This is the module docstring.

It provides utilities for data processing.
"""

import os

def main():
    pass
'''
        parser.parse(source)
        docstring = parser.extract_docstring()

        assert docstring is not None
        assert "module docstring" in docstring

    def test_count_lines(self, parser):
        """Test counting lines of code."""
        source = '''# Comment line
import os

def function():
    # Another comment
    x = 1
    y = 2

    return x + y
'''
        parser.parse(source)
        loc = parser.count_lines()

        # Should count: import os, def function():, x = 1, y = 2, return x + y
        # Should NOT count: comments, blank lines
        assert loc == 5

    def test_empty_source(self, parser):
        """Test parsing empty source."""
        parser.parse("")

        assert parser.extract_classes() == []
        assert parser.extract_functions() == []
        assert parser.extract_imports() == []
        assert parser.extract_docstring() is None
        assert parser.count_lines() == 0

    def test_complex_function_parameters(self, parser):
        """Test extracting function with complex parameters."""
        source = '''
def complex_func(a, b=10, *args, **kwargs):
    pass
'''
        parser.parse(source)
        functions = parser.extract_functions()

        assert len(functions) == 1
        params = functions[0].parameters
        assert "a" in params
        assert "b" in params

    def test_public_symbols(self, parser):
        """Test getting public symbols."""
        source = '''
class PublicClass:
    pass

class _PrivateClass:
    pass

def public_function():
    pass

def _private_function():
    pass
'''
        parser.parse(source)
        public = parser.get_public_symbols()

        assert "PublicClass" in public
        assert "_PrivateClass" not in public
        assert "public_function" in public
        assert "_private_function" not in public
