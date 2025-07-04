#!/usr/bin/env python3
"""
Example usage of GPX Track Analyzer as a Python module.

This script demonstrates how to use the gpx_parser module
programmatically instead of from the command line.
"""

from gpx_parser import parse_gpx_file, print_track_summary

def main():
    """Example of using gpx_parser as a module."""
    
    # Parse a GPX file (limit to 3 tracks for this example)
    print("Parsing GPX file...")
    tracks = parse_gpx_file("explore.gpx", max_tracks=3)
    
    if tracks:
        print(f"Successfully parsed {len(tracks)} tracks")
        
        # Print summary to console
        print_track_summary(tracks)
        
        # Save to a custom file
        with open("example_output.txt", 'w') as f:
            f.write("Example GPX Analysis\n")
            f.write("=" * 50 + "\n")
            print_track_summary(tracks, f)
        
        print("\nExample analysis saved to: example_output.txt")
        
        # Access individual track data
        print("\nFirst track details:")
        first_track = tracks[0]
        print(f"  Name: {first_track['name']}")
        print(f"  Route: {first_track['route_name']}")
        print(f"  Distance: {first_track['speed_stats'].get('total_distance_km', 0):.2f} km")
        
    else:
        print("No tracks found or error occurred.")

if __name__ == "__main__":
    main()
