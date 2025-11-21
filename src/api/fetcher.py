"""Data fetcher orchestrator"""

from typing import Dict, Any, List, Optional
from src.api.orcid import ORCIDClient
from src.api.arxiv import ArXivClient
from src.api.semantic_scholar import SemanticScholarClient
from src.db.database import Database
from src.core.config import Config


class DataFetcher:
    """Orchestrates data fetching from multiple platforms"""

    def __init__(self, config: Config, db: Database):
        self.config = config
        self.db = db

    def fetch_platform(self, platform: str) -> Dict[str, Any]:
        """Fetch data from a specific platform"""
        platform_config = self.config.platforms.get(platform)

        if not platform_config or not platform_config.enabled:
            raise Exception(f"Platform {platform} not enabled")

        if platform == 'orcid':
            return self._fetch_orcid()
        elif platform == 'arxiv':
            return self._fetch_arxiv()
        elif platform == 'semantic_scholar':
            return self._fetch_semantic_scholar()
        elif platform == 'google_scholar':
            return self._fetch_google_scholar()
        else:
            raise Exception(f"Platform {platform} not supported yet")

    def _fetch_orcid(self) -> Dict[str, Any]:
        """Fetch data from ORCID"""
        platform_config = self.config.platforms['orcid']
        client = ORCIDClient(
            orcid_id=self.config.user.orcid,
            client_id=platform_config.client_id,
            client_secret=platform_config.client_secret
        )

        if platform_config.client_id and platform_config.client_secret:
            client.authenticate()

        works = client.get_works()

        papers_count = 0
        citations_count = 0

        for work in works:
            if work.get('title'):
                paper_id = self.db.add_paper(
                    title=work['title'],
                    doi=work.get('doi'),
                    year=work.get('year'),
                    venue=work.get('venue'),
                    url=work.get('url')
                )
                papers_count += 1

        self.db.update_sync_status('orcid', 'success')

        return {
            'platform': 'orcid',
            'papers': papers_count,
            'citations': citations_count
        }

    def _fetch_arxiv(self) -> Dict[str, Any]:
        """Fetch data from arXiv"""
        platform_config = self.config.platforms['arxiv']

        # If author_id is not set, try to use user name
        author_name = self.config.user.name

        client = ArXivClient(author_name=author_name)
        papers = client.search_by_author(max_results=200)

        papers_count = 0

        for paper in papers:
            if paper.get('title'):
                paper_id = self.db.add_paper(
                    title=paper['title'],
                    doi=paper.get('doi'),
                    arxiv_id=paper.get('arxiv_id'),
                    year=paper.get('year'),
                    abstract=paper.get('abstract'),
                    authors=paper.get('authors'),
                    url=paper.get('url')
                )
                papers_count += 1

        self.db.update_sync_status('arxiv', 'success')

        return {
            'platform': 'arxiv',
            'papers': papers_count,
            'citations': 0  # arXiv doesn't provide citation counts directly
        }

    def _fetch_semantic_scholar(self) -> Dict[str, Any]:
        """Fetch data from Semantic Scholar"""
        platform_config = self.config.platforms['semantic_scholar']

        client = SemanticScholarClient(
            api_key=platform_config.api_key,
            author_id=platform_config.author_id
        )

        # If author_id not configured, search by name
        if not platform_config.author_id:
            author_info = client.search_author(self.config.user.name)
            if author_info:
                platform_config.author_id = author_info['author_id']
                # Save the author_id back to config
                self.config.save(Config.get_config_dir() / 'config.yaml')
            else:
                raise Exception("Could not find author on Semantic Scholar")

        papers = client.get_author_papers(author_id=platform_config.author_id)

        papers_count = 0
        total_citations = 0

        for paper in papers:
            if paper.get('title'):
                paper_id = self.db.add_paper(
                    title=paper['title'],
                    doi=paper.get('doi'),
                    arxiv_id=paper.get('arxiv_id'),
                    year=paper.get('year'),
                    venue=paper.get('venue'),
                    abstract=paper.get('abstract'),
                    authors=paper.get('authors'),
                    url=paper.get('url')
                )

                citations = paper.get('citations', 0)
                total_citations += citations

                # Store citation count
                self.db.add_citation_record(
                    paper_id=paper_id,
                    platform='semantic_scholar',
                    citation_count=citations
                )

                papers_count += 1

        self.db.update_sync_status('semantic_scholar', 'success')

        return {
            'platform': 'semantic_scholar',
            'papers': papers_count,
            'citations': total_citations
        }

    def _fetch_google_scholar(self) -> Dict[str, Any]:
        """Fetch data from Google Scholar"""
        try:
            from scholarly import scholarly, ProxyGenerator

            # Set up proxy if needed (Google Scholar often blocks automated requests)
            # pg = ProxyGenerator()
            # pg.FreeProxies()
            # scholarly.use_proxy(pg)

            # Search for author
            search_query = scholarly.search_author(self.config.user.name)
            author = next(search_query, None)

            if not author:
                raise Exception("Author not found on Google Scholar")

            # Fill author details
            author = scholarly.fill(author)

            papers_count = 0
            total_citations = author.get('citedby', 0)
            h_index = author.get('hindex', 0)

            # Get publications
            for pub in author.get('publications', []):
                pub_details = scholarly.fill(pub)

                paper_id = self.db.add_paper(
                    title=pub_details.get('bib', {}).get('title', ''),
                    year=int(pub_details.get('bib', {}).get('pub_year', 0)) if pub_details.get('bib', {}).get('pub_year') else None,
                    venue=pub_details.get('bib', {}).get('venue'),
                    abstract=pub_details.get('bib', {}).get('abstract'),
                    url=pub_details.get('pub_url')
                )

                citations = pub_details.get('num_citations', 0)

                self.db.add_citation_record(
                    paper_id=paper_id,
                    platform='google_scholar',
                    citation_count=citations,
                    h_index=h_index
                )

                papers_count += 1

            self.db.update_sync_status('google_scholar', 'success')

            return {
                'platform': 'google_scholar',
                'papers': papers_count,
                'citations': total_citations,
                'h_index': h_index
            }

        except Exception as e:
            self.db.update_sync_status('google_scholar', 'error', str(e))
            raise Exception(f"Google Scholar fetch failed: {str(e)}")

    def fetch_all(self) -> Dict[str, Any]:
        """Fetch data from all enabled platforms"""
        results = {}

        for platform, config in self.config.platforms.items():
            if config.enabled:
                try:
                    result = self.fetch_platform(platform)
                    results[platform] = result
                except Exception as e:
                    results[platform] = {'error': str(e)}

        return results
