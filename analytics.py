"""
SpaceScan Analytics - Advanced analysis features
Provides file type analysis, duplicate detection, and performance insights.
"""

import os
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict, Counter
import mimetypes
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class FileAnalytics:
    """Advanced file analysis for identifying space usage patterns."""
    
    def __init__(self):
        self.file_types = Counter()
        self.large_files = []
        self.duplicate_files = defaultdict(list)
        self.lock = threading.Lock()
        
    def get_file_type(self, filepath: Path) -> str:
        """Determine file type from extension."""
        suffix = filepath.suffix.lower()
        
        # Common categories
        image_types = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'}
        video_types = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
        audio_types = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'}
        document_types = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages'}
        archive_types = {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'}
        code_types = {'.py', '.js', '.html', '.css', '.cpp', '.java', '.c', '.h', '.php'}
        
        if suffix in image_types:
            return 'Images'
        elif suffix in video_types:
            return 'Videos'
        elif suffix in audio_types:
            return 'Audio'
        elif suffix in document_types:
            return 'Documents'
        elif suffix in archive_types:
            return 'Archives'
        elif suffix in code_types:
            return 'Code'
        elif suffix == '':
            return 'No Extension'
        else:
            return f'Other ({suffix})'
    
    def analyze_file(self, filepath: Path, size: int, find_duplicates: bool = False):
        """Analyze a single file for type and optionally check for duplicates."""
        file_type = self.get_file_type(filepath)
        
        with self.lock:
            self.file_types[file_type] += size
            
            # Track large files (>10MB)
            if size > 10 * 1024 * 1024:
                self.large_files.append((str(filepath), size, file_type))
        
        # Duplicate detection for files >1MB
        if find_duplicates and size > 1024 * 1024:
            try:
                file_hash = self._calculate_hash(filepath)
                with self.lock:
                    self.duplicate_files[file_hash].append((str(filepath), size))
            except (PermissionError, OSError):
                pass
    
    def _calculate_hash(self, filepath: Path, chunk_size: int = 8192) -> str:
        """Calculate MD5 hash of file for duplicate detection."""
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    hash_md5.update(chunk)
        except (PermissionError, OSError):
            return ""
        return hash_md5.hexdigest()
    
    def get_type_analysis(self) -> List[Tuple[str, int, float]]:
        """Get file type analysis sorted by size."""
        total_size = sum(self.file_types.values())
        if total_size == 0:
            return []
        
        results = []
        for file_type, size in self.file_types.most_common():
            percentage = (size / total_size) * 100
            results.append((file_type, size, percentage))
        
        return results
    
    def get_large_files(self, limit: int = 20) -> List[Tuple[str, int, str]]:
        """Get largest files sorted by size."""
        return sorted(self.large_files, key=lambda x: x[1], reverse=True)[:limit]
    
    def get_duplicates(self) -> List[Tuple[List[str], int, int]]:
        """Get duplicate file groups with total wasted space."""
        duplicates = []
        for file_hash, file_list in self.duplicate_files.items():
            if len(file_list) > 1:
                # Calculate wasted space (all copies except one)
                file_size = file_list[0][1]
                wasted_space = file_size * (len(file_list) - 1)
                file_paths = [fp for fp, _ in file_list]
                duplicates.append((file_paths, file_size, wasted_space))
        
        return sorted(duplicates, key=lambda x: x[2], reverse=True)


class ProgressTracker:
    """Real-time progress tracking for long-running operations."""
    
    def __init__(self):
        self.start_time = time.time()
        self.directories_scanned = 0
        self.files_processed = 0
        self.current_directory = ""
        self.lock = threading.Lock()
    
    def update_directory(self, directory: str):
        """Update current directory being scanned."""
        with self.lock:
            self.current_directory = directory
            self.directories_scanned += 1
    
    def update_files(self, count: int):
        """Update file count."""
        with self.lock:
            self.files_processed += count
    
    def get_progress_info(self) -> Dict:
        """Get current progress information."""
        elapsed = time.time() - self.start_time
        with self.lock:
            return {
                'elapsed_time': elapsed,
                'directories_scanned': self.directories_scanned,
                'files_processed': self.files_processed,
                'current_directory': self.current_directory,
                'files_per_second': self.files_processed / elapsed if elapsed > 0 else 0
            }
    
    def print_progress(self, force: bool = False):
        """Print progress update (throttled to avoid spam)."""
        current_time = time.time()
        
        # Only print every 2 seconds unless forced
        if not force and hasattr(self, '_last_print') and current_time - self._last_print < 2:
            return
        
        self._last_print = current_time
        info = self.get_progress_info()
        
        print(f"\rProgress: {info['directories_scanned']} dirs, "
              f"{info['files_processed']:,} files, "
              f"{info['files_per_second']:.0f} files/sec | "
              f"Current: {info['current_directory'][:60]}...", end='', flush=True)


class PerformanceMonitor:
    """Monitor and optimize scanning performance."""
    
    def __init__(self):
        self.scan_times = []
        self.memory_usage = []
        self.thread_efficiency = {}
        
    def record_scan_time(self, directory: str, scan_time: float):
        """Record time taken to scan a directory."""
        self.scan_times.append((directory, scan_time))
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics."""
        if not self.scan_times:
            return {}
        
        times = [t for _, t in self.scan_times]
        return {
            'total_scan_time': sum(times),
            'average_scan_time': sum(times) / len(times),
            'slowest_directory': max(self.scan_times, key=lambda x: x[1]),
            'fastest_directory': min(self.scan_times, key=lambda x: x[1]),
            'directories_scanned': len(self.scan_times)
        }


def format_bytes(size_bytes: int) -> str:
    """Enhanced byte formatting with more precision."""
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
    elif unit_index <= 2:  # KB, MB - show 1 decimal
        return f"{size:.1f} {units[unit_index]}"
    else:  # GB, TB, PB - show 2 decimals
        return f"{size:.2f} {units[unit_index]}"


def print_analytics_report(analytics: FileAnalytics, show_duplicates: bool = True):
    """Print comprehensive analytics report."""
    print("\n" + "=" * 80)
    print("📊 ADVANCED ANALYTICS REPORT")
    print("=" * 80)
    
    # File type analysis
    print("\n📁 FILE TYPE BREAKDOWN:")
    print("-" * 50)
    type_analysis = analytics.get_type_analysis()
    
    if type_analysis:
        print(f"{'Type':<15} {'Size':<12} {'Percentage':<10}")
        print("-" * 40)
        for file_type, size, percentage in type_analysis:
            print(f"{file_type:<15} {format_bytes(size):<12} {percentage:>6.1f}%")
    
    # Large files
    print(f"\n🔍 LARGEST FILES (Top 10):")
    print("-" * 50)
    large_files = analytics.get_large_files(10)
    
    if large_files:
        print(f"{'Size':<12} {'Type':<10} {'Path'}")
        print("-" * 70)
        for filepath, size, file_type in large_files:
            # Truncate long paths
            display_path = filepath if len(filepath) <= 50 else "..." + filepath[-47:]
            print(f"{format_bytes(size):<12} {file_type:<10} {display_path}")
    
    # Duplicate files
    if show_duplicates:
        print(f"\n🔄 DUPLICATE FILES:")
        print("-" * 50)
        duplicates = analytics.get_duplicates()
        
        if duplicates:
            total_wasted = sum(wasted for _, _, wasted in duplicates)
            print(f"Total wasted space: {format_bytes(total_wasted)}")
            print(f"Duplicate groups found: {len(duplicates)}")
            print("\nTop 5 space wasters:")
            
            for i, (file_paths, file_size, wasted_space) in enumerate(duplicates[:5]):
                print(f"\n{i+1}. {format_bytes(file_size)} each, {len(file_paths)} copies, "
                      f"wastes {format_bytes(wasted_space)}")
                for path in file_paths[:3]:  # Show first 3 paths
                    display_path = path if len(path) <= 60 else "..." + path[-57:]
                    print(f"   {display_path}")
                if len(file_paths) > 3:
                    print(f"   ... and {len(file_paths) - 3} more")
        else:
            print("No duplicate files found (files >1MB only)")
    
    print("\n" + "=" * 80)