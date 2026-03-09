
from typing import List, Dict, Any, Optional
from datetime import datetime

from clarity.persistence import CoverageReport
from clarity.search_toolkit import SearchResult


class ResponseFormatter:
    """Formats responses with structured output."""
    
    def format_search_response(self, query: str, matches: List[SearchResult], 
                             coverage: CoverageReport, truncated: bool) -> str:
        """Format search response with citations and coverage."""
        
        response_parts = []
        
        # Header
        response_parts.append(f"## Search Results")
        response_parts.append(f"**Query:** {query}")
        response_parts.append(f"**Found:** {len(matches)} matches")
        if truncated:
            response_parts.append(f"**Warning:** Results truncated due to limits")
        response_parts.append("")
        
        # Matches section
        if matches:
            response_parts.append("### Matches")
            for i, match in enumerate(matches, 1):
                response_parts.append(f"**{i}.** `{match.file_path}:{match.location}`")
                response_parts.append("```")
                response_parts.append(match.snippet.rstrip())
                response_parts.append("```")
                response_parts.append("")
        else:
            response_parts.append("### No matches found")
            response_parts.append("")
        
        # Coverage section
        coverage_section = self._format_coverage_section(coverage)
        response_parts.append(coverage_section)
        
        # Confidence section
        confidence = self._calculate_confidence(matches, coverage)
        response_parts.append(f"### Confidence: {confidence['level']}")
        response_parts.append(f"{confidence['reason']}")
        
        return "\n".join(response_parts)
    
    def format_ask_response(self, question: str, matches: List[SearchResult],
                           coverage: CoverageReport, truncated: bool) -> str:
        """Format ask response with answer, citations, and coverage."""
        
        response_parts = []
        
        # Generate answer
        answer = self._generate_answer(question, matches)
        
        # Header
        response_parts.append(f"## Answer")
        response_parts.append(answer)
        response_parts.append("")
        
        # Citations section
        if matches:
            response_parts.append("### Citations")
            for i, match in enumerate(matches, 1):
                response_parts.append(f"**{i}.** `{match.file_path}:{match.location}`")
                response_parts.append("```")
                response_parts.append(match.snippet.rstrip())
                response_parts.append("```")
                response_parts.append("")
        else:
            response_parts.append("### No sources found")
            response_parts.append("")
        
        # Coverage section
        coverage_section = self._format_coverage_section(coverage)
        response_parts.append(coverage_section)
        
        # Confidence section
        confidence = self._calculate_confidence(matches, coverage)
        response_parts.append(f"### Confidence: {confidence['level']}")
        response_parts.append(f"{confidence['reason']}")
        
        return "\n".join(response_parts)
    
    def format_sources_response(self, coverage: CoverageReport) -> str:
        """Format sources/coverage response."""
        response_parts = []
        response_parts.append("## Last Search Coverage")
        response_parts.append("")
        
        coverage_section = self._format_coverage_section(coverage)
        response_parts.append(coverage_section)
        
        return "\n".join(response_parts)
    
    def format_health_response(self, health_info: Dict[str, Any]) -> str:
        """Format health check response."""
        response_parts = []
        response_parts.append("## Clarity OS T4 Health Check")
        response_parts.append("")
        
        # Version
        response_parts.append(f"**Version:** {health_info['version']}")
        response_parts.append("")
        
        # Dependencies
        response_parts.append("### Dependencies")
        for dep, status in health_info["dependencies"].items():
            status_icon = "✅" if status == "available" else "❌"
            response_parts.append(f"- **{dep}:** {status_icon} {status}")
        response_parts.append("")
        
        # Boot doc
        boot_doc = health_info["boot_doc"]
        boot_icon = "✅" if boot_doc["status"] == "valid" else "❌"
        response_parts.append(f"### Boot Document")
        response_parts.append(f"- **Path:** {boot_doc['path']}")
        response_parts.append(f"- **Status:** {boot_icon} {boot_doc['status']}")
        response_parts.append("")
        
        # Limits
        response_parts.append("### Safety Limits")
        limits = health_info["limits"]
        response_parts.append(f"- **Max Files:** {limits['max_files']:,}")
        response_parts.append(f"- **Max Matches:** {limits['max_matches']:,}")
        response_parts.append(f"- **Max File Size:** {limits['max_file_size']:,} bytes")
        response_parts.append("")
        
        # Allowlisted roots
        roots = health_info["allowlisted_roots"]
        if roots:
            response_parts.append("### Allowlisted Roots")
            for root in roots:
                response_parts.append(f"- `{root}`")
        else:
            response_parts.append("### Allowlisted Roots: None (all roots allowed)")
        
        return "\n".join(response_parts)
    
    def _format_coverage_section(self, coverage: CoverageReport) -> str:
        """Format coverage report section."""
        parts = []
        parts.append("### Coverage Report")
        
        # Search scope
        parts.append("**Search Scope:**")
        for root in coverage.roots:
            parts.append(f"- Root: `{root}`")
        for glob in coverage.globs:
            parts.append(f"- Pattern: `{glob}`")
        
        # Statistics
        parts.append(f"**Statistics:**")
        parts.append(f"- Files scanned: {coverage.scanned_files:,}")
        parts.append(f"- Files with matches: {coverage.matched_files:,}")
        
        # Limits applied
        if coverage.limits_applied:
            parts.append("**Limits Applied:**")
            for limit, value in coverage.limits_applied.items():
                parts.append(f"- {limit}: {value}")
        
        # Skipped files
        if coverage.skipped_files:
            parts.append(f"**Skipped Files:** ({len(coverage.skipped_files)} total)")
            # Show first 10 skipped files
            for skipped in coverage.skipped_files[:10]:
                parts.append(f"- {skipped}")
            if len(coverage.skipped_files) > 10:
                parts.append(f"- ... and {len(coverage.skipped_files) - 10} more")
        
        # Errors
        if coverage.errors:
            parts.append(f"**Errors:** ({len(coverage.errors)} total)")
            for error in coverage.errors:
                parts.append(f"- {error}")
        
        return "\n".join(parts)
    
    def _calculate_confidence(self, matches: List[SearchResult], coverage: CoverageReport) -> Dict[str, str]:
        """Calculate confidence level and reasoning."""
        if not matches:
            return {
                "level": "low",
                "reason": "No matches found for the query"
            }
        
        match_density = coverage.matched_files / max(coverage.scanned_files, 1)
        total_matches = len(matches)
        
        if total_matches >= 10 and match_density >= 0.1:
            return {
                "level": "high",
                "reason": f"Found {total_matches} matches across {coverage.matched_files} files"
            }
        elif total_matches >= 3 and match_density >= 0.05:
            return {
                "level": "medium",
                "reason": f"Found {total_matches} matches across {coverage.matched_files} files"
            }
        else:
            return {
                "level": "low",
                "reason": f"Only {total_matches} matches found, results may be limited"
            }
    
    def _generate_answer(self, question: str, matches: List[SearchResult]) -> str:
        """Generate concise answer based on search matches."""
        if not matches:
            return f"No information found to answer: {question}"
        
        # Simple answer generation - in a real implementation, this would use LLM
        # For T4, we provide a basic summarization
        unique_files = len(set(match.file_path for match in matches))
        total_matches = len(matches)
        
        answer = f"Found {total_matches} relevant matches across {unique_files} file"
        if unique_files != 1:
            answer += "s"
        
        # Extract key information from first few matches
        if matches:
            answer += ". Key information includes:"
            for i, match in enumerate(matches[:3]):
                # Extract first line of snippet as key point
                first_line = match.snippet.split('\n')[0].strip()
                if first_line:
                    answer += f"\n- {first_line}"
        
        return answer
