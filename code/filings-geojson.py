from __future__ import division

import datetime
import json
import pyproj
import re
import sys
import yaml
from math import ceil, cos, degrees as deg, pi, radians, sin, tan
# from pyproj import Proj, transform

line_re = re.compile(r'(N|S) +(\d+) +(\d+) +([\d.]+) +(E|W) +([\d.]+)')
curve_re = re.compile(r'(L|R) +([\d.]+) +(\d+) +(\d+) +([\d.]+)(?: +([\d.]+))?')
# proj = Proj('EPSG:2236')
THRESHOLD = 1  # feet

class OffsetEnding(ValueError):
    pass

def make_url(doc):
    return 'http://or.occompt.com/recorder/eagleweb/downloads/{0}.pdf?parent={0}'.format(doc)

def make_points(origin, beginning, shape, include_origin=False, closed=False, ignore_end=True):
    if include_origin:
        yield origin, False  # Origin

    x, y = origin

    for bearing, distance, interpolated in beginning:
        horizontal = sin(bearing) * distance
        vertical = cos(bearing) * distance
        x += horizontal
        y += vertical

        if include_origin:
            yield (x, y), interpolated  # Point from origin to beginning

    beginning = (x, y)
    if not include_origin:
        yield beginning, False  # Only if the origin wasn't already included

    shape = list(shape)
    last_i = len(shape) - 1

    for i, (bearing, distance, interpolated) in enumerate(shape):
        horizontal = sin(bearing) * distance
        vertical = cos(bearing) * distance
        x += horizontal
        y += vertical
        if i == last_i:
            off = point_distance((x, y), beginning)
            if off < THRESHOLD:
                # Reached the end and it's close enough to the beginning that the
                # difference is likely just floating point error
                yield beginning, False
            elif ignore_end:
                yield (x, y), interpolated
                if closed:
                    yield beginning, False
            else:
                raise OffsetEnding("End differs from beginning by %s" % off)
        else:
            yield (x, y), interpolated

def point_distance(a, b):
    return (abs(a[0] - b[0]) ** 2 + abs(a[1] - b[1]) ** 2) ** .5

s_crs = pyproj.Proj('+proj=tmerc +lat_0=24.33333333333333 +lon_0=-81 +k=0.999941177 +x_0=200000.0001016002 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=us-ft +no_defs')
t_crs = pyproj.Proj(proj='latlong', datum='WGS84')
def reproject(points):
    return list(points)
    # return list(points)
    # return [s_crs(x, y, inverse=True) for x, y in points]
    # return [s_crs(x, y, inverse=True) for x, y in points]
    # x = []
    # y = []
    # for p in points:
    #     x.append(p[0])
    #     y.append(p[1])
    # x, y = pyproj.transform(s_crs, t_crs, x, y)
    # return [(x[i], y[i]) for i in range(len(x))]

def make_polygon(point, beginning, shape, **kwargs):
    points = reproject(make_points(point, beginning, shape, closed=True))
    for coordinates, interpolated in points:
        yield {
            'type': 'Point',
            'coordinates': coordinates,
            'properties': {
                'source:geometry:interpolated': 'yes' if interpolated else 'no',
            }
        }
    yield {
        'type': 'Polygon',
        'coordinates': [[coordinates for coordinates, interpolated in points]],
    }
    # return 'POLYGON((%s))' % ','.join('%s %s' % p for p in points)

def make_linestring(point, beginning, shape, width, **kwargs):
    points = reproject(make_points(point, beginning, shape, closed=False, ignore_end=True))
    for coordinates, interpolated in points:
        yield {
            'type': 'Point',
            'coordinates': coordinates,
            'properties': {
                'source:geometry:interpolated': 'yes' if interpolated else 'no',
            }
        }
    yield {
        'type': 'LineString',
        'coordinates': [coordinates for coordinates, interpolated in points],
    }
    # yield from reproject(points)
    # return 'LINESTRING(%s)' % ','.join('%s %s' % p for p in points)

make_shapes = {
    'centerline': make_linestring,
    'outline': make_polygon,
}

def make_angle(degrees, minutes=0, seconds=0):
    return radians(degrees + (minutes + seconds / 60) / 60)

def rotate(bearing, angle, right):
    return (bearing + angle * (1 if right else -1)) % radians(360)

def bearings(strings, angle_step=2, angle_steps=None, bearing=None):
    for string in strings:

        # Lines

        match = line_re.match(string)
        if match:
            ns, degrees, minutes, seconds, ew, distance = match.groups()
            north = ns == 'N'
            south = not north

            east = ew == 'E'
            west = not east

            degrees = int(degrees)
            minutes = int(minutes)
            seconds = float(seconds)

            degrees += (minutes + seconds / 60) / 60

            if north and east:
                pass
            if north and west:
                degrees = -degrees
            if south and west:
                degrees = 180 + degrees
            if south and east:
                degrees = 180 - degrees

            bearing = radians(degrees)

            yield bearing, float(distance), False  # Not interpolated

        # Curves
        # TODO: Use actual trigonometry to calculate points along the curve

        match = curve_re.match(string)
        if match:
            lr, radius, degrees, minutes, seconds, distance = match.groups()
            right = lr == 'R'
            angle = make_angle(int(degrees), int(minutes), float(seconds))
            radius = float(radius) or (angle / radians(360)) / pi / 2
            distance = float(distance or 0)

            steps = angle_steps or int(ceil(angle / make_angle(angle_step)))
            step_angle = angle / (steps or 1)
            step_distance = 2 * (sin(step_angle / 2) * radius)

            # Entering the curve requires half of the continuing angle
            bearing = rotate(bearing, step_angle / 2, right)
            yield bearing, step_distance, True  # Interpolated

            for step in range(1, steps):
                bearing = rotate(bearing, step_angle, right)
                yield bearing, step_distance, step == steps - 1  # All but the last step are interpolated

            # Adjust the final bearing for future calculations
            bearing = rotate(bearing, step_angle / 2, right)

plss = yaml.load(open('../maps.data/plss.yaml'))

def get_subdivision()

known_geometries = {}

def get_geometry(identifier, property):
    if isinstance(property, str):
        if identifier in known_geometries:
            yield known_geometries[identifier]
        else:
            raise Exception('Unknown property %r' % property)

    shape_type = property.pop('type', 'outline')
    make_shape = make_shapes[shape_type]
    origin = plss[property.pop('origin')]
    beginning = list(bearings(property.pop('beginning')))
    shape = property.pop('shape')
    for geometry in make_shape(
        origin,
        beginning,
        bearings(shape, bearing=beginning[-1][0]),
        **property
    ):
        yield geometry

    known_geometries[identifier] = geometry

    # return geometry

def get_features(filings):
    for filing in filings:
        if 'hidden' in filing:
            continue

        try:
            doc = filing.pop('doc')
            property_description = filing.pop('property')
            properties = dict(
                date=filing.pop('date').strftime('%Y-%m-%d'),
                doc=doc,
                desc=filing.pop('desc', ''),
                url=make_url(doc),
                **filing
            )
            properties['source:geometry'] = 'orccompt'
            properties['source:geometry:method'] = 'plss'
            properties['source:geometry:url'] = properties['url']
            for geometry in get_geometry(doc, property_description):
                yield geometry, dict(properties, **geometry.pop('properties', {}))
        except Exception as exc:
            print('%s %s: %s' % (doc, exc.__class__.__name__, exc), file=sys.stderr)


features = [
    {
        'type': 'Feature',
        'geometry': geometry,
        'properties': properties,
    }
    for (geometry, properties) in
    get_features(yaml.load_all(open('../maps.data/filings.yaml')))
]

print(json.dumps({
    'type': 'FeatureCollection',
    'features': features,
}), file=sys.stdout)
