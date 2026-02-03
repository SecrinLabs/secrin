"""
Tests for TypeScript parser.
"""

import pytest
from ...parsers.typescript_parser import TypeScriptParser


class TestTypeScriptParser:
    """Tests for TypeScript AST parser."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return TypeScriptParser()

    @pytest.fixture
    def tsx_parser(self):
        """Create a TSX parser instance."""
        return TypeScriptParser(tsx=True)

    def test_extract_class_with_types(self, parser):
        """Test extracting a class with TypeScript types."""
        source = """
class UserService {
    private db: Database;

    constructor(db: Database) {
        this.db = db;
    }

    getUser(id: string): User {
        return this.db.find(id);
    }

    async saveUser(user: User): Promise<void> {
        await this.db.save(user);
    }
}
"""
        parser.parse(source)
        classes = parser.extract_classes()

        assert len(classes) == 1
        assert classes[0].name == "UserService"
        assert "getUser" in classes[0].methods
        assert "saveUser" in classes[0].methods

    def test_extract_interface(self, parser):
        """Test extracting TypeScript interface."""
        source = """
interface User {
    id: string;
    name: string;
    email: string;
    getFullName(): string;
}
"""
        parser.parse(source)
        classes = parser.extract_classes()

        assert len(classes) == 1
        assert classes[0].name == "User"
        # Interfaces are marked with 'interface' decorator
        assert "interface" in classes[0].decorators

    def test_extract_class_with_implements(self, parser):
        """Test extracting class that implements interfaces."""
        source = """
class UserModel implements IUser, Serializable {
    id: string;
    name: string;

    serialize(): string {
        return JSON.stringify(this);
    }
}
"""
        parser.parse(source)
        classes = parser.extract_classes()

        assert len(classes) == 1
        assert classes[0].name == "UserModel"
        # Check that implements are in bases
        assert any("IUser" in b for b in classes[0].bases)

    def test_extract_typed_functions(self, parser):
        """Test extracting functions with TypeScript types."""
        source = """
function add(a: number, b: number): number {
    return a + b;
}

async function fetchData<T>(url: string): Promise<T> {
    const response = await fetch(url);
    return response.json();
}

const multiply = (x: number, y: number): number => x * y;
"""
        parser.parse(source)
        functions = parser.extract_functions()

        names = [f.name for f in functions]
        assert "add" in names
        assert "fetchData" in names
        assert "multiply" in names

        # Check async
        fetch_func = next(f for f in functions if f.name == "fetchData")
        assert fetch_func.is_async is True

    def test_extract_imports_with_types(self, parser):
        """Test extracting TypeScript imports."""
        source = """
import { User, UserRole } from './models';
import type { Config } from './config';
import * as utils from './utils';
"""
        parser.parse(source)
        imports = parser.extract_imports()

        modules = [i.module for i in imports]
        assert "./models" in modules
        assert "./config" in modules
        assert "./utils" in modules

    def test_interface_extends(self, parser):
        """Test interface with extends."""
        source = """
interface AdminUser extends User {
    permissions: string[];
    isAdmin: boolean;
}
"""
        parser.parse(source)
        classes = parser.extract_classes()

        assert len(classes) == 1
        assert classes[0].name == "AdminUser"
        assert "User" in classes[0].bases

    def test_count_lines(self, parser):
        """Test counting lines of code."""
        source = """
// Comment
interface User {
    id: string;
}

/*
 * Multi-line comment
 */

class UserService {
    getUser(id: string): User {
        return {} as User;
    }
}
"""
        parser.parse(source)
        loc = parser.count_lines()

        assert loc > 0
        assert loc < 20

    def test_extract_docstring(self, parser):
        """Test extracting JSDoc from TypeScript."""
        source = """
/**
 * User management service.
 * Handles all user-related operations.
 */

export class UserService {}
"""
        parser.parse(source)
        docstring = parser.extract_docstring()

        assert docstring is not None
        assert "User management" in docstring


class TestTypeScriptParserTSX:
    """Tests for TSX parsing."""

    @pytest.fixture
    def parser(self):
        return TypeScriptParser(tsx=True)

    def test_parse_tsx_component(self, parser):
        """Test parsing TSX React component."""
        source = """
import React from 'react';

interface Props {
    name: string;
}

const Greeting: React.FC<Props> = ({ name }) => {
    return <div>Hello, {name}!</div>;
};

export default Greeting;
"""
        parser.parse(source)

        # Should extract the interface
        classes = parser.extract_classes()
        assert any(c.name == "Props" for c in classes)

        # Should extract the component function
        functions = parser.extract_functions()
        assert any(f.name == "Greeting" for f in functions)


class TestTypeScriptParserEdgeCases:
    """Edge case tests for TypeScript parser."""

    @pytest.fixture
    def parser(self):
        return TypeScriptParser()

    def test_empty_file(self, parser):
        """Test parsing empty file."""
        parser.parse("")
        assert parser.extract_classes() == []
        assert parser.extract_functions() == []
        assert parser.extract_imports() == []
        assert parser.count_lines() == 0

    def test_type_alias(self, parser):
        """Test type alias (not extracted as class)."""
        source = """
type UserId = string;
type UserList = User[];
"""
        parser.parse(source)
        # Type aliases are not extracted as classes
        classes = parser.extract_classes()
        assert len(classes) == 0

    def test_enum(self, parser):
        """Test TypeScript enum."""
        source = """
enum UserRole {
    Admin = 'ADMIN',
    User = 'USER',
    Guest = 'GUEST'
}
"""
        parser.parse(source)
        # Enums are not extracted as classes in current implementation
        classes = parser.extract_classes()
        # This is expected behavior

    def test_decorated_class(self, parser):
        """Test decorated class."""
        source = """
@Injectable()
@Controller('users')
export class UserController {
    @Get()
    findAll(): User[] {
        return [];
    }
}
"""
        parser.parse(source)
        classes = parser.extract_classes()

        assert len(classes) == 1
        assert classes[0].name == "UserController"
        assert "findAll" in classes[0].methods

    def test_optional_parameters(self, parser):
        """Test function with optional parameters."""
        source = """
function greet(name: string, greeting?: string): string {
    return `${greeting || 'Hello'}, ${name}!`;
}
"""
        parser.parse(source)
        functions = parser.extract_functions()

        assert len(functions) == 1
        params = functions[0].parameters
        assert "name" in params
        assert "greeting" in params
