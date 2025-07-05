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
- HTML visualization export for animated track visualizations

Requirements:
- geopy library for reverse geocoding

Usage:
    python3 gpx_parser.py [filename] [--max-tracks=N] [--output=filename] [--csv=filename] [--html=filename] [--help]
    
Examples:
    python3 gpx_parser.py                    # Process all tracks in explore.gpx
    python3 gpx_parser.py --max-tracks=5     # Process first 5 tracks only
    python3 gpx_parser.py myfile.gpx         # Process all tracks in myfile.gpx
    python3 gpx_parser.py myfile.gpx --max-tracks=10  # Process first 10 tracks
    python3 gpx_parser.py --output=my_tracks.txt      # Save to custom file name
    python3 gpx_parser.py --csv=tracks.csv   # Export to CSV file
    python3 gpx_parser.py --html=viz.html    # Export to HTML visualization
    python3 gpx_parser.py myfile.gpx --max-tracks=5 --output=summary.txt --csv=export.csv --html=viz.html  # All options
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


def export_tracks_to_html_visualization(tracks, html_filename, gpx_file_path):
    """
    Export track data to an interactive HTML visualization with point-by-point animation.
    
    Args:
        tracks (list): List of track dictionaries
        html_filename (str): Path to the output HTML file
        gpx_file_path (str): Path to the original GPX file for detailed point extraction
    """
    if not tracks:
        print("No tracks to export to HTML visualization.")
        return
    
    # Calculate track data for visualization with all GPS points
    track_data = []
    
    # Re-parse the GPX file to get all detailed points
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(gpx_file_path)
        root = tree.getroot()
        
        # Handle namespace
        namespace = {'gpx': 'http://www.topografix.com/GPX/1/1'}
        if root.tag.startswith('{'):
            ns_uri = root.tag.split('}')[0][1:]
            namespace = {'gpx': ns_uri}
        
        track_elements = root.findall('.//gpx:trk', namespace)
        
        for track_idx, (track, track_elem) in enumerate(zip(tracks, track_elements)):
            try:
                # Extract all GPS points for this track
                points_data = extract_detailed_track_points(gpx_file_path, track_elem, namespace)
                
                if points_data and len(points_data) > 1:
                    # Convert to relative coordinates for animation
                    relative_points = []
                    if points_data:
                        # Calculate relative movements from the first point
                        first_lat = points_data[0]['lat']
                        first_lon = points_data[0]['lon']
                        
                        for point in points_data:
                            # Calculate relative displacement in degrees
                            relative_lat = point['lat'] - first_lat
                            relative_lon = point['lon'] - first_lon
                            
                            # Convert to approximate distances (rough approximation)
                            # 1 degree latitude ≈ 111 km, longitude varies by latitude
                            lat_km = relative_lat * 111
                            lon_km = relative_lon * 111 * abs(math.cos(math.radians(first_lat)))
                            
                            relative_points.append({
                                'lat': point['lat'],
                                'lon': point['lon'],
                                'relative_lat_km': lat_km,
                                'relative_lon_km': lon_km,
                                'time': point['time'].isoformat() if point['time'] else None
                            })
                    
                    track_data.append({
                        'index': track['index'],
                        'name': track['name'],
                        'route_name': track['route_name'],
                        'points': relative_points,
                        'total_distance': track['speed_stats'].get('total_distance_km', 0),
                        'avg_speed': track['speed_stats'].get('avg_speed_kmh', 0),
                        'duration': (track['last_time'] - track['first_time']).total_seconds() / 3600 if track['first_time'] and track['last_time'] else 0
                    })
            except Exception as e:
                print(f"Warning: Could not process track {track['index']} for visualization: {e}")
                continue
    except Exception as e:
        print(f"Warning: Could not re-parse GPX file for visualization: {e}")
        return
    
    # Generate HTML content
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GPX Track Visualization</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            min-height: 100vh;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }}
        
        .header p {{
            margin: 10px 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        
        .controls {{
            text-align: center;
            margin-bottom: 30px;
        }}
        
        .controls button {{
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            border: none;
            color: white;
            padding: 12px 24px;
            margin: 0 10px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}
        
        .controls button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }}
        
        .controls button:disabled {{
            background: #666;
            cursor: not-allowed;
            transform: none;
        }}
        
        .controls label {{
            margin-left: 20px;
            font-weight: bold;
        }}
        
        .controls input[type="range"] {{
            margin-left: 10px;
            width: 150px;
        }}
        
        .canvas-container {{
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }}
        
        #trackCanvas {{
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 10px;
            background: rgba(0,0,0,0.2);
            display: block;
            margin: 0 auto;
            cursor: crosshair;
        }}
        
        .tooltip {{
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 10px;
            border-radius: 8px;
            font-size: 0.9em;
            pointer-events: none;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.2);
            max-width: 300px;
            display: none;
        }}
        
        .tooltip h4 {{
            margin: 0 0 8px 0;
            color: #ff6b6b;
            font-size: 1em;
        }}
        
        .tooltip p {{
            margin: 4px 0;
            line-height: 1.3;
        }}
        
        .track-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .track-item {{
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid;
            backdrop-filter: blur(5px);
        }}
        
        .track-item h3 {{
            margin: 0 0 10px 0;
            font-size: 1.1em;
        }}
        
        .track-item p {{
            margin: 5px 0;
            opacity: 0.9;
            font-size: 0.9em;
        }}
        
        .stats {{
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}
        
        .stats h2 {{
            margin: 0 0 20px 0;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}
        
        .stat-item {{
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            display: block;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            opacity: 0.8;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🗺️ GPX Track Visualization</h1>
        <p>Interactive visualization of {len(tracks)} GPS tracks</p>
        <p>All tracks start from the center and radiate outward showing relative movement patterns</p>
    </div>
    
    <div class="controls">
        <button id="startBtn">▶️ Start Animation</button>
        <button id="pauseBtn" disabled>⏸️ Pause</button>
        <button id="resetBtn">🔄 Reset</button>
        <label for="speedSlider">Speed:</label>
        <input type="range" id="speedSlider" min="0.1" max="3" step="0.1" value="0.5">
        <span id="speedValue">0.5x</span>
    </div>
    
    <div class="canvas-container">
        <canvas id="trackCanvas" width="1200" height="800"></canvas>
        <div id="tooltip" class="tooltip"></div>
    </div>
    
    <div class="track-info" id="trackInfo">
        <!-- Track information will be populated by JavaScript -->
    </div>
    
    <div class="stats">
        <h2>📊 Summary Statistics</h2>
        <div class="stats-grid">
            <div class="stat-item">
                <span class="stat-value">{len(tracks)}</span>
                <span class="stat-label">Total Tracks</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">{sum(t['speed_stats'].get('total_distance_km', 0) for t in tracks):.1f} km</span>
                <span class="stat-label">Total Distance</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">{sum(t['speed_stats'].get('moving_time_hours', 0) for t in tracks):.1f} hrs</span>
                <span class="stat-label">Total Moving Time</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">{(sum(t['speed_stats'].get('total_distance_km', 0) for t in tracks) / max(sum(t['speed_stats'].get('moving_time_hours', 0) for t in tracks), 1)):.1f} km/h</span>
                <span class="stat-label">Average Speed</span>
            </div>
        </div>
    </div>

    <script>
        // Track data from Python
        const trackData = {repr(track_data)};
        
        // Canvas setup
        const canvas = document.getElementById('trackCanvas');
        const ctx = canvas.getContext('2d');
        
        // Animation state
        let isAnimating = false;
        let animationSpeed = 0.5;
        let currentFrame = 0;
        let animationId = null;
        
        // Mouse tracking for tooltips
        let mouseX = 0;
        let mouseY = 0;
        let hoveredTrack = null;
        let trackPaths = []; // Store track path data for hit detection
        
        // Visualization settings
        const TRACK_HEIGHT = 30;
        const TRACK_SPACING = 40;
        const CANVAS_PADDING = 50;
        const POINT_SPACING = 3;
        
        // Color palette for tracks
        const colors = [
            '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57',
            '#ff9ff3', '#54a0ff', '#5f27cd', '#00d2d3', '#ff9f43',
            '#10ac84', '#ee5253', '#0abde3', '#3742fa', '#2f3542'
        ];
        
        // Control event listeners
        document.getElementById('startBtn').addEventListener('click', startAnimation);
        document.getElementById('pauseBtn').addEventListener('click', pauseAnimation);
        document.getElementById('resetBtn').addEventListener('click', resetAnimation);
        document.getElementById('speedSlider').addEventListener('input', updateSpeed);
        
        // Mouse event listeners for tooltips
        canvas.addEventListener('mousemove', handleMouseMove);
        canvas.addEventListener('mouseleave', handleMouseLeave);
        
        function updateSpeed(e) {{
            animationSpeed = parseFloat(e.target.value);
            document.getElementById('speedValue').textContent = animationSpeed + 'x';
        }}
        
        function handleMouseMove(e) {{
            const rect = canvas.getBoundingClientRect();
            mouseX = e.clientX - rect.left;
            mouseY = e.clientY - rect.top;
            
            // Check if mouse is over any track
            const newHoveredTrack = getTrackAtPosition(mouseX, mouseY);
            
            if (newHoveredTrack !== hoveredTrack) {{
                hoveredTrack = newHoveredTrack;
                updateTooltip(e.clientX, e.clientY);
            }}
        }}
        
        function handleMouseLeave() {{
            hoveredTrack = null;
            hideTooltip();
        }}
        
        function getTrackAtPosition(x, y) {{
            const tolerance = 8; // Pixels tolerance for hit detection
            
            for (let trackIndex = 0; trackIndex < trackPaths.length; trackIndex++) {{
                const path = trackPaths[trackIndex];
                if (!path || path.length < 2) continue;
                
                for (let i = 1; i < path.length; i++) {{
                    const p1 = path[i - 1];
                    const p2 = path[i];
                    
                    if (distanceToLineSegment(x, y, p1.x, p1.y, p2.x, p2.y) < tolerance) {{
                        return trackIndex;
                    }}
                }}
            }}
            return null;
        }}
        
        function distanceToLineSegment(px, py, x1, y1, x2, y2) {{
            const dx = x2 - x1;
            const dy = y2 - y1;
            const length = Math.sqrt(dx * dx + dy * dy);
            
            if (length === 0) {{
                return Math.sqrt((px - x1) * (px - x1) + (py - y1) * (py - y1));
            }}
            
            const t = Math.max(0, Math.min(1, ((px - x1) * dx + (py - y1) * dy) / (length * length)));
            const projection = {{
                x: x1 + t * dx,
                y: y1 + t * dy
            }};
            
            return Math.sqrt((px - projection.x) * (px - projection.x) + (py - projection.y) * (py - projection.y));
        }}
        
        function updateTooltip(clientX, clientY) {{
            const tooltip = document.getElementById('tooltip');
            
            if (hoveredTrack !== null && hoveredTrack < trackData.length) {{
                const track = trackData[hoveredTrack];
                const color = colors[hoveredTrack % colors.length];
                
                tooltip.innerHTML = `
                    <h4 style="color: ${{color}}">Track ${{track.index}}: ${{track.name}}</h4>
                    <p><strong>Route:</strong> ${{track.route_name}}</p>
                    <p><strong>Distance:</strong> ${{track.total_distance.toFixed(2)}} km</p>
                    <p><strong>Average Speed:</strong> ${{track.avg_speed.toFixed(1)}} km/h</p>
                    <p><strong>Duration:</strong> ${{track.duration.toFixed(1)}} hours</p>
                    <p><strong>Points:</strong> ${{track.points.length}}</p>
                `;
                
                // Position tooltip near mouse but keep it on screen
                const tooltipRect = tooltip.getBoundingClientRect();
                let left = clientX + 10;
                let top = clientY - 10;
                
                // Adjust if tooltip would go off screen
                if (left + 300 > window.innerWidth) {{
                    left = clientX - 310;
                }}
                if (top < 10) {{
                    top = clientY + 20;
                }}
                
                tooltip.style.left = left + 'px';
                tooltip.style.top = top + 'px';
                tooltip.style.display = 'block';
            }} else {{
                hideTooltip();
            }}
        }}
        
        function hideTooltip() {{
            document.getElementById('tooltip').style.display = 'none';
        }}
        
        function startAnimation() {{
            isAnimating = true;
            document.getElementById('startBtn').disabled = true;
            document.getElementById('pauseBtn').disabled = false;
            animate();
        }}
        
        function pauseAnimation() {{
            isAnimating = false;
            document.getElementById('startBtn').disabled = false;
            document.getElementById('pauseBtn').disabled = true;
            if (animationId) {{
                clearTimeout(animationId);  // Use clearTimeout instead of cancelAnimationFrame
            }}
        }}
        
        function resetAnimation() {{
            isAnimating = false;
            currentFrame = 0;
            document.getElementById('startBtn').disabled = false;
            document.getElementById('pauseBtn').disabled = true;
            if (animationId) {{
                clearTimeout(animationId);  // Use clearTimeout instead of cancelAnimationFrame
            }}
            
            // Clear the canvas completely
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Redraw the background and center point
            ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Draw center point
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;
            ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
            ctx.beginPath();
            ctx.arc(centerX, centerY, 4, 0, 2 * Math.PI);
            ctx.fill();
        }}
        
        function drawTracks() {{
            // Clear canvas
            ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Reset track paths for hit detection
            trackPaths = [];
            
            // Calculate canvas center
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;
            
            // Find the maximum extent for dynamic scaling
            let maxExtent = 0;
            
            trackData.forEach(track => {{
                if (track.points && track.points.length > 0) {{
                    // Show points based on current frame (now 1:1 with actual points)
                    const pointsToShow = Math.min(currentFrame, track.points.length);
                    
                    for (let i = 0; i < pointsToShow; i++) {{
                        const point = track.points[i];
                        const distance = Math.sqrt(
                            Math.pow(point.relative_lat_km, 2) + 
                            Math.pow(point.relative_lon_km, 2)
                        );
                        maxExtent = Math.max(maxExtent, distance);
                    }}
                }}
            }});
            
            // Calculate scale to fit all tracks with padding
            const availableSize = Math.min(canvas.width, canvas.height) - 2 * CANVAS_PADDING;
            const scale = maxExtent > 0 ? availableSize / (maxExtent * 2.2) : 1;
            
            // Draw center point
            ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
            ctx.beginPath();
            ctx.arc(centerX, centerY, 4, 0, 2 * Math.PI);
            ctx.fill();
            
            // Draw each track starting from center
            trackData.forEach((track, trackIndex) => {{
                if (!track.points || track.points.length === 0) {{
                    trackPaths[trackIndex] = [];
                    return;
                }}
                
                const color = colors[trackIndex % colors.length];
                
                // Calculate how many points to show based on current frame
                const pointsToShow = Math.min(currentFrame, track.points.length);
                
                // Initialize path storage for this track
                trackPaths[trackIndex] = [];
                
                if (pointsToShow > 0) {{
                    // Set drawing style
                    ctx.strokeStyle = color;
                    ctx.lineWidth = 2;
                    ctx.globalAlpha = 0.8;
                    
                    // Starting position (center of canvas)
                    let currentX = centerX;
                    let currentY = centerY;
                    
                    // Store starting point for hit detection
                    trackPaths[trackIndex].push({{x: currentX, y: currentY}});
                    
                    // Draw start point
                    ctx.fillStyle = color;
                    ctx.globalAlpha = 1;
                    ctx.beginPath();
                    ctx.arc(currentX, currentY, 3, 0, 2 * Math.PI);
                    ctx.fill();
                    
                    // Draw path segments
                    ctx.globalAlpha = 0.8;
                    for (let i = 1; i < pointsToShow; i++) {{
                        const point = track.points[i];
                        const prevPoint = track.points[i-1];
                        
                        // Calculate relative movement from previous point
                        const deltaLat = point.relative_lat_km - prevPoint.relative_lat_km;
                        const deltaLon = point.relative_lon_km - prevPoint.relative_lon_km;
                        
                        // Scale and apply to canvas coordinates
                        const deltaX = deltaLon * scale;
                        const deltaY = -deltaLat * scale; // Negative because canvas Y increases downward
                        
                        const newX = currentX + deltaX;
                        const newY = currentY + deltaY;
                        
                        // Store point for hit detection
                        trackPaths[trackIndex].push({{x: newX, y: newY}});
                        
                        // Draw line to new position
                        ctx.strokeStyle = color;
                        ctx.lineWidth = 2;
                        ctx.beginPath();
                        ctx.moveTo(currentX, currentY);
                        ctx.lineTo(newX, newY);
                        ctx.stroke();
                        
                        // Draw small point
                        ctx.fillStyle = color;
                        ctx.globalAlpha = 0.6;
                        ctx.beginPath();
                        ctx.arc(newX, newY, 1, 0, 2 * Math.PI);
                        ctx.fill();
                        
                        currentX = newX;
                        currentY = newY;
                    }}
                    
                    // Draw current position with larger dot if animation is active
                    if (pointsToShow > 0 && pointsToShow < track.points.length) {{
                        ctx.fillStyle = color;
                        ctx.globalAlpha = 1;
                        ctx.beginPath();
                        ctx.arc(currentX, currentY, 5, 0, 2 * Math.PI);
                        ctx.fill();
                        
                        // Add a glow effect
                        ctx.shadowColor = color;
                        ctx.shadowBlur = 10;
                        ctx.beginPath();
                        ctx.arc(currentX, currentY, 3, 0, 2 * Math.PI);
                        ctx.fill();
                        ctx.shadowBlur = 0;
                    }}
                    
                    ctx.globalAlpha = 1;
                }}
            }});
            
            // Draw scale indicator
            if (maxExtent > 0) {{
                ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
                ctx.font = '12px Arial';
                ctx.textAlign = 'left';
                ctx.fillText(`Scale: 1 pixel = ${{(1/scale).toFixed(2)}} km`, 10, canvas.height - 10);
            }}
        }}
        
        function animate() {{
            if (!isAnimating) return;
            
            currentFrame += 1;  // Always increment by 1 for smoother control
            drawTracks();
            
            // Check if animation is complete
            const maxFrames = Math.max(...trackData.map(track => track.points ? track.points.length : 0));
            if (currentFrame >= maxFrames) {{
                pauseAnimation();
                return;
            }}
            
            // Use setTimeout with speed-controlled delay instead of requestAnimationFrame
            const delay = Math.max(10, 1000 / (animationSpeed * 60));  // Convert speed to milliseconds delay
            animationId = setTimeout(animate, delay);
        }}
        
        // Initialize track info
        function initializeTrackInfo() {{
            const trackInfoContainer = document.getElementById('trackInfo');
            
            trackData.forEach((track, index) => {{
                const trackItem = document.createElement('div');
                trackItem.className = 'track-item';
                trackItem.style.borderLeftColor = colors[index % colors.length];
                
                trackItem.innerHTML = `
                    <h3>Track ${{track.index}}: ${{track.name}}</h3>
                    <p><strong>Route:</strong> ${{track.route_name}}</p>
                    <p><strong>Distance:</strong> ${{track.total_distance.toFixed(2)}} km</p>
                    <p><strong>Average Speed:</strong> ${{track.avg_speed.toFixed(1)}} km/h</p>
                    <p><strong>Duration:</strong> ${{track.duration.toFixed(1)}} hours</p>
                `;
                
                trackInfoContainer.appendChild(trackItem);
            }});
        }}
        
        // Initialize visualization
        drawTracks();
        initializeTrackInfo();
        
        // Resize canvas on window resize
        window.addEventListener('resize', () => {{
            // Could add responsive canvas resizing here
        }});
    </script>
</body>
</html>'''
    
    try:
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML visualization exported to: {html_filename}")
        
    except Exception as e:
        print(f"Error writing HTML visualization file: {e}")


def extract_detailed_track_points(file_path, track_element, namespace):
    """
    Extract detailed GPS points from a specific track for visualization.
    
    Args:
        file_path (str): Path to the GPX file
        track_element: XML track element
        namespace: XML namespace dictionary
        
    Returns:
        list: List of GPS points with lat, lon, time
    """
    points = []
    
    try:
        segments = track_element.findall('gpx:trkseg', namespace)
        
        for segment in segments:
            track_points = segment.findall('gpx:trkpt', namespace)
            
            for point in track_points:
                lat = float(point.get('lat', 0))
                lon = float(point.get('lon', 0))
                
                time_elem = point.find('gpx:time', namespace)
                point_time = None
                
                if time_elem is not None and time_elem.text:
                    try:
                        point_time = datetime.fromisoformat(time_elem.text.replace('Z', '+00:00'))
                    except ValueError:
                        pass
                
                points.append({
                    'lat': lat,
                    'lon': lon,
                    'time': point_time
                })
    
    except Exception as e:
        print(f"Warning: Could not extract detailed points: {e}")
    
    return points


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
  %(prog)s explore.gpx --html visualization.html
  %(prog)s explore.gpx --max-tracks 5 --output summary.txt --csv export.csv --html viz.html'''
    )
    
    parser.add_argument('gpx_file', help='GPX file to parse')
    parser.add_argument('--max-tracks', type=int, metavar='N', 
                       help='Maximum number of tracks to process')
    parser.add_argument('--output', metavar='FILE', default='track_list.txt',
                       help='Output file name (default: track_list.txt)')
    parser.add_argument('--csv', metavar='FILE',
                       help='Export per-track data to CSV file')
    parser.add_argument('--html', metavar='FILE',
                       help='Export interactive HTML visualization')
    
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
    html_file = args.html
    
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
        
        # Export to HTML visualization if requested
        if html_file:
            export_tracks_to_html_visualization(tracks, html_file, file_path)
        elif not csv_file:  # Auto-generate HTML visualization if no specific output requested
            auto_html_file = output_file.replace('.txt', '_visualization.html')
            export_tracks_to_html_visualization(tracks, auto_html_file, file_path)
    
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
