"""ORCID API integration"""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime


class ORCIDClient:
    """Client for ORCID API"""

    BASE_URL = "https://pub.orcid.org/v3.0"

    def __init__(self, orcid_id: str, client_id: Optional[str] = None,
                 client_secret: Optional[str] = None):
        self.orcid_id = orcid_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None

    def authenticate(self):
        """Authenticate with ORCID API (for private data)"""
        if not self.client_id or not self.client_secret:
            return False

        token_url = "https://orcid.org/oauth/token"
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
            'scope': '/read-public'
        }

        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            self.access_token = response.json()['access_token']
            return True
        return False

    def get_works(self) -> List[Dict[str, Any]]:
        """Fetch all works from ORCID profile"""
        url = f"{self.BASE_URL}/{self.orcid_id}/works"

        headers = {
            'Accept': 'application/json'
        }

        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise Exception(f"ORCID API error: {response.status_code}")

        data = response.json()
        works = []

        # Parse ORCID works
        if 'group' in data:
            for group in data['group']:
                work_summary = group.get('work-summary', [])
                if work_summary:
                    summary = work_summary[0]

                    # Extract work details
                    title = summary.get('title', {}).get('title', {}).get('value', '')

                    # Extract DOI from external IDs
                    doi = None
                    external_ids = summary.get('external-ids', {}).get('external-id', [])
                    for ext_id in external_ids:
                        if ext_id.get('external-id-type') == 'doi':
                            doi = ext_id.get('external-id-value')
                            break

                    # Publication year
                    pub_date = summary.get('publication-date')
                    year = None
                    if pub_date and pub_date.get('year'):
                        year = int(pub_date['year']['value'])

                    # Journal/venue
                    venue = summary.get('journal-title', {}).get('value') if summary.get('journal-title') else None

                    # URL
                    url_info = summary.get('url', {}).get('value') if summary.get('url') else None

                    work = {
                        'title': title,
                        'doi': doi,
                        'year': year,
                        'venue': venue,
                        'url': url_info,
                        'type': summary.get('type', 'unknown'),
                        'put_code': summary.get('put-code')
                    }

                    works.append(work)

        return works

    def get_person_info(self) -> Dict[str, Any]:
        """Get person information from ORCID"""
        url = f"{self.BASE_URL}/{self.orcid_id}/person"

        headers = {
            'Accept': 'application/json'
        }

        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise Exception(f"ORCID API error: {response.status_code}")

        data = response.json()

        name_data = data.get('name', {})
        given_names = name_data.get('given-names', {}).get('value', '')
        family_name = name_data.get('family-name', {}).get('value', '')

        return {
            'name': f"{given_names} {family_name}".strip(),
            'given_names': given_names,
            'family_name': family_name,
            'orcid': self.orcid_id
        }
