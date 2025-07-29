"""
Utility functions for graph operations.
"""
import re
import json
from typing import Dict, List, Set


def extract_references(text: str) -> Dict[str, List[str]]:
    """Extract references to issues, PRs, commits from text"""
    references = {
        'issues': [],
        'prs': [],
        'commits': [],
        'files': []
    }
    
    # GitHub issue references (#123, issue #123)
    issue_pattern = r'#(\d+)|issue\s+#(\d+)'
    issues = re.findall(issue_pattern, text.lower())
    references['issues'] = [i[0] or i[1] for i in issues if i[0] or i[1]]
    
    # PR references (PR #123, pull request #123)
    pr_pattern = r'pr\s+#(\d+)|pull\s+request\s+#(\d+)'
    prs = re.findall(pr_pattern, text.lower())
    references['prs'] = [p[0] or p[1] for p in prs if p[0] or p[1]]
    
    # Commit hashes (40 or 7+ character hex)
    commit_pattern = r'\b([a-f0-9]{7,40})\b'
    commits = re.findall(commit_pattern, text.lower())
    references['commits'] = commits
    
    # File references
    file_pattern = r'([a-zA-Z0-9_\-./]+\.(py|js|html|css|json|yml|yaml|md|txt))'
    files = re.findall(file_pattern, text)
    references['files'] = [f[0] for f in files]
    
    return references


def find_content_similarity(content1: str, content2: str) -> float:
    """Calculate content similarity between two texts"""
    # Simple keyword-based similarity (can be enhanced with embeddings)
    words1 = set(content1.lower().split())
    words2 = set(content2.lower().split())
    
    if not words1 or not words2:
        return 0.0
        
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0


def sanitize_metadata(metadata: Dict) -> Dict:
    """Sanitize metadata to ensure vectorstore compatibility"""
    sanitized = {}
    for key, value in metadata.items():
        if isinstance(value, (list, tuple)):
            # Convert arrays to comma-separated strings
            sanitized[key] = ", ".join(str(v) for v in value)
        elif isinstance(value, dict):
            # Convert dicts to JSON strings
            sanitized[key] = json.dumps(value)
        elif isinstance(value, (str, int, float, bool)) or value is None:
            # Keep scalar values as is
            sanitized[key] = value
        else:
            # Convert other types to strings
            sanitized[key] = str(value)
    return sanitized


def extract_keywords(text: str) -> Set[str]:
    """Extract meaningful keywords from text"""
    # Simple keyword extraction - can be enhanced with NLP
    import re
    
    # Remove common words and extract meaningful terms
    common_words = {'the', 'is', 'at', 'which', 'on', 'and', 'or', 'but', 'in', 'with', 'to', 'for', 'of', 'as', 'by', 'from', 'up', 'into', 'over', 'after'}
    
    # Extract words, function names, class names, etc.
    words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b', text.lower())
    
    # Filter out common words and short words
    keywords = {word for word in words if word not in common_words and len(word) > 2}
    
    # Limit to top keywords to avoid noise
    return set(list(keywords)[:50])  # Top 50 keywords per document
