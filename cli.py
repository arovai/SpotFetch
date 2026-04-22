#!/usr/bin/env python3
"""CLI tool for SpotFetch - Download audio from YouTube/YouTube Music"""

import argparse
import os
import sys
import glob
from pathlib import Path
from typing import List, Tuple
import csv
import functions
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table


console = Console()


class CSVFormat:
    """Detect and categorize CSV file formats"""
    EXPORTIFY = "exportify"
    TUNEMYMUSIC = "tunemymusic"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


def detect_csv_format(file_path: str) -> str:
    """Detect the format of a CSV file based on its headers"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                return CSVFormat.UNKNOWN
            
            headers = set(reader.fieldnames)
            
            # Check for Exportify format
            if 'Track Name' in headers and 'Artist Name(s)' in headers and 'Album Name' in headers:
                return CSVFormat.EXPORTIFY
            
            # Check for TuneMyMusic format
            if 'Track name' in headers and 'Artist name' in headers:
                return CSVFormat.TUNEMYMUSIC
            
            # Check for Custom format
            if 'name' in headers and 'artist' in headers:
                return CSVFormat.CUSTOM
            
            return CSVFormat.UNKNOWN
    except Exception as e:
        console.print(f"Error detecting CSV format: {e}", style="red")
        return CSVFormat.UNKNOWN


def create_output_folder(csv_file_path: str, output_base_path: str) -> str:
    """
    Create a folder in output_base_path with the CSV filename (without extension)
    Returns the full path to the created folder
    """
    # Extract CSV filename without extension
    csv_filename = Path(csv_file_path).stem
    output_folder = os.path.join(output_base_path, csv_filename)
    
    # Create the folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    return output_folder


def process_csv_file(
    csv_file: str,
    output_path: str,
    format: str = "mp3",
    platform: str = "ytmusic",
    cookie_file: str = None,
    auto_format: bool = True
) -> None:
    """Process a single CSV file"""
    
    if not os.path.exists(csv_file):
        console.print(f"❌ CSV file not found: {csv_file}", style="red")
        return
    
    # Create output folder based on CSV filename
    csv_output_folder = create_output_folder(csv_file, output_path)
    
    console.print(f"\n📁 Output folder: {csv_output_folder}", style="cyan")
    
    # Detect CSV format if auto_format is enabled
    csv_format = detect_csv_format(csv_file) if auto_format else CSVFormat.CUSTOM
    
    try:
        if csv_format == CSVFormat.EXPORTIFY:
            console.print("📋 Detected format: Exportify", style="blue")
            songs = functions.read_exportify_csv_file(csv_file)
            download_spotify_songs(songs, csv_output_folder, format, platform, cookie_file)
        
        elif csv_format == CSVFormat.TUNEMYMUSIC:
            console.print("📋 Detected format: TuneMyMusic", style="blue")
            songs = functions.read_tunemymusic_csv_file(csv_file)
            download_songs(songs, csv_output_folder, format, platform, cookie_file)
        
        elif csv_format == CSVFormat.CUSTOM:
            console.print("📋 Detected format: Custom", style="blue")
            functions.read_download_custom_csv(csv_file, format, csv_output_folder, cookie_file, platform)
        
        else:
            console.print("❌ Unable to detect CSV format. Trying custom format...", style="yellow")
            functions.read_download_custom_csv(csv_file, format, csv_output_folder, cookie_file, platform)
        
        console.print(f"✅ Successfully processed: {csv_file}", style="green")
    
    except Exception as e:
        console.print(f"❌ Error processing {csv_file}: {e}", style="red")


def download_songs(songs: List, output_path: str, format: str, platform: str, cookie_file: str = None) -> None:
    """Download songs from a list using search queries"""
    if not songs:
        console.print("⚠️  No songs found in the CSV file", style="yellow")
        return
    
    total_songs = len(songs)
    console.print(f"🎵 Starting download of {total_songs} songs...\n", style="bold blue")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        for i, song in enumerate(songs, 1):
            try:
                track_name = song.get('track_name', 'Unknown')
                artist_name = song.get('artist_name', 'Unknown')
                
                progress.update(progress.add_task(
                    f"[{i}/{total_songs}] {track_name} by {artist_name}",
                    total=None
                ))
                
                functions.download_from_query(song, format, output_path, cookie_file, platform)
                console.print(f"  ✓ {track_name}", style="green")
            
            except Exception as e:
                console.print(f"  ✗ Failed to download {track_name}: {e}", style="red")
                continue


def download_spotify_songs(songs: List, output_path: str, format: str, platform: str, cookie_file: str = None) -> None:
    """Download Spotify songs with full metadata"""
    if not songs:
        console.print("⚠️  No songs found in the CSV file", style="yellow")
        return
    
    total_songs = len(songs)
    console.print(f"🎵 Starting download of {total_songs} Spotify songs with metadata...\n", style="bold blue")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        for i, song in enumerate(songs, 1):
            try:
                track_name = song.get('track_name', 'Unknown')
                artists = ', '.join(song.get('artist_names', ['Unknown']))
                
                progress.update(progress.add_task(
                    f"[{i}/{total_songs}] {track_name} by {artists}",
                    total=None
                ))
                
                functions.download_spotify_song(format, song, output_path, cookie_file, platform)
                console.print(f"  ✓ {track_name}", style="green")
            
            except Exception as e:
                console.print(f"  ✗ Failed to download {track_name}: {e}", style="red")
                continue


def find_csv_files(pattern: str) -> List[str]:
    """
    Find CSV files matching the given pattern
    Supports glob patterns like /path/to/*.csv
    """
    matching_files = glob.glob(pattern)
    csv_files = [f for f in matching_files if f.endswith('.csv')]
    return sorted(csv_files)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="SpotFetch CLI - Download audio from YouTube/YouTube Music using CSV playlists",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download from single CSV
  %(prog)s --input-csv playlist.csv --output ./downloads
  
  # Batch mode - download all CSVs in a folder
  %(prog)s --input-csv ./playlists/*.csv --output ./downloads
  
  # With custom format and platform
  %(prog)s --input-csv playlist.csv --output ./downloads --format flac --platform youtube
  
  # With cookie file for age-restricted content
  %(prog)s --input-csv playlist.csv --output ./downloads --cookies ~/youtube.txt
        """
    )
    
    parser.add_argument(
        "-i", "--input-csv",
        required=True,
        help="Path to CSV file(s). Supports glob patterns (e.g., ./playlists/*.csv)",
        metavar="PATH"
    )
    
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Base output directory where folders will be created",
        metavar="PATH"
    )
    
    parser.add_argument(
        "-f", "--format",
        choices=["mp3", "m4a", "flac"],
        default="mp3",
        help="Audio format (default: mp3)"
    )
    
    parser.add_argument(
        "-p", "--platform",
        choices=["youtube", "ytmusic"],
        default="ytmusic",
        help="Download platform (default: ytmusic)"
    )
    
    parser.add_argument(
        "-c", "--cookies",
        help="Path to cookies file for age-restricted content",
        metavar="PATH"
    )
    
    parser.add_argument(
        "--no-detect",
        action="store_true",
        help="Disable automatic CSV format detection, use custom format"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Validate output directory
    if not os.path.exists(args.output):
        try:
            os.makedirs(args.output, exist_ok=True)
            console.print(f"📁 Created output directory: {args.output}", style="blue")
        except Exception as e:
            console.print(f"❌ Failed to create output directory: {e}", style="red")
            sys.exit(1)
    
    # Validate cookie file if provided
    cookie_file = None
    if args.cookies:
        if not os.path.exists(args.cookies):
            console.print(f"❌ Cookie file not found: {args.cookies}", style="red")
            sys.exit(1)
        cookie_file = args.cookies
        console.print(f"🔑 Using cookie file: {cookie_file}", style="blue")
    
    # Find CSV files
    csv_files = find_csv_files(args.input_csv)
    
    if not csv_files:
        console.print(f"❌ No CSV files found matching: {args.input_csv}", style="red")
        sys.exit(1)
    
    # Display summary
    console.print(Panel(
        f"[bold cyan]SpotFetch CLI[/bold cyan]\n\n"
        f"[yellow]Files to process:[/yellow] {len(csv_files)}\n"
        f"[yellow]Output directory:[/yellow] {args.output}\n"
        f"[yellow]Audio format:[/yellow] {args.format.upper()}\n"
        f"[yellow]Platform:[/yellow] {args.platform}\n"
        f"[yellow]Auto-detect format:[/yellow] {'Yes' if not args.no_detect else 'No'}",
        title="Configuration",
        border_style="cyan"
    ))
    
    if args.verbose:
        console.print("\n📋 Files to process:", style="blue")
        for csv_file in csv_files:
            console.print(f"  • {csv_file}", style="cyan")
        console.print()
    
    # Process each CSV file
    for idx, csv_file in enumerate(csv_files, 1):
        console.print(f"\n{'='*70}", style="bright_black")
        console.print(f"[{idx}/{len(csv_files)}] Processing: {Path(csv_file).name}", style="bold cyan")
        console.print('='*70, style="bright_black")
        
        process_csv_file(
            csv_file=csv_file,
            output_path=args.output,
            format=args.format,
            platform=args.platform,
            cookie_file=cookie_file,
            auto_format=not args.no_detect
        )
    
    # Final summary
    console.print(f"\n{'='*70}", style="bright_black")
    console.print("✅ All downloads complete!", style="green bold")
    console.print('='*70, style="bright_black")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n⏹️  Download interrupted by user", style="yellow")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n❌ Unexpected error: {e}", style="red")
        if "--verbose" in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)
