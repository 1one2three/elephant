"""Command implementations for Citation Mind CLI"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
import yaml
from datetime import datetime, timedelta
from typing import Optional, List

from src.core.config import Config, UserConfig, PlatformConfig
from src.db.database import Database
from src.api.fetcher import DataFetcher
from src.analytics.recommendations import RecommendationEngine
from src.analytics.metrics import MetricsCalculator

console = Console()


def init_command(orcid: str, email: str, name: str):
    """Initialize Citation Mind configuration"""
    console.print("[bold blue]Initializing Citation Mind...[/bold blue]")

    config_dir = Config.get_config_dir()
    config_path = config_dir / 'config.yaml'

    # Create basic configuration
    config_data = {
        'user': {
            'name': name,
            'email': email,
            'orcid': orcid
        },
        'platforms': {
            'orcid': {'enabled': True},
            'arxiv': {'enabled': True},
            'semantic_scholar': {'enabled': True},
            'google_scholar': {'enabled': True},
            'web_of_science': {'enabled': False},
            'scopus': {'enabled': False}
        },
        'database': {
            'path': str(Config.get_data_dir() / 'citations.db')
        },
        'tracking': {
            'auto_fetch': True,
            'fetch_interval_hours': 24
        },
        'alerts': {
            'enabled': True,
            'email_notifications': False,
            'min_citation_threshold': 1
        },
        'recommendations': {
            'enabled': True,
            'check_trending_topics': True,
            'suggest_collaborations': True,
            'identify_low_visibility_papers': True
        }
    }

    with open(config_path, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False)

    # Initialize database
    db = Database(str(Config.get_data_dir() / 'citations.db'))
    db.initialize()

    console.print(f"[green]✓[/green] Configuration saved to {config_path}")
    console.print(f"[green]✓[/green] Database initialized")
    console.print("\n[yellow]Next steps:[/yellow]")
    console.print("1. Add API keys to ~/.citation-mind/.env (see .env.example)")
    console.print("2. Run 'citation-mind fetch --all' to fetch your data")
    console.print("3. Run 'citation-mind dashboard' to view your metrics")


def fetch_command(config: Optional[Config], fetch_all: bool, platforms: tuple, force: bool):
    """Fetch citation data from platforms"""
    if not config:
        console.print("[red]Error:[/red] Not initialized. Run 'citation-mind init' first.")
        return

    console.print("[bold blue]Fetching citation data...[/bold blue]\n")

    db = Database(config.database.path)
    fetcher = DataFetcher(config, db)

    platforms_to_fetch = []
    if fetch_all:
        platforms_to_fetch = [p for p, cfg in config.platforms.items() if cfg.enabled]
    elif platforms:
        platforms_to_fetch = list(platforms)
    else:
        console.print("[yellow]Specify --all or --platform. Use --help for more info.[/yellow]")
        return

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        for platform in platforms_to_fetch:
            task = progress.add_task(f"Fetching from {platform}...", total=None)
            try:
                result = fetcher.fetch_platform(platform)
                progress.update(task, completed=True)
                console.print(f"[green]✓[/green] {platform}: {result['papers']} papers, {result['citations']} citations")
            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"[red]✗[/red] {platform}: {str(e)}")

    console.print(f"\n[green]Data fetch completed![/green]")


def dashboard_command(config: Optional[Config], detailed: bool, period: str):
    """Display citation dashboard"""
    if not config:
        console.print("[red]Error:[/red] Not initialized. Run 'citation-mind init' first.")
        return

    db = Database(config.database.path)
    metrics = MetricsCalculator(db)

    # Get metrics for the period
    stats = metrics.get_summary_stats(period)

    # Header
    console.print(Panel.fit(
        f"[bold]{config.user.name}[/bold]\n"
        f"ORCID: {config.user.orcid}\n"
        f"Period: {period.capitalize()}",
        title="Citation Dashboard",
        border_style="blue"
    ))

    # Overall metrics
    table = Table(title="\nOverall Metrics", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="green")
    table.add_column("Change", justify="right")

    table.add_row("Total Papers", str(stats['total_papers']), f"+{stats.get('papers_change', 0)}")
    table.add_row("Total Citations", str(stats['total_citations']), f"+{stats.get('citations_change', 0)}")
    table.add_row("H-Index", str(stats['h_index']), f"+{stats.get('h_index_change', 0)}")
    table.add_row("Avg Citations/Paper", f"{stats['avg_citations']:.1f}", "")

    console.print(table)

    if detailed:
        # Top cited papers
        top_papers = metrics.get_top_papers(limit=5)

        papers_table = Table(title="\nTop Cited Papers", show_header=True, header_style="bold cyan")
        papers_table.add_column("Title", style="cyan", max_width=50)
        papers_table.add_column("Citations", justify="right", style="green")
        papers_table.add_column("Year", justify="center")

        for paper in top_papers:
            papers_table.add_row(
                paper['title'][:47] + "..." if len(paper['title']) > 50 else paper['title'],
                str(paper['citations']),
                str(paper['year'])
            )

        console.print(papers_table)


def recommend_command(config: Optional[Config], top: int, category: Optional[str]):
    """Get recommendations to boost citations"""
    if not config:
        console.print("[red]Error:[/red] Not initialized. Run 'citation-mind init' first.")
        return

    db = Database(config.database.path)
    engine = RecommendationEngine(config, db)

    console.print("[bold blue]Analyzing your citation profile...[/bold blue]\n")

    recommendations = engine.generate_recommendations(limit=top, category=category)

    for i, rec in enumerate(recommendations, 1):
        console.print(Panel(
            f"[bold]{rec['title']}[/bold]\n\n"
            f"{rec['description']}\n\n"
            f"[cyan]Impact:[/cyan] {rec['impact']}\n"
            f"[cyan]Effort:[/cyan] {rec['effort']}\n"
            f"[cyan]Action:[/cyan] {rec['action']}",
            title=f"Recommendation {i} - {rec['category']}",
            border_style="green" if rec['priority'] == 'high' else "yellow"
        ))


def track_command(config: Optional[Config], doi: Optional[str], arxiv: Optional[str],
                  title: Optional[str], list_tracked: bool):
    """Track specific papers"""
    if not config:
        console.print("[red]Error:[/red] Not initialized. Run 'citation-mind init' first.")
        return

    db = Database(config.database.path)

    if list_tracked:
        tracked = db.get_tracked_papers()

        table = Table(title="Tracked Papers", show_header=True, header_style="bold cyan")
        table.add_column("Title", style="cyan", max_width=50)
        table.add_column("Citations", justify="right", style="green")
        table.add_column("Last Updated", justify="center")

        for paper in tracked:
            table.add_row(
                paper['title'][:47] + "..." if len(paper['title']) > 50 else paper['title'],
                str(paper['citations']),
                paper['last_updated'].strftime("%Y-%m-%d")
            )

        console.print(table)
        return

    # Add paper to tracking
    if doi or arxiv or title:
        db.add_tracked_paper(doi=doi, arxiv_id=arxiv, title=title)
        console.print(f"[green]✓[/green] Paper added to tracking")
    else:
        console.print("[yellow]Specify --doi, --arxiv, or --title to track a paper[/yellow]")


def export_command(config: Optional[Config], output_format: str, output: Optional[str]):
    """Export citation data"""
    if not config:
        console.print("[red]Error:[/red] Not initialized. Run 'citation-mind init' first.")
        return

    import pandas as pd

    db = Database(config.database.path)
    data = db.export_all_data()

    df = pd.DataFrame(data)

    if not output:
        output = f"citations_{datetime.now().strftime('%Y%m%d')}.{output_format}"

    if output_format == 'csv':
        df.to_csv(output, index=False)
    elif output_format == 'json':
        df.to_json(output, orient='records', indent=2)
    elif output_format == 'xlsx':
        df.to_excel(output, index=False)

    console.print(f"[green]✓[/green] Data exported to {output}")


def alert_command(config: Optional[Config], enable: bool, threshold: Optional[int]):
    """Configure citation alerts"""
    if not config:
        console.print("[red]Error:[/red] Not initialized. Run 'citation-mind init' first.")
        return

    config.alerts.enabled = enable
    if threshold is not None:
        config.alerts.min_citation_threshold = threshold

    config_path = Config.get_config_dir() / 'config.yaml'
    config.save(config_path)

    status = "enabled" if enable else "disabled"
    console.print(f"[green]✓[/green] Alerts {status}")
    if threshold:
        console.print(f"[green]✓[/green] Citation threshold set to {threshold}")


def stats_command(config: Optional[Config], paper: Optional[str]):
    """Show detailed statistics"""
    if not config:
        console.print("[red]Error:[/red] Not initialized. Run 'citation-mind init' first.")
        return

    db = Database(config.database.path)
    metrics = MetricsCalculator(db)

    if paper:
        # Show stats for specific paper
        paper_stats = metrics.get_paper_stats(paper)

        console.print(Panel(
            f"[bold]{paper_stats['title']}[/bold]\n\n"
            f"Citations: {paper_stats['citations']}\n"
            f"Year: {paper_stats['year']}\n"
            f"Venue: {paper_stats.get('venue', 'N/A')}\n"
            f"DOI: {paper_stats.get('doi', 'N/A')}\n\n"
            f"Citation Growth:\n"
            f"  Last 7 days: +{paper_stats.get('citations_7d', 0)}\n"
            f"  Last 30 days: +{paper_stats.get('citations_30d', 0)}\n"
            f"  Last year: +{paper_stats.get('citations_1y', 0)}",
            title="Paper Statistics",
            border_style="blue"
        ))
    else:
        # Show overall detailed stats
        console.print("[cyan]Use --paper DOI or arXiv ID to see paper-specific stats[/cyan]")
