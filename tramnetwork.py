from gt_parsing import *

PATH_SAVE_DIRECTORY = "export-paths"
PATH_VISUALIZATIONS_DIRECTORY = "visualizations"

def get_tram_color(tram_name) -> str:
    if isinstance(tram_name, TramName):
        tram_name = tram_name.name
    if tram_name in gt_tram_route_map:
        gt_route = gt_tram_route_map[tram_name]
        return {
            "foreground": "#" + gt_route["route_text_color"],
            "background": "#" + gt_route["route_color"]
        }
    else:
        return {
            "foreground": "#000000",
            "background": "#00FF00"
        }

network: "TramNetwork" = None

tram_name_uid_counter = 0
class TramName:

    def __init__(self, name, uid=None):
        global tram_name_uid_counter
        self.name: str = name

        if uid is None:
            self.uid: int = tram_name_uid_counter
            tram_name_uid_counter += 1
        else:
            self.uid = uid

    def __eq__(self, other):
        if isinstance(other, TramName):
            return self.uid == other.uid
        return False
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self.name!r}, uid={self.uid!r})"
    
    def __str__(self):
        return f"T{self.name}"
    
    def __hash__(self):
        return hash(self.uid)
    
    def save_str(self) -> str:
        return f"T{self.name}:{self.uid}"
    
    @classmethod
    def from_save_str(cls, string: str) -> str:
        if string.startswith("T"):
            string = string[1:]
        if ":" in string:
            name, uid = string.split(":")
            uid = int(uid)
            return cls(name, uid)
        else:
            return cls(string)

class TramPath:

    def __init__(self, stops=None, stop_arrival_times=None, stop_departure_times=None, transportation_names=None, route_ids=None):
        self.stops: list[TramStop] = [] if stops is None else stops
        self.stop_arrival_times: list[datetime] = [] if stop_arrival_times is None else stop_arrival_times
        self.stop_departure_times: list[datetime] = [] if stop_departure_times is None else stop_departure_times
        self.transportation_names: list[TramName] = [] if transportation_names is None else transportation_names
        
    def __str__(self):
        out_str = ""
        for stop, ari, dep, tra in self.zip():
            ari = f"[{ari}]" if ari is not None else ""
            tra = f"({tra})" if tra is not None else ""
            dep = f"[{dep}]" if dep is not None else ""
            out_str += f"{ari} {stop.name:30} {tra} {dep}\n"
        return out_str
    
    def make_file_content(self):
        out_str = ""
        for stop, ari, dep, tra in self.zip():
            ari = f"[{ari}]" if ari is not None else ""
            tra = f"({tra.save_str()})" if tra is not None else ""
            dep = f"[{dep}]" if dep is not None else ""
            out_str += f"{ari} {stop.name:30} {tra} {dep}\n"
        return out_str

    def zip(self):
        return zip(self.stops, self.stop_arrival_times, self.stop_departure_times, self.transportation_names)

    def add_stop(self, stop: "TramStop"=None, arrival_time: datetime=None,
                 departure_time: datetime=None, transportation_name: TramName=None):
        self.stops.append(stop)
        self.stop_arrival_times.append(arrival_time)
        self.stop_departure_times.append(departure_time)
        self.transportation_names.append(transportation_name)
    
    def slice(self, index) -> "TramPath":
        copy = TramPath()
        copy.stops = self.stops[index:]
        copy.stop_arrival_times = self.stop_arrival_times[index:]
        copy.stop_departure_times = self.stop_departure_times[index:]
        copy.transportation_names = self.transportation_names[index:]
        return copy
    
    def __len__(self):
        return len(self.stops)
    
    @property
    def tram_name(self):
        return self.transportation_names[0]
    
    @property
    def arrival_times(self):
        return self.stop_arrival_times
    
    @property
    def departure_times(self):
        return self.stop_departure_times
    
    @property
    def arrival_time(self):
        return self.stop_arrival_times[0]
    
    @property
    def departure_time(self):
        return self.stop_departure_times[0]
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self.stops}, {self.stop_arrival_times}, {self.stop_departure_times}, {self.transportation_names})"
    
    def __lt__(self, other):
        return False
    
    def __gt__(self, other):
        return True
    
    def time_delta(self) -> timedelta:
        return self.arrival_times[-1] - self.departure_times[0]

    def cost(self) -> float:
        return self.time_delta().total_seconds()
    
    def get_info_lines(self) -> list[str]:
        return [
            f"Start: {self.stops[0].name}",
            f"Destination: {self.stops[-1].name}",
            f"Total Time: {self.time_delta()}",
            f"Start Time: {self.departure_times[0]}",
            f"Total Stops: {len(self)}",
        ]
    
    def print_summary(self):
        print(*self.get_info_lines(), sep="\n")
    
    def pop(self, index=-1):
        return (
            self.stops.pop(index),
            self.stop_arrival_times.pop(index),
            self.stop_departure_times.pop(index),
            self.transportation_names.pop(index),
        )
    
    def add_path(self, path: "TramPath", combine_trail=True):
        if len(self.stops) > 0 and self.stops[-1] == path.stops[0] and combine_trail:
            self.pop()
        self.stops += path.stops[:]
        self.stop_arrival_times += path.stop_arrival_times[:]
        self.stop_departure_times += path.stop_departure_times[:]
        self.transportation_names += path.transportation_names[:]
    
    def get_file_name(self, path_name: str, filetype="txt") -> str:
        departure_date = self.departure_times[0].date()
        time_delta = str(self.time_delta()).replace(":", "-").replace(" ", "_")
        return f"{path_name}.{departure_date}--{time_delta}.{filetype}"
    
    def save(self, path_name: str):
        file_name = self.get_file_name(path_name)
        with open(os.path.join(PATH_SAVE_DIRECTORY, file_name), "w", encoding="utf-8") as file:
            file.write(self.make_file_content())
        return file_name

    @classmethod
    def load(cls, file_name: str, network: "TramNetwork") -> "TramPath":
        path = cls()
        with open(os.path.join(PATH_SAVE_DIRECTORY, file_name), "r", encoding="utf-8") as file:
            lines = [line for line in file.read().split("\n") if line]
            last_tram_str = None
            curr_tra = None
            for line_index, line in enumerate(lines):
                # consider me the regex god (basically the following format with optional entries)
                # [2025-01-21 19:06:12] Zürich, Zürichbergstrasse      (T6:123) [2025-01-21 19:06:24]
                match = re.match(r"^(?:\[(\d+-\d+-\d+\s\d+:\d+:\d+)\])?((?:[a-zA-Zäöüß\\\/\s\,\.\-\_]|(?:\([a-zA-Zäöüß\\\/\s\,\.\-\_]*\)))+)(?:\((T?\d+(?:\:\d+)?)\))?\s*(?:\[(\d+-\d+-\d+\s\d+:\d+:\d+)\])?$", line)
                if match is None:
                    raise Exception(f"Invalid file format in {file_name=} {line_index=}")
                ari, sto, tra, dep = match.groups()
                ari = datetime.fromisoformat(ari) if ari is not None else None
                dep = datetime.fromisoformat(dep) if dep is not None else None
                stops = network.search_stops(sto.strip())
                if len(stops) == 0:
                    raise Exception(f"Unknown Stop {sto!r}")
                sto = stops[0]
                if tra == last_tram_str and curr_tra is not None:
                    tra = curr_tra
                elif tra is not None:
                    last_tram_str = tra
                    tra = TramName.from_save_str(tra)
                    curr_tra = tra
                path.add_stop(sto, ari, dep, tra)
        return path
    
    def generate_image(self, mark_stop_func=lambda s: False) -> Image:
        background_image_path = "assets/karte3.png"
        top_left_coords = (47.459425, 8.437827)
        bottom_right_coords = (47.310020, 8.637158)

        image = Image.open(background_image_path)
        draw = ImageDraw.Draw(image)
        small_font = ImageFont.truetype("C:\\Windows\\Fonts\\CascadiaCode.ttf", 12)
        big_font = ImageFont.truetype("C:\\Windows\\Fonts\\CascadiaCode.ttf", 40)
        
        def px_from_coords(coords: tuple[float]) -> list[float]:
            lat_delta = top_left_coords[0] - bottom_right_coords[0]
            lon_delta = bottom_right_coords[1] - top_left_coords[1]
            relative_x = (coords[1] - top_left_coords[1]) / lon_delta
            relative_y = 1 - (coords[0] - bottom_right_coords[0]) / lat_delta
            return [float(relative_x * image.size[0]), float(relative_y * image.size[1])]
        
        def draw_sign(position: tuple[float], text: str, foreground: str,
                      background: str, font=small_font, padding=(0, 0), line_spacing=3):
            # Break text into lines
            lines = text.split("\n")

            # Get overall font metrics: ascent is how far text goes above the baseline,
            # descent is how far it goes below.
            ascent, descent = font.getmetrics()
            
            # The "line height" is typically ascent + descent.
            # We'll add a user-defined line_spacing between lines.
            line_height = ascent + descent

            # Measure the maximum width of any line
            max_width = 0
            for line in lines:
                # For Pillow >= 8.0.0
                left, top, right, bottom = font.getbbox(line)
                width = right - left
                if width > max_width:
                    max_width = width

            # Total text height is #lines * line_height plus extra spacing between them
            # (but no extra line spacing after the last line, so use (len(lines)-1)).
            total_height = len(lines) * line_height + (len(lines) - 1) * line_spacing

            # Compute coordinates for the background box
            x1, y1 = position
            pad_x, pad_y = padding
            x2 = x1 + max_width  + 2 * pad_x
            y2 = y1 + total_height + 2 * pad_y

            # Draw the background rectangle
            draw.rectangle([x1, y1, x2, y2], fill=background)

            # We'll start drawing text at y1 + pad_y, but we need to adjust for the ascent,
            # so it looks aligned at the top of the box:
            #   - The baseline is typically "ascent" below the top of the text area.
            current_y = y1 + pad_y

            # Draw each line using the baseline approach
            for line in lines:
                # The baseline is current_y + ascent (since ascent is the top distance above baseline)
                draw.text((x1 + pad_x, current_y), line, font=font, fill=foreground)
                # Move down by line_height + line_spacing
                current_y += line_height + line_spacing
            
        for i, line in enumerate(self.get_info_lines()):
            draw_sign((10, 10 + 65 * i), line, "#FFFFFF",
                      "#000000", font=big_font, padding=(10, 5))
            
        for i, stop in enumerate(self.stops[:-1]):
            next_stop = self.stops[i + 1]
            p1 = px_from_coords(stop.coords)
            p2 = px_from_coords(next_stop.coords)
            tram = self.transportation_names[i]
            color = get_tram_color(tram)["background"]
            draw.line(p1 + p2, fill=color, width=5)
            
        stop_numbers: dict["TramStop", int] = {}
        for i, stop in enumerate(self.stops):
            if stop in stop_numbers:
                stop_numbers[stop] += 1
            else:
                stop_numbers[stop] = 1

            position = px_from_coords(stop.coords)
            position[1] += (stop_numbers[stop] - 1) * 14
            prev_tram = self.transportation_names[i - 1] if i > 0 else None
            colors = get_tram_color(prev_tram)
            if mark_stop_func(stop):
                colors = {"foreground": "#000000", "background": "#00FF00"}

            draw_sign(
                position, f"{(i + 1):03}",
                foreground=colors["foreground"],
                background=colors["background"],
                padding=(2, 0),
                font=small_font
            )
        
        return image
    
    def show(self):
        image = self.generate_image()
        image.show()

    def save_image(self, name):
        image = self.generate_image()
        file_name = self.get_file_name(name, filetype="png")
        image.save(os.path.join(PATH_VISUALIZATIONS_DIRECTORY, file_name))
        return file_name
    
    def get_direction_str(self) -> str:
        out = ""
        last_tram = None
        last_start = None
        stop_count = 0
        for stop, ari, dep, curr_tram in self.zip():
            if curr_tram is None and last_tram is not None:
                out += f"{last_start} -> {stop} ({last_tram}, {stop_count} stops)\n"
                last_start = None
            if last_tram is not None and curr_tram is not None and last_tram == curr_tram:
                stop_count += 1
            if last_tram is not None and curr_tram is not None and last_tram != curr_tram:
                out += f"{last_start} -> {stop} ({last_tram}, {stop_count} stops)\n"
                last_start = None
            if last_start is None:
                last_start = stop
                stop_count = 1
            last_tram = curr_tram
        return out[:-1]

class TramStop:

    def __repr__(self):
        return f"TramStop(name='{self.name}')"
    
    def __str__(self):
        if self.name.startswith("Zürich, "):
            return self.name[8:]
        return self.name

    def __init__(self, gt_stop):
        self.gt_stop = gt_stop

        # first stop of every tramstop connection is
        # the stop itself with arrival and departure time
        self.connections = []

    def get_departure_times(self) -> list[datetime]:
        return [c.departure_times[0] for c in self.connections]
    
    def get_arrival_times(self) -> list[datetime]:
        return [c.arrival_times[0] for c in self.connections]
    
    def get_departures_after(self, time: datetime) -> list[TramPath]:
        return [
            c for c in self.connections
            if c.departure_times[0] >= time
        ]

    def __eq__(self, value):
        if isinstance(value, TramStop):
            return self.name == value.name
        return self == value
    
    def __ne__(self, value):
        return not self.__eq__(value)
    
    def __hash__(self):
        return hash(self.name)
 
    @property
    def name(self) -> str:
        return self.gt_stop["stop_name"]
    
    @property
    def id(self):
        return self.gt_stop["stop_id"]
    
    @property
    def coords(self) -> set[float]:
        return (
            float(self.gt_stop["stop_lat"]),
            float(self.gt_stop["stop_lon"]),
        )
    
    def add_connection(self, connection):
        self.connections.append(connection)

    def sort_connections(self):
        self.connections = sorted(
            self.connections,
            key=lambda con: con.departure_time
        )

class TramNetwork:

    def __init__(self):
        self.stops: list[TramStop] = []
        self.stops_map: dict[str, TramStop] = {}
        self.loaded_date_strs: set[str] = set()

    def get_stop_from_gt(self, gt_stop) -> TramStop:
        stop_name = gt_stop["stop_name"]
        if stop_name not in self.stops_map:
            new_stop = TramStop(gt_stop)
            self.stops_map[stop_name] = new_stop
            self.stops.append(new_stop)
        return self.stops_map[stop_name]
    
    def search_stops(self, name) -> list[TramStop]:
        return [s for s in self.stops if name in s.name]

    def load_day(self, date_str: str):
        if date_str in self.loaded_date_strs:
            raise Exception(f"Already loaded {date_str}")
        
        for gt_tram_route in gt_tram_routes:
            if not gt_tram_route["route_short_name"].isnumeric():
                continue

            tram_route_name = gt_tram_route['route_short_name']
            print(f"Processing Tram Route #{tram_route_name}           ", end="\r")

            gt_tram_trips = gt_get_all(gt_trips, "route_id", gt_tram_route["route_id"])

            for gt_tram_trip in gt_tram_trips:
                if not is_trip_available(gt_tram_trip["service_id"], date_str):
                    continue

                tram_route = TramName(tram_route_name)

                gt_tram_trip_stop_times = sorted(
                    gt_stop_times_map[gt_tram_trip["trip_id"]],
                    key=lambda stop_time: int(stop_time["stop_sequence"])
                )

                gt_tram_trip_stops = [
                    gt_stops_map[stop_time["stop_id"]]
                    for stop_time in gt_tram_trip_stop_times
                ]

                # if it has a parent, select that one instead
                for i, stop in enumerate(gt_tram_trip_stops):
                    if stop["parent_station"]:
                        # rename parent because many parents are renamed to similar things
                        # like "Bahnhof" which isn't good since I assume unique names
                        parent_stop = gt_stops_map[stop["parent_station"]]
                        if "has_been_renamed" not in parent_stop:
                            parent_stop["stop_name"] = stop["stop_name"]
                            parent_stop["has_been_renamed"] = True
                        gt_tram_trip_stops[i] = parent_stop

                connection = TramPath()
                for gt_stop_time, gt_stop in zip(gt_tram_trip_stop_times, gt_tram_trip_stops):
                    tram_stop: TramStop = self.get_stop_from_gt(gt_stop)

                    connection.add_stop(tram_stop,
                        gt_parse_time(gt_stop_time["arrival_time"], date_str),
                        gt_parse_time(gt_stop_time["departure_time"], date_str),
                        tram_route)

                for i, tram_stop in enumerate(connection.stops):
                    connection_slice = connection.slice(i)
                    if len(connection_slice.stops) > 1:
                        tram_stop.add_connection(connection_slice)

        print(f"Found {len(self.stops)} Tram Stops ({date_str}).          ")

        for tram_stop in self.stops:
            tram_stop.sort_connections()

        self.loaded_date_strs.add(date_str)