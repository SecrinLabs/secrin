"""
Tests for JavaScript parser.
"""

import pytest
from ...parsers.javascript_parser import JavaScriptParser


class TestJavaScriptParser:
    """Tests for JavaScript AST parser."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return JavaScriptParser()

    def test_extract_class(self, parser):
        """Test extracting a simple class."""
        source = """
class UserService {
    constructor(db) {
        this.db = db;
    }

    getUser(id) {
        return this.db.find(id);
    }

    saveUser(user) {
        return this.db.save(user);
    }
}
"""
        parser.parse(source)
        classes = parser.extract_classes()

        assert len(classes) == 1
        assert classes[0].name == "UserService"
        assert "constructor" in classes[0].methods
        assert "getUser" in classes[0].methods
        assert "saveUser" in classes[0].methods

    def test_extract_class_with_extends(self, parser):
        """Test extracting class with inheritance."""
        source = """
class AdminService extends UserService {
    deleteUser(id) {
        return this.db.delete(id);
    }
}
"""
        parser.parse(source)
        classes = parser.extract_classes()

        assert len(classes) == 1
        assert classes[0].name == "AdminService"
        assert "UserService" in classes[0].bases

    def test_extract_functions(self, parser):
        """Test extracting function declarations."""
        source = """
function add(a, b) {
    return a + b;
}

async function fetchData(url) {
    const response = await fetch(url);
    return response.json();
}

const multiply = (x, y) => x * y;

const divide = function(a, b) {
    return a / b;
};
"""
        parser.parse(source)
        functions = parser.extract_functions()

        names = [f.name for f in functions]
        assert "add" in names
        assert "fetchData" in names
        assert "multiply" in names
        assert "divide" in names

        # Check async function
        fetch_func = next(f for f in functions if f.name == "fetchData")
        assert fetch_func.is_async is True

    def test_extract_function_parameters(self, parser):
        """Test extracting function parameters."""
        source = """
function greet(name, greeting = 'Hello', ...options) {
    console.log(greeting, name);
}
"""
        parser.parse(source)
        functions = parser.extract_functions()

        assert len(functions) == 1
        params = functions[0].parameters
        assert "name" in params
        assert "greeting" in params
        assert "...options" in params

    def test_extract_es6_imports(self, parser):
        """Test extracting ES6 import statements."""
        source = """
import React from 'react';
import { useState, useEffect } from 'react';
import * as utils from './utils';
import './styles.css';
"""
        parser.parse(source)
        imports = parser.extract_imports()

        assert len(imports) >= 3
        modules = [i.module for i in imports]
        assert "react" in modules
        assert "./utils" in modules

    def test_extract_require_imports(self, parser):
        """Test extracting CommonJS require statements."""
        source = """
const express = require('express');
const { Router } = require('express');
const path = require('path');
"""
        parser.parse(source)
        imports = parser.extract_imports()

        modules = [i.module for i in imports]
        assert "express" in modules
        assert "path" in modules

    def test_extract_docstring(self, parser):
        """Test extracting JSDoc comment."""
        source = """
/**
 * This is the main module for user management.
 * @module UserModule
 */

class User {}
"""
        parser.parse(source)
        docstring = parser.extract_docstring()

        assert docstring is not None
        assert "main module" in docstring

    def test_count_lines(self, parser):
        """Test counting lines of code."""
        source = """
// This is a comment
function add(a, b) {
    // Another comment
    return a + b;
}

/*
 * Multi-line comment
 */

const x = 10;
"""
        parser.parse(source)
        loc = parser.count_lines()

        # Should count non-empty, non-comment lines
        assert loc > 0
        assert loc < 15  # Not all lines should be counted


class TestJavaScriptParserEdgeCases:
    """Edge case tests for JavaScript parser."""

    @pytest.fixture
    def parser(self):
        return JavaScriptParser()

    def test_empty_file(self, parser):
        """Test parsing empty file."""
        parser.parse("")
        assert parser.extract_classes() == []
        assert parser.extract_functions() == []
        assert parser.extract_imports() == []
        assert parser.count_lines() == 0

    def test_arrow_function_single_param(self, parser):
        """Test arrow function with single parameter (no parens)."""
        source = """
const double = x => x * 2;
"""
        parser.parse(source)
        functions = parser.extract_functions()

        assert len(functions) == 1
        assert functions[0].name == "double"

    def test_class_with_static_methods(self, parser):
        """Test class with static methods."""
        source = """
class Utils {
    static formatDate(date) {
        return date.toISOString();
    }

    static parseDate(str) {
        return new Date(str);
    }
}
"""
        parser.parse(source)
        classes = parser.extract_classes()

        assert len(classes) == 1
        assert "formatDate" in classes[0].methods
        assert "parseDate" in classes[0].methods

    def test_export_default_function(self, parser):
        """Test export default function."""
        source = """
export default function main() {
    console.log('Main function');
}
"""
        parser.parse(source)
        functions = parser.extract_functions()

        names = [f.name for f in functions]
        assert "main" in names
