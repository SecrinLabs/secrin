"""
Content sanitizer for LLM-generated documentation.

Cleans up common issues in LLM output like:
- Bracket placeholders [like this]
- Template markers (PROBLEM_1, SOLUTION_1, etc.)
- Duplicate/stray markdown formatting
"""

import re
from typing import Optional


def sanitize_llm_content(text: Optional[str]) -> str:
    """
    Clean LLM-generated content for use in documentation.
    
    Removes:
    - Bracket placeholders like [Step 1] or [Description here]
    - Numbered template markers like PROBLEM_1:, SOLUTION_1:
    - Stray markdown that would appear as raw text
    - Excessive whitespace/newlines
    
    Args:
        text: Raw LLM output text
        
    Returns:
        Cleaned text safe for markdown rendering
    """
    if not text:
        return ""
    
    result = text.strip()
    
    # Remove bracket placeholders with generic descriptions
    # Matches [Text here], [Some description], [Step X], etc.
    result = re.sub(r'\[(?:Step \d+|Prerequisite \d+|Feature \d+|Goal \d+|.*?here.*?|Description|Title|Name|Value)\]', '', result, flags=re.IGNORECASE)
    
    # Remove leftover template markers that aren't section headers
    # e.g., "PROBLEM_1:" "SOLUTION_2:" but not "PROBLEM:" or "SOLUTION:"
    result = re.sub(r'\b(PROBLEM|SOLUTION|STEP|ITEM|POINT)_\d+:\s*', '', result)
    
    # Clean up double asterisks that would show as raw text
    # When content already has ** and we wrap with **, user sees raw **
    # Only clean if they're not part of proper bold formatting
    # Pattern: ** at start of line not followed by text then **
    result = re.sub(r'^\*\*\s*$', '', result, flags=re.MULTILINE)
    
    # Remove empty bullet points
    result = re.sub(r'^[-*]\s*$', '', result, flags=re.MULTILINE)
    
    # Collapse multiple blank lines into one
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    # Clean up leading/trailing whitespace per line
    lines = [line.rstrip() for line in result.split('\n')]
    result = '\n'.join(lines)
    
    return result.strip()


def sanitize_list_item(text: Optional[str]) -> str:
    """
    Clean a single list item from LLM output.
    
    Args:
        text: A single list item or step text
        
    Returns:
        Cleaned text without placeholders
    """
    if not text:
        return ""
    
    result = text.strip()
    
    # Remove bracket placeholders entirely
    result = re.sub(r'\[.*?\]', '', result)
    
    # Remove template variable patterns ${var} or {{var}}
    result = re.sub(r'[\$\{][\{]?[\w_]+[\}]?[\}]?', '', result)
    
    # Clean up resulting double spaces
    result = re.sub(r'\s{2,}', ' ', result)
    
    return result.strip()


def is_placeholder_content(text: Optional[str]) -> bool:
    """
    Check if text is just placeholder content that should be skipped.
    
    Args:
        text: Text to check
        
    Returns:
        True if the text appears to be only placeholder content
    """
    if not text:
        return True
    
    cleaned = text.strip()
    
    # Empty after stripping
    if not cleaned:
        return True
    
    # Just a bracket placeholder
    if re.match(r'^\[.*\]$', cleaned):
        return True
    
    # Template instruction text
    placeholder_patterns = [
        r'^(Step|Prerequisite|Goal|Feature|Item|Point)\s*\d*$',
        r'^(What|How|Why|When|Where)\s+(to|the|this)',
        r'^(Description|Title|Name|Value)\s*(here)?$',
        r'^\[.*\]$',
    ]
    
    for pattern in placeholder_patterns:
        if re.match(pattern, cleaned, re.IGNORECASE):
            return True
    
    return False
