import csv, os, copy, re, math
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

GT_DIRECTORY_PATH = "2025_google_transit"
GT_TRAM_STOP_TYPE = "0"

def haversine_distance(coord1, coord2):
    R = 6371.0
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    a = math.sin(delta_lat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

def load_gt_file(file_name):
    file_path = os.path.join(GT_DIRECTORY_PATH, file_name)
    with open(file_path, "r", encoding="utf-8-sig") as file:
        reader = csv.reader(file, delimiter=",", quotechar='"')
        headers = next(reader)
        exported_rows = []
        for row in reader:
            exported_row = {}
            for header, item in zip(headers, row):
                exported_row[header] = item
            exported_rows.append(exported_row)
        print(f"loaded {file_name}")
        return exported_rows
    
def gt_get_first(data_rows, field_name, value):
    for row in data_rows:
        if row[field_name] == value:
            return row
    raise Exception(f"Row not found with {field_name=} {value=}")

def gt_has_row(data_rows, field_name, value):
    for row in data_rows:
        if row[field_name] == value:
            return True
    return False

def gt_make_1_1_map(data_rows, id_field_name, force=False):
    data_map = {}
    for row in data_rows:
        row_id = row[id_field_name]
        if row_id in data_map and not force:
            raise Exception("multiple rows with same id found")
        data_map[row_id] = row
    return data_map

def gt_make_1_many_map(data_rows, id_field_name):
    data_map = {}
    for row in data_rows:
        row_id = row[id_field_name]
        if row_id in data_map:
            data_map[row_id].append(row)
        else:
            data_map[row_id] = [row]
    return data_map

def gt_get_all(data_rows, field_name, value):
    return [
        row for row in data_rows
        if row[field_name] == value
    ]

def gt_parse_date(date_str):
    year = int(date_str[0:4])
    month = int(date_str[4:6])
    day = int(date_str[6:8])
    return datetime(year, month, day)

def gt_parse_time(time_str, date_str: str):
    h, m, s = [int(i) for i in time_str.split(":")]
    date = gt_parse_date(date_str)
    if h >= 24:
        h -= 24
        date += timedelta(days=1)
    return datetime(date.year, date.month, date.day, h, m, s)

def gt_date_strs_between(start_date_str, end_date_str, test_date_str):
    start_date = gt_parse_date(start_date_str)
    end_date = gt_parse_date(end_date_str)
    test_date = gt_parse_date(test_date_str)
    return gt_dates_between(start_date, end_date, test_date)

def gt_dates_between(start_date, end_date, test_date):
    return (start_date <= test_date) and (test_date <= end_date)

gt_routes = load_gt_file("routes.txt")
gt_transfers = load_gt_file("transfers.txt")
gt_stops = load_gt_file("stops.txt")
gt_trips = load_gt_file("trips.txt")
gt_stop_times = load_gt_file("stop_times.txt")
gt_calendar = load_gt_file("calendar.txt")
gt_calendar_dates = load_gt_file("calendar_dates.txt")

gt_stops_map = gt_make_1_1_map(gt_stops, "stop_id")
gt_stop_times_map = gt_make_1_many_map(gt_stop_times, "trip_id")
gt_calendar_map = gt_make_1_1_map(gt_calendar, "service_id")
gt_calendar_dates_map = gt_make_1_many_map(gt_calendar_dates, "service_id")
gt_route_map = gt_make_1_1_map(gt_routes, "route_id")

gt_tram_routes = [
    route for route in gt_routes
    if route["route_type"] == GT_TRAM_STOP_TYPE
]

gt_tram_route_map = gt_make_1_1_map(gt_tram_routes, "route_short_name")

GT_WEEKDAY_NAMES = [
    "monday", "tuesday", "wednesday",
    "thursday", "friday", "saturday", "sunday"
]

def is_trip_available(service_id, date_str):
    lookup_date = gt_parse_date(date_str)
    calendar = gt_calendar_map[service_id]
    start_date = gt_parse_date(calendar["start_date"])
    end_date = gt_parse_date(calendar["end_date"])
    if not gt_dates_between(start_date, end_date, lookup_date):
        return False
    
    weekday_name = GT_WEEKDAY_NAMES[lookup_date.weekday()]
    normally_available = calendar[weekday_name] == "1"

    if service_id in gt_calendar_dates_map:
        exception_calendar_dates = gt_calendar_dates_map[service_id]
        for calendar_date in exception_calendar_dates:
            if calendar_date != date_str:
                continue
            exception_type = calendar_date["exception_type"]
            if exception_type == "1":
                return True # service added
            elif exception_type == "2":
                return False # service removed
        
    return normally_available