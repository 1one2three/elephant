"""Semantic Scholar API integration"""

import requests
from typing import List, Dict, Any, Optional
import time


class SemanticScholarClient:
    """Client for Semantic Scholar API"""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key: Optional[str] = None, author_id: Optional[str] = None):
        self.api_key = api_key
        self.author_id = author_id
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({'x-api-key': api_key})

    def search_author(self, author_name: str) -> Optional[Dict[str, Any]]:
        """Search for author by name"""
        url = f"{self.BASE_URL}/author/search"
        params = {'query': author_name, 'limit': 1}

        response = self.session.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            if data.get('data'):
                author = data['data'][0]
                return {
                    'author_id': author['authorId'],
                    'name': author['name'],
                    'paper_count': author.get('paperCount', 0),
                    'citation_count': author.get('citationCount', 0),
                    'h_index': author.get('hIndex', 0)
                }
        return None

    def get_author_papers(self, author_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all papers for an author"""
        aid = author_id or self.author_id

        if not aid:
            raise ValueError("Author ID required")

        url = f"{self.BASE_URL}/author/{aid}/papers"
        params = {
            'fields': 'paperId,title,year,citationCount,referenceCount,publicationDate,venue,externalIds,abstract,authors,url',
            'limit': limit
        }

        papers = []
        offset = 0

        while True:
            params['offset'] = offset
            response = self.session.get(url, params=params)

            if response.status_code == 429:  # Rate limited
                time.sleep(5)
                continue

            if response.status_code != 200:
                break

            data = response.json()
            batch = data.get('data', [])

            if not batch:
                break

            for paper in batch:
                external_ids = paper.get('externalIds', {})

                paper_data = {
                    'title': paper.get('title'),
                    'paper_id': paper.get('paperId'),
                    'doi': external_ids.get('DOI'),
                    'arxiv_id': external_ids.get('ArXiv'),
                    'year': paper.get('year'),
                    'venue': paper.get('venue'),
                    'citations': paper.get('citationCount', 0),
                    'references': paper.get('referenceCount', 0),
                    'abstract': paper.get('abstract'),
                    'url': paper.get('url'),
                    'publication_date': paper.get('publicationDate'),
                    'authors': [a['name'] for a in paper.get('authors', [])]
                }

                papers.append(paper_data)

            offset += len(batch)

            if len(batch) < limit or offset >= 1000:  # API limit
                break

            time.sleep(0.5)  # Be nice to the API

        return papers

    def get_paper_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """Get paper details by DOI"""
        url = f"{self.BASE_URL}/paper/DOI:{doi}"
        params = {
            'fields': 'paperId,title,year,citationCount,referenceCount,publicationDate,venue,externalIds,abstract,authors,url,citations,references'
        }

        response = self.session.get(url, params=params)

        if response.status_code == 200:
            paper = response.json()
            external_ids = paper.get('externalIds', {})

            return {
                'title': paper.get('title'),
                'paper_id': paper.get('paperId'),
                'doi': external_ids.get('DOI'),
                'arxiv_id': external_ids.get('ArXiv'),
                'year': paper.get('year'),
                'venue': paper.get('venue'),
                'citations': paper.get('citationCount', 0),
                'references': paper.get('referenceCount', 0),
                'abstract': paper.get('abstract'),
                'url': paper.get('url'),
                'publication_date': paper.get('publicationDate'),
                'authors': [a['name'] for a in paper.get('authors', [])],
                'citing_papers': paper.get('citations', [])[:10],  # Top 10 citing papers
                'referenced_papers': paper.get('references', [])[:10]  # Top 10 references
            }

        return None

    def get_paper_citations(self, paper_id: str) -> List[Dict[str, Any]]:
        """Get papers citing this paper"""
        url = f"{self.BASE_URL}/paper/{paper_id}/citations"
        params = {
            'fields': 'paperId,title,year,authors,venue',
            'limit': 100
        }

        response = self.session.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            return [
                {
                    'paper_id': cite['citingPaper']['paperId'],
                    'title': cite['citingPaper'].get('title'),
                    'year': cite['citingPaper'].get('year'),
                    'venue': cite['citingPaper'].get('venue'),
                    'authors': [a['name'] for a in cite['citingPaper'].get('authors', [])]
                }
                for cite in data.get('data', [])
            ]

        return []
