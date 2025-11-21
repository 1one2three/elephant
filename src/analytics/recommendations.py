"""Recommendation engine for citation improvement"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from src.db.database import Database
from src.core.config import Config
from src.analytics.metrics import MetricsCalculator


class RecommendationEngine:
    """Generate recommendations to boost citations"""

    def __init__(self, config: Config, db: Database):
        self.config = config
        self.db = db
        self.metrics = MetricsCalculator(db)

    def generate_recommendations(self, limit: int = 5, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []

        # Different categories of recommendations
        if not category or category == 'visibility':
            recommendations.extend(self._visibility_recommendations())

        if not category or category == 'collaboration':
            recommendations.extend(self._collaboration_recommendations())

        if not category or category == 'trending':
            recommendations.extend(self._trending_recommendations())

        if not category or category == 'profile':
            recommendations.extend(self._profile_recommendations())

        # Sort by priority and limit
        recommendations.sort(key=lambda x: self._priority_score(x), reverse=True)

        return recommendations[:limit]

    def _visibility_recommendations(self) -> List[Dict[str, Any]]:
        """Recommendations to increase paper visibility"""
        recommendations = []

        # Find low-visibility papers
        low_vis_papers = self.metrics.identify_low_visibility_papers(threshold=5)

        if low_vis_papers:
            top_paper = low_vis_papers[0]
            recommendations.append({
                'category': 'visibility',
                'priority': 'high',
                'title': 'Promote under-cited paper',
                'description': f'Your paper "{top_paper["title"][:50]}..." has only {top_paper["citations"]} citations after {top_paper["age"]} years. Consider promoting it.',
                'impact': 'High - Can significantly increase citations',
                'effort': 'Medium - Requires targeted outreach',
                'action': f'Share on ResearchGate, Academia.edu, and relevant social media. Contact researchers in the field. Present at conferences.',
                'data': {'paper': top_paper}
            })

        # Check for papers without DOIs
        papers = self.db.get_papers_with_latest_citations()
        no_doi = [p for p in papers if not p.get('doi')]

        if no_doi:
            recommendations.append({
                'category': 'visibility',
                'priority': 'medium',
                'title': 'Add DOIs to papers',
                'description': f'{len(no_doi)} papers are missing DOIs, reducing discoverability.',
                'impact': 'Medium - Improves findability',
                'effort': 'Low - Administrative task',
                'action': 'Register DOIs for papers without them. Contact publishers or use services like Zenodo for preprints.',
                'data': {'count': len(no_doi)}
            })

        return recommendations

    def _collaboration_recommendations(self) -> List[Dict[str, Any]]:
        """Recommendations for collaborations"""
        recommendations = []

        # Analyze co-author patterns
        papers = self.db.get_papers_with_latest_citations()

        # Simple analysis: papers with more co-authors tend to get more citations
        solo_papers = []
        for paper in papers:
            if paper.get('authors'):
                import json
                try:
                    authors = json.loads(paper['authors'])
                    if len(authors) <= 2:
                        solo_papers.append(paper)
                except:
                    pass

        if len(solo_papers) > len(papers) * 0.3:  # More than 30% solo/duo papers
            recommendations.append({
                'category': 'collaboration',
                'priority': 'high',
                'title': 'Increase collaboration',
                'description': f'{len(solo_papers)} papers have minimal co-authors. Collaborative papers typically receive more citations.',
                'impact': 'High - Collaborative papers get 2-3x more citations',
                'effort': 'High - Requires networking',
                'action': 'Reach out to researchers in your field. Join research groups. Attend conferences and workshops. Use platforms like ResearchGate to connect.',
                'data': {'solo_count': len(solo_papers)}
            })

        return recommendations

    def _trending_recommendations(self) -> List[Dict[str, Any]]:
        """Recommendations based on trending topics"""
        recommendations = []

        # This would ideally connect to external APIs to find trending topics
        # For now, providing generic advice

        recommendations.append({
            'category': 'trending',
            'priority': 'medium',
            'title': 'Align with current trends',
            'description': 'Publishing in trending research areas can increase visibility and citations.',
            'impact': 'Medium to High - Trending topics attract more attention',
            'effort': 'High - Requires new research direction',
            'action': 'Monitor arXiv, Google Scholar alerts, and conference proceedings for emerging topics. Consider interdisciplinary work.',
            'data': {}
        })

        return recommendations

    def _profile_recommendations(self) -> List[Dict[str, Any]]:
        """Recommendations for profile improvement"""
        recommendations = []

        # Check profile completeness
        platforms = self.config.platforms

        inactive_platforms = [
            name for name, config in platforms.items()
            if not config.enabled
        ]

        if inactive_platforms:
            recommendations.append({
                'category': 'profile',
                'priority': 'medium',
                'title': 'Activate more platforms',
                'description': f'You have {len(inactive_platforms)} inactive platforms. More presence increases discoverability.',
                'impact': 'Medium - Broader reach',
                'effort': 'Low - Profile setup',
                'action': f'Set up profiles on: {", ".join(inactive_platforms)}. Keep them updated with your latest work.',
                'data': {'platforms': inactive_platforms}
            })

        # Check for recent updates
        sync_status = self.db.conn.execute('SELECT * FROM sync_status ORDER BY last_sync DESC').fetchall()

        if sync_status:
            oldest_sync = min(sync_status, key=lambda x: x['last_sync'] if x['last_sync'] else '')
            # Check if oldest sync is more than 7 days old
            # This is a simplified check

            recommendations.append({
                'category': 'profile',
                'priority': 'low',
                'title': 'Regular updates',
                'description': 'Regularly update your profiles and citation data.',
                'impact': 'Low - Maintenance',
                'effort': 'Low - Automated with this tool',
                'action': 'Run "citation-mind fetch --all" weekly. Set up automated alerts.',
                'data': {}
            })

        return recommendations

    def _priority_score(self, recommendation: Dict[str, Any]) -> float:
        """Calculate priority score for sorting"""
        priority_map = {'high': 3.0, 'medium': 2.0, 'low': 1.0}
        return priority_map.get(recommendation['priority'], 0.0)

    def get_actionable_insights(self) -> Dict[str, Any]:
        """Get quick actionable insights"""
        papers = self.db.get_papers_with_latest_citations()

        insights = {
            'total_papers': len(papers),
            'total_citations': sum(p['citations'] for p in papers),
            'h_index': self.metrics.calculate_h_index([p['citations'] for p in papers]),
            'top_paper': max(papers, key=lambda x: x['citations'])['title'] if papers else None,
            'avg_citations': sum(p['citations'] for p in papers) / len(papers) if papers else 0,
            'low_visibility_count': len(self.metrics.identify_low_visibility_papers()),
        }

        return insights
