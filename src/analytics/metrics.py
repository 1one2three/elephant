"""Metrics calculation for citations"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from src.db.database import Database


class MetricsCalculator:
    """Calculate citation metrics and statistics"""

    def __init__(self, db: Database):
        self.db = db

    def calculate_h_index(self, citation_counts: List[int]) -> int:
        """Calculate h-index from list of citation counts"""
        if not citation_counts:
            return 0

        sorted_citations = sorted(citation_counts, reverse=True)

        h_index = 0
        for i, citations in enumerate(sorted_citations, 1):
            if citations >= i:
                h_index = i
            else:
                break

        return h_index

    def get_summary_stats(self, period: str = 'all') -> Dict[str, Any]:
        """Get summary statistics for a time period"""
        papers = self.db.get_papers_with_latest_citations()

        # Calculate current stats
        total_papers = len(papers)
        total_citations = sum(p['citations'] for p in papers)
        citation_counts = [p['citations'] for p in papers]
        h_index = self.calculate_h_index(citation_counts)
        avg_citations = total_citations / total_papers if total_papers > 0 else 0

        stats = {
            'total_papers': total_papers,
            'total_citations': total_citations,
            'h_index': h_index,
            'avg_citations': avg_citations,
            'papers_change': 0,
            'citations_change': 0,
            'h_index_change': 0
        }

        # Calculate changes based on period
        # This would require historical data comparison
        # For now, returning 0 for changes

        return stats

    def get_top_papers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top cited papers"""
        papers = self.db.get_papers_with_latest_citations()

        top_papers = sorted(papers, key=lambda x: x['citations'], reverse=True)[:limit]

        return [
            {
                'title': p['title'],
                'citations': p['citations'],
                'year': p['year'],
                'doi': p.get('doi'),
                'venue': p.get('venue')
            }
            for p in top_papers
        ]

    def get_paper_stats(self, identifier: str) -> Dict[str, Any]:
        """Get detailed statistics for a specific paper"""
        # Find paper by DOI or arXiv ID
        self.db.connect()

        cursor = self.db.conn.execute(
            'SELECT * FROM papers WHERE doi = ? OR arxiv_id = ?',
            (identifier, identifier)
        )

        paper = cursor.fetchone()

        if not paper:
            raise Exception(f"Paper not found: {identifier}")

        paper_id = paper['id']

        # Get citation history
        history = self.db.get_citation_history(paper_id, days=365)

        # Calculate growth metrics
        citations_7d = 0
        citations_30d = 0
        citations_1y = 0

        now = datetime.now()

        for record in history:
            record_date = datetime.fromisoformat(record['timestamp'])
            days_ago = (now - record_date).days

            if days_ago <= 7:
                citations_7d = max(citations_7d, record['citation_count'])
            if days_ago <= 30:
                citations_30d = max(citations_30d, record['citation_count'])
            if days_ago <= 365:
                citations_1y = max(citations_1y, record['citation_count'])

        # Get latest citation count
        latest_cursor = self.db.conn.execute(
            'SELECT MAX(citation_count) as citations FROM citations WHERE paper_id = ?',
            (paper_id,)
        )
        latest = latest_cursor.fetchone()
        current_citations = latest['citations'] if latest and latest['citations'] else 0

        return {
            'title': paper['title'],
            'doi': paper['doi'],
            'arxiv_id': paper['arxiv_id'],
            'year': paper['year'],
            'venue': paper['venue'],
            'citations': current_citations,
            'citations_7d': current_citations - citations_7d if citations_7d else 0,
            'citations_30d': current_citations - citations_30d if citations_30d else 0,
            'citations_1y': current_citations - citations_1y if citations_1y else 0
        }

    def get_citation_trends(self) -> Dict[str, Any]:
        """Get citation trends over time"""
        papers = self.db.get_papers_with_latest_citations()

        # Group by year
        by_year = {}
        for paper in papers:
            year = paper.get('year')
            if year:
                if year not in by_year:
                    by_year[year] = {'papers': 0, 'citations': 0}
                by_year[year]['papers'] += 1
                by_year[year]['citations'] += paper['citations']

        return {
            'by_year': by_year,
            'total_papers': len(papers),
            'total_citations': sum(p['citations'] for p in papers)
        }

    def identify_low_visibility_papers(self, threshold: int = 5) -> List[Dict[str, Any]]:
        """Identify papers with low citation counts that might need promotion"""
        papers = self.db.get_papers_with_latest_citations()

        low_visibility = []

        for paper in papers:
            # Papers older than 1 year with few citations
            if paper.get('year'):
                age = datetime.now().year - paper['year']
                if age >= 1 and paper['citations'] < threshold:
                    low_visibility.append({
                        'title': paper['title'],
                        'year': paper['year'],
                        'citations': paper['citations'],
                        'age': age,
                        'doi': paper.get('doi'),
                        'potential': self._estimate_potential(paper)
                    })

        # Sort by potential impact
        low_visibility.sort(key=lambda x: x['potential'], reverse=True)

        return low_visibility

    def _estimate_potential(self, paper: Dict[str, Any]) -> float:
        """Estimate the potential impact of a paper for promotion"""
        # Simple heuristic: papers in good venues with some citations
        # but not enough have high potential

        score = 0.0

        # Venue quality (simplified)
        venue = paper.get('venue', '').lower()
        if any(term in venue for term in ['nature', 'science', 'cell', 'lancet', 'pnas']):
            score += 10.0
        elif any(term in venue for term in ['ieee', 'acm', 'springer']):
            score += 5.0

        # Recent papers have more potential
        if paper.get('year'):
            age = datetime.now().year - paper['year']
            if age < 3:
                score += (3 - age) * 2.0

        # Some citations indicate interest
        citations = paper.get('citations', 0)
        if citations > 0:
            score += min(citations, 10) * 0.5

        return score
