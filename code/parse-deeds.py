import contextlib
import glob
import inspect
import json
import os
import re
import sys

import geojson
import numpy
import yaml
from pyproj import CRS, Transformer


FLORIDA_EAST = CRS.from_epsg(2236)
WEB_MERCATOR = CRS.from_epsg(4326)
TRANSFORMER = Transformer.from_crs(FLORIDA_EAST, WEB_MERCATOR)

FILENAMES = [
    "/Users/gulopine/Dropbox/maps.documents/deeds/ocr/DOCC547925.pdf.txt",
    "/Users/gulopine/Dropbox/maps.documents/deeds/ocr/DOCC550899.pdf.txt",
    "/Users/gulopine/Dropbox/maps.documents/deeds/ocr/DOCC550900.pdf.txt",
    "/Users/gulopine/Dropbox/maps.documents/deeds/ocr/DOCC551075.pdf.txt",
]

WHITESPACE_RE = re.compile(r"\s+")
GROUP_NAME_RE = re.compile(r"\(\?P<(\w+)>")
PLSS = yaml.safe_load(open('../maps.data/plss.yaml'))

key_lists = {
    ("nw", "nw"): "NW",
    ("nw", "ne"): "N",
    ("nw", "se"): "C",
    ("nw", "sw"): "W",

    ("ne", "nw"): "N",
    ("ne", "ne"): "NE",
    ("ne", "se"): "E",
    ("ne", "sw"): "C",

    ("se", "nw"): "C",
    ("se", "ne"): "E",
    ("se", "se"): "SE",
    ("se", "sw"): "S",

    ("sw", "nw"): "W",
    ("sw", "ne"): "C",
    ("sw", "se"): "S",
    ("sw", "sw"): "SW",
}

KEY_LISTS = {
    "nw": ["NW", "N", "C", "W"],
    "ne": ["N", "NE", "E", "C"],
    "se": ["C", "E", "SE", "S"],
    "sw": ["W", "C", "S", "SW"],
}

DEBUG = os.environ.get("DEBUG", False)
def debug(*args):
    if args and callable(args[0]):
        func = args[0]
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            debug(func.__name__, result)
            return result
        return wrapper
    if DEBUG:
        print(*args)


def stderr(*args):
    if DEBUG:
        redirect = contextlib.nullcontext()
    else:
        redirect = contextlib.redirect_stdout(sys.stderr)

    with redirect:
        print(*args)


def get_midpoint(a, b):
    return get_ratio_point(0.5, a, b)

    # ax, ay = a
    # bx, by = b
    # return ((ax + bx) / 2, (ay + by) / 2)


def get_distance(v, u):
   s = 0
   for v_i, u_i in zip(v, u):
       s += (v_i - u_i)**2
   return s ** 0.5


def get_edgepoint(amount, a, b):
    ax, ay = a
    bx, by = b
    dx = bx - ax
    dy = by - ay
    distance = (abs(dx) ** 2 + abs(dy) ** 2) ** 0.5
    ratio = amount / distance
    x = ax + ratio * dx
    y = ay + ratio * dy
    return x, y


def get_ratio_point(ratio, a, b):
    ax, ay = a
    bx, by = b
    dx = bx - ax
    dy = by - ay
    x = ax + ratio * dx
    y = ay + ratio * dy
    return x, y


def get_corner(corner, points):
    # nw, ne, se, sw = points
    if corner == "nw":
        return get_half("north", get_half("west", points))
        # return [
        #     nw,
        #     get_midpoint(nw, ne),
        #     get_midpoint(nw, se),
        #     get_midpoint(nw, sw),
        # ]
    if corner == "ne":
        return get_half("north", get_half("east", points))
        # return [
        #     get_midpoint(ne, nw),
        #     ne,
        #     get_midpoint(ne, se),
        #     get_midpoint(ne, sw),
        # ]
    if corner == "se":
        return get_half("south", get_half("east", points))
        # return [
        #     get_midpoint(se, nw),
        #     get_midpoint(se, ne),
        #     se,
        #     get_midpoint(se, sw),
        # ]
    if corner == "sw":
        return get_half("south", get_half("west", points))
        # return [
        #     get_midpoint(sw, nw),
        #     get_midpoint(sw, ne),
        #     get_midpoint(sw, se),
        #     sw,
        # ]
    return points


def get_subarea(direction, divider, amount, points):
    distance = abs(float(amount))
    nw, ne, se, sw = points
    if direction == "north":
        edge_w = divider(distance, nw, sw)
        edge_e = divider(distance, ne, se)
        if amount > 0:
            return [
                nw,
                ne,
                edge_e,
                edge_w,
            ]
        else:
            return [
                edge_w,
                edge_e,
                se,
                sw,
            ]
    if direction == "east":
        edge_n = divider(distance, ne, nw)
        edge_s = divider(distance, se, sw)
        if amount > 0:
            return [
                edge_n,
                ne,
                se,
                edge_s,
            ]
        else:
            return [
                nw,
                edge_n,
                edge_s,
                sw,
            ]
    if direction == "south":
        edge_w = divider(distance, sw, nw)
        edge_e = divider(distance, se, ne)
        if amount > 0:
            return [
                edge_w,
                edge_e,
                se,
                sw,
            ]
        else:
            return [
                nw,
                ne,
                edge_e,
                edge_w,
            ]
    if direction == "west":
        edge_n = divider(distance, nw, ne)
        edge_s = divider(distance, sw, se)
        if amount > 0:
            return [
                nw,
                edge_n,
                edge_s,
                sw,
            ]
        else:
            return [
                edge_n,
                ne,
                se,
                edge_s,
            ]

    return points


def get_ratio_edge(direction, ratio, points):
    return get_subarea(direction, get_ratio_point, ratio, points)


def get_half(direction, points):
    return get_ratio_edge(direction, 0.5, points)

    # nw, ne, se, sw = points
    # if direction == "north":
    #     return [
    #         nw,
    #         ne,
    #         get_midpoint(ne, se),
    #         get_midpoint(nw, sw),
    #     ]
    # if direction == "east":
    #     return [
    #         get_midpoint(nw, ne),
    #         ne,
    #         se,
    #         get_midpoint(se, sw),
    #     ]
    # if direction == "south":
    #     return [
    #         get_midpoint(nw, sw),
    #         get_midpoint(ne, se),
    #         se,
    #         sw,
    #     ]
    # if direction == "west":
    #     return [
    #         nw,
    #         get_midpoint(ne, nw),
    #         get_midpoint(se, sw),
    #         sw,
    #     ]

    # return points


def get_edge(direction, amount, points):
    return get_subarea(direction, get_edgepoint, amount, points, include=amount > 0)

    # nw, ne, se, sw = points
    # distance = abs(float(amount))
    # if direction == "north":
    #     edge_w = get_edgepoint(distance, nw, sw)
    #     edge_e = get_edgepoint(distance, ne, se)
    #     if amount > 0:
    #         return [
    #             nw,
    #             ne,
    #             edge_e,
    #             edge_w,
    #         ]
    #     else:
    #         return [
    #             edge_w,
    #             edge_e,
    #             se,
    #             sw,
    #         ]
    # if direction == "east":
    #     edge_n = get_edgepoint(distance, ne, nw)
    #     edge_s = get_edgepoint(distance, se, sw)
    #     if amount > 0:
    #         return [
    #             edge_n,
    #             ne,
    #             se,
    #             edge_s,
    #         ]
    #     else:
    #         return [
    #             nw,
    #             edge_n,
    #             edge_s,
    #             sw,
    #         ]
    # if direction == "south":
    #     edge_w = get_edgepoint(distance, sw, nw)
    #     edge_e = get_edgepoint(distance, se, ne)
    #     if amount > 0:
    #         return [
    #             edge_w,
    #             edge_e,
    #             se,
    #             sw,
    #         ]
    #     else:
    #         return [
    #             nw,
    #             ne,
    #             edge_e,
    #             edge_w,
    #         ]
    # if direction == "west":
    #     edge_n = get_edgepoint(distance, nw, ne)
    #     edge_s = get_edgepoint(distance, sw, se)
    #     if amount > 0:
    #         return [
    #             nw,
    #             edge_n,
    #             edge_s,
    #             sw,
    #         ]
    #     else:
    #         return [
    #             edge_n,
    #             ne,
    #             se,
    #             edge_s,
    #         ]

    # return points


def get_lot_position(index, lot_counts=(16, 8)):
    x_count, y_count = lot_counts
    total_lots = x_count * y_count

    if not 0 <= index < total_lots:
        raise ValueError("Lot index out of range", index=index)

    # N/S position is easy, because it only goes one direction, with 16 lots per row
    # E/W position is trickier, because it alternates direction on each row

    # First, a divmod separates the lots by row, leaving a remainder that indicates
    # the index within the given row. It's fine for the y-axis, but the x-axis isn't
    # done yet because lot numbers alternate directions on each row.
    # We'll deal with that soon.
    y, x = divmod(index, x_count)

    if y % 2 == 0:
        # Even-numbered rows (0-indexed) are right-to-left
        x = x_count - x - 1

    return x, y


def get_lot_area(number, *, section, lot_counts=(16, 8)):
    nw, ne, se, sw = section
    x_count, y_count = lot_counts

    # Math below is easier if this is 0-indexed
    number -= 1

    x, y = get_lot_position(number, lot_counts=lot_counts)

    n1 = get_ratio_point(y / y_count, nw, sw)
    n2 = get_ratio_point(y / y_count, ne, se)
    s1 = get_ratio_point((y + 1) / y_count, nw, sw)
    s2 = get_ratio_point((y + 1) / y_count, ne, se)

    nw = get_ratio_point(x / x_count, n1, n2)
    ne = get_ratio_point((x + 1) / x_count, n1, n2)
    se = get_ratio_point((x + 1) / x_count, s1, s2)
    sw = get_ratio_point(x / x_count, s1, s2)

    return nw, ne, se, sw


lot_examples = [
    (1, (15, 0), (True, True, False, False)),
    (2, (14, 0), (True, False, False, False)),
    (15, (1, 0), (True, False, False, False)),
    (16, (0, 0), (True, False, False, True)),
    (17, (0, 1), (False, False, True, True)),
    (18, (1, 1), (False, False, True, False)),
    (31, (14, 1), (False, False, True, False)),
    (32, (15, 1), (False, True, True, False)),
    (97, (15, 6), (True, True, False, False)),
    (98, (14, 6), (True, False, False, False)),
    (111, (1, 6), (True, False, False, False)),
    (112, (0, 6), (True, False, False, True)),
    (113, (0, 7), (False, False, True, True)),
    (114, (1, 7), (False, False, True, False)),
    (127, (14, 7), (False, False, True, False)),
    (128, (15, 7), (False, True, True, False)),
]
for lot_number, position, right_of_way in lot_examples:
    # Math below is easier if this is 0-indexed
    lot_index = lot_number - 1

    x, y = get_lot_position(lot_index)
    assert (x, y) == position

    points = [(0, 0), (100, 0), (100, 100), (0, 100)]
    for direction in ["north", "east", "south", "west"]:
        assert get_half(direction, points) == get_ratio_edge(direction, 0.5, points)
    get_lot_area(lot_number, section=points)


class Area:
    def __init__(self, obj):
        self.subdivision = None
        self.divisions = []
        self.lots = []
        self.add_data(obj)

    def __add__(self, other):
        self.add_data(other)
        return self

    def add_data(self, obj):
        debug(f"Adding {obj!r}")
        method = getattr(self, f"add_{obj.__class__.__name__}")
        method(obj)

    def add_Acres(self, acres):
        # This doesn't actually do anything, but there's no harm in storing it
        self.acres = acres

    def add_Township(self, township):
        self.township = township

    def add_Range(self, range):
        self.range = range

    def add_Section(self, section):
        self.section = section

    def add_Half(self, half):
        self.divisions.insert(0, half)

    def add_Quarter(self, quarter):
        self.divisions.insert(0, quarter)

    def add_Edge(self, edge):
        self.divisions.append(edge)

    def add_LessEdge(self, edge):
        self.divisions.append(edge)

    def add_Lots(self, lots):
        self.lots.extend(lots)

    def add_Lot(self, lot):
        self.lots.append(lot)

    def add_Subdivision(self, subdivision):
        self.subdivision = subdivision

    def divide_area(self, data, division):
        method = getattr(self, f"divide_{division.__class__.__name__}")
        return method(data, division)

    def divide_Half(self, area, half):
        return get_half(half.direction, area)

    def divide_Quarter(self, area, quarter):
        if not area:
            plss_prefix = f"{self.township.number} {self.range.number} {self.section.number}"
            return [tuple(PLSS[f"{plss_prefix} {key}"]) for key in KEY_LISTS[quarter.corner]]
        else:
            return get_corner(quarter.corner, area)

    def divide_Edge(self, area, edge):
        return get_edge(edge.direction, edge.amount, area)

    def divide_LessEdge(self, area, edge):
        return get_edge(edge.direction, -edge.amount, area)

    def calculate(self):
        area = []

        if self.subdivision:
            # TODO: Figure out a good way to deal with this later.
            # Lot numbers and sizes look predictable so far, so maybe I can auto-generate areas for them?
            stderr(f"Skipping {len(self.lots)} lots in {self.subdivision}")
            # for lot in self.lots:
            #     stderr(f"  {lot}")
            return area

        for division in self.divisions:
            debug(repr(division))
            area = self.divide_area(area, division)
            for x, y in area:
                x, y = TRANSFORMER.transform(x, y)
                debug(f"{x}, {y}")
            debug()
        return area

    def as_geometry(self):
        area = [tuple(reversed(TRANSFORMER.transform(x, y))) for x, y in self.calculate()]
        # return geojson.Polygon(area)
        return geojson.Polygon([area])


class Expression:
    def __add__(self, other):
        debug('__add__', self, other)
        return Area(self) + other

    def __radd__(self, other):
        return Area(self)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self}>"

    @classmethod
    def pattern(cls):
        original = cls.__doc__
        matches = GROUP_NAME_RE.findall(original)
        prefixed = GROUP_NAME_RE.sub(rf"(?P<{cls.__name__}_\1>", original)
        return rf"(?P<{cls.__name__}>{prefixed})"

    @classmethod
    def from_groupdict(cls, groupdict):
        sig = inspect.signature(cls.__init__)
        args = list(sig.parameters.keys())[1:]
        return cls(**{arg: WHITESPACE_RE.sub(' ', groupdict[f"{cls.__name__}_{arg}"]) for arg in args if groupdict.get(f"{cls.__name__}_{arg}")})


class Acres(Expression):
    r"(?:consisting\s+of\s+)(?P<amount>[0-9.]+|[a-z](?:[a-z]|\s)+)\s+ac(?:-\s+)?res(?:\s+more\s+or\s+less)?"

    def __init__(self, amount):
        self.amount = amount

    def __str__(self):
        return f"{self.amount} acres".title()


class Quarter(Expression):
    r"(?:(?P<corner>[ns][ew])|(?P<ns>north|south)(?P<ew>east|west)(?:ern|erly)?)\s+(?:1/4|quar(?:-\s+)?ter)"

    def __init__(self, corner=None, ns=None, ew=None):
        if corner:
            self.corner = corner
        else:
            self.corner = f"{ns[0]}{ew[0]}"

    def __str__(self):
        return f"{self.corner.upper()} Quarter"


class Half(Expression):
    r"(?P<direction>north|east|south|west)(?:ern|erly)?\s+(?:1/2|half)"

    def __init__(self, direction):
        self.direction = direction

    def __str__(self):
        return f"{self.direction} half".title()


class Section(Expression):
    r"sec(?:-\s+)?tion\s+(?P<number>[0-9]+)"

    def __init__(self, number):
        self.number = number

    def __str__(self):
        return f"Section {self.number}"


class Township(Expression):
    r"town(?:-\s+)?ship\s+(?P<number>[0-9]+)\s*(?P<direction>n|s)"

    def __init__(self, number, direction):
        self.number = number
        self.direction = direction

    def __str__(self):
        return f"Township {self.number} {self.direction}".title()


class Range(Expression):
    r"range\s+(?P<number>[0-9]+)\s*(?P<direction>w|e)"

    def __init__(self, number, direction):
        self.number = number
        self.direction = direction

    def __str__(self):
        return f"Range {self.number} {self.direction}".title()


class Edge(Expression):
    r"(?:\s+the\s+)?(?P<direction>north|east|south|west)(?:ern|erly)?[^0-9]+(?P<amount>[0-9]+)[^0-9]*\s+(?P<unit>feet|miles)"

    def __init__(self, direction, amount, unit):
        self.direction = direction
        self.amount = float(amount)
        self.unit = unit

    def __str__(self):
        return f"{self.direction} {self.amount} {self.unit}".title()


class LessEdge(Edge):
    # Format strings don't work as native docstrings, but we can use an assignment to get around that
    __doc__ = rf"less{Edge.__doc__}"


class Lot(Expression):
    r"lot\s+(?P<number>[0-9]+)\s+"

    def __init__(self, number):
        self.number = number

    def __str__(self):
        return f"Lot {self.number}"


class Lots(Expression):
    r"lots\s+(?P<numbers>(?:[0-9]+(?:[,.]\s+|\s+and\s+|\s+(?P<through>through|thru)\s+)?)+)"

    def __init__(self, numbers, through=False):
        self.numbers = Lots.RE_INTERNAL.findall(numbers)
        if through and len(self.numbers) == 2:
            first, last = self.numbers
            self.numbers = [str(n) for n in range(int(first), int(last) + 1)]

    def __str__(self):
        most = self.numbers[:-1]
        last = self.numbers[-1]
        return f"Lots {', '.join(most)} and {last}"

    RE_INTERNAL = re.compile(r"[0-9]+")

    def __iter__(self):
        for number in self.numbers:
            yield Lot(number)


class Subdivision(Expression):
    r"(?:in\s+|of\s+)?(?P<name>.+?)\s+(?:subdivision|s/d)"

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"{self.name} subdivision".title()


PROPERTY_RE = re.compile("|".join([
    Acres.pattern(),
    Quarter.pattern(),
    Half.pattern(),
    Section.pattern(),
    Township.pattern(),
    Range.pattern(),
    LessEdge.pattern(),
    Edge.pattern(),
    Lot.pattern(),
    Lots.pattern(),
    Subdivision.pattern(),
]))

if __name__ == "__main__":
    FILENAMES = sorted(glob.glob("/Users/gulopine/Dropbox/maps.documents/deeds/DOCC*.pdf.json"))
    print(FILENAMES)
    # FILENAMES = [
    #     "/Users/gulopine/Dropbox/maps.documents/deeds/DOCC589892.pdf.json",
    # ]
    all_features = []
    for i, json_filename in enumerate(FILENAMES):
        metadata = json.load(open(json_filename))
        debug(f"{metadata['parent']}:")
        txt_filename = f"/Users/gulopine/Dropbox/maps.documents/deeds/ocr/{metadata['filename']}.txt"
        extract_filename = f"/Users/gulopine/Dropbox/maps.documents/deeds/ocr/{metadata['filename']}.extract.txt"
        content = open(txt_filename).read().lower()

        if 'division' in content.lower():
            # TODO: Figure out subdivisions later, this is too much of a mess right now
            stderr(f"Skipping subdivision reference in {metadata['parent']}")

        start = 0
        end = len(content)
        parts = []
        try:
            extract = open(extract_filename).read()
        except IOError:
            with open(extract_filename, "w") as extract_file:
                matches = list(PROPERTY_RE.finditer(content.lower()))
                extract = content[matches[0].start():matches[-1].end()]
                extract_file.write(extract)

        features = []
        for match in PROPERTY_RE.finditer(content.lower()):
            if start == 0:
                start = match.start()
            end = match.end()
            klass = ""
            kwargs = {}
            for key, val in match.groupdict().items():
                if key[0].isupper() and val:
                    klass = locals()[key]
                    break
            if klass:
                # parts.append(klass(**kwargs))
                parts.append(klass.from_groupdict(match.groupdict()))
            if match.groupdict()['Range']:
                # Range is presumed to be the last entry in a property description
                debug(content[start:end])
                for part in parts:
                    debug(f"  {part}")
                area = sum(parts)
                try:
                    bbox = area.calculate()
                    if bbox:
                        stderr(f"Outputting {metadata['parent']}")
                        feature = geojson.Feature(
                            id=metadata["parent"],
                            geometry=area.as_geometry(),
                            properties=metadata,
                        )
                        features.append(feature)
                except Exception:
                    stderr(f"Error occured while processing {metadata['parent']}")
                start = 0
                end = len(content)
                parts = []
        if features:
            geojson_filename = f"/Users/gulopine/Dropbox/maps.data/deeds/{metadata['parent']}.pdf.geojson"
            with open(geojson_filename, "w") as geojson_file:
                geojson.dump(geojson.FeatureCollection(features), geojson_file)
            all_features.extend(features)
        # break
        if i == 100:
            break
    debug("\n-----\n")
    print(geojson.dumps(geojson.FeatureCollection(all_features)))
    # print(geojson.dumps(collection, indent=2, sort_keys=True))
