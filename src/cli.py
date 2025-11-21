#!/usr/bin/env python3
"""
Citation Mind CLI
Main entry point for the command-line interface
"""

import click
from rich.console import Console
from pathlib import Path
import sys

from src.core.config import Config
from src.core.commands import (
    init_command,
    fetch_command,
    dashboard_command,
    recommend_command,
    track_command,
    export_command,
    alert_command,
    stats_command
)

console = Console()

@click.group()
@click.version_option(version='0.1.0')
@click.pass_context
def main(ctx):
    """Citation Mind - Boost your scientific citations"""
    ctx.ensure_object(dict)

    # Load configuration
    config_path = Path.home() / '.citation-mind' / 'config.yaml'
    if config_path.exists():
        ctx.obj['config'] = Config.load(config_path)
    else:
        ctx.obj['config'] = None


@main.command()
@click.option('--orcid', prompt='Your ORCID ID', help='Your ORCID identifier')
@click.option('--email', prompt='Your email', help='Your email address')
@click.option('--name', prompt='Your name', help='Your full name')
@click.pass_context
def init(ctx, orcid, email, name):
    """Initialize Citation Mind with your credentials"""
    init_command(orcid, email, name)


@main.command()
@click.option('--all', 'fetch_all', is_flag=True, help='Fetch from all platforms')
@click.option('--platform', multiple=True, help='Specific platform(s) to fetch')
@click.option('--force', is_flag=True, help='Force refresh even if recently updated')
@click.pass_context
def fetch(ctx, fetch_all, platform, force):
    """Fetch latest citation data from platforms"""
    fetch_command(ctx.obj.get('config'), fetch_all, platform, force)


@main.command()
@click.option('--detailed', is_flag=True, help='Show detailed metrics')
@click.option('--period', default='all', help='Time period: week, month, year, all')
@click.pass_context
def dashboard(ctx, detailed, period):
    """Display your citation dashboard"""
    dashboard_command(ctx.obj.get('config'), detailed, period)


@main.command()
@click.option('--top', default=5, help='Number of recommendations to show')
@click.option('--category', help='Filter by category: visibility, collaboration, trending')
@click.pass_context
def recommend(ctx, top, category):
    """Get recommendations to boost citations"""
    recommend_command(ctx.obj.get('config'), top, category)


@main.command()
@click.option('--doi', help='DOI of paper to track')
@click.option('--arxiv', help='arXiv ID of paper to track')
@click.option('--title', help='Title of paper to track')
@click.option('--list', 'list_tracked', is_flag=True, help='List all tracked papers')
@click.pass_context
def track(ctx, doi, arxiv, title, list_tracked):
    """Track specific papers"""
    track_command(ctx.obj.get('config'), doi, arxiv, title, list_tracked)


@main.command()
@click.option('--format', 'output_format', type=click.Choice(['csv', 'json', 'xlsx']), default='csv')
@click.option('--output', help='Output file path')
@click.pass_context
def export(ctx, output_format, output):
    """Export citation data"""
    export_command(ctx.obj.get('config'), output_format, output)


@main.command()
@click.option('--enable/--disable', default=True, help='Enable or disable alerts')
@click.option('--threshold', type=int, help='Minimum citations to trigger alert')
@click.pass_context
def alert(ctx, enable, threshold):
    """Configure citation alerts"""
    alert_command(ctx.obj.get('config'), enable, threshold)


@main.command()
@click.option('--paper', help='Show stats for specific paper (DOI or arXiv ID)')
@click.pass_context
def stats(ctx, paper):
    """Show detailed statistics"""
    stats_command(ctx.obj.get('config'), paper)


if __name__ == '__main__':
    main()
