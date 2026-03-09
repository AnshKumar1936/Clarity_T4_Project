
import os
from pathlib import Path
from typing import Optional, List


class ClarityConfig:
    """Configuration for Clarity OS T4."""
    
    # Default safety limits
    DEFAULT_MAX_FILES = 5000
    DEFAULT_MAX_MATCHES = 2000
    DEFAULT_MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
    DEFAULT_CONTEXT_LINES = 2
    
    # Supported file types
    TEXT_EXTENSIONS = {'.txt', '.md', '.log'}
    CODE_EXTENSIONS = {'.py', '.js', '.ts', '.json', '.yaml', '.yml', '.toml', '.ini'}
    DATA_EXTENSIONS = {'.csv'}
    DOCUMENT_EXTENSIONS = {'.docx', '.pdf'}
    
    ALL_SUPPORTED_EXTENSIONS = (
        TEXT_EXTENSIONS | CODE_EXTENSIONS | DATA_EXTENSIONS | DOCUMENT_EXTENSIONS
    )
    
    def __init__(self):
        self.boot_doc_path: Optional[str] = os.getenv("CLARITY_BOOT_DOC_PATH")
        self.allowlisted_roots: List[str] = self._get_allowlisted_roots()
        
        # Safety limits
        self.max_files = int(os.getenv("CLARITY_MAX_FILES", self.DEFAULT_MAX_FILES))
        self.max_matches = int(os.getenv("CLARITY_MAX_MATCHES", self.DEFAULT_MAX_MATCHES))
        self.max_file_size_bytes = int(
            os.getenv("CLARITY_MAX_FILE_SIZE", str(self.DEFAULT_MAX_FILE_SIZE_BYTES))
        )
        
    def _get_allowlisted_roots(self) -> List[str]:
        """Get allowlisted root directories from environment."""
        roots_str = os.getenv("CLARITY_ALLOWLISTED_ROOTS", "")
        return [root.strip() for root in roots_str.split(",") if root.strip()]
    
    def is_root_allowed(self, root_path: str) -> bool:
        """Check if root path is allowed for search."""
        if not self.allowlisted_roots:
            return True  # No allowlist means all roots allowed
        return any(Path(root_path).is_relative_to(Path(allowed)) for allowed in self.allowlisted_roots)
    
    def validate_boot_doc(self) -> bool:
        """Validate boot document exists and is readable."""
        if not self.boot_doc_path:
            return True  # No boot doc required
        
        boot_path = Path(self.boot_doc_path)
        return boot_path.exists() and boot_path.is_file()
