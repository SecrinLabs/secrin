"""Tree-sitter language configuration and management"""
from typing import Optional, Dict
from tree_sitter import Language

try:
    import tree_sitter_python  # type: ignore[import-untyped]
except ImportError:
    tree_sitter_python = None  # type: ignore[assignment]

try:
    import tree_sitter_javascript  # type: ignore[import-untyped]
except ImportError:
    tree_sitter_javascript = None  # type: ignore[assignment]

try:
    import tree_sitter_typescript  # type: ignore[import-untyped]
except ImportError:
    tree_sitter_typescript = None  # type: ignore[assignment]

# Add more as needed: tree_sitter_java, etc.


class LanguageRegistry:
    """Registry for tree-sitter languages"""
    
    def __init__(self):
        self._languages: Dict[str, Language] = {}
        self._load_default_languages()
    
    def _load_default_languages(self):
        """Load default supported languages"""
        if tree_sitter_python is not None:
            try:
                self._languages["python"] = Language(tree_sitter_python.language())  # type: ignore[attr-defined]
            except Exception as e:
                print(f"Warning: Could not load Python language: {e}")
        else:
            print("Warning: tree_sitter_python not installed. Install with: pip install tree-sitter-python")
        
        if tree_sitter_javascript is not None:
            try:
                self._languages["javascript"] = Language(tree_sitter_javascript.language())  # type: ignore[attr-defined]
            except Exception as e:
                print(f"Warning: Could not load JavaScript language: {e}")
        else:
            print("Warning: tree_sitter_javascript not installed. Install with: pip install tree-sitter-javascript")
        
        if tree_sitter_typescript is not None:
            try:
                # Load TypeScript language
                self._languages["typescript"] = Language(tree_sitter_typescript.language_typescript())  # type: ignore[attr-defined]
                # We could also load TSX if needed, maybe as "tsx" language
                # self._languages["tsx"] = Language(tree_sitter_typescript.language_tsx())
            except Exception as e:
                print(f"Warning: Could not load TypeScript language: {e}")
        else:
            print("Warning: tree_sitter_typescript not installed. Install with: pip install tree-sitter-typescript")
        
        # Add more languages here as needed
        # self._languages["typescript"] = Language(tree_sitter_typescript.language_typescript())
        # self._languages["java"] = Language(tree_sitter_java.language())
    
    def get_language(self, name: str) -> Optional[Language]:
        """
        Get a tree-sitter Language object by name
        
        Args:
            name: Language name (e.g., 'python', 'javascript')
        
        Returns:
            Language object or None if not found
        """
        return self._languages.get(name.lower())
    
    def is_supported(self, name: str) -> bool:
        """
        Check if a language is supported
        
        Args:
            name: Language name
        
        Returns:
            True if the language is supported
        """
        return name.lower() in self._languages
    
    def supported_languages(self) -> list[str]:
        """
        Get list of all supported language names
        
        Returns:
            List of language names
        """
        return list(self._languages.keys())


# Singleton instance
language_registry = LanguageRegistry()
