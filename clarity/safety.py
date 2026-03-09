import re
from typing import List, Dict, Any

from clarity.search_toolkit import SearchResult


class SafetyLayer:
    """Safety and security controls for Clarity OS T4."""
    
    # Patterns for potential secrets that should be redacted
    SECRET_PATTERNS = [
        # API Keys
        r'(api[_-]?key["\'\s]*[:=]["\'\s]*[a-zA-Z0-9_-]{20,})',
        r'(sk-[a-zA-Z0-9_-]{20,})',  # Stripe keys
        r'(AIza[a-zA-Z0-9_-]{35})',  # Google API keys
        
        # Passwords
        r'(password["\'\s]*[:=]["\'\s]*[^\s]{8,})',
        r'(pwd["\'\s]*[:=]["\'\s]*[^\s]{6,})',
        
        # Tokens
        r'(token["\'\s]*[:=]["\'\s]*[a-zA-Z0-9_-]{20,})',
        r'(bearer["\'\s]+[a-zA-Z0-9_-]{20,})',
        
        # Database URLs
        r'(mongodb://[^\s]+)',
        r'(postgresql://[^\s]+)',
        r'(mysql://[^\s]+)',
        
        # AWS keys
        r'(AKIA[0-9A-Z]{16})',  # AWS access key ID
        
        # Private keys
        r'-----BEGIN [A-Z]+ KEY-----',
        r'-----BEGIN PRIVATE KEY-----',
    ]
    
    def __init__(self):
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.SECRET_PATTERNS]
    
    def redact_matches(self, matches: List[SearchResult]) -> List[SearchResult]:
        """Apply redaction to search result snippets."""
        redacted_matches = []
        
        for match in matches:
            redacted_snippet = self.redact_text(match.snippet)
            redacted_match = SearchResult(
                file_path=match.file_path,
                location=match.location,
                snippet=redacted_snippet
            )
            redacted_matches.append(redacted_match)
        
        return redacted_matches
    
    def redact_text(self, text: str) -> str:
        """Redact potential secrets from text."""
        redacted_text = text
        
        for pattern in self.compiled_patterns:
            redacted_text = pattern.sub('[REDACTED]', redacted_text)
        
        return redacted_text
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """Validate search query for safety."""
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Check for potentially dangerous regex patterns
        if self._has_dangerous_regex(query):
            validation_result["errors"].append("Query contains potentially dangerous regex pattern")
            validation_result["valid"] = False
        
        # Check for very long queries
        if len(query) > 1000:
            validation_result["warnings"].append("Query is very long, may impact performance")
        
        return validation_result
    
    def _has_dangerous_regex(self, query: str) -> bool:
        """Check for potentially dangerous regex patterns."""
        dangerous_patterns = [
            r'\*\*.*\*\*',  # Nested quantifiers
            r'\+\+\+',       # Excessive repetition
            r'\*\{1000,\}',  # Very large quantifiers
            r'\(\.\*\)\{50,\}',  # Large repetition groups
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query):
                return True
        
        return False
    
    def sanitize_file_path(self, file_path: str) -> str:
        """Sanitize file path for display."""
        # Convert to relative path if possible
        try:
            import os
            cwd = os.getcwd()
            if file_path.startswith(cwd):
                return file_path[len(cwd):].lstrip('/\\')
        except Exception:
            pass
        
        return file_path
    
    def check_file_size_safe(self, file_size_bytes: int, max_size_bytes: int) -> bool:
        """Check if file size is within safe limits."""
        return file_size_bytes <= max_size_bytes
    
    def estimate_memory_usage(self, num_files: int, avg_file_size: int = 1024*1024) -> int:
        """Estimate memory usage for search operations."""
        # Rough estimation: each file + context + overhead
        estimated_bytes = num_files * (avg_file_size + 1024)  # 1KB overhead per file
        return estimated_bytes
