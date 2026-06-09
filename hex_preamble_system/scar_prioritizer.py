"""
Scar Prioritizer - Tags and prioritizes scars for inclusion in the hex preamble.

Scars are issues/problems that have been documented. This system:
1. Tags scars as critical, warning, or resolved
2. Filters scars relevant to the current problem
3. Prioritizes which scars to include in the preamble
"""

from typing import List, Dict, Optional, Literal
from enum import Enum
from datetime import datetime


class ScarSeverity(Enum):
    """Severity levels for scars."""
    CRITICAL = "critical"  # Blocks work, must be addressed
    WARNING = "warning"    # Impacts work, should be addressed
    RESOLVED = "resolved"  # Already fixed, for reference
    INFO = "info"          # Informational, low priority


class ScarPrioritizer:
    """Prioritize and filter scars for the hex preamble."""
    
    # Severity rankings (higher = more important)
    SEVERITY_RANK = {
        ScarSeverity.CRITICAL: 4,
        ScarSeverity.WARNING: 3,
        ScarSeverity.INFO: 2,
        ScarSeverity.RESOLVED: 1,
    }
    
    @staticmethod
    def tag_scar(
        scar: Dict,
        severity: ScarSeverity = ScarSeverity.WARNING
    ) -> Dict:
        """
        Tag a scar with severity and metadata.
        
        Args:
            scar: The scar object
            severity: Severity level
        
        Returns:
            Tagged scar object
        """
        tagged = scar.copy()
        tagged['severity'] = severity.value
        tagged['severity_rank'] = ScarPrioritizer.SEVERITY_RANK[severity]
        tagged['tagged_at'] = datetime.now().isoformat()
        
        return tagged
    
    @staticmethod
    def filter_by_severity(
        scars: List[Dict],
        min_severity: ScarSeverity = ScarSeverity.WARNING
    ) -> List[Dict]:
        """
        Filter scars by minimum severity level.
        
        Args:
            scars: List of scars
            min_severity: Minimum severity to include
        
        Returns:
            Filtered scars
        """
        min_rank = ScarPrioritizer.SEVERITY_RANK[min_severity]
        
        return [
            s for s in scars
            if ScarPrioritizer.SEVERITY_RANK.get(
                ScarSeverity(s.get('severity', 'info')),
                0
            ) >= min_rank
        ]
    
    @staticmethod
    def filter_by_problem(
        scars: List[Dict],
        problem_keywords: List[str]
    ) -> List[Dict]:
        """
        Filter scars relevant to the current problem.
        
        Args:
            scars: List of scars
            problem_keywords: Keywords from the problem statement
        
        Returns:
            Filtered scars
        """
        relevant_scars = []
        
        for scar in scars:
            scar_text = (
                scar.get('title', '') + ' ' +
                scar.get('description', '') + ' ' +
                scar.get('tags', '')
            ).lower()
            
            # Check if any keyword matches
            for keyword in problem_keywords:
                if keyword.lower() in scar_text:
                    relevant_scars.append(scar)
                    break
        
        return relevant_scars
    
    @staticmethod
    def prioritize_scars(
        scars: List[Dict],
        problem_keywords: Optional[List[str]] = None,
        max_scars: int = 10
    ) -> List[Dict]:
        """
        Prioritize scars for inclusion in the preamble.
        
        Args:
            scars: List of scars
            problem_keywords: Optional keywords to filter by
            max_scars: Maximum number of scars to return
        
        Returns:
            Prioritized scars
        """
        # Filter by problem keywords if provided
        if problem_keywords:
            scars = ScarPrioritizer.filter_by_problem(scars, problem_keywords)
        
        # Filter out resolved scars (unless critical)
        active_scars = [
            s for s in scars
            if s.get('severity') != ScarSeverity.RESOLVED.value
        ]
        
        # Sort by severity rank (descending) and recency
        active_scars.sort(
            key=lambda s: (
                -ScarPrioritizer.SEVERITY_RANK.get(
                    ScarSeverity(s.get('severity', 'info')),
                    0
                ),
                s.get('updated_at', ''),  # Most recent first
            ),
            reverse=True
        )
        
        return active_scars[:max_scars]
    
    @staticmethod
    def get_active_scars(
        all_scars: List[Dict],
        problem_keywords: Optional[List[str]] = None,
        include_resolved: bool = False,
        max_scars: int = 5
    ) -> List[Dict]:
        """
        Get active scars for the current context.
        
        Args:
            all_scars: All available scars
            problem_keywords: Optional keywords to filter by
            include_resolved: Whether to include resolved scars
            max_scars: Maximum number of scars to return
        
        Returns:
            Active scars for this context
        """
        # Filter by problem keywords if provided
        if problem_keywords:
            scars = ScarPrioritizer.filter_by_problem(all_scars, problem_keywords)
        else:
            scars = all_scars
        
        # Filter by severity (exclude resolved unless requested)
        if not include_resolved:
            scars = ScarPrioritizer.filter_by_severity(
                scars, ScarSeverity.WARNING
            )
        
        # Sort by severity and recency
        scars.sort(
            key=lambda s: (
                -ScarPrioritizer.SEVERITY_RANK.get(
                    ScarSeverity(s.get('severity', 'info')),
                    0
                ),
                s.get('updated_at', ''),
            ),
            reverse=True
        )
        
        return scars[:max_scars]
    
    @staticmethod
    def classify_scar(scar: Dict) -> ScarSeverity:
        """
        Automatically classify a scar's severity based on its content.
        
        Args:
            scar: The scar object
        
        Returns:
            Classified severity level
        """
        title = scar.get('title', '').lower()
        description = scar.get('description', '').lower()
        tags = scar.get('tags', '').lower()
        
        text = f"{title} {description} {tags}"
        
        # Critical keywords
        if any(word in text for word in ['blocks', 'broken', 'crash', 'fail', 'critical']):
            return ScarSeverity.CRITICAL
        
        # Warning keywords
        if any(word in text for word in ['error', 'bug', 'issue', 'problem', 'warning']):
            return ScarSeverity.WARNING
        
        # Resolved keywords
        if any(word in text for word in ['fixed', 'resolved', 'closed', 'done']):
            return ScarSeverity.RESOLVED
        
        # Default to info
        return ScarSeverity.INFO
    
    @staticmethod
    def summarize_scars(scars: List[Dict]) -> Dict:
        """
        Generate a summary of scar status.
        
        Args:
            scars: List of scars
        
        Returns:
            Summary dictionary
        """
        summary = {
            'total': len(scars),
            'critical': 0,
            'warning': 0,
            'resolved': 0,
            'info': 0,
        }
        
        for scar in scars:
            severity = scar.get('severity', 'info')
            if severity in summary:
                summary[severity] += 1
        
        return summary


# Example usage
if __name__ == '__main__':
    # Example scars
    example_scars = [
        {
            'title': 'Build error in simulation.ts',
            'description': 'TypeScript import error blocking production build',
            'tags': 'typescript,build,critical',
            'updated_at': '2026-06-09T10:00:00Z'
        },
        {
            'title': 'StateOfSystem hardcoded values',
            'description': 'Component uses hardcoded metrics instead of tRPC data',
            'tags': 'component,data,warning',
            'updated_at': '2026-06-09T09:30:00Z'
        },
        {
            'title': 'MobileMenuButton unused',
            'description': 'Component no longer used after GlobalNav integration',
            'tags': 'cleanup,resolved',
            'updated_at': '2026-06-08T15:00:00Z'
        },
    ]
    
    # Test auto-classification
    print("Auto-classified scars:")
    for scar in example_scars:
        severity = ScarPrioritizer.classify_scar(scar)
        print(f"  {scar['title']}: {severity.value}")
    
    # Test prioritization
    print("\nPrioritized scars (max 2):")
    prioritized = ScarPrioritizer.prioritize_scars(example_scars, max_scars=2)
    for scar in prioritized:
        print(f"  {scar['title']}")
    
    # Test summary
    print("\nScar summary:")
    summary = ScarPrioritizer.summarize_scars(example_scars)
    print(f"  {summary}")
