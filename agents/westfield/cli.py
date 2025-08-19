"""
CLI interface for the Westfield local politics agent.
"""

import asyncio
import os
import sys
from pathlib import Path
import click
import logging
from typing import Optional
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.logging import RichHandler
from rich.panel import Panel
from rich.text import Text

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.westfield.reddit.client import RedditClient
from agents.westfield.reddit.downloader import RedditDownloader
from agents.westfield.storage.vector_store import VectorStore
from agents.westfield.models.reddit_data import PoliticalTopic

# Set up rich console
console = Console()

# Configure logging with rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
def cli(debug):
    """Westfield Agent - Local Politics Intelligence from Social Media"""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.command()
@click.option("--subreddit", default="newjersey", help="Subreddit to download from")
@click.option("--days", default=30, type=int, help="Number of days of history to fetch")
@click.option("--with-comments", is_flag=True, help="Also fetch comments for posts")
@click.option("--comment-limit", default=50, type=int, help="Max comments per post")
def download(subreddit, days, with_comments, comment_limit):
    """Download initial data from Reddit"""
    
    console.print(Panel.fit(
        f"[bold cyan]Downloading from r/{subreddit}[/bold cyan]\n"
        f"History: {days} days\n"
        f"Comments: {'Yes' if with_comments else 'No'}",
        title="Reddit Download"
    ))
    
    async def run_download():
        try:
            # Initialize client
            client = RedditClient()
            downloader = RedditDownloader(client)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Downloading posts...", total=None)
                
                # Download data
                result = await downloader.download_initial_data(
                    subreddit=subreddit,
                    days_back=days,
                    fetch_comments=with_comments,
                    comment_limit=comment_limit
                )
                
                progress.update(task, completed=100)
            
            # Display results
            table = Table(title="Download Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Total Posts", str(result["total_posts"]))
            table.add_row("Total Comments", str(result["total_comments"]))
            table.add_row("Date Range", f"{result['date_range']['start'][:10]} to {result['date_range']['end'][:10]}")
            
            console.print(table)
            console.print("[green]✓[/green] Download complete!")
            
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)
    
    asyncio.run(run_download())


@cli.command()
@click.option("--subreddit", default="newjersey", help="Subreddit to monitor")
@click.option("--interval", default=300, type=int, help="Update interval in seconds")
def monitor(subreddit, interval):
    """Continuously monitor subreddit for new posts"""
    
    console.print(Panel.fit(
        f"[bold cyan]Monitoring r/{subreddit}[/bold cyan]\n"
        f"Update interval: {interval} seconds\n"
        f"Press Ctrl+C to stop",
        title="Live Monitoring"
    ))
    
    async def run_monitor():
        try:
            client = RedditClient()
            downloader = RedditDownloader(client)
            
            await downloader.continuous_monitoring(
                subreddit=subreddit,
                update_interval=interval
            )
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Monitoring stopped by user[/yellow]")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)
    
    asyncio.run(run_monitor())


@cli.command()
@click.option("--subreddit", default="newjersey", help="Subreddit to update")
def update(subreddit):
    """Fetch new posts since last update"""
    
    async def run_update():
        try:
            client = RedditClient()
            downloader = RedditDownloader(client)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Checking for updates...", total=None)
                
                result = await downloader.update_data(
                    subreddit=subreddit,
                    fetch_comments=True
                )
                
                progress.update(task, completed=100)
            
            if result["new_posts"] > 0:
                console.print(f"[green]✓[/green] Found {result['new_posts']} new posts and {result['new_comments']} comments")
            else:
                console.print("[yellow]No new posts found[/yellow]")
                
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)
    
    asyncio.run(run_update())


@cli.command()
@click.argument("query")
@click.option("--limit", default=10, type=int, help="Number of results")
@click.option("--post-only", is_flag=True, help="Search only posts")
@click.option("--comment-only", is_flag=True, help="Search only comments")
def search(query, limit, post_only, comment_only):
    """Search for content using semantic similarity"""
    
    try:
        # Initialize vector store
        store = VectorStore()
        
        # Build filter
        filter_metadata = None
        if post_only:
            filter_metadata = {"type": "post"}
        elif comment_only:
            filter_metadata = {"type": "comment"}
        
        # Search
        results = store.search(
            query=query,
            n_results=limit,
            filter_metadata=filter_metadata
        )
        
        if not results:
            console.print("[yellow]No results found[/yellow]")
            return
        
        # Display results
        console.print(Panel.fit(f"[bold]Search Results for: {query}[/bold]", style="cyan"))
        
        for i, (metadata, score) in enumerate(results, 1):
            # Format result
            if metadata["type"] == "post":
                title = Text(f"{i}. [POST] ", style="bold green")
                # Get post content
                result = store.collection.get(ids=[f"post_{metadata['post_id']}"])
                if result["documents"]:
                    content = result["documents"][0].split("\n")[0]  # First line (title)
                    title.append(content[:100], style="white")
            else:
                title = Text(f"{i}. [COMMENT] ", style="bold blue")
                result = store.collection.get(ids=[f"comment_{metadata['comment_id']}"])
                if result["documents"]:
                    content = result["documents"][0][:100]
                    title.append(content, style="white")
            
            console.print(title)
            console.print(f"   Score: {score:.3f} | Author: {metadata['author']} | Date: {metadata['created_utc'][:10]}")
            console.print(f"   [link]{metadata['url']}[/link]")
            console.print()
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("topic", type=click.Choice([t.value for t in PoliticalTopic]))
@click.option("--limit", default=10, type=int, help="Number of results")
def search_topic(topic, limit):
    """Search for content by political topic"""
    
    try:
        store = VectorStore()
        topic_enum = PoliticalTopic(topic)
        
        results = store.search_by_topic(topic_enum, n_results=limit)
        
        if not results:
            console.print(f"[yellow]No results found for topic: {topic}[/yellow]")
            return
        
        console.print(Panel.fit(f"[bold]Posts about {topic.replace('_', ' ').title()}[/bold]", style="cyan"))
        
        for i, metadata in enumerate(results[:limit], 1):
            if metadata["type"] == "post":
                console.print(f"{i}. [green]Score: {metadata['score']}[/green] | Comments: {metadata['num_comments']}")
                console.print(f"   [link]{metadata['url']}[/link]")
            console.print()
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
def stats():
    """Show statistics about stored data"""
    
    try:
        store = VectorStore()
        stats = store.get_statistics()
        
        # Create statistics table
        table = Table(title="Vector Store Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")
        
        table.add_row("Total Documents", str(stats["total_documents"]))
        table.add_row("Posts", str(stats["posts"]))
        table.add_row("Comments", str(stats["comments"]))
        table.add_row("High Relevance", str(stats["high_relevance"]))
        table.add_row("Medium Relevance", str(stats["medium_relevance"]))
        table.add_row("Low Relevance", str(stats["low_relevance"]))
        
        console.print(table)
        
        # Show top topics
        if stats["topics"]:
            topic_table = Table(title="Top Topics")
            topic_table.add_column("Topic", style="cyan")
            topic_table.add_column("Count", style="green")
            
            sorted_topics = sorted(stats["topics"].items(), key=lambda x: x[1], reverse=True)
            for topic, count in sorted_topics[:10]:
                if topic:  # Skip empty topics
                    topic_table.add_row(topic.replace("_", " ").title(), str(count))
            
            console.print(topic_table)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("query")
def context(query):
    """Get RAG context for a query"""
    
    try:
        store = VectorStore()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Retrieving context...", total=None)
            
            context_text = store.get_context_for_query(
                query=query,
                max_tokens=2000,
                include_metadata=True
            )
            
            progress.update(task, completed=100)
        
        if not context_text:
            console.print("[yellow]No relevant context found[/yellow]")
            return
        
        console.print(Panel.fit(f"[bold]Context for: {query}[/bold]", style="cyan"))
        console.print(context_text)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
def index():
    """Build/rebuild vector index from downloaded data"""
    
    try:
        from agents.westfield.reddit.downloader import RedditDownloader
        
        console.print("[cyan]Building vector index from downloaded data...[/cyan]")
        
        # Initialize components
        client = RedditClient()
        downloader = RedditDownloader(client)
        store = VectorStore()
        
        # Load posts
        posts = downloader.load_posts()
        console.print(f"Found {len(posts)} posts to index")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Indexing posts...", total=len(posts))
            
            for post in posts:
                store.add_post(post)
                
                # Also add comments if they exist
                comments = downloader.load_comments(post.id)
                for comment in comments:
                    store.add_comment(comment, post.id)
                
                progress.update(task, advance=1)
        
        # Update relevance scores
        console.print("[cyan]Updating relevance scores...[/cyan]")
        store.update_relevance_scores()
        
        console.print("[green]✓[/green] Index built successfully!")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()