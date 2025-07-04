#!/usr/bin/env python3
"""
GPX Parser Test - Test version that processes only first 3 tracks
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gpx_parser import parse_gpx_file, print_track_summary

def test_first_tracks():
    """Test the parser with first 3 tracks only"""
    print("Testing GPX parser with first 3 tracks...")
    
    # Parse the GPX file
    test_tracks = parse_gpx_file("explore.gpx", 3)
    
    if test_tracks:
        print_track_summary(test_tracks)
        
        # Save test results
        output_file = "test_track_list.txt"
        with open(output_file, 'w') as f:
            f.write("GPX Track Summary (First 3 Tracks - Test)\n")
            f.write("=" * 80 + "\n\n")
            for track in test_tracks:
                f.write(f"Track #{track['index']}: {track['name']}\n")
                f.write(f"  Route: {track['route_name']}\n")
                f.write(f"  Segments: {track['num_segments']}, Points: {track['total_points']}\n")
                
                if track['first_time'] and track['last_time']:
                    f.write(f"  Time Range: {track['first_time'].strftime('%Y-%m-%d %H:%M:%S')} to {track['last_time'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                speed_stats = track['speed_stats']
                if speed_stats['total_distance_km'] > 0:
                    f.write(f"  Distance: {speed_stats['total_distance_km']:.2f} km ({speed_stats['total_distance_miles']:.2f} miles, {speed_stats['total_distance_nautical_miles']:.2f} nm)\n")
                    f.write(f"  Moving Time: {speed_stats['moving_time_hours']:.2f} hours\n")
                    f.write(f"  Average Speed: {speed_stats['avg_speed_kmh']:.2f} km/h ({speed_stats['avg_speed_mph']:.2f} mph, {speed_stats['avg_speed_knots']:.2f} knots)\n")
                
                f.write("\n")
        print(f"\nTest results saved to: {output_file}")
    else:
        print("No tracks found or error occurred.")

if __name__ == "__main__":
    test_first_tracks()
