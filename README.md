# SpaceScan - Efficient Disk Space Analyzer

SpaceScan is a high-performance Python tool for analyzing disk space usage. It efficiently traverses directory structures and reports folder sizes in descending order, making it easy to identify space-consuming directories.

## Features

- **High Performance**: Uses multi-threading for fast directory traversal
- **Memory Efficient**: Optimized for large directory structures
- **Flexible Depth Scanning**: Scan immediate subdirectories or go deeper
- **Size Filtering**: Filter results by minimum size thresholds
- **Multiple Output Formats**: Table, CSV, and JSON output formats
- **Export Capabilities**: Save results to files
- **Error Handling**: Graceful handling of permission errors and inaccessible directories
- **Progress Feedback**: Real-time scanning feedback
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Installation

1. Clone or download this repository
2. Ensure you have Python 3.7+ installed
3. No additional dependencies required (uses only Python standard library)

## Quick Start

### Basic Usage

```bash
# Scan immediate subdirectories of C:\Users
python spacescan.py C:\Users

# Using the enhanced CLI
python spacescan_cli.py C:\Users
```

### Advanced Usage

```bash
# Use 8 threads for faster scanning
python spacescan_cli.py C:\Projects --threads 8

# Scan 2 levels deep
python spacescan_cli.py C:\Data --depth 2

# Show only folders larger than 100MB
python spacescan_cli.py C:\Users --min-size 100MB

# Export results to CSV
python spacescan_cli.py C:\Projects --export results.csv --format csv

# Quiet mode with JSON output
python spacescan_cli.py /home --quiet --format json
```

## Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--threads` | `-t` | Number of worker threads (default: auto-detect) |
| `--depth` | `-d` | Scan depth (1=immediate subdirs, 2=include their subdirs, etc.) |
| `--min-size` | | Minimum size to display (e.g., 100MB, 1GB, 500KB) |
| `--export` | `-e` | Export results to specified file |
| `--quiet` | `-q` | Suppress progress messages |
| `--format` | | Output format: table, csv, json (default: table) |

## Performance Optimizations

SpaceScan implements several optimizations for handling large directory structures:

1. **Multi-threading**: Parallel processing of subdirectories
2. **os.scandir()**: Fast directory iteration instead of os.listdir()
3. **Minimal Memory Usage**: Processes directories incrementally
4. **Error Recovery**: Continues scanning even when encountering permission errors
5. **Optimized Threading**: Automatically determines optimal thread count based on CPU cores

## Example Output

```
Scanning directory: C:\Users
Depth: 1, Threads: 4
================================================================================
Analyzing subdirectories... (this may take a while for large directories)

Directory sizes (sorted by size, largest first):
--------------------------------------------------------------------------------
Size         Path
--------------------------------------------------------------------------------
15.23 GB     C:\Users\John\Documents
8.91 GB      C:\Users\John\Desktop
4.56 GB      C:\Users\John\Downloads
2.34 GB      C:\Users\John\Pictures
1.12 GB      C:\Users\John\Videos
--------------------------------------------------------------------------------
Total directories scanned: 5
Total size: 32.16 GB
Files processed: 45,821
Scan completed in: 12.34 seconds
```

## Size Format Examples

You can specify minimum sizes using these formats:
- `100` or `100B` - 100 bytes
- `50KB` - 50 kilobytes
- `100MB` - 100 megabytes  
- `1.5GB` - 1.5 gigabytes
- `2TB` - 2 terabytes

## Error Handling

SpaceScan gracefully handles common issues:
- **Permission Denied**: Skips inaccessible directories and continues
- **File Not Found**: Handles files/directories that disappear during scanning
- **Invalid Paths**: Validates input paths before scanning
- **Interruption**: Clean exit on Ctrl+C

## Technical Details

- **Language**: Python 3.7+
- **Dependencies**: None (uses only standard library)
- **Threading**: ThreadPoolExecutor for parallel processing
- **Memory Usage**: Low memory footprint even for large directory trees
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Project Structure

```
SpaceScan/
├── spacescan.py          # Core scanning engine
├── spacescan_cli.py      # Enhanced command-line interface
├── README.md             # This documentation
└── .github/
    └── copilot-instructions.md  # Development guidelines
```

## Contributing

When contributing to SpaceScan, please follow these guidelines:
- Focus on performance and memory efficiency
- Implement proper error handling for edge cases
- Follow Python PEP 8 style guidelines
- Add tests for new functionality
- Update documentation for new features

## License

This project is open source. Feel free to use, modify, and distribute as needed.

## Troubleshooting

### Common Issues

1. **Permission Errors**: Run with appropriate permissions or expect some directories to be skipped
2. **Slow Performance**: Try reducing thread count or scanning smaller directory trees
3. **Memory Usage**: For extremely large directories, consider using depth limiting

### Performance Tips

- Use SSD storage for better I/O performance
- Increase thread count on systems with many CPU cores
- Use depth limiting for very deep directory structures
- Run during off-peak hours for large scans