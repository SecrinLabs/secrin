"""
Fumadocs Static Site Generator

This module transforms the generated wiki documentation into a Fumadocs-compatible
static site structure that can be built and deployed.
"""

import os
import re
import json
import shutil
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class FumadocsGenerator:
    """
    Generates a Fumadocs static site from wiki documentation.
    
    This class handles:
    - Copying the Fumadocs template to the output directory
    - Transforming markdown files to MDX with proper frontmatter
    - Generating navigation structure from module_tree.json
    - Creating meta.json files for sidebar navigation
    """
    
    def __init__(self, docs_dir: str, output_dir: Optional[str] = None):
        """
        Initialize the Fumadocs generator.
        
        Args:
            docs_dir: Path to the generated wiki documentation (contains .md files)
            output_dir: Path for the Fumadocs site output (defaults to docs_dir/site)
        """
        self.docs_dir = Path(docs_dir)
        self.output_dir = Path(output_dir) if output_dir else self.docs_dir / "site"
        self.template_dir = Path(__file__).parent / "fumadocs_template"
        self.content_dir = self.output_dir / "content" / "docs"
    
    def generate(self) -> str:
        """
        Generate the complete Fumadocs site.
        
        Returns:
            Path to the generated site directory
        """
        logger.info("🚀 Starting Fumadocs site generation...")
        
        # Step 1: Copy template to output directory
        self._copy_template()
        
        # Step 2: Load module tree for navigation structure
        module_tree = self._load_module_tree()
        
        # Step 3: Transform and copy markdown files to MDX
        self._transform_markdown_files(module_tree)
        
        # Step 4: Generate meta.json for navigation
        self._generate_meta_files(module_tree)
        
        logger.info(f"✅ Fumadocs site generated at: {self.output_dir}")
        logger.info(f"   Run 'cd {self.output_dir} && pnpm install && pnpm dev' to preview")
        logger.info(f"   Run 'cd {self.output_dir} && pnpm build' to build static site")
        
        return str(self.output_dir)
    
    def _copy_template(self) -> None:
        """Copy the Fumadocs template to the output directory."""
        logger.info(f"📁 Copying Fumadocs template to {self.output_dir}")
        
        temp_nm: Optional[Path] = None
        
        if self.output_dir.exists():
            # Remove existing site but preserve node_modules if exists
            node_modules = self.output_dir / "node_modules"
            has_node_modules = node_modules.exists()
            
            if has_node_modules:
                # Temporarily move node_modules
                temp_nm = self.output_dir.parent / "_temp_node_modules"
                shutil.move(str(node_modules), str(temp_nm))
            
            shutil.rmtree(self.output_dir)
            
            if has_node_modules and temp_nm is not None:
                self.output_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(temp_nm), str(self.output_dir / "node_modules"))
        
        # Copy template
        shutil.copytree(self.template_dir, self.output_dir, dirs_exist_ok=True)
        
        # Ensure content directory exists
        self.content_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_module_tree(self) -> Dict[str, Any]:
        """Load the module tree from the docs directory."""
        module_tree_path = self.docs_dir / "module_tree.json"
        
        if module_tree_path.exists():
            with open(module_tree_path, 'r') as f:
                return json.load(f)
        
        logger.warning("module_tree.json not found, using flat structure")
        return {}
    
    def _transform_markdown_files(self, module_tree: Dict[str, Any]) -> None:
        """Transform markdown files to MDX with frontmatter."""
        logger.info("📝 Transforming markdown files to MDX...")
        
        # Process overview.md as index
        overview_path = self.docs_dir / "overview.md"
        if overview_path.exists():
            self._transform_file(
                overview_path,
                self.content_dir / "index.mdx",
                title="Overview",
                description="Project documentation overview"
            )
        
        # Process all other markdown files
        for md_file in self.docs_dir.glob("*.md"):
            if md_file.name == "overview.md":
                continue
            
            # Get module name from filename
            module_name = md_file.stem
            
            # Find module info in tree for metadata
            module_info = self._find_module_info(module_tree, module_name)
            
            # Create MDX file
            output_path = self.content_dir / f"{self._slugify(module_name)}.mdx"
            
            self._transform_file(
                md_file,
                output_path,
                title=self._format_title(module_name),
                description=module_info.get("description", f"Documentation for {module_name}")
            )
    
    def _transform_file(
        self,
        input_path: Path,
        output_path: Path,
        title: str,
        description: str
    ) -> None:
        """Transform a single markdown file to MDX with frontmatter."""
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if frontmatter already exists
        if content.startswith('---'):
            # Extract existing content after frontmatter
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2].strip()
        
        # Extract title from first heading if present
        title_match = re.match(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
            # Remove the first heading since Fumadocs will render the title
            content = re.sub(r'^#\s+.+\n*', '', content, count=1)
        
        # Create frontmatter
        frontmatter = f"""---
title: "{title}"
description: "{description}"
---

"""
        
        # Write MDX file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter + content)
        
        logger.debug(f"  ✓ {input_path.name} → {output_path.name}")
    
    def _generate_meta_files(self, module_tree: Dict[str, Any]) -> None:
        """Generate meta.json files for Fumadocs navigation."""
        logger.info("🗂️  Generating navigation structure...")
        
        # Build navigation pages list
        pages = ["index"]  # Overview first
        
        # Add modules in order
        for md_file in sorted(self.docs_dir.glob("*.md")):
            if md_file.name != "overview.md":
                pages.append(self._slugify(md_file.stem))
        
        # Create meta.json
        meta = {
            "title": "Documentation",
            "pages": pages
        }
        
        meta_path = self.content_dir / "meta.json"
        with open(meta_path, 'w') as f:
            json.dump(meta, f, indent=2)
        
        logger.debug(f"  ✓ Generated meta.json with {len(pages)} pages")
    
    def _find_module_info(self, module_tree: Dict[str, Any], module_name: str) -> Dict[str, Any]:
        """Recursively find module info in the tree."""
        def search(tree: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            for name, info in tree.items():
                if name == module_name:
                    return info
                if isinstance(info, dict) and "children" in info:
                    result = search(info["children"])
                    if result:
                        return result
            return None
        
        return search(module_tree) or {}
    
    def _slugify(self, name: str) -> str:
        """Convert a module name to a URL-friendly slug."""
        # Replace special characters
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    def _format_title(self, name: str) -> str:
        """Format a module name as a human-readable title."""
        # Replace underscores and hyphens with spaces
        title = name.replace('_', ' ').replace('-', ' ')
        # Capitalize words
        return title.title()


def generate_fumadocs_site(docs_dir: str, output_dir: Optional[str] = None) -> str:
    """
    Convenience function to generate a Fumadocs site.
    
    Args:
        docs_dir: Path to the generated wiki documentation
        output_dir: Optional custom output directory for the site
    
    Returns:
        Path to the generated site directory
    """
    generator = FumadocsGenerator(docs_dir, output_dir)
    return generator.generate()
