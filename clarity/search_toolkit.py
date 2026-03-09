import csv
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import logging

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from clarity.config import ClarityConfig
from clarity.persistence import PersistenceManager, CoverageReport


class SearchResult:
    """Represents a single search result match."""
    
    def __init__(self, file_path: str, location: Union[int, str], snippet: str):
        self.file_path = file_path
        self.location = location  # line number for text, page/offset for docs
        self.snippet = snippet




class LocalSearchToolkit:
    """Local search toolkit with read-only operations."""
    
    def __init__(self, config: ClarityConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._last_coverage: Optional[CoverageReport] = None
        self._coverage_store = []  # Store multiple coverage reports
        self.persistence = PersistenceManager()
    
    def list_dir(self, root: str, glob_patterns: Optional[List[str]] = None, 
                 max_files: Optional[int] = None) -> Dict[str, Any]:
        """List files in directory with optional glob patterns."""
        root_path = Path(root).resolve()
        
        if not root_path.exists():
            raise ValueError(f"Root directory does not exist: {root}")
        
        if not self.config.is_root_allowed(str(root_path)):
            raise ValueError(f"Root directory not allowed: {root}")
        
        max_files = max_files or self.config.max_files
        glob_patterns = glob_patterns or ["*"]
        
        files = []
        coverage = CoverageReport()
        coverage.roots = [str(root_path)]
        coverage.globs = glob_patterns
        coverage.limits_applied["max_files"] = max_files
        
        try:
            for pattern in glob_patterns:
                pattern_files = list(root_path.rglob(pattern))
                for file_path in pattern_files:
                    if len(files) >= max_files:
                        coverage.skipped_files.append(f"Reached max_files limit ({max_files})")
                        break
                    
                    if file_path.is_file():
                        # Check file size
                        if file_path.stat().st_size > self.config.max_file_size_bytes:
                            coverage.skipped_files.append(f"File too large: {file_path}")
                            continue
                        
                        # Check supported extension
                        if file_path.suffix.lower() in self.config.ALL_SUPPORTED_EXTENSIONS:
                            files.append(str(file_path))
                        else:
                            coverage.skipped_files.append(f"Unsupported file type: {file_path}")
                
                if len(files) >= max_files:
                    break
            
            coverage.scanned_files = len(files)
            self._last_coverage = coverage
            self._coverage_store.append(coverage)  # Store for sources command
            
        except Exception as e:
            coverage.errors.append(f"Directory listing error: {e}")
            raise
        
        return {
            "files": files,
            "truncated": len(files) >= max_files,
            "coverage": coverage
        }
    
    def read_text_file(self, path: str, max_bytes: Optional[int] = None) -> Dict[str, Any]:
        """Read text file content with size limits."""
        file_path = Path(path).resolve()
        
        if not file_path.exists():
            raise ValueError(f"File does not exist: {path}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        
        max_bytes = max_bytes or self.config.max_file_size_bytes
        file_size = file_path.stat().st_size
        
        if file_size > max_bytes:
            return {
                "text": None,
                "truncated": True,
                "reason": f"File too large ({file_size} > {max_bytes} bytes)"
            }
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(max_bytes)
            
            return {
                "text": content,
                "truncated": file_size > max_bytes,
                "size": file_size
            }
            
        except Exception as e:
            raise ValueError(f"Failed to read file {path}: {e}")
    
    def search_text(self, root: str, query: str, file_globs: Optional[List[str]] = None,
                   case_sensitive: bool = False, regex: bool = False,
                   context_lines: int = 2, max_matches: Optional[int] = None,
                   max_files: Optional[int] = None) -> Dict[str, Any]:
        """Search for text across files with context."""
        max_matches = max_matches or self.config.max_matches
        
        # Get files to search
        list_result = self.list_dir(root, file_globs, max_files)
        files = list_result["files"]
        
        matches = []
        coverage = list_result.get("coverage", CoverageReport())
        coverage.limits_applied["max_matches"] = max_matches
        coverage.limits_applied["context_lines"] = context_lines
        
        # Prepare search pattern
        if regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            pattern = re.compile(query, flags)
        else:
            search_query = query if case_sensitive else query.lower()
        
        matched_files_count = 0
        
        try:
            for file_path in files:
                if len(matches) >= max_matches:
                    break
                
                # Skip unsupported files for text search
                if Path(file_path).suffix.lower() not in (
                    self.config.TEXT_EXTENSIONS | self.config.CODE_EXTENSIONS | 
                    self.config.DATA_EXTENSIONS
                ):
                    continue
                
                try:
                    file_result = self.read_text_file(file_path)
                    if not file_result["text"]:
                        continue
                    
                    lines = file_result["text"].splitlines()
                    file_matches = []
                    
                    for line_num, line in enumerate(lines, 1):
                        # Check for match
                        if regex:
                            if pattern.search(line):
                                pass  # Match found
                            else:
                                continue
                        else:
                            search_line = line if case_sensitive else line.lower()
                            if search_query not in search_line:
                                continue
                        
                        # Extract context
                        start_line = max(1, line_num - context_lines)
                        end_line = min(len(lines), line_num + context_lines)
                        context_lines_list = lines[start_line - 1:end_line]
                        snippet = "\n".join(context_lines_list)
                        
                        match = SearchResult(
                            file_path=file_path,
                            location=line_num,
                            snippet=snippet
                        )
                        matches.append(match)
                        file_matches.append(match)
                        
                        if len(matches) >= max_matches:
                            break
                    
                    if file_matches:
                        matched_files_count += 1
                
                except Exception as e:
                    coverage.errors.append(f"Error searching {file_path}: {e}")
                    continue
        
        except Exception as e:
            coverage.errors.append(f"Search error: {e}")
            raise
        
        coverage.matched_files = matched_files_count
        self._last_coverage = coverage
        self._coverage_store.append(coverage)  # Store for sources command
        self.persistence.save_coverage_report(coverage)  # Persist for future CLI calls
        
        return {
            "matches": matches,
            "truncated": len(matches) >= max_matches,
            "coverage": coverage
        }
    
    def extract_docx_text(self, path: str) -> Dict[str, Any]:
        """Extract text from DOCX file."""
        if not DOCX_AVAILABLE:
            return {
                "text": None,
                "error": "python-docx not available"
            }
        
        file_path = Path(path).resolve()
        
        if not file_path.exists():
            raise ValueError(f"File does not exist: {path}")
        
        if file_path.suffix.lower() != '.docx':
            raise ValueError(f"File is not a DOCX file: {path}")
        
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
            return {
                "text": text,
                "success": True
            }
            
        except Exception as e:
            return {
                "text": None,
                "error": f"Failed to extract DOCX text: {e}"
            }
    
    def extract_pdf_text(self, path: str) -> Dict[str, Any]:
        """Extract text from PDF file (best-effort)."""
        if not PDF_AVAILABLE:
            return {
                "text": None,
                "error": "PyPDF2 not available"
            }
        
        file_path = Path(path).resolve()
        
        if not file_path.exists():
            raise ValueError(f"File does not exist: {path}")
        
        if file_path.suffix.lower() != '.pdf':
            raise ValueError(f"File is not a PDF file: {path}")
        
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num, page in enumerate(reader.pages):
                    try:
                        text += page.extract_text() + "\n"
                    except Exception:
                        # Continue with other pages if one fails
                        continue
            
            return {
                "text": text,
                "success": True,
                "pages": len(reader.pages)
            }
            
        except Exception as e:
            return {
                "text": None,
                "error": f"Failed to extract PDF text: {e}"
            }
    
    def read_csv(self, path: str, max_rows: Optional[int] = None) -> Dict[str, Any]:
        """Read CSV file with row limits."""
        file_path = Path(path).resolve()
        
        if not file_path.exists():
            raise ValueError(f"File does not exist: {path}")
        
        if file_path.suffix.lower() != '.csv':
            raise ValueError(f"File is not a CSV file: {path}")
        
        max_rows = max_rows or 1000  # Default CSV row limit
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
                reader = csv.reader(file)
                rows = []
                
                for i, row in enumerate(reader):
                    if len(rows) >= max_rows:
                        break
                    rows.append(row)
                
                # Get columns from first row
                columns = rows[0] if rows else []
                
                return {
                    "rows": rows,
                    "columns": columns,
                    "truncated": i >= max_rows - 1,
                    "total_rows_found": i + 1
                }
                
        except Exception as e:
            raise ValueError(f"Failed to read CSV {path}: {e}")
    
    def get_last_coverage(self) -> Optional[CoverageReport]:
        """Get coverage report from last search operation."""
        # First try in-memory store
        if self._coverage_store:
            return self._coverage_store[-1]
        
        # Then try persistent storage
        return self.persistence.get_last_coverage()
