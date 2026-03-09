"""
Tests for Local Search Toolkit
"""

import pytest
import tempfile
import os
from pathlib import Path

from clarity.search_toolkit import LocalSearchToolkit, SearchResult
from clarity.config import ClarityConfig


class TestLocalSearchToolkit:
    """Test cases for LocalSearchToolkit."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = ClarityConfig()
        self.toolkit = LocalSearchToolkit(self.config)
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test files
        self.test_file1 = Path(self.temp_dir) / "test1.txt"
        self.test_file1.write_text("Hello world\nThis is a test\nSearch term here")
        
        self.test_file2 = Path(self.temp_dir) / "test2.md"
        self.test_file2.write_text("# Title\nContent with search term\nMore content")
        
        self.test_csv = Path(self.temp_dir) / "data.csv"
        self.test_csv.write_text("name,value\ntest1,123\ntest2,456")
    
    def teardown_method(self):
        """Cleanup test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_list_dir_basic(self):
        """Test basic directory listing."""
        result = self.toolkit.list_dir(self.temp_dir)
        
        assert "files" in result
        assert len(result["files"]) >= 3  # At least our test files
        assert any("test1.txt" in f for f in result["files"])
        assert any("test2.md" in f for f in result["files"])
        assert any("data.csv" in f for f in result["files"])
    
    def test_list_dir_with_globs(self):
        """Test directory listing with glob patterns."""
        result = self.toolkit.list_dir(self.temp_dir, ["*.txt"])
        
        assert "files" in result
        assert len(result["files"]) == 1
        assert "test1.txt" in result["files"][0]
    
    def test_read_text_file(self):
        """Test reading text files."""
        result = self.toolkit.read_text_file(str(self.test_file1))
        
        assert "text" in result
        assert "Hello world" in result["text"]
        assert "Search term here" in result["text"]
        assert not result["truncated"]
    
    def test_search_text_basic(self):
        """Test basic text search."""
        result = self.toolkit.search_text(self.temp_dir, "search term")
        
        assert "matches" in result
        assert len(result["matches"]) >= 2  # Should find in both files
        assert any("test1.txt" in match.file_path for match in result["matches"])
        assert any("test2.md" in match.file_path for match in result["matches"])
    
    def test_search_text_case_sensitive(self):
        """Test case-sensitive search."""
        result_lower = self.toolkit.search_text(self.temp_dir, "search term", case_sensitive=False)
        result_upper = self.toolkit.search_text(self.temp_dir, "SEARCH TERM", case_sensitive=True)
        
        assert len(result_lower["matches"]) >= 2
        assert len(result_upper["matches"]) == 0
    
    def test_search_text_regex(self):
        """Test regex search."""
        result = self.toolkit.search_text(self.temp_dir, r"search\s+\w+", regex=True)
        
        assert "matches" in result
        assert len(result["matches"]) >= 2
    
    def test_read_csv(self):
        """Test CSV reading."""
        result = self.toolkit.read_csv(str(self.test_csv))
        
        assert "rows" in result
        assert "columns" in result
        assert len(result["rows"]) == 3  # Header + 2 data rows
        assert result["columns"] == ["name", "value"]
        assert result["rows"][1] == ["test1", "123"]
    
    def test_coverage_report(self):
        """Test coverage report generation."""
        result = self.toolkit.search_text(self.temp_dir, "search")
        coverage = result["coverage"]
        
        assert coverage.scanned_files > 0
        assert coverage.matched_files > 0
        assert len(coverage.roots) == 1
        assert coverage.roots[0] == str(Path(self.temp_dir).resolve())
    
    def test_max_files_limit(self):
        """Test max files limit."""
        # Create many test files
        for i in range(10):
            file_path = Path(self.temp_dir) / f"file_{i}.txt"
            file_path.write_text(f"Content {i}")
        
        result = self.toolkit.list_dir(self.temp_dir, max_files=5)
        
        assert len(result["files"]) <= 5
    
    def test_unsupported_file_type(self):
        """Test handling of unsupported file types."""
        # Create unsupported file
        unsupported_file = Path(self.temp_dir) / "test.xyz"
        unsupported_file.write_text("content")
        
        result = self.toolkit.list_dir(self.temp_dir)
        
        # Should not include unsupported files
        assert not any("test.xyz" in f for f in result["files"])
    
    def test_nonexistent_directory(self):
        """Test handling of nonexistent directory."""
        with pytest.raises(ValueError, match="Root directory does not exist"):
            self.toolkit.list_dir("/nonexistent/path")
    
    def test_nonexistent_file(self):
        """Test handling of nonexistent file."""
        with pytest.raises(ValueError, match="File does not exist"):
            self.toolkit.read_text_file("/nonexistent/file.txt")


class TestSearchResult:
    """Test cases for SearchResult class."""
    
    def test_search_result_creation(self):
        """Test SearchResult creation."""
        result = SearchResult("/path/to/file.txt", 10, "snippet content")
        
        assert result.file_path == "/path/to/file.txt"
        assert result.location == 10
        assert result.snippet == "snippet content"


if __name__ == "__main__":
    pytest.main([__file__])
