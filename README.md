# GPX Track Analyzer

A comprehensive Python script for parsing and analyzing GPX (GPS Exchange Format) files with detailed track statistics, reverse geocoding, and multi-unit distance/speed calculations.

## Features

### Core Functionality
- **GPX File Parsing**: Extracts track information from GPX files including segments, points, and metadata
- **Reverse Geocoding**: Converts GPS coordinates to friendly place names (e.g., "Seattle, WA")
- **Moving Speed Calculation**: Calculates accurate speeds by ignoring stationary periods
- **Multi-Unit Support**: Displays distances and speeds in multiple units:
  - Distance: Kilometers (km), Miles (mi), Nautical Miles (nm)
  - Speed: km/h, mph, knots

### Advanced Features
- **Track Limiting**: Process only the first N tracks for quick analysis
- **Custom Output Files**: Specify custom output file names
- **CSV Export**: Export structured track data to CSV files for analysis
- **HTML Visualization**: Generate interactive animated visualizations with point-by-point track drawing, speed controls, and mouseover tooltips for detailed track inspection
- **Comprehensive Statistics**: Track-by-track analysis plus overall summary
- **Simultaneous Output**: Console display and file output happen simultaneously
- **Error Handling**: Graceful handling of missing data and malformed files

### Output Information
For each track:
- Track name and route description
- Geographic start/end locations with place names
- Number of segments and GPS points
- Time range and duration
- Distance in all supported units
- Moving time (excluding stationary periods)
- Average speed in all supported units
- Geographic bounds (min/max coordinates)

Summary statistics:
- Total tracks, segments, and points
- Overall time span and elapsed time
- Total distance and moving time
- Overall average speed
- Longest/shortest track statistics
- Fastest/slowest speed statistics

## Installation

### Prerequisites
- Python 3.6 or higher
- pip package manager

### Dependencies
Install the required dependencies:

```bash
# Using pip directly
pip install geopy

# Or using requirements.txt (recommended)
pip install -r requirements.txt
```

### Download
Clone this repository or download the `gpx_parser.py` file:

```bash
git clone https://github.com/yourusername/gpx-track-analyzer.git
cd gpx-track-analyzer
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Process all tracks in default file (explore.gpx)
python3 gpx_parser.py

# Process specific GPX file
python3 gpx_parser.py my_tracks.gpx

# Process first 5 tracks only
python3 gpx_parser.py --max-tracks=5

# Save to custom output file
python3 gpx_parser.py --output=my_analysis.txt

# Export track data to CSV
python3 gpx_parser.py --csv=tracks.csv

# Generate interactive HTML visualization
python3 gpx_parser.py --html=visualization.html

# Combine all options
python3 gpx_parser.py my_tracks.gpx --max-tracks=10 --output=summary.txt --csv=export.csv --html=viz.html

# Show help
python3 gpx_parser.py --help
```

### Using as a Python Module

You can also use the GPX parser programmatically in your own Python scripts:

```python
from gpx_parser import parse_gpx_file, print_track_summary

# Parse GPX file
tracks = parse_gpx_file("my_tracks.gpx", max_tracks=5)

# Print summary to console
print_track_summary(tracks)

# Save to file
with open("output.txt", 'w') as f:
    print_track_summary(tracks, f)

# Access individual track data
for track in tracks:
    print(f"Track: {track['name']}")
    print(f"Distance: {track['speed_stats'].get('total_distance_km', 0):.2f} km")
```

See `example.py` for a complete example of programmatic usage.

### Command Line Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `filename` | GPX file to process (default: `explore.gpx`) | `python3 gpx_parser.py tracks.gpx` |
| `--max-tracks=N` | Process only first N tracks | `--max-tracks=5` |
| `--output=filename` | Custom output file name (default: `track_list.txt`) | `--output=analysis.txt` |
| `--csv=filename` | Export per-track data to CSV file | `--csv=tracks.csv` |
| `--html=filename` | Generate interactive HTML visualization | `--html=visualization.html` |
| `--help`, `-h` | Show help message and exit | `--help` |

### Example Output

```
================================================================================
GPX FILE SUMMARY
================================================================================
Total number of tracks: 3
================================================================================

Track #1
  Name: Morning Run
  Route: Seattle, WA - Bainbridge Island, WA
  Segments: 1
  Total Points: 245
  Time Range: 2019-12-14 20:02:30 to 2019-12-14 20:46:45
  Duration: 0:44:15
  Distance: 6.92 km (4.30 miles, 3.74 nm)
  Moving Time: 0.63 hours
  Average Speed: 10.93 km/h (6.79 mph, 5.90 knots)
  Start: Seattle, WA
  End: Bainbridge Island, WA
  Bounds: (47.628533, -122.459771) to (47.671598, -122.395420)

================================================================================
SUMMARY STATISTICS
================================================================================
Total Tracks: 3
Total Segments: 3
Total Points: 687
Time Span: 2019-12-14 20:02:30 to 2019-12-15 23:05:15
Total Elapsed Time: 1 day, 3:02:45
Tracks with Timestamps: 3
Total Distance: 15.32 km (9.52 miles, 8.27 nm)
Total Moving Time: 1.83 hours
Overall Average Speed: 8.35 km/h (5.19 mph, 4.51 knots)
Longest Track: 6.92 km
Shortest Track: 3.06 km
Average Track Length: 5.11 km
Fastest Average Speed: 10.93 km/h
Slowest Average Speed: 4.59 km/h
================================================================================
```

## CSV Export

The script can export track data to CSV files for further analysis in spreadsheet applications or other tools. The CSV output includes one row per track with comprehensive data in a structured format.

### CSV Features
- **Header Row**: Descriptive column names for all data fields
- **One Row Per Track**: Individual track data without summary statistics
- **Multiple Units**: Distance and speed data in kilometers, miles, nautical miles, km/h, mph, and knots
- **Complete Data**: All track information including timestamps, locations, and geographic bounds
- **UTF-8 Encoding**: Proper handling of international characters in place names

### CSV Columns
The exported CSV includes the following columns:
- `Track_Number`: Sequential track number
- `Track_Name`: Original track name from GPX file
- `Route_Description`: Start and end locations (e.g., "Seattle, WA - Bainbridge Island, WA")
- `Start_Location`: Reverse-geocoded start location
- `End_Location`: Reverse-geocoded end location (if different from start)
- `Segments`: Number of track segments
- `Total_Points`: Total number of GPS points
- `Start_Time`: Track start time (YYYY-MM-DD HH:MM:SS)
- `End_Time`: Track end time (YYYY-MM-DD HH:MM:SS)
- `Duration_Hours`: Total track duration in hours
- `Distance_KM`: Distance in kilometers
- `Distance_Miles`: Distance in miles
- `Distance_Nautical_Miles`: Distance in nautical miles
- `Moving_Time_Hours`: Moving time (excluding stationary periods) in hours
- `Average_Speed_KMH`: Average moving speed in km/h
- `Average_Speed_MPH`: Average moving speed in mph
- `Average_Speed_Knots`: Average moving speed in knots
- `Min_Latitude`: Minimum latitude coordinate
- `Max_Latitude`: Maximum latitude coordinate
- `Min_Longitude`: Minimum longitude coordinate
- `Max_Longitude`: Maximum longitude coordinate

### CSV Usage Examples

```bash
# Export all tracks to CSV
python3 gpx_parser.py my_tracks.gpx --csv=all_tracks.csv

# Export limited tracks to CSV
python3 gpx_parser.py my_tracks.gpx --max-tracks=10 --csv=first_10_tracks.csv

# Generate both text summary and CSV export
python3 gpx_parser.py my_tracks.gpx --output=summary.txt --csv=data.csv
```

### CSV Import
The generated CSV files can be imported into:
- **Excel**: Open directly or use Data > From Text/CSV
- **Google Sheets**: File > Import > Upload > Select file
- **LibreOffice Calc**: File > Open > Select file type as CSV
- **Python/Pandas**: `pd.read_csv('tracks.csv')`
- **R**: `read.csv('tracks.csv')`

## HTML Visualization

The script can generate interactive HTML visualizations that show animated, point-by-point track drawings. This feature creates a unique view of your GPS data by displaying each track's shape and movement patterns relative to their starting points.

### Visualization Features
- **Point-by-Point Animation**: Each track draws itself out progressively, showing the exact path taken
- **Relative Positioning**: Tracks are positioned relative to their starting points, emphasizing shape over geography
- **Interactive Controls**: Play, pause, reset, and speed controls for the animation
- **Color-Coded Tracks**: Each track gets a unique color for easy identification
- **Track Information**: Displays track names, distances, speeds, and point counts
- **Interactive Tooltips**: Hover over any track to see detailed information including name, route, distance, speed, duration, and point count
- **Responsive Design**: Works on desktop and mobile devices
- **Modern UI**: Beautiful gradient backgrounds and smooth animations

### How It Works
The visualization converts GPS coordinates into relative movements:
1. **Starting Point**: Each track starts from the center of its allocated space
2. **Relative Movement**: Each subsequent point is positioned relative to the previous point
3. **Scaling**: All tracks are scaled to fit within the visualization area
4. **Animation**: Points are drawn progressively to show the track development over time

### Visualization Usage

```bash
# Generate HTML visualization for all tracks
python3 gpx_parser.py my_tracks.gpx --html=tracks.html

# Generate visualization for first 10 tracks
python3 gpx_parser.py my_tracks.gpx --max-tracks=10 --html=viz.html

# Generate both text analysis and visualization
python3 gpx_parser.py my_tracks.gpx --output=analysis.txt --html=visualization.html

# Generate all outputs (text, CSV, HTML)
python3 gpx_parser.py my_tracks.gpx --output=analysis.txt --csv=data.csv --html=viz.html
```

### Visualization Controls
- **▶️ Start Animation**: Begin the point-by-point drawing animation
- **⏸️ Pause**: Pause the animation at any point
- **🔄 Reset**: Reset all tracks to their starting positions
- **Speed Slider**: Adjust animation speed from 0.1x to 3x for precise control
- **Interactive Inspection**: Hover over any track to see detailed information in a tooltip

### Interactive Features
The HTML visualization includes several interactive elements:

**Mouse Interaction:**
- **Hover for Details**: Move your mouse over any track to see a tooltip with:
  - Track name and route description
  - Total distance (in km, miles, and nautical miles)
  - Average speed (in km/h, mph, and knots)
  - Duration and total points
- **Visual Feedback**: Tracks highlight when hovered over

**Animation Controls:**
- **Speed Control**: Fine-tune animation speed with the slider (0.1x to 3x)
- **Play/Pause**: Start and stop the animation at any time
- **Reset**: Return all tracks to their starting positions

### Why Use Relative Visualization?
Traditional GPS visualizations show tracks on maps, but relative visualization offers unique benefits:
- **Shape Focus**: Emphasizes the actual path taken rather than geographic location
- **Pattern Recognition**: Makes it easier to spot similar movement patterns
- **Comparative Analysis**: Shows how different tracks relate to each other in terms of complexity
- **Animation Appeal**: Creates engaging, animated presentations of GPS data

### Browser Compatibility
The HTML visualization works in modern web browsers including:
- Chrome 60+
- Firefox 55+
- Safari 10.1+
- Edge 15+

## Technical Details

### Speed Calculation
The script calculates "moving speed" by:
1. Filtering out stationary periods (movement < 10 meters)
2. Ignoring time gaps longer than 1 hour between points
3. Computing total distance and total moving time
4. Calculating average speed from actual movement

### Reverse Geocoding
- Uses OpenStreetMap via the Nominatim service
- Implements retry logic for network issues
- Provides friendly place names with proper formatting
- Falls back to coordinates if geocoding fails
- Optimizes by reusing location names for nearby points

### Distance Calculations
- Uses the Haversine formula for great-circle distances
- Accounts for Earth's curvature for accurate measurements
- Supports multiple unit conversions:
  - 1 km = 0.621371 miles = 0.539957 nautical miles
  - 1 km/h = 0.621371 mph = 0.539957 knots

## Garmin InReach Users

If you're using a Garmin InReach GPS and downloading GPX files from [explore.garmin.com](https://explore.garmin.com), you may encounter an issue where sent messages are included in the GPX output even when not explicitly selected for export.

### Issue
InReach messages are embedded in the GPX file within `<desc></desc>` tags, which can:
- Clutter the track analysis output
- Include sensitive or personal message content
- Affect the readability of track descriptions

### Solution
Before processing your GPX file with this analyzer, clean the message data by removing content from description tags:

**Find and Replace Pattern:**
- **Find:** `<desc>.*?</desc>`
- **Replace:** `<desc />`

### How to Clean Your GPX File

**Using a Text Editor with Regex Support:**
1. Open your GPX file in a text editor that supports regular expressions (VS Code, Notepad++, Sublime Text, etc.)
2. Open the Find and Replace dialog
3. Enable "Regular Expression" mode
4. Find: `<desc>.*?</desc>`
5. Replace: `<desc />`
6. Replace All
7. Save the file

**Using Command Line (macOS/Linux):**
```bash
sed -i 's/<desc>.*?<\/desc>/<desc \/>/g' your_file.gpx
```

**Using Command Line (Windows PowerShell):**
```powershell
(Get-Content your_file.gpx) -replace '<desc>.*?</desc>', '<desc />' | Set-Content your_file.gpx
```

This will remove all message content while preserving the GPX file structure and ensuring clean track analysis output.

## File Structure

```
gpx-track-analyzer/
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI workflow
├── .gitignore                 # Git ignore rules
├── CONTRIBUTING.md            # Contribution guidelines
├── LICENSE                    # MIT License
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── gpx_parser.py             # Main script
├── test_gpx_parser.py        # Test script for development
├── example.py                # Example usage as Python module
├── explore.gpx               # Example GPX file
└── track_list.txt            # Default output file
```

## Output Files

The script generates text files with the complete analysis:
- Identical content to console output
- Formatted for easy reading
- Includes all track details and summary statistics
- Can be customized with `--output` parameter

## Error Handling

The script handles various error conditions gracefully:
- Missing or malformed GPX files
- Network issues during reverse geocoding
- Incomplete track data (missing timestamps, coordinates)
- Invalid command line arguments

## Development

### Testing
A test script is included for development:

```bash
python3 test_gpx_parser.py
```

This processes only the first 3 tracks for quick testing during development.

### Extending the Script
The code is modular and can be extended with:
- Additional output formats (JSON, CSV)
- More detailed statistics
- Integration with mapping services
- Database storage capabilities

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review the code comments for technical details

## Acknowledgments

- Uses the [geopy](https://geopy.readthedocs.io/) library for geocoding
- Reverse geocoding powered by [OpenStreetMap](https://www.openstreetmap.org/) and [Nominatim](https://nominatim.org/)
- GPX format specification: [GPX 1.1 Schema](https://www.topografix.com/GPX/1/1/)
