
import argparse
import sys
from pathlib import Path
from typing import Optional

from clarity.search_toolkit import LocalSearchToolkit
from clarity.commands import SearchCommand, AskCommand, SourcesCommand, HealthCommand
from clarity.config import ClarityConfig


def create_parser() -> argparse.ArgumentParser:
    """Create main CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="clarity",
        description="Clarity OS T4 - Local Knowledge Search Assistant"
    )
    parser.add_argument("--version", action="version", version="Clarity OS T4 4.0.0")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # search command
    search_parser = subparsers.add_parser("search", help="Search across local files")
    search_parser.add_argument("--root", required=True, help="Root directory to search")
    search_parser.add_argument("--query", required=True, help="Search query")
    search_parser.add_argument("--globs", default="**/*.txt,**/*.md,**/*.py", 
                              help="File glob patterns (comma-separated)")
    search_parser.add_argument("--regex", action="store_true", help="Enable regex search")
    search_parser.add_argument("--case-sensitive", action="store_true", help="Case-sensitive search")
    search_parser.add_argument("--context", type=int, default=2, help="Context lines around matches")
    search_parser.add_argument("--max-files", type=int, default=5000, help="Maximum files to scan")
    search_parser.add_argument("--max-matches", type=int, default=2000, help="Maximum matches to return")
    
    # ask command
    ask_parser = subparsers.add_parser("ask", help="Search and summarize with citations")
    ask_parser.add_argument("--root", required=True, help="Root directory to search")
    ask_parser.add_argument("--question", required=True, help="Question to answer")
    ask_parser.add_argument("--globs", default="**/*.txt,**/*.md,**/*.py",
                           help="File glob patterns (comma-separated)")
    ask_parser.add_argument("--regex", action="store_true", help="Enable regex search")
    ask_parser.add_argument("--case-sensitive", action="store_true", help="Case-sensitive search")
    ask_parser.add_argument("--context", type=int, default=2, help="Context lines around matches")
    ask_parser.add_argument("--max-files", type=int, default=5000, help="Maximum files to scan")
    ask_parser.add_argument("--max-matches", type=int, default=2000, help="Maximum matches to return")
    
    # sources command
    sources_parser = subparsers.add_parser("sources", help="Show last coverage report")
    sources_parser.add_argument("--last", action="store_true", help="Show last search coverage")
    
    # health command
    health_parser = subparsers.add_parser("health", help="Check system health")
    
    return parser


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize config and validate boot doc
    config = ClarityConfig()
    is_valid, error_message = config.validate_boot_doc()
    if not is_valid:
        print(f"ERROR: {error_message}", file=sys.stderr)
        return 1
    
    # Initialize search toolkit
    toolkit = LocalSearchToolkit(config)
    
    try:
        if args.command == "search":
            cmd = SearchCommand(toolkit)
            return cmd.execute(args)
        elif args.command == "ask":
            cmd = AskCommand(toolkit)
            return cmd.execute(args)
        elif args.command == "sources":
            cmd = SourcesCommand(toolkit)
            return cmd.execute(args)
        elif args.command == "health":
            cmd = HealthCommand(toolkit)
            return cmd.execute(args)
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 1
            
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
