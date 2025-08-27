"""
SpaceScan CLI - Enhanced command-line interface
Provides advanced options for directory scanning and reporting.
"""

import argparse
import os
import sys
import re
from pathlib import Path
from typing import List
from spacescan import SpaceScan

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="SpaceScan - Efficient disk space analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  spacescan_cli.py C:\\Users                         # Basic scan (immediate subdirs)
  spacescan_cli.py C:\\Users --all                  # ALL subdirectories recursively
  spacescan_cli.py /home --all --threads 8          # Use 8 threads, scan all
  spacescan_cli.py C:\\Projects --all --depth 3     # Limit to 3 levels deep
  spacescan_cli.py . --all --min-size 100MB         # Show folders >= 100MB, all subdirs
  spacescan_cli.py /data --all --export results.txt --max-display 100  # Export top 100
        """
    )
    
    parser.add_argument(
        'path',
        help='Directory path to analyze'
    )
    
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Scan ALL subdirectories recursively (not just immediate ones)'
    )
    
    parser.add_argument(
        '--threads', '-t',
        type=int,
        default=None,
        help='Number of worker threads (default: auto-detect optimal)'
    )
    
    parser.add_argument(
        '--depth', '-d',
        type=int,
        default=None,
        help='Maximum scan depth (only works with --all flag)'
    )
    
    parser.add_argument(
        '--min-size',
        type=str,
        default='0',
        help='Minimum size to display (e.g., 100MB, 1GB, 500KB)'
    )
    
    parser.add_argument(
        '--max-display',
        type=int,
        default=50,
        help='Maximum number of directories to display (default: 50)'
    )
    
    parser.add_argument(
        '--export', '-e',
        type=str,
        help='Export results to specified file'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress messages'
    )
    
    parser.add_argument(
        '--format',
        choices=['table', 'csv', 'json'],
        default='table',
        help='Output format (default: table)'
    )
    
    parser.add_argument(
        '--no-threading',
        action='store_true',
        help='Disable threading (use recursive mode instead)'
    )
    
    return parser.parse_args()


def parse_size_string(size_str: str) -> int:
    """
    Parse size string like '100MB', '1.5GB' into bytes.
    
    Args:
        size_str: Size string with unit
        
    Returns:
        Size in bytes
    """
    size_str = size_str.upper().strip()
    
    if size_str == '0':
        return 0
    
    # Extract number and unit
    match = re.match(r'^(\d+(?:\.\d+)?)\s*([KMGTPB]?B?)$', size_str)
    if not match:
        raise ValueError(f"Invalid size format: {size_str}")
    
    number, unit = match.groups()
    number = float(number)
    
    # Convert to bytes
    multipliers = {
        'B': 1,
        'KB': 1024,
        'MB': 1024**2,
        'GB': 1024**3,
        'TB': 1024**4,
        'PB': 1024**5
    }
    
    if unit == '':
        unit = 'B'
    
    if unit not in multipliers:
        raise ValueError(f"Unknown unit: {unit}")
    
    return int(number * multipliers[unit])


class EnhancedSpaceScan(SpaceScan):
    """Enhanced SpaceScan with additional CLI features."""
    
    def __init__(self, max_workers: int = 4, max_depth: int = None):
        super().__init__(max_workers)
        self.max_depth = max_depth
    
    def scan_with_depth_limit(self, root_path: Path, use_threading: bool = True) -> List:
        """
        Scan directories with configurable depth limit.
        
        Args:
            root_path: Root directory to scan
            use_threading: Whether to use threading
            
        Returns:
            List of (path, size, depth) tuples filtered by max_depth
        """
        if use_threading:
            results = self.scan_all_subdirectories_threaded(root_path)
        else:
            results = self.scan_all_subdirectories_recursive(root_path)
        
        # Filter by depth if specified
        if self.max_depth is not None:
            results = [(path, size, depth) for path, size, depth in results 
                      if depth <= self.max_depth]
        
        return results
    
    def export_results_enhanced(self, results: List, filepath: str, format_type: str, include_depth: bool = False):
        """Export results to file in specified format with optional depth info."""
        import json
        import csv
        
        if format_type == 'json':
            if include_depth:
                data = [
                    {
                        'path': path,
                        'size_bytes': size,
                        'size_formatted': self.format_size(size),
                        'depth': depth if len(result) > 2 else 0
                    }
                    for result in results
                    for path, size, *depth_info in [result]
                    for depth in [depth_info[0] if depth_info else 0]
                ]
            else:
                data = [
                    {
                        'path': path,
                        'size_bytes': size,
                        'size_formatted': self.format_size(size)
                    }
                    for result in results
                    for path, size in [(result[0], result[1])]
                ]
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        
        elif format_type == 'csv':
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                
                if include_depth:
                    writer.writerow(['Path', 'Size (Bytes)', 'Size (Formatted)', 'Depth'])
                    for result in results:
                        path, size = result[0], result[1]
                        depth = result[2] if len(result) > 2 else 0
                        writer.writerow([path, size, self.format_size(size), depth])
                else:
                    writer.writerow(['Path', 'Size (Bytes)', 'Size (Formatted)'])
                    for result in results:
                        path, size = result[0], result[1]
                        writer.writerow([path, size, self.format_size(size)])
        
        else:  # table format
            with open(filepath, 'w') as f:
                if include_depth:
                    f.write(f"{'Size':<12} {'Depth':<6} {'Path'}\n")
                    f.write("=" * 100 + "\n")
                    for result in results:
                        path, size = result[0], result[1]
                        depth = result[2] if len(result) > 2 else 0
                        indent = "  " * min(depth, 10)
                        display_path = Path(path).name
                        f.write(f"{self.format_size(size):<12} {depth:<6} {indent}{display_path}\n")
                else:
                    f.write(f"{'Size':<12} {'Path'}\n")
                    f.write("-" * 80 + "\n")
                    for result in results:
                        path, size = result[0], result[1]
                        f.write(f"{self.format_size(size):<12} {path}\n")


def main():
    """Enhanced CLI main function with recursive directory support."""
    try:
        args = parse_arguments()
        
        # Determine optimal thread count
        max_workers = args.threads or min(8, os.cpu_count() or 4)
        
        # Parse minimum size
        min_size_bytes = parse_size_string(args.min_size)
        
        # Create enhanced scanner
        scanner = EnhancedSpaceScan(
            max_workers=max_workers,
            max_depth=args.depth
        )
        
        root_path = Path(args.path).resolve()
        
        if not root_path.exists():
            print(f"Error: Path '{args.path}' does not exist.")
            sys.exit(1)
        
        if not root_path.is_dir():
            print(f"Error: Path '{args.path}' is not a directory.")
            sys.exit(1)
        
        if not args.quiet:
            print(f"🔍 SpaceScan {'Pro' if args.all else 'Standard'}")
            print(f"📁 Target: {root_path}")
            print(f"🧵 Threads: {max_workers}")
            print(f"📊 Mode: {'All Subdirectories' if args.all else 'Immediate Subdirectories'}")
            if args.all and args.depth:
                print(f"📏 Max Depth: {args.depth}")
            if min_size_bytes > 0:
                print(f"📐 Min Size: {scanner.format_size(min_size_bytes)}")
            print("=" * 80)
        
        # Perform scan
        if args.all:
            # Scan ALL subdirectories recursively
            if hasattr(scanner, 'scan_with_depth_limit'):
                results = scanner.scan_with_depth_limit(root_path, not args.no_threading)
            else:
                if not args.no_threading:
                    results = scanner.scan_all_subdirectories_threaded(root_path)
                else:
                    results = scanner.scan_all_subdirectories_recursive(root_path)
            
            # Results have depth information: (path, size, depth)
            include_depth = True
        else:
            # Original immediate subdirectories only
            temp_results = scanner.scan_subdirectories(root_path)
            # Convert to consistent format: (path, size, depth)
            results = [(path, size, 0) for path, size in temp_results]
            include_depth = False
        
        # Filter by minimum size
        if min_size_bytes > 0:
            results = [(path, size, depth) for path, size, depth in results if size >= min_size_bytes]
        
        # Sort by size (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        if not results:
            print("No directories found matching criteria.")
            return
        
        # Limit display count
        display_results = results[:args.max_display] if args.max_display > 0 else results
        
        # Display or export results
        if args.export:
            scanner.export_results_enhanced(results, args.export, args.format, include_depth)
            if not args.quiet:
                print(f"💾 Results exported to: {args.export}")
        
        # Display results (unless very quiet and exporting)
        if not (args.quiet and args.export):
            if args.format == 'table':
                print(f"\n📂 DIRECTORY SIZES ({'All Subdirectories' if args.all else 'Immediate Subdirectories'}):")
                if include_depth:
                    print("=" * 100)
                    print(f"{'Size':<12} {'Depth':<6} {'Path'}")
                    print("=" * 100)
                    
                    for path, size, depth in display_results:
                        formatted_size = scanner.format_size(size)
                        indent = "  " * min(depth, 10)
                        display_path = Path(path).name
                        if len(display_path) > 60:
                            display_path = display_path[:57] + "..."
                        print(f"{formatted_size:<12} {depth:<6} {indent}{display_path}")
                else:
                    print("-" * 80)
                    print(f"{'Size':<12} {'Path'}")
                    print("-" * 80)
                    
                    for path, size, depth in display_results:
                        formatted_size = scanner.format_size(size)
                        print(f"{formatted_size:<12} {path}")
                
                # Show truncation message
                if len(results) > args.max_display > 0:
                    remaining = len(results) - args.max_display
                    print(f"... and {remaining} more directories (use --max-display to show more)")
                
            elif args.format == 'csv':
                if include_depth:
                    print("Path,Size (Bytes),Size (Formatted),Depth")
                    for path, size, depth in display_results:
                        print(f'"{path}",{size},{scanner.format_size(size)},{depth}')
                else:
                    print("Path,Size (Bytes),Size (Formatted)")
                    for path, size, depth in display_results:
                        print(f'"{path}",{size},{scanner.format_size(size)}')
            
            elif args.format == 'json':
                import json
                if include_depth:
                    data = [
                        {
                            'path': path,
                            'size_bytes': size,
                            'size_formatted': scanner.format_size(size),
                            'depth': depth
                        }
                        for path, size, depth in display_results
                    ]
                else:
                    data = [
                        {
                            'path': path,
                            'size_bytes': size,
                            'size_formatted': scanner.format_size(size)
                        }
                        for path, size, depth in display_results
                    ]
                print(json.dumps(data, indent=2))
        
        # Summary
        if not args.quiet:
            total_size = sum(size for _, size, _ in results)
            print("=" * (100 if include_depth else 80))
            print(f"📊 SUMMARY:")
            print("-" * 30)
            print(f"Total directories found: {len(results):,}")
            print(f"Directories displayed: {len(display_results)}")
            print(f"Total size: {scanner.format_size(total_size)}")
            print(f"Files processed: {scanner.total_files_processed:,}")
            if scanner.total_errors > 0:
                print(f"⚠️  Errors encountered: {scanner.total_errors}")
            
            # Depth distribution for recursive scans
            if args.all and include_depth:
                depth_counts = {}
                for _, _, depth in results:
                    depth_counts[depth] = depth_counts.get(depth, 0) + 1
                
                if len(depth_counts) > 1:
                    print(f"\n📏 DEPTH DISTRIBUTION:")
                    print("-" * 30)
                    for depth in sorted(depth_counts.keys()):
                        print(f"Level {depth}: {depth_counts[depth]:,} directories")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Scan interrupted by user.")
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()