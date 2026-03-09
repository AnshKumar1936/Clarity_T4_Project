
import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


class CoverageReport:
    """Coverage report for search operations (moved here to avoid circular import)."""
    
    def __init__(self):
        self.roots: List[str] = []
        self.globs: List[str] = []
        self.scanned_files: int = 0
        self.matched_files: int = 0
        self.skipped_files: List[str] = []
        self.errors: List[str] = []
        self.limits_applied: Dict[str, Any] = {}


class PersistenceManager:
    """Manages persistent storage for search history."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir is None:
            storage_dir = os.path.expanduser("~/.clarity")
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        self.history_file = self.storage_dir / "search_history.json"
        self.max_history_entries = 50
    
    def save_coverage_report(self, coverage: CoverageReport) -> None:
        """Save a coverage report to persistent storage."""
        # Convert coverage report to serializable format
        coverage_data = {
            "timestamp": datetime.now().isoformat(),
            "roots": coverage.roots,
            "globs": coverage.globs,
            "scanned_files": coverage.scanned_files,
            "matched_files": coverage.matched_files,
            "skipped_files": coverage.skipped_files[:10],  # Limit stored skipped files
            "errors": coverage.errors,
            "limits_applied": coverage.limits_applied
        }
        
        # Load existing history
        history = self._load_history()
        
        # Add new entry
        history.append(coverage_data)
        
        # Limit history size
        if len(history) > self.max_history_entries:
            history = history[-self.max_history_entries:]
        
        # Save history
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)
    
    def get_last_coverage(self) -> Optional[CoverageReport]:
        """Get the most recent coverage report from storage."""
        history = self._load_history()
        
        if not history:
            return None
        
        # Get the most recent entry
        last_entry = history[-1]
        
        # Convert back to CoverageReport object
        coverage = CoverageReport()
        coverage.roots = last_entry.get("roots", [])
        coverage.globs = last_entry.get("globs", [])
        coverage.scanned_files = last_entry.get("scanned_files", 0)
        coverage.matched_files = last_entry.get("matched_files", 0)
        coverage.skipped_files = last_entry.get("skipped_files", [])
        coverage.errors = last_entry.get("errors", [])
        coverage.limits_applied = last_entry.get("limits_applied", {})
        
        return coverage
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load search history from storage."""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def clear_history(self) -> None:
        """Clear all search history."""
        if self.history_file.exists():
            self.history_file.unlink()
    
    def get_history_summary(self) -> Dict[str, Any]:
        """Get a summary of search history."""
        history = self._load_history()
        
        if not history:
            return {
                "total_searches": 0,
                "latest_search": None,
                "most_searched_roots": []
            }
        
        # Calculate statistics
        total_searches = len(history)
        latest_search = history[-1]["timestamp"] if history else None
        
        # Count searches by root
        root_counts = {}
        for entry in history:
            for root in entry.get("roots", []):
                root_counts[root] = root_counts.get(root, 0) + 1
        
        most_searched_roots = sorted(root_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_searches": total_searches,
            "latest_search": latest_search,
            "most_searched_roots": most_searched_roots
        }
