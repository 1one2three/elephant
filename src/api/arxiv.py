"""arXiv API integration"""

import arxiv
from typing import List, Dict, Any, Optional


class ArXivClient:
    """Client for arXiv API"""

    def __init__(self, author_id: Optional[str] = None, author_name: Optional[str] = None):
        self.author_id = author_id
        self.author_name = author_name
        self.client = arxiv.Client()

    def search_by_author(self, author_name: Optional[str] = None, max_results: int = 100) -> List[Dict[str, Any]]:
        """Search arXiv papers by author name"""
        search_name = author_name or self.author_name

        if not search_name:
            raise ValueError("Author name required")

        search = arxiv.Search(
            query=f'au:"{search_name}"',
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )

        papers = []
        for result in self.client.results(search):
            paper = {
                'title': result.title,
                'arxiv_id': result.entry_id.split('/abs/')[-1],
                'doi': result.doi,
                'year': result.published.year,
                'abstract': result.summary,
                'authors': [author.name for author in result.authors],
                'url': result.entry_id,
                'categories': result.categories,
                'primary_category': result.primary_category,
                'published': result.published.isoformat(),
                'updated': result.updated.isoformat() if result.updated else None
            }
            papers.append(paper)

        return papers

    def get_paper_by_id(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific paper by arXiv ID"""
        search = arxiv.Search(id_list=[arxiv_id])

        try:
            result = next(self.client.results(search))
            return {
                'title': result.title,
                'arxiv_id': arxiv_id,
                'doi': result.doi,
                'year': result.published.year,
                'abstract': result.summary,
                'authors': [author.name for author in result.authors],
                'url': result.entry_id,
                'categories': result.categories,
                'primary_category': result.primary_category,
                'published': result.published.isoformat(),
                'updated': result.updated.isoformat() if result.updated else None
            }
        except StopIteration:
            return None
