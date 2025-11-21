"""Configuration management for Citation Mind"""

import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv


class PlatformConfig(BaseModel):
    """Configuration for a single platform"""
    enabled: bool = True
    api_key: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    author_id: Optional[str] = None


class UserConfig(BaseModel):
    """User information"""
    name: str
    email: str
    orcid: str


class DatabaseConfig(BaseModel):
    """Database configuration"""
    path: str = "data/citations.db"


class TrackingConfig(BaseModel):
    """Tracking configuration"""
    auto_fetch: bool = True
    fetch_interval_hours: int = 24


class AlertsConfig(BaseModel):
    """Alerts configuration"""
    enabled: bool = True
    email_notifications: bool = False
    min_citation_threshold: int = 1


class RecommendationsConfig(BaseModel):
    """Recommendations configuration"""
    enabled: bool = True
    check_trending_topics: bool = True
    suggest_collaborations: bool = True
    identify_low_visibility_papers: bool = True


class Config(BaseModel):
    """Main configuration class"""
    user: UserConfig
    platforms: Dict[str, PlatformConfig] = Field(default_factory=dict)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    tracking: TrackingConfig = Field(default_factory=TrackingConfig)
    alerts: AlertsConfig = Field(default_factory=AlertsConfig)
    recommendations: RecommendationsConfig = Field(default_factory=RecommendationsConfig)

    @classmethod
    def load(cls, config_path: Path) -> 'Config':
        """Load configuration from YAML file"""
        load_dotenv()

        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)

        # Inject environment variables for API keys
        for platform, config in data.get('platforms', {}).items():
            env_key = f"{platform.upper()}_API_KEY"
            if env_key in os.environ:
                config['api_key'] = os.environ[env_key]

            # Handle ORCID separately
            if platform == 'orcid':
                if 'ORCID_CLIENT_ID' in os.environ:
                    config['client_id'] = os.environ['ORCID_CLIENT_ID']
                if 'ORCID_CLIENT_SECRET' in os.environ:
                    config['client_secret'] = os.environ['ORCID_CLIENT_SECRET']

        return cls(**data)

    def save(self, config_path: Path):
        """Save configuration to YAML file"""
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w') as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)

    @classmethod
    def get_config_dir(cls) -> Path:
        """Get the configuration directory"""
        config_dir = Path.home() / '.citation-mind'
        config_dir.mkdir(exist_ok=True)
        return config_dir

    @classmethod
    def get_data_dir(cls) -> Path:
        """Get the data directory"""
        data_dir = cls.get_config_dir() / 'data'
        data_dir.mkdir(exist_ok=True)
        return data_dir
