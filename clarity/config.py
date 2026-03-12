
import json
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
        
        # Load config from file if available
        self._load_config_file()
        
        # Override with environment variables
        self.max_files = int(os.getenv("CLARITY_MAX_FILES", self.max_files))
        self.max_matches = int(os.getenv("CLARITY_MAX_MATCHES", self.max_matches))
        self.max_file_size_bytes = int(
            os.getenv("CLARITY_MAX_FILE_SIZE", str(self.max_file_size_bytes))
        )
        
    def _load_config_file(self):
        """Load configuration from t4_config.json if it exists."""
        config_path = Path("t4_config.json")
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                self.max_files = config_data.get("max_files", self.DEFAULT_MAX_FILES)
                self.max_matches = config_data.get("max_matches", self.DEFAULT_MAX_MATCHES)
                self.max_file_size_bytes = config_data.get("max_file_size_bytes", self.DEFAULT_MAX_FILE_SIZE_BYTES)
                self.context_lines = config_data.get("context_lines", self.DEFAULT_CONTEXT_LINES)
                self.allowlisted_roots = config_data.get("allowlisted_roots", [])
                
            except Exception as e:
                # Use defaults if config file is invalid
                self.max_files = self.DEFAULT_MAX_FILES
                self.max_matches = self.DEFAULT_MAX_MATCHES
                self.max_file_size_bytes = self.DEFAULT_MAX_FILE_SIZE_BYTES
                self.context_lines = self.DEFAULT_CONTEXT_LINES
                self.allowlisted_roots = []
        else:
            # Use defaults if no config file
            self.max_files = self.DEFAULT_MAX_FILES
            self.max_matches = self.DEFAULT_MAX_MATCHES
            self.max_file_size_bytes = self.DEFAULT_MAX_FILE_SIZE_BYTES
            self.context_lines = self.DEFAULT_CONTEXT_LINES
        
    def _get_allowlisted_roots(self) -> List[str]:
        """Get allowlisted root directories from environment."""
        roots_str = os.getenv("CLARITY_ALLOWLISTED_ROOTS", "")
        return [root.strip() for root in roots_str.split(",") if root.strip()]
    
    def is_root_allowed(self, root_path: str) -> bool:
        """Check if root path is allowed for search."""
        if not self.allowlisted_roots:
            return True  # No allowlist means all roots allowed
        return any(Path(root_path).is_relative_to(Path(allowed)) for allowed in self.allowlisted_roots)
    
    def validate_boot_doc(self) -> tuple[bool, Optional[str]]:
        """Validate boot document exists and contains required sections.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not self.boot_doc_path:
            return True, None  # No boot doc required
        
        boot_path = Path(self.boot_doc_path)
        
        # Check if file exists
        if not boot_path.exists() or not boot_path.is_file():
            return False, f"Boot document not found: {self.boot_doc_path}"
        
        # Validate JSON structure
        try:
            with open(boot_path, 'r', encoding='utf-8') as f:
                boot_doc = json.load(f)
        except json.JSONDecodeError as e:
            return False, f"Boot document invalid JSON: {e}"
        except Exception as e:
            return False, f"Boot document read error: {e}"
        
        # Check required top-level keys
        required_keys = ['identity', 'operating_rules', 'modes_personas', 'memory_rules']
        missing_keys = [key for key in required_keys if key not in boot_doc]
        
        if missing_keys:
            return False, f"Boot document invalid. Missing: {', '.join(missing_keys)}"
        
        return True, None
