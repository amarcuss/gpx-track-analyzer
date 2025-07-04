#!/usr/bin/env python3
"""
GPX Parser - Enhanced script to parse GPX files and analyze tracks.

This script reads a GPX file and extracts comprehensive information about all tracks,
including:
- Track names and descriptions
- Geographic place names for start/end locations using reverse geocoding
- Number of track segments and points
- Time ranges and durations
- Distance calculations and moving speed statistics (km, miles, nautical miles)
- Geographic bounds

Features:
- Reverse geocoding to get friendly place names for start/end locations
- Moving speed calculation (ignores stationary periods)
- Distance calculations using haversine formula
- Multiple unit support: kilometers, miles, nautical miles, km/h, mph, knots
- Command-line options to limit processing to first N tracks
- CSV export for structured data analysis
- Detailed console output and text file summary

Requirements:
- geopy library for reverse geocoding

Usage:
    python3 gpx_parser.py [filename] [--max-tracks=N] [--output=filename] [--csv=filename] [--help]
    
Examples:
    python3 gpx_parser.py                    # Process all tracks in explore.gpx
    python3 gpx_parser.py --max-tracks=5     # Process first 5 tracks only
    python3 gpx_parser.py myfile.gpx         # Process all tracks in myfile.gpx
    python3 gpx_parser.py myfile.gpx --max-tracks=10  # Process first 10 tracks
    python3 gpx_parser.py --output=my_tracks.txt      # Save to custom file name
    python3 gpx_parser.py --csv=tracks.csv   # Export to CSV file
    python3 gpx_parser.py myfile.gpx --max-tracks=5 --output=summary.txt --csv=export.csv  # All options
    python3 gpx_parser.py --help             # Show help message
"""

import xml.etree.ElementTree as ET
import sys
from datetime import datetime
import math
import time
import csv
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points on the earth (specified in decimal degrees).
    Returns distance in kilometers.
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r


def get_place_name(lat, lon, geolocator, max_retries=3):
    """
    Get a friendly place name for given coordinates using reverse geocoding.
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        geolocator: Nominatim geolocator instance
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        str: Friendly place name or coordinates if geocoding fails
    """
    for attempt in range(max_retries):
        try:
            location = geolocator.reverse(f"{lat}, {lon}", timeout=10)
            if location:
                address = location.raw.get('address', {})
                
                # Try to get a meaningful place name in order of preference
                place_parts = []
                
                # City/Town/Village
                city = (address.get('city') or 
                       address.get('town') or 
                       address.get('village') or 
                       address.get('hamlet'))
                
                # State/Province
                state = (address.get('state') or 
                        address.get('province') or 
                        address.get('region'))
                
                # Country
                country = address.get('country')
                
                # Build the place name
                if city:
                    place_parts.append(city)
                elif address.get('suburb'):
                    place_parts.append(address.get('suburb'))
                elif address.get('neighbourhood'):
                    place_parts.append(address.get('neighbourhood'))
                
                if state and country != 'United States':
                    place_parts.append(state)
                elif state and country == 'United States':
                    # For US, use state abbreviation if available
                    state_abbrev = get_state_abbreviation(state)
                    place_parts.append(state_abbrev)
                
                if country and country != 'United States':
                    place_parts.append(country)
                
                if place_parts:
                    return ', '.join(place_parts)
                else:
                    return f"({lat:.4f}, {lon:.4f})"
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            if attempt < max_retries - 1:
                time.sleep(1)  # Wait before retry
                continue
            else:
                print(f"Geocoding failed after {max_retries} attempts: {e}")
    
    # Return coordinates if all geocoding attempts fail
    return f"({lat:.4f}, {lon:.4f})"


def get_state_abbreviation(state_name):
    """
    Get US state abbreviation from full state name.
    """
    state_abbrevs = {
        'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
        'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
        'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
        'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
        'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
        'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
        'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
        'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
        'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
        'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
        'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
        'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
        'Wisconsin': 'WI', 'Wyoming': 'WY'
    }
    return state_abbrevs.get(state_name, state_name)


def calculate_moving_speed(segments, namespace):
    """
    Calculate average moving speed for a track, ignoring stationary periods.
    
    Args:
        segments: List of track segments
        namespace: XML namespace dictionary
        
    Returns:
        dict: Dictionary with speed statistics
    """
    total_distance = 0  # in km
    total_moving_time = 0  # in seconds
    min_movement_threshold = 0.01  # km (10 meters)
    
    all_points = []
    
    # Collect all points with time and position data
    for segment in segments:
        points = segment.findall('gpx:trkpt', namespace)
        for point in points:
            lat = float(point.get('lat', 0))
            lon = float(point.get('lon', 0))
            time_elem = point.find('gpx:time', namespace)
            
            if time_elem is not None and time_elem.text:
                try:
                    point_time = datetime.fromisoformat(time_elem.text.replace('Z', '+00:00'))
                    all_points.append({
                        'lat': lat,
                        'lon': lon,
                        'time': point_time
                    })
                except ValueError:
                    continue
    
    # Calculate moving speed
    if len(all_points) < 2:
        return {
            'avg_speed_kmh': 0,
            'avg_speed_mph': 0,
            'total_distance_km': 0,
            'total_distance_miles': 0,
            'moving_time_seconds': 0,
            'moving_time_hours': 0
        }
    
    # Sort points by time
    all_points.sort(key=lambda x: x['time'])
    
    for i in range(1, len(all_points)):
        prev_point = all_points[i-1]
        curr_point = all_points[i]
        
        # Calculate distance between consecutive points
        distance = haversine_distance(
            prev_point['lat'], prev_point['lon'],
            curr_point['lat'], curr_point['lon']
        )
        
        # Calculate time difference
        time_diff = (curr_point['time'] - prev_point['time']).total_seconds()
        
        # Only count as movement if distance is above threshold and time difference is reasonable
        if distance >= min_movement_threshold and 0 < time_diff <= 3600:  # Max 1 hour between points
            total_distance += distance
            total_moving_time += time_diff
    
    # Calculate speeds
    if total_moving_time > 0:
        avg_speed_kmh = (total_distance / total_moving_time) * 3600  # km/h
        avg_speed_mph = avg_speed_kmh * 0.621371  # mph
        moving_time_hours = total_moving_time / 3600
    else:
        avg_speed_kmh = 0
        avg_speed_mph = 0
        moving_time_hours = 0
    
    return {
        'avg_speed_kmh': avg_speed_kmh,
        'avg_speed_mph': avg_speed_mph,
        'avg_speed_knots': avg_speed_kmh * 0.539957,  # Convert km/h to knots
        'total_distance_km': total_distance,
        'total_distance_miles': total_distance * 0.621371,
        'total_distance_nautical_miles': total_distance * 0.539957,  # Convert km to nautical miles
        'moving_time_seconds': total_moving_time,
        'moving_time_hours': moving_time_hours
    }


def parse_gpx_file(file_path, max_tracks=None):
    """
    Parse a GPX file and extract track information.
    
    Args:
        file_path (str): Path to the GPX file
        max_tracks (int, optional): Maximum number of tracks to process
        
    Returns:
        list: List of dictionaries containing track information
    """
    # Initialize geocoder
    geolocator = Nominatim(user_agent="gpx_parser_v1.0")
    
    try:
        # Parse the XML file
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # GPX namespace (needed for proper XML parsing)
        namespace = {'gpx': 'http://www.topografix.com/GPX/1/1'}
        
        # Find all track elements
        tracks = root.findall('.//gpx:trk', namespace)
        
        track_info = []
        
        print(f"Found {len(tracks)} tracks. Processing...")
        
        # Limit tracks to process if requested
        if max_tracks and len(tracks) > max_tracks:
            tracks = tracks[:max_tracks]
            print(f"Limited to processing first {max_tracks} tracks")
        
        for i, track in enumerate(tracks, 1):
            print(f"Processing track {i}/{len(tracks)}...", end=' ')
            
            # Extract track name
            name_elem = track.find('gpx:name', namespace)
            track_name = name_elem.text if name_elem is not None else f"Unnamed Track {i}"
            
            # Extract track description
            desc_elem = track.find('gpx:desc', namespace)
            track_desc = desc_elem.text if desc_elem is not None and desc_elem.text else ""
            
            # Count track segments
            segments = track.findall('gpx:trkseg', namespace)
            num_segments = len(segments)
            
            # Count total track points and find start/end coordinates
            total_points = 0
            first_time = None
            last_time = None
            start_lat = start_lon = end_lat = end_lon = None
            
            for segment in segments:
                points = segment.findall('gpx:trkpt', namespace)
                total_points += len(points)
                
                # Get first point coordinates (start location)
                if points and start_lat is None:
                    start_lat = float(points[0].get('lat', 0))
                    start_lon = float(points[0].get('lon', 0))
                
                # Get last point coordinates (end location)
                if points:
                    end_lat = float(points[-1].get('lat', 0))
                    end_lon = float(points[-1].get('lon', 0))
                
                # Get time range for this track
                for point in points:
                    time_elem = point.find('gpx:time', namespace)
                    if time_elem is not None and time_elem.text:
                        try:
                            point_time = datetime.fromisoformat(time_elem.text.replace('Z', '+00:00'))
                            if first_time is None or point_time < first_time:
                                first_time = point_time
                            if last_time is None or point_time > last_time:
                                last_time = point_time
                        except ValueError:
                            pass  # Skip invalid time formats
            
            # Calculate track bounds (min/max lat/lon)
            min_lat = max_lat = min_lon = max_lon = None
            
            for segment in segments:
                points = segment.findall('gpx:trkpt', namespace)
                for point in points:
                    lat = float(point.get('lat', 0))
                    lon = float(point.get('lon', 0))
                    
                    if min_lat is None or lat < min_lat:
                        min_lat = lat
                    if max_lat is None or lat > max_lat:
                        max_lat = lat
                    if min_lon is None or lon < min_lon:
                        min_lon = lon
                    if max_lon is None or lon > max_lon:
                        max_lon = lon
            
            # Get place names for start and end locations
            start_place = "Unknown"
            end_place = "Unknown"
            
            if start_lat is not None and start_lon is not None:
                start_place = get_place_name(start_lat, start_lon, geolocator)
            
            if end_lat is not None and end_lon is not None:
                # Only do separate lookup if end is significantly different from start
                if (start_lat is None or start_lon is None or 
                    haversine_distance(start_lat, start_lon, end_lat, end_lon) > 0.5):  # 500m threshold
                    end_place = get_place_name(end_lat, end_lon, geolocator)
                else:
                    end_place = start_place
            
            # Create friendly route name
            if start_place == end_place:
                route_name = start_place
            else:
                route_name = f"{start_place} - {end_place}"
            
            # Calculate moving speed statistics
            speed_stats = calculate_moving_speed(segments, namespace)
            
            track_info.append({
                'index': i,
                'name': track_name,
                'route_name': route_name,
                'description': track_desc,
                'num_segments': num_segments,
                'total_points': total_points,
                'first_time': first_time,
                'last_time': last_time,
                'start_location': {'lat': start_lat, 'lon': start_lon, 'place': start_place},
                'end_location': {'lat': end_lat, 'lon': end_lon, 'place': end_place},
                'bounds': {
                    'min_lat': min_lat,
                    'max_lat': max_lat,
                    'min_lon': min_lon,
                    'max_lon': max_lon
                },
                'speed_stats': speed_stats
            })
            
            print("✓")
        
        return track_info
        
    except ET.ParseError as e:
        print(f"Error parsing GPX file: {e}")
        return []
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []


def print_track_summary(tracks, output_file_handle=None):
    """
    Print a summary of all tracks in the GPX file.
    
    Args:
        tracks (list): List of track dictionaries
        output_file_handle (file, optional): Open file handle for simultaneous writing
    """
    def write_line(line=""):
        """Write to both console and file if file handle is provided."""
        print(line)
        if output_file_handle:
            output_file_handle.write(line + "\n")
    
    if not tracks:
        write_line("No tracks found in the GPX file.")
        return
    
    # Calculate running totals during the summary display
    total_tracks = len(tracks)
    total_points = 0
    total_segments = 0
    total_distance_km = 0
    total_distance_miles = 0
    total_distance_nm = 0
    total_moving_time_hours = 0
    earliest_time = None
    latest_time = None
    tracks_with_time = []
    valid_distances = []
    valid_speeds = []
    
    write_line(f"\n{'='*80}")
    write_line(f"GPX FILE SUMMARY")
    write_line(f"{'='*80}")
    write_line(f"Total number of tracks: {total_tracks}")
    write_line(f"{'='*80}")
    
    for track in tracks:
        write_line(f"\nTrack #{track['index']}")
        write_line(f"  Name: {track['name']}")
        write_line(f"  Route: {track['route_name']}")
        
        if track['description']:
            write_line(f"  Description: {track['description']}")
        
        write_line(f"  Segments: {track['num_segments']}")
        write_line(f"  Total Points: {track['total_points']}")
        
        # Add to running totals
        total_points += track['total_points']
        total_segments += track['num_segments']
        
        if track['first_time'] and track['last_time']:
            write_line(f"  Time Range: {track['first_time'].strftime('%Y-%m-%d %H:%M:%S')} to {track['last_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            duration = track['last_time'] - track['first_time']
            write_line(f"  Duration: {duration}")
            
            # Track time range for summary
            tracks_with_time.append(track)
            if earliest_time is None or track['first_time'] < earliest_time:
                earliest_time = track['first_time']
            if latest_time is None or track['last_time'] > latest_time:
                latest_time = track['last_time']
        
        # Speed and distance information
        speed_stats = track['speed_stats']
        if speed_stats.get('total_distance_km', 0) > 0:
            distance_km = speed_stats.get('total_distance_km', 0)
            distance_miles = speed_stats.get('total_distance_miles', 0)
            distance_nm = speed_stats.get('total_distance_nautical_miles', 0)
            moving_time = speed_stats.get('moving_time_hours', 0)
            avg_speed_kmh = speed_stats.get('avg_speed_kmh', 0)
            avg_speed_mph = speed_stats.get('avg_speed_mph', 0)
            avg_speed_knots = speed_stats.get('avg_speed_knots', 0)
            
            write_line(f"  Distance: {distance_km:.2f} km ({distance_miles:.2f} miles, {distance_nm:.2f} nm)")
            write_line(f"  Moving Time: {moving_time:.2f} hours")
            write_line(f"  Average Speed: {avg_speed_kmh:.2f} km/h ({avg_speed_mph:.2f} mph, {avg_speed_knots:.2f} knots)")
            
            # Add to running totals
            total_distance_km += distance_km
            total_distance_miles += distance_miles
            total_distance_nm += distance_nm
            total_moving_time_hours += moving_time
            
            # Track for statistics
            if distance_km > 0:
                valid_distances.append(distance_km)
            if avg_speed_kmh > 0:
                valid_speeds.append(avg_speed_kmh)
        
        # Location information
        if track['start_location']['place'] != "Unknown":
            write_line(f"  Start: {track['start_location']['place']}")
        if track['end_location']['place'] != "Unknown" and track['end_location']['place'] != track['start_location']['place']:
            write_line(f"  End: {track['end_location']['place']}")
        
        bounds = track['bounds']
        if all(v is not None for v in bounds.values()):
            write_line(f"  Bounds: ({bounds['min_lat']:.6f}, {bounds['min_lon']:.6f}) to ({bounds['max_lat']:.6f}, {bounds['max_lon']:.6f})")
        
        write_line(f"  {'-'*70}")
    
    # Display summary statistics
    if total_tracks > 1:
        write_line(f"\n{'='*80}")
        write_line(f"SUMMARY STATISTICS")
        write_line(f"{'='*80}")
        
        write_line(f"Total Tracks: {total_tracks}")
        write_line(f"Total Segments: {total_segments}")
        write_line(f"Total Points: {total_points:,}")
        
        if earliest_time and latest_time:
            total_elapsed_time = latest_time - earliest_time
            write_line(f"Time Span: {earliest_time.strftime('%Y-%m-%d %H:%M:%S')} to {latest_time.strftime('%Y-%m-%d %H:%M:%S')}")
            write_line(f"Total Elapsed Time: {total_elapsed_time}")
            write_line(f"Tracks with Timestamps: {len(tracks_with_time)}")
        
        if total_distance_km > 0:
            write_line(f"Total Distance: {total_distance_km:.2f} km ({total_distance_miles:.2f} miles, {total_distance_nm:.2f} nm)")
            write_line(f"Total Moving Time: {total_moving_time_hours:.2f} hours")
            
            # Calculate overall average speed
            if total_moving_time_hours > 0:
                overall_avg_speed_kmh = total_distance_km / total_moving_time_hours
                overall_avg_speed_mph = overall_avg_speed_kmh * 0.621371
                overall_avg_speed_knots = overall_avg_speed_kmh * 0.539957
                write_line(f"Overall Average Speed: {overall_avg_speed_kmh:.2f} km/h ({overall_avg_speed_mph:.2f} mph, {overall_avg_speed_knots:.2f} knots)")
        
        # Additional statistics
        if valid_distances:
            write_line(f"Longest Track: {max(valid_distances):.2f} km")
            write_line(f"Shortest Track: {min(valid_distances):.2f} km")
            write_line(f"Average Track Length: {sum(valid_distances) / len(valid_distances):.2f} km")
        
        if valid_speeds:
            write_line(f"Fastest Average Speed: {max(valid_speeds):.2f} km/h")
            write_line(f"Slowest Average Speed: {min(valid_speeds):.2f} km/h")
        
        write_line(f"{'='*80}")
    
    write_line()  # Add final newline for better formatting


def export_tracks_to_csv(tracks, csv_filename):
    """
    Export track data to a CSV file.
    
    Args:
        tracks (list): List of track dictionaries
        csv_filename (str): Path to the output CSV file
    """
    if not tracks:
        print("No tracks to export to CSV.")
        return
    
    # Define CSV headers
    headers = [
        'Track_Number',
        'Track_Name',
        'Route_Description',
        'Start_Location',
        'End_Location',
        'Segments',
        'Total_Points',
        'Start_Time',
        'End_Time',
        'Duration_Hours',
        'Distance_KM',
        'Distance_Miles',
        'Distance_Nautical_Miles',
        'Moving_Time_Hours',
        'Average_Speed_KMH',
        'Average_Speed_MPH',
        'Average_Speed_Knots',
        'Min_Latitude',
        'Max_Latitude',
        'Min_Longitude',
        'Max_Longitude'
    ]
    
    try:
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header row
            writer.writerow(headers)
            
            # Write data rows
            for track in tracks:
                # Calculate duration in hours
                duration_hours = 0
                if track['first_time'] and track['last_time']:
                    duration = track['last_time'] - track['first_time']
                    duration_hours = duration.total_seconds() / 3600
                
                # Get speed stats
                speed_stats = track['speed_stats']
                
                # Format times
                start_time = track['first_time'].strftime('%Y-%m-%d %H:%M:%S') if track['first_time'] else ''
                end_time = track['last_time'].strftime('%Y-%m-%d %H:%M:%S') if track['last_time'] else ''
                
                # Prepare row data
                row = [
                    track['index'],
                    track['name'],
                    track['route_name'],
                    track['start_location']['place'],
                    track['end_location']['place'] if track['end_location']['place'] != track['start_location']['place'] else '',
                    track['num_segments'],
                    track['total_points'],
                    start_time,
                    end_time,
                    round(duration_hours, 2) if duration_hours > 0 else '',
                    round(speed_stats.get('total_distance_km', 0), 2),
                    round(speed_stats.get('total_distance_miles', 0), 2),
                    round(speed_stats.get('total_distance_nautical_miles', 0), 2),
                    round(speed_stats.get('moving_time_hours', 0), 2),
                    round(speed_stats.get('avg_speed_kmh', 0), 2),
                    round(speed_stats.get('avg_speed_mph', 0), 2),
                    round(speed_stats.get('avg_speed_knots', 0), 2),
                    round(track['bounds']['min_lat'], 6) if track['bounds']['min_lat'] is not None else '',
                    round(track['bounds']['max_lat'], 6) if track['bounds']['max_lat'] is not None else '',
                    round(track['bounds']['min_lon'], 6) if track['bounds']['min_lon'] is not None else '',
                    round(track['bounds']['max_lon'], 6) if track['bounds']['max_lon'] is not None else ''
                ]
                
                writer.writerow(row)
        
        print(f"CSV data exported to: {csv_filename}")
        
    except Exception as e:
        print(f"Error writing CSV file: {e}")


def parse_arguments():
    """Parse command line arguments."""
    import argparse
    parser = argparse.ArgumentParser(
        description='Parse GPX files and extract track information with reverse geocoding.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Examples:
  %(prog)s explore.gpx
  %(prog)s explore.gpx --max-tracks 3
  %(prog)s explore.gpx --output my_tracks.txt
  %(prog)s explore.gpx --csv tracks.csv
  %(prog)s explore.gpx --max-tracks 5 --output summary.txt --csv export.csv'''
    )
    
    parser.add_argument('gpx_file', help='GPX file to parse')
    parser.add_argument('--max-tracks', type=int, metavar='N', 
                       help='Maximum number of tracks to process')
    parser.add_argument('--output', metavar='FILE', default='track_list.txt',
                       help='Output file name (default: track_list.txt)')
    parser.add_argument('--csv', metavar='FILE',
                       help='Export per-track data to CSV file')
    
    return parser.parse_args()


def main():
    """
    Main function to run the GPX parser.
    """
    # Default file path
    default_file = "explore.gpx"
    
    # Parse command line arguments
    args = parse_arguments()
    
    file_path = args.gpx_file if args.gpx_file != '-' else default_file
    max_tracks = args.max_tracks
    output_file = args.output
    csv_file = args.csv
    
    if file_path == default_file or file_path.endswith('.gpx'):
        print(f"Parsing GPX file: {file_path}")
    else:
        print(f"Error: Invalid GPX file specified: {file_path}")
        return
    
    if max_tracks:
        print(f"Processing only first {max_tracks} tracks")
    
    try:
        # Parse the GPX file
        tracks = parse_gpx_file(file_path, max_tracks)
        
        if not tracks:
            print("No tracks found in the GPX file.")
            return
        
        # Write output to file and console simultaneously
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            header = f"GPX Track Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            header += f"Source file: {file_path}\n"
            print(header, end='')
            f.write(header)
            
            # Print track summary (using existing function)
            print_track_summary(tracks, f)
        
        print(f"\nTrack information written to '{output_file}'")
        
        # Export to CSV if requested
        if csv_file:
            export_tracks_to_csv(tracks, csv_file)
    
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except ET.ParseError as e:
        print(f"Error parsing GPX file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
