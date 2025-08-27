"""
SpaceScan Pro - Enhanced disk space analyzer with advanced analytics
Integrates file type analysis, duplicate detection, and real-time progress tracking.
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import List, Dict
from spacescan import SpaceScan
from analytics import FileAnalytics, ProgressTracker, PerformanceMonitor, print_analytics_report, format_bytes


class SpaceScanPro(SpaceScan):
    """Enhanced SpaceScan with advanced analytics capabilities."""
    
    def __init__(self, max_workers: int = 4, enable_analytics: bool = True, 
                 find_duplicates: bool = False, show_progress: bool = True):
        super().__init__(max_workers)
        self.enable_analytics = enable_analytics
        self.find_duplicates = find_duplicates
        self.show_progress = show_progress
        
        if enable_analytics:
            self.analytics = FileAnalytics()
            self.progress = ProgressTracker()
            self.performance = PerformanceMonitor()
    
    def get_directory_size_with_analytics(self, path: Path) -> int:
        """Enhanced directory size calculation with analytics."""
        if self.show_progress:
            self.progress.update_directory(str(path))
            self.progress.print_progress()
        
        start_time = time.time()
        total_size = 0
        file_count = 0
        
        try:
            for entry in os.scandir(path):
                try:
                    if entry.is_file(follow_symlinks=False):
                        file_size = entry.stat().st_size
                        total_size += file_size
                        file_count += 1
                        
                        # Analytics
                        if self.enable_analytics:
                            self.analytics.analyze_file(
                                Path(entry.path), 
                                file_size, 
                                self.find_duplicates
                            )
                        
                        with self.lock:
                            self.total_files_processed += 1
                            
                    elif entry.is_dir(follow_symlinks=False):
                        total_size += self.get_directory_size_with_analytics(Path(entry.path))
                        
                except (PermissionError, FileNotFoundError, OSError):
                    with self.lock:
                        self.total_errors += 1
                    continue
                    
        except (PermissionError, FileNotFoundError, OSError):
            with self.lock:
                self.total_errors += 1
            return 0
        
        # Update progress
        if self.enable_analytics:
            self.progress.update_files(file_count)
            scan_time = time.time() - start_time
            self.performance.record_scan_time(str(path), scan_time)
        
        return total_size
    
    def scan_with_analytics(self, target_path: str) -> Dict:
        """Perform comprehensive scan with analytics."""
        root_path = Path(target_path).resolve()
        
        if not root_path.exists():
            raise ValueError(f"Path '{target_path}' does not exist.")
        
        if not root_path.is_dir():
            raise ValueError(f"Path '{target_path}' is not a directory.")
        
        print(f"🔍 SpaceScan Pro - Advanced Analysis")
        print(f"📁 Target: {root_path}")
        print(f"🧵 Threads: {self.max_workers}")
        print(f"📊 Analytics: {'Enabled' if self.enable_analytics else 'Disabled'}")
        print(f"🔄 Duplicates: {'Enabled' if self.find_duplicates else 'Disabled'}")
        print("=" * 80)
        
        start_time = time.time()
        
        # Scan subdirectories with analytics
        results = []
        subdirectories = []
        
        try:
            for entry in os.scandir(root_path):
                if entry.is_dir(follow_symlinks=False):
                    subdirectories.append(Path(entry.path))
        except PermissionError:
            print(f"Permission denied accessing: {root_path}")
            return {}
        
        # Process each subdirectory
        for subdir in subdirectories:
            if self.show_progress:
                print(f"\n📂 Scanning: {subdir.name}")
            
            size = self.get_directory_size_with_analytics(subdir)
            results.append((str(subdir), size))
        
        end_time = time.time()
        
        # Clear progress line
        if self.show_progress:
            print("\r" + " " * 100 + "\r", end='')
        
        # Sort results
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Compile results
        scan_results = {
            'directories': results,
            'total_size': sum(size for _, size in results),
            'scan_time': end_time - start_time,
            'files_processed': self.total_files_processed,
            'errors': self.total_errors
        }
        
        if self.enable_analytics:
            scan_results['analytics'] = self.analytics
            scan_results['performance'] = self.performance.get_performance_stats()
        
        return scan_results
    
    def print_enhanced_report(self, results: Dict):
        """Print comprehensive report with analytics."""
        print("\n" + "=" * 80)
        print("📋 DIRECTORY SIZE REPORT")
        print("=" * 80)
        
        # Directory sizes
        directories = results['directories']
        if directories:
            print(f"\n📁 DIRECTORY SIZES (Top {min(20, len(directories))}):")
            print("-" * 60)
            print(f"{'Size':<12} {'%':<6} {'Path'}")
            print("-" * 60)
            
            total_size = results['total_size']
            for i, (path, size) in enumerate(directories[:20]):
                percentage = (size / total_size * 100) if total_size > 0 else 0
                path_display = Path(path).name if len(Path(path).name) <= 45 else Path(path).name[:42] + "..."
                print(f"{format_bytes(size):<12} {percentage:>5.1f}% {path_display}")
                
                if i == 9 and len(directories) > 10:
                    print("   ...")
        
        # Summary statistics
        print(f"\n📊 SCAN SUMMARY:")
        print("-" * 30)
        print(f"Total directories: {len(directories)}")
        print(f"Total size: {format_bytes(results['total_size'])}")
        print(f"Files processed: {results['files_processed']:,}")
        print(f"Scan time: {results['scan_time']:.2f} seconds")
        print(f"Speed: {results['files_processed']/results['scan_time']:.0f} files/sec")
        if results['errors'] > 0:
            print(f"⚠️  Errors: {results['errors']}")
        
        # Performance stats
        if 'performance' in results:
            perf = results['performance']
            if perf:
                print(f"\n⚡ PERFORMANCE DETAILS:")
                print("-" * 30)
                print(f"Average scan time per dir: {perf['average_scan_time']:.3f}s")
                slowest = perf['slowest_directory']
                print(f"Slowest directory: {Path(slowest[0]).name} ({slowest[1]:.2f}s)")
        
        # Analytics report
        if 'analytics' in results:
            print_analytics_report(results['analytics'], self.find_duplicates)


def parse_enhanced_arguments():
    """Parse command-line arguments for SpaceScan Pro."""
    parser = argparse.ArgumentParser(
        description="SpaceScan Pro - Advanced disk space analyzer with analytics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🚀 Advanced Features:
  --analytics     File type analysis and large file detection
  --duplicates    Find duplicate files (slower but comprehensive)
  --no-progress   Disable real-time progress updates
  --top N         Show top N directories (default: 20)

Examples:
  spacescan_pro.py C:\\Users --analytics
  spacescan_pro.py /home --duplicates --threads 8
  spacescan_pro.py . --analytics --duplicates --export analysis.json
        """
    )
    
    parser.add_argument('path', help='Directory path to analyze')
    
    parser.add_argument(
        '--threads', '-t', type=int, default=None,
        help='Number of worker threads (default: auto-detect)'
    )
    
    parser.add_argument(
        '--analytics', '-a', action='store_true',
        help='Enable file type analysis and large file detection'
    )
    
    parser.add_argument(
        '--duplicates', '-d', action='store_true',
        help='Find duplicate files (files >1MB, slower scan)'
    )
    
    parser.add_argument(
        '--no-progress', action='store_true',
        help='Disable real-time progress updates'
    )
    
    parser.add_argument(
        '--export', '-e', type=str,
        help='Export detailed results to JSON file'
    )
    
    parser.add_argument(
        '--top', type=int, default=20,
        help='Number of top directories to display (default: 20)'
    )
    
    parser.add_argument(
        '--min-size', type=str, default='0',
        help='Minimum directory size to display (e.g., 100MB)'
    )
    
    parser.add_argument(
        '--quiet', '-q', action='store_true',
        help='Minimal output mode'
    )
    
    return parser.parse_args()


def export_results_json(results: Dict, filepath: str):
    """Export comprehensive results to JSON."""
    import json
    
    export_data = {
        'scan_info': {
            'total_directories': len(results['directories']),
            'total_size_bytes': results['total_size'],
            'total_size_formatted': format_bytes(results['total_size']),
            'files_processed': results['files_processed'],
            'scan_time_seconds': results['scan_time'],
            'errors_encountered': results['errors']
        },
        'directories': [
            {
                'path': path,
                'size_bytes': size,
                'size_formatted': format_bytes(size),
                'percentage': (size / results['total_size'] * 100) if results['total_size'] > 0 else 0
            }
            for path, size in results['directories']
        ]
    }
    
    # Add analytics if available
    if 'analytics' in results:
        analytics = results['analytics']
        
        export_data['file_types'] = [
            {
                'type': file_type,
                'size_bytes': size,
                'size_formatted': format_bytes(size),
                'percentage': percentage
            }
            for file_type, size, percentage in analytics.get_type_analysis()
        ]
        
        export_data['largest_files'] = [
            {
                'path': path,
                'size_bytes': size,
                'size_formatted': format_bytes(size),
                'type': file_type
            }
            for path, size, file_type in analytics.get_large_files(50)
        ]
        
        duplicates = analytics.get_duplicates()
        if duplicates:
            export_data['duplicates'] = [
                {
                    'files': file_paths,
                    'file_size_bytes': file_size,
                    'file_size_formatted': format_bytes(file_size),
                    'copies': len(file_paths),
                    'wasted_space_bytes': wasted_space,
                    'wasted_space_formatted': format_bytes(wasted_space)
                }
                for file_paths, file_size, wasted_space in duplicates
            ]
    
    with open(filepath, 'w') as f:
        json.dump(export_data, f, indent=2)


def main():
    """Main entry point for SpaceScan Pro."""
    try:
        args = parse_enhanced_arguments()
        
        # Parse minimum size
        from spacescan_cli import parse_size_string
        min_size_bytes = parse_size_string(args.min_size)
        
        # Determine thread count
        max_workers = args.threads or min(8, os.cpu_count() or 4)
        
        # Create enhanced scanner
        scanner = SpaceScanPro(
            max_workers=max_workers,
            enable_analytics=args.analytics,
            find_duplicates=args.duplicates,
            show_progress=not args.no_progress and not args.quiet
        )
        
        # Perform scan
        results = scanner.scan_with_analytics(args.path)
        
        # Filter by minimum size
        if min_size_bytes > 0:
            results['directories'] = [
                (path, size) for path, size in results['directories'] 
                if size >= min_size_bytes
            ]
            results['total_size'] = sum(size for _, size in results['directories'])
        
        # Display results
        if not args.quiet:
            scanner.print_enhanced_report(results)
        
        # Export if requested
        if args.export:
            export_results_json(results, args.export)
            if not args.quiet:
                print(f"\n💾 Results exported to: {args.export}")
        
        # Quick summary for quiet mode
        if args.quiet:
            print(f"Scanned {len(results['directories'])} directories, "
                  f"{format_bytes(results['total_size'])} total, "
                  f"{results['files_processed']:,} files in {results['scan_time']:.1f}s")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Scan interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()