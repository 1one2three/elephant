"""Database management for Citation Mind"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import json


class Database:
    """SQLite database for storing citation data"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = None

    def connect(self):
        """Connect to database"""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def initialize(self):
        """Initialize database schema"""
        self.connect()

        # Papers table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                doi TEXT,
                arxiv_id TEXT,
                year INTEGER,
                venue TEXT,
                authors TEXT,
                abstract TEXT,
                url TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(doi, arxiv_id)
            )
        ''')

        # Citations table (time-series data)
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS citations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER,
                platform TEXT NOT NULL,
                citation_count INTEGER DEFAULT 0,
                h_index INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (paper_id) REFERENCES papers(id)
            )
        ''')

        # Tracked papers
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS tracked_papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                alert_enabled BOOLEAN DEFAULT 1,
                FOREIGN KEY (paper_id) REFERENCES papers(id)
            )
        ''')

        # Platform sync status
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS sync_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT UNIQUE NOT NULL,
                last_sync TIMESTAMP,
                status TEXT,
                error_message TEXT
            )
        ''')

        # Recommendations history
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT,
                generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                actioned BOOLEAN DEFAULT 0,
                actioned_date TIMESTAMP
            )
        ''')

        # Citation alerts
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER,
                alert_type TEXT NOT NULL,
                message TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                read BOOLEAN DEFAULT 0,
                FOREIGN KEY (paper_id) REFERENCES papers(id)
            )
        ''')

        self.conn.commit()

    def add_paper(self, title: str, doi: Optional[str] = None, arxiv_id: Optional[str] = None,
                  year: Optional[int] = None, venue: Optional[str] = None,
                  authors: Optional[List[str]] = None, abstract: Optional[str] = None,
                  url: Optional[str] = None) -> int:
        """Add a paper to the database"""
        self.connect()

        authors_json = json.dumps(authors) if authors else None

        cursor = self.conn.execute('''
            INSERT OR IGNORE INTO papers (title, doi, arxiv_id, year, venue, authors, abstract, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, doi, arxiv_id, year, venue, authors_json, abstract, url))

        if cursor.lastrowid == 0:
            # Paper already exists, get its ID
            cursor = self.conn.execute(
                'SELECT id FROM papers WHERE doi = ? OR arxiv_id = ?',
                (doi, arxiv_id)
            )
            row = cursor.fetchone()
            paper_id = row[0] if row else None
        else:
            paper_id = cursor.lastrowid

        self.conn.commit()
        return paper_id

    def add_citation_record(self, paper_id: int, platform: str, citation_count: int,
                           h_index: Optional[int] = None, metadata: Optional[Dict] = None):
        """Add a citation record"""
        self.connect()

        metadata_json = json.dumps(metadata) if metadata else None

        self.conn.execute('''
            INSERT INTO citations (paper_id, platform, citation_count, h_index, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (paper_id, platform, citation_count, h_index, metadata_json))

        self.conn.execute(
            'UPDATE papers SET last_updated = CURRENT_TIMESTAMP WHERE id = ?',
            (paper_id,)
        )

        self.conn.commit()

    def get_total_citations(self, platform: Optional[str] = None) -> int:
        """Get total citations across all papers"""
        self.connect()

        query = '''
            SELECT SUM(citation_count) as total
            FROM (
                SELECT paper_id, MAX(citation_count) as citation_count
                FROM citations
        '''

        if platform:
            query += ' WHERE platform = ?'
            params = (platform,)
        else:
            params = ()

        query += ' GROUP BY paper_id) as latest'

        cursor = self.conn.execute(query, params)
        result = cursor.fetchone()
        return result[0] if result and result[0] else 0

    def get_paper_count(self) -> int:
        """Get total number of papers"""
        self.connect()

        cursor = self.conn.execute('SELECT COUNT(*) FROM papers')
        return cursor.fetchone()[0]

    def get_tracked_papers(self) -> List[Dict[str, Any]]:
        """Get all tracked papers"""
        self.connect()

        cursor = self.conn.execute('''
            SELECT p.*, MAX(c.citation_count) as citations, p.last_updated
            FROM tracked_papers tp
            JOIN papers p ON tp.paper_id = p.id
            LEFT JOIN citations c ON p.id = c.paper_id
            GROUP BY p.id
            ORDER BY citations DESC
        ''')

        return [dict(row) for row in cursor.fetchall()]

    def add_tracked_paper(self, doi: Optional[str] = None, arxiv_id: Optional[str] = None,
                         title: Optional[str] = None):
        """Add a paper to tracking"""
        self.connect()

        # Find the paper
        if doi:
            cursor = self.conn.execute('SELECT id FROM papers WHERE doi = ?', (doi,))
        elif arxiv_id:
            cursor = self.conn.execute('SELECT id FROM papers WHERE arxiv_id = ?', (arxiv_id,))
        elif title:
            cursor = self.conn.execute('SELECT id FROM papers WHERE title LIKE ?', (f'%{title}%',))
        else:
            return None

        row = cursor.fetchone()
        if row:
            paper_id = row[0]
            self.conn.execute('''
                INSERT OR IGNORE INTO tracked_papers (paper_id) VALUES (?)
            ''', (paper_id,))
            self.conn.commit()
            return paper_id

        return None

    def get_papers_with_latest_citations(self) -> List[Dict[str, Any]]:
        """Get all papers with their latest citation counts"""
        self.connect()

        cursor = self.conn.execute('''
            SELECT p.*,
                   COALESCE(MAX(c.citation_count), 0) as citations,
                   p.last_updated
            FROM papers p
            LEFT JOIN citations c ON p.id = c.paper_id
            GROUP BY p.id
            ORDER BY citations DESC
        ''')

        return [dict(row) for row in cursor.fetchall()]

    def update_sync_status(self, platform: str, status: str, error_message: Optional[str] = None):
        """Update platform sync status"""
        self.connect()

        self.conn.execute('''
            INSERT OR REPLACE INTO sync_status (platform, last_sync, status, error_message)
            VALUES (?, CURRENT_TIMESTAMP, ?, ?)
        ''', (platform, status, error_message))

        self.conn.commit()

    def get_citation_history(self, paper_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Get citation history for a paper"""
        self.connect()

        cursor = self.conn.execute('''
            SELECT platform, citation_count, timestamp
            FROM citations
            WHERE paper_id = ?
            AND timestamp >= datetime('now', '-' || ? || ' days')
            ORDER BY timestamp DESC
        ''', (paper_id, days))

        return [dict(row) for row in cursor.fetchall()]

    def export_all_data(self) -> List[Dict[str, Any]]:
        """Export all data for export command"""
        self.connect()

        cursor = self.conn.execute('''
            SELECT p.title, p.doi, p.arxiv_id, p.year, p.venue,
                   COALESCE(MAX(c.citation_count), 0) as citations
            FROM papers p
            LEFT JOIN citations c ON p.id = c.paper_id
            GROUP BY p.id
            ORDER BY citations DESC
        ''')

        return [dict(row) for row in cursor.fetchall()]

    def add_recommendation(self, category: str, title: str, description: str, priority: str):
        """Add a recommendation"""
        self.connect()

        self.conn.execute('''
            INSERT INTO recommendations (category, title, description, priority)
            VALUES (?, ?, ?, ?)
        ''', (category, title, description, priority))

        self.conn.commit()

    def add_alert(self, paper_id: Optional[int], alert_type: str, message: str):
        """Add an alert"""
        self.connect()

        self.conn.execute('''
            INSERT INTO alerts (paper_id, alert_type, message)
            VALUES (?, ?, ?)
        ''', (paper_id, alert_type, message))

        self.conn.commit()
