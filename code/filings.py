from __future__ import division

import csv
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

def make_points((x, y), beginning, shape, include_origin=False, ignore_end=True):
    if include_origin:
        yield (x, y)  # Origin

    for bearing, distance in beginning:
        horizontal = sin(bearing) * distance
        vertical = cos(bearing) * distance
        x += horizontal
        y += vertical

        if include_origin:
            yield (x, y)  # Point from origin to beginning

    beginning = (x, y)
    if not include_origin:
        yield beginning  # Only if the origin wasn't already included

    shape = list(shape)
    last_i = len(shape) - 1

    for i, (bearing, distance) in enumerate(shape):
        horizontal = sin(bearing) * distance
        vertical = cos(bearing) * distance
        x += horizontal
        y += vertical
        if i == last_i:
            off = point_distance((x, y), beginning)
            if off < THRESHOLD:
                # Reached the end and it's close enough to the beginning that the
                # difference is likely just floating point error
                yield beginning
            elif ignore_end:
                yield (x, y)
            else:
                raise OffsetEnding("End differs from beginning by %s" % off)
        else:
            yield (x, y)

def point_distance(a, b):
    return (abs(a[0] - b[0]) ** 2 + abs(a[1] - b[1]) ** 2) ** .5

def make_polygon(point, beginning, shape, **kwargs):
    points = make_points(point, beginning, shape)
    return 'POLYGON((%s))' % ','.join('%s %s' % p for p in points)

def make_linestring(point, beginning, shape, width, **kwargs):
    points = make_points(point, beginning, shape, ignore_end=True)
    return 'LINESTRING(%s)' % ','.join('%s %s' % p for p in points)

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

            yield bearing, float(distance)

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
            yield bearing, step_distance

            for step in range(1, steps):
                bearing = rotate(bearing, step_angle, right)
                yield bearing, step_distance

            # Adjust the final bearing for future calculations
            bearing = rotate(bearing, step_angle / 2, right)

plss = yaml.load(open('plss.yaml'))

writers = {key: csv.writer(open('%s.csv' % key, 'wb')) for key in make_shapes}

for writer in writers.values():
    writer.writerow([
        'date',
        'doc',
        'desc',
        'url',
        'geometry',
    ])

for filing in yaml.load_all(open('filings.yaml')):
    if 'hidden' not in filing:
        try:
            shape_type = filing.get('type', 'outline')
            make_shape = make_shapes[shape_type]
            beginning = list(bearings(filing.pop('beginning')))
            shape = filing.pop('shape')
            writers[shape_type].writerow([
                filing['date'],
                filing['doc'],
                filing.get('desc', ''),
                make_url(filing['doc']),
                make_shape(
                    plss[filing['origin']],
                    beginning,
                    bearings(shape, bearing=beginning[-1][0]),
                    **filing
                )
            ])
        except Exception as exc:
            print '%s %s: %s' % (filing['doc'], exc.__class__.__name__, exc)
