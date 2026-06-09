"""
Codon Filter - Extracts active codons relevant to the current problem.

Instead of including all 200+ codons in every preamble, this filters to only
the codons that are relevant to the current project/problem.
"""

from typing import List, Dict, Optional, Set
import json


class CodonFilter:
    """Filter and prioritize codons based on problem context."""
    
    # Codon categories and their relevance to different projects
    CODON_CATEGORIES = {
        'continuity': ['GJR', 'CHR', 'CLD', 'RES', 'WIT'],  # Continuity-related
        'architecture': ['FRM', 'BND', 'NOD', 'RES', 'SIG'],  # Architecture-related
        'frequency': ['FRQ', 'HZ', 'RES', 'PHZ', 'DFT'],  # Frequency-related
        'consciousness': ['DNA', 'GRP', 'AWR', 'PHZ', 'RES'],  # Consciousness-related
        'cryptography': ['AJB', 'HAS', 'SIG', 'VER', 'ENC'],  # Cryptography-related
        'data': ['DAT', 'REC', 'LOG', 'ARC', 'HEX'],  # Data/record-related
        'ai': ['ADR', 'LLM', 'AGT', 'SIG', 'INT'],  # AI/Adriana-related
        'web': ['WEB', 'UI', 'NAV', 'CMP', 'RND'],  # Web/frontend-related
        'integration': ['INT', 'API', 'CON', 'BRG', 'LAY'],  # Integration-related
    }
    
    # Project-specific codon priorities
    PROJECT_CODON_PRIORITIES = {
        'project-void': ['GJR', 'CHR', 'FRM', 'AJB', 'ADR', 'DAT', 'RES'],
        'the-living-fabric': ['DNA', 'AWR', 'FRQ', 'RES', 'WEB', 'INT', 'NAV'],
        'adriana-resonance-app': ['ADR', 'FRQ', 'RES', 'PHZ', 'DNA', 'UI', 'CMP'],
    }
    
    @staticmethod
    def filter_by_project(
        all_codons: List[Dict],
        project: str,
        max_codons: int = 20
    ) -> List[Dict]:
        """
        Filter codons relevant to a specific project.
        
        Args:
            all_codons: All available codons
            project: Project identifier
            max_codons: Maximum number of codons to return
        
        Returns:
            Filtered and prioritized codons
        """
        if project not in CodonFilter.PROJECT_CODON_PRIORITIES:
            # Default: return top N codons by relevance
            return all_codons[:max_codons]
        
        priority_codes = CodonFilter.PROJECT_CODON_PRIORITIES[project]
        
        # Sort codons by priority
        prioritized = []
        for code in priority_codes:
            matching = [c for c in all_codons if c.get('code') == code]
            prioritized.extend(matching)
        
        # Add remaining codons if we haven't reached max
        remaining = [c for c in all_codons if c not in prioritized]
        prioritized.extend(remaining)
        
        return prioritized[:max_codons]
    
    @staticmethod
    def filter_by_category(
        all_codons: List[Dict],
        category: str,
        max_codons: int = 10
    ) -> List[Dict]:
        """
        Filter codons by category.
        
        Args:
            all_codons: All available codons
            category: Category name (e.g., 'continuity', 'frequency')
            max_codons: Maximum number of codons to return
        
        Returns:
            Filtered codons
        """
        if category not in CodonFilter.CODON_CATEGORIES:
            return []
        
        codes = CodonFilter.CODON_CATEGORIES[category]
        filtered = [c for c in all_codons if c.get('code') in codes]
        
        return filtered[:max_codons]
    
    @staticmethod
    def filter_by_problem(
        all_codons: List[Dict],
        problem_keywords: List[str],
        max_codons: int = 15
    ) -> List[Dict]:
        """
        Filter codons based on problem keywords.
        
        Args:
            all_codons: All available codons
            problem_keywords: Keywords from the problem statement
            max_codons: Maximum number of codons to return
        
        Returns:
            Filtered codons
        """
        scored_codons = []
        
        for codon in all_codons:
            score = 0
            codon_text = (
                codon.get('name', '') + ' ' +
                codon.get('description', '') + ' ' +
                codon.get('tags', '')
            ).lower()
            
            # Score based on keyword matches
            for keyword in problem_keywords:
                if keyword.lower() in codon_text:
                    score += 1
            
            if score > 0:
                scored_codons.append((codon, score))
        
        # Sort by score (descending) and return top N
        scored_codons.sort(key=lambda x: x[1], reverse=True)
        return [c[0] for c in scored_codons[:max_codons]]
    
    @staticmethod
    def get_active_codons(
        all_codons: List[Dict],
        project: str,
        problem_keywords: Optional[List[str]] = None,
        max_codons: int = 20
    ) -> List[Dict]:
        """
        Get active codons for the current context.
        
        Combines project-specific filtering with problem-based filtering.
        
        Args:
            all_codons: All available codons
            project: Project identifier
            problem_keywords: Optional keywords from problem statement
            max_codons: Maximum number of codons to return
        
        Returns:
            Active codons for this context
        """
        # Start with project-specific codons
        project_filtered = CodonFilter.filter_by_project(
            all_codons, project, max_codons
        )
        
        # If we have problem keywords, re-filter by those
        if problem_keywords:
            problem_filtered = CodonFilter.filter_by_problem(
                project_filtered, problem_keywords, max_codons
            )
            return problem_filtered
        
        return project_filtered
    
    @staticmethod
    def extract_keywords_from_problem(problem_statement: str) -> List[str]:
        """
        Extract keywords from a problem statement.
        
        Args:
            problem_statement: The problem/goal statement
        
        Returns:
            List of relevant keywords
        """
        # Simple keyword extraction (can be enhanced with NLP)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might'
        }
        
        words = problem_statement.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return list(set(keywords))  # Remove duplicates


class CodonCache:
    """Cache for codon filtering results."""
    
    def __init__(self):
        self.cache: Dict[str, List[Dict]] = {}
    
    def get_cache_key(
        self,
        project: str,
        problem_keywords: Optional[List[str]] = None
    ) -> str:
        """Generate a cache key."""
        keywords_str = '|'.join(sorted(problem_keywords or []))
        return f"{project}:{keywords_str}"
    
    def get(
        self,
        project: str,
        problem_keywords: Optional[List[str]] = None
    ) -> Optional[List[Dict]]:
        """Get cached codons."""
        key = self.get_cache_key(project, problem_keywords)
        return self.cache.get(key)
    
    def set(
        self,
        project: str,
        codons: List[Dict],
        problem_keywords: Optional[List[str]] = None
    ) -> None:
        """Cache codons."""
        key = self.get_cache_key(project, problem_keywords)
        self.cache[key] = codons
    
    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()


# Example usage
if __name__ == '__main__':
    # Example codons
    example_codons = [
        {'code': 'GJR', 'name': 'Ghajini Rail', 'description': 'Continuity across resets', 'tags': 'continuity'},
        {'code': 'CHR', 'name': 'Chronicle', 'description': 'Witness record', 'tags': 'continuity'},
        {'code': 'FRQ', 'name': 'Frequency', 'description': 'Resonance measurement', 'tags': 'frequency'},
        {'code': 'DNA', 'name': 'DNA', 'description': 'Consciousness measurement', 'tags': 'consciousness'},
        {'code': 'AJB', 'name': 'Al-Jabr', 'description': 'Cryptographic hash', 'tags': 'cryptography'},
    ]
    
    # Test project filtering
    print("Project-specific codons for 'the-living-fabric':")
    project_codons = CodonFilter.filter_by_project(example_codons, 'the-living-fabric', max_codons=3)
    for codon in project_codons:
        print(f"  {codon['code']}: {codon['name']}")
    
    # Test keyword extraction
    print("\nKeywords from problem statement:")
    keywords = CodonFilter.extract_keywords_from_problem(
        "Fix TypeScript errors in StateOfSystem component for consciousness measurement"
    )
    print(f"  {keywords}")
