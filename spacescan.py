"""
SpaceScan - Efficient Disk Space Analyzer
Main module for scanning directories and calculating folder sizes.
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Tuple, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import threading


class SpaceScan:
    """
    High-performance directory scanner that calculates folder sizes
    and displays them in descending order.
    """
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize SpaceScan with threading configuration.
        
        Args:
            max_workers: Maximum number of worker threads for parallel processing
        """
        self.max_workers = max_workers
        self.total_files_processed = 0
        self.total_errors = 0
        self.lock = threading.Lock()
        self.all_directories = {}  # Store all directory sizes
        
    def get_directory_size(self, path: Path) -> int:
        """
        Calculate the total size of a directory and all its contents.
        
        Args:
            path: Path object representing the directory
            
        Returns:
            Total size in bytes
        """
        total_size = 0
        error_count = 0
        
        try:
            for entry in os.scandir(path):
                try:
                    if entry.is_file(follow_symlinks=False):
                        total_size += entry.stat().st_size
                        with self.lock:
                            self.total_files_processed += 1
                    elif entry.is_dir(follow_symlinks=False):
                        total_size += self.get_directory_size(Path(entry.path))
                except (PermissionError, FileNotFoundError, OSError):
                    error_count += 1
                    continue
                    
        except (PermissionError, FileNotFoundError, OSError):
            with self.lock:
                self.total_errors += 1
            return 0
            
        if error_count > 0:
            with self.lock:
                self.total_errors += error_count
                
        return total_size
    
    def scan_all_subdirectories_recursive(self, root_path: Path, collect_all: bool = True) -> List[Tuple[str, int, int]]:
        """
        Recursively scan all subdirectories and collect their sizes.
        
        Args:
            root_path: Root directory to scan
            collect_all: If True, collect all subdirectories; if False, only immediate ones
            
        Returns:
            List of tuples containing (directory_path, size_in_bytes, depth_level)
        """
        if not root_path.exists() or not root_path.is_dir():
            raise ValueError(f"Invalid directory path: {root_path}")
        
        all_results = []
        
        def scan_directory_recursive(current_path: Path, depth: int = 0) -> int:
            """Recursively scan directory and collect all subdirectory sizes."""
            try:
                subdirectories = []
                total_size = 0
                
                # Get all entries in current directory
                for entry in os.scandir(current_path):
                    try:
                        if entry.is_file(follow_symlinks=False):
                            file_size = entry.stat().st_size
                            total_size += file_size
                            with self.lock:
                                self.total_files_processed += 1
                        elif entry.is_dir(follow_symlinks=False):
                            subdirectories.append(Path(entry.path))
                    except (PermissionError, FileNotFoundError, OSError):
                        with self.lock:
                            self.total_errors += 1
                        continue
                
                # Process subdirectories
                for subdir in subdirectories:
                    try:
                        # Recursively get size of subdirectory
                        subdir_size = scan_directory_recursive(subdir, depth + 1)
                        total_size += subdir_size
                        
                        # Add this subdirectory to results if collecting all
                        if collect_all:
                            all_results.append((str(subdir), subdir_size, depth + 1))
                            
                    except (PermissionError, FileNotFoundError, OSError):
                        with self.lock:
                            self.total_errors += 1
                        continue
                
                return total_size
                
            except (PermissionError, FileNotFoundError, OSError):
                with self.lock:
                    self.total_errors += 1
                return 0
        
        # Start recursive scanning
        try:
            # Get immediate subdirectories first
            immediate_subdirs = []
            for entry in os.scandir(root_path):
                if entry.is_dir(follow_symlinks=False):
                    immediate_subdirs.append(Path(entry.path))
        except PermissionError:
            print(f"Permission denied accessing: {root_path}")
            return []
        
        # Process each immediate subdirectory
        for subdir in immediate_subdirs:
            try:
                subdir_size = scan_directory_recursive(subdir, 0)
                all_results.append((str(subdir), subdir_size, 0))
            except Exception as e:
                print(f"Error processing {subdir}: {e}")
                with self.lock:
                    self.total_errors += 1
        
        return all_results
    
    def scan_all_subdirectories_threaded(self, root_path: Path) -> List[Tuple[str, int, int]]:
        """
        Scan all subdirectories using threading for better performance.
        
        Args:
            root_path: Root directory to scan
            
        Returns:
            List of tuples containing (directory_path, size_in_bytes, depth_level)
        """
        if not root_path.exists() or not root_path.is_dir():
            raise ValueError(f"Invalid directory path: {root_path}")
        
        # First, get all directories recursively
        def collect_all_directories(path: Path, depth: int = 0) -> List[Tuple[Path, int]]:
            """Collect all directories in the tree."""
            directories = []
            try:
                for entry in os.scandir(path):
                    if entry.is_dir(follow_symlinks=False):
                        subdir_path = Path(entry.path)
                        directories.append((subdir_path, depth))
                        # Recursively collect subdirectories
                        directories.extend(collect_all_directories(subdir_path, depth + 1))
            except (PermissionError, FileNotFoundError, OSError):
                pass
            return directories
        
        print("Discovering all directories...")
        all_directories = collect_all_directories(root_path)
        print(f"Found {len(all_directories)} directories to analyze")
        
        results = []
        
        # Calculate sizes using threading
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all directory scanning tasks
            future_to_path_depth = {
                executor.submit(self.get_directory_size, dir_path): (dir_path, depth)
                for dir_path, depth in all_directories
            }
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_path_depth):
                dir_path, depth = future_to_path_depth[future]
                try:
                    size = future.result()
                    results.append((str(dir_path), size, depth))
                    completed += 1
                    
                    # Progress indicator
                    if completed % 100 == 0 or completed == len(all_directories):
                        print(f"Progress: {completed}/{len(all_directories)} directories processed")
                        
                except Exception as e:
                    print(f"Error processing {dir_path}: {e}")
                    with self.lock:
                        self.total_errors += 1
        
        return results
    
    def scan_subdirectories(self, root_path: Path) -> List[Tuple[str, int]]:
        """
        Scan all immediate subdirectories and calculate their sizes using threading.
        
        Args:
            root_path: Root directory to scan
            
        Returns:
            List of tuples containing (directory_path, size_in_bytes)
        """
        if not root_path.exists() or not root_path.is_dir():
            raise ValueError(f"Invalid directory path: {root_path}")
        
        subdirectories = []
        try:
            for entry in os.scandir(root_path):
                if entry.is_dir(follow_symlinks=False):
                    subdirectories.append(Path(entry.path))
        except PermissionError:
            print(f"Permission denied accessing: {root_path}")
            return []
        
        results = []
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all directory scanning tasks
            future_to_path = {
                executor.submit(self.get_directory_size, subdir): subdir 
                for subdir in subdirectories
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_path):
                subdir = future_to_path[future]
                try:
                    size = future.result()
                    results.append((str(subdir), size))
                except Exception as e:
                    print(f"Error processing {subdir}: {e}")
                    with self.lock:
                        self.total_errors += 1
        
        return results
    
    def format_size(self, size_bytes: int) -> str:
        """
        Convert bytes to human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string (e.g., "1.23 GB")
        """
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.2f} {units[unit_index]}"
    
    def scan_and_report(self, target_path: str, show_progress: bool = True) -> None:
        """
        Main method to scan a directory and display results in descending order.
        
        Args:
            target_path: Path to scan
            show_progress: Whether to show progress indicators
        """
        root_path = Path(target_path).resolve()
        
        if not root_path.exists():
            print(f"Error: Path '{target_path}' does not exist.")
            return
        
        if not root_path.is_dir():
            print(f"Error: Path '{target_path}' is not a directory.")
            return
        
        print(f"Scanning directory: {root_path}")
        print("=" * 80)
        
        start_time = time.time()
        
        if show_progress:
            print("Analyzing subdirectories... (this may take a while for large directories)")
        
        # Scan all subdirectories
        results = self.scan_subdirectories(root_path)
        
        end_time = time.time()
        scan_duration = end_time - start_time
        
        if not results:
            print("No subdirectories found or accessible.")
            return
        
        # Sort by size in descending order
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Display results
        print(f"\nDirectory sizes (sorted by size, largest first):")
        print("-" * 80)
        print(f"{'Size':<12} {'Path'}")
        print("-" * 80)
        
        total_size = 0
        for path, size in results:
            formatted_size = self.format_size(size)
            print(f"{formatted_size:<12} {path}")
            total_size += size
        
        # Display summary
        print("-" * 80)
        print(f"Total directories scanned: {len(results)}")
        print(f"Total size: {self.format_size(total_size)}")
        print(f"Files processed: {self.total_files_processed:,}")
        if self.total_errors > 0:
            print(f"Errors encountered: {self.total_errors}")
        print(f"Scan completed in: {scan_duration:.2f} seconds")
    
    def scan_and_report_all_subdirectories(self, target_path: str, show_progress: bool = True, 
                                         use_threading: bool = True, max_display: int = 50) -> None:
        """
        Scan and report ALL subdirectories (recursive) in descending order by size.
        
        Args:
            target_path: Path to scan
            show_progress: Whether to show progress indicators
            use_threading: Whether to use threading for better performance
            max_display: Maximum number of directories to display
        """
        root_path = Path(target_path).resolve()
        
        if not root_path.exists():
            print(f"Error: Path '{target_path}' does not exist.")
            return
        
        if not root_path.is_dir():
            print(f"Error: Path '{target_path}' is not a directory.")
            return
        
        print(f"🔍 SpaceScan - ALL Subdirectories Analysis")
        print(f"📁 Scanning: {root_path}")
        print(f"🧵 Threads: {self.max_workers}")
        print(f"📊 Mode: {'Threaded' if use_threading else 'Recursive'}")
        print("=" * 80)
        
        start_time = time.time()
        
        if show_progress:
            print("Analyzing ALL subdirectories recursively... (this may take a while)")
        
        # Scan all subdirectories
        if use_threading:
            results = self.scan_all_subdirectories_threaded(root_path)
        else:
            results = self.scan_all_subdirectories_recursive(root_path)
        
        end_time = time.time()
        scan_duration = end_time - start_time
        
        if not results:
            print("No subdirectories found or accessible.")
            return
        
        # Sort by size in descending order
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Display results
        print(f"\n📂 ALL DIRECTORY SIZES (sorted by size, largest first):")
        print("=" * 100)
        print(f"{'Size':<12} {'Depth':<6} {'Path'}")
        print("=" * 100)
        
        total_size = 0
        displayed_count = 0
        
        for path, size, depth in results:
            if displayed_count >= max_display:
                remaining = len(results) - displayed_count
                print(f"... and {remaining} more directories (use --max-display to show more)")
                break
                
            formatted_size = self.format_size(size)
            
            # Add indentation based on depth for visual hierarchy
            indent = "  " * min(depth, 10)  # Limit indentation to avoid line wrapping
            display_path = Path(path).name
            
            # Truncate very long paths
            if len(display_path) > 60:
                display_path = display_path[:57] + "..."
            
            print(f"{formatted_size:<12} {depth:<6} {indent}{display_path}")
            total_size += size
            displayed_count += 1
        
        # Display comprehensive summary
        print("=" * 100)
        print(f"📊 COMPREHENSIVE SUMMARY:")
        print("-" * 40)
        print(f"Total directories found: {len(results):,}")
        print(f"Directories displayed: {displayed_count}")
        print(f"Total size analyzed: {self.format_size(total_size)}")
        print(f"Files processed: {self.total_files_processed:,}")
        print(f"Processing speed: {self.total_files_processed/scan_duration:.0f} files/sec")
        if self.total_errors > 0:
            print(f"⚠️  Errors encountered: {self.total_errors}")
        print(f"Scan completed in: {scan_duration:.2f} seconds")
        
        # Show depth distribution
        depth_counts = {}
        for _, _, depth in results:
            depth_counts[depth] = depth_counts.get(depth, 0) + 1
        
        print(f"\n📏 DEPTH DISTRIBUTION:")
        print("-" * 30)
        for depth in sorted(depth_counts.keys()):
            print(f"Level {depth}: {depth_counts[depth]:,} directories")

def main():
    """Main entry point for the SpaceScan application."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="SpaceScan - Comprehensive directory size analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python spacescan.py C:\\Users                    # Immediate subdirectories only
  python spacescan.py C:\\Users --all             # ALL subdirectories recursively
  python spacescan.py /home --all --max-display 100  # Show top 100 directories
  python spacescan.py . --all --no-threading      # Use recursive mode instead of threading
        """
    )
    
    parser.add_argument('path', help='Directory path to analyze')
    
    parser.add_argument(
        '--all', '-a', action='store_true',
        help='Scan ALL subdirectories recursively (not just immediate ones)'
    )
    
    parser.add_argument(
        '--max-display', type=int, default=50,
        help='Maximum number of directories to display (default: 50)'
    )
    
    parser.add_argument(
        '--no-threading', action='store_true',
        help='Disable threading (use recursive mode)'
    )
    
    parser.add_argument(
        '--threads', '-t', type=int, default=None,
        help='Number of worker threads (default: auto-detect)'
    )
    
    args = parser.parse_args()
    
    # Create scanner instance
    max_workers = args.threads or min(8, os.cpu_count() or 4)
    scanner = SpaceScan(max_workers=max_workers)
    
    try:
        if args.all:
            # Scan ALL subdirectories recursively
            scanner.scan_and_report_all_subdirectories(
                args.path, 
                show_progress=True,
                use_threading=not args.no_threading,
                max_display=args.max_display
            )
        else:
            # Original behavior - immediate subdirectories only
            scanner.scan_and_report(args.path)
            
    except KeyboardInterrupt:
        print("\n\nScan interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()