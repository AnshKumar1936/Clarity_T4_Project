
import argparse
import re
from typing import List, Dict, Any
from pathlib import Path

from clarity.search_toolkit import LocalSearchToolkit, SearchResult
from clarity.persistence import CoverageReport
from clarity.response_formatter import ResponseFormatter
from clarity.safety import SafetyLayer


class BaseCommand:
    """Base class for CLI commands."""
    
    def __init__(self, toolkit: LocalSearchToolkit):
        self.toolkit = toolkit
        self.safety = SafetyLayer()
        self.formatter = ResponseFormatter()
    
    def execute(self, args: argparse.Namespace) -> int:
        """Execute command. Returns exit code."""
        raise NotImplementedError


class SearchCommand(BaseCommand):
    """Execute search command."""
    
    def execute(self, args: argparse.Namespace) -> int:
        """Execute search command."""
        try:
            # Parse glob patterns
            globs = [g.strip() for g in args.globs.split(",")]
            
            # Perform search
            result = self.toolkit.search_text(
                root=args.root,
                query=args.query,
                file_globs=globs,
                case_sensitive=args.case_sensitive,
                regex=args.regex,
                context_lines=args.context,
                max_matches=args.max_matches,
                max_files=args.max_files
            )
            
            # Format and print response
            response = self.formatter.format_search_response(
                query=args.query,
                matches=result["matches"],
                coverage=result["coverage"],
                truncated=result["truncated"]
            )
            
            print(response)
            return 0
            
        except Exception as e:
            print(f"Search error: {e}", file=__import__("sys").stderr)
            return 1


class AskCommand(BaseCommand):
    """Execute ask command (search + summarize)."""
    
    def execute(self, args: argparse.Namespace) -> int:
        """Execute ask command."""
        try:
            # Parse glob patterns
            globs = [g.strip() for g in args.globs.split(",")]
            
            # Perform search
            result = self.toolkit.search_text(
                root=args.root,
                query=args.question,
                file_globs=globs,
                case_sensitive=args.case_sensitive,
                regex=args.regex,
                context_lines=args.context,
                max_matches=args.max_matches,
                max_files=args.max_files
            )
            
            # Apply redaction to snippets
            redacted_matches = self.safety.redact_matches(result["matches"])
            
            # Generate answer with citations
            response = self.formatter.format_ask_response(
                question=args.question,
                matches=redacted_matches,
                coverage=result["coverage"],
                truncated=result["truncated"]
            )
            
            print(response)
            return 0
            
        except Exception as e:
            print(f"Ask error: {e}", file=__import__("sys").stderr)
            return 1


class SourcesCommand(BaseCommand):
    """Execute sources command."""
    
    def execute(self, args: argparse.Namespace) -> int:
        """Execute sources command."""
        try:
            coverage = self.toolkit.get_last_coverage()
            
            if not coverage:
                print("No search history available. Run a search or ask command first.")
                return 0
            
            response = self.formatter.format_sources_response(coverage)
            print(response)
            return 0
            
        except Exception as e:
            print(f"Sources error: {e}", file=__import__("sys").stderr)
            return 1


class HealthCommand(BaseCommand):
    """Execute health command."""
    
    def execute(self, args: argparse.Namespace) -> int:
        """Execute health command."""
        try:
            health_info = self._get_health_info()
            response = self.formatter.format_health_response(health_info)
            print(response)
            return 0
            
        except Exception as e:
            print(f"Health error: {e}", file=__import__("sys").stderr)
            return 1
    
    def _get_health_info(self) -> Dict[str, Any]:
        """Gather system health information."""
        from clarity.config import ClarityConfig
        
        config = ClarityConfig()
        
        # Check dependencies
        deps = {}
        try:
            import docx
            deps["docx"] = "available"
        except ImportError:
            deps["docx"] = "missing"
        
        try:
            import PyPDF2
            deps["pdf"] = "available"
        except ImportError:
            deps["pdf"] = "missing"
        
        # Check boot doc
        boot_doc_status = "valid" if config.validate_boot_doc() else "invalid"
        boot_doc_path = config.boot_doc_path or "not set"
        
        return {
            "version": "4.0.0",
            "dependencies": deps,
            "boot_doc": {
                "path": boot_doc_path,
                "status": boot_doc_status
            },
            "limits": {
                "max_files": config.max_files,
                "max_matches": config.max_matches,
                "max_file_size": config.max_file_size_bytes
            },
            "allowlisted_roots": config.allowlisted_roots
        }
