import pathlib
import re
import sys

LOT_RE = re.compile(r'Lot (?P<lot>\d+) of (?P<subdivision>.+? division)', re.IGNORECASE)
SECTION_RE = re.compile(r'Sec(?:- )?tion,? (?P<section>\d+)', re.IGNORECASE)
TOWNSHIP_RE = re.compile(r'Town(?:- )?ship,? (?P<township>\d+) *S(?:outh)', re.IGNORECASE)
RANGE_RE = re.compile(r'Range (?P<range>\d+) *[EF](?:ast)', re.IGNORECASE)

SECTION_RE = re.compile(r'.{0,5}'.join([
    # r'of',
    r'Sec(?:- )?tion,? (?P<section>\d+)',
    r'Town(?:- )?ship,? (?P<township>\d+) *S(?:outh)',
    r'Range (?P<range>\d+) *[EF](?:ast)',
]), re.IGNORECASE)


class Expression:
    @classmethod
    def finditer(cls, data):
        for match in cls.regex.finditer(data):
            yield cls(match)

    def __init__(self, match):
        self.__dict__ = match.groupdict()
        self._full_match = match.group(0)

    def __str__(self):
        return self._full_match

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self}>'


class Lot(Expression):
    regex = re.compile(r'Lot (?P<lot>\d+) of (?P<subdivision>.+? division)', re.IGNORECASE)


class Section(Expression):
    regex = re.compile(r'.{0,5}'.join([
        r'(?:of)',
        r'Sec(?:- )?tion,? (?P<section>\d+)',
        r'Town(?:- )?ship,? (?P<township>\d+) *S(?:outh)',
        r'Range (?P<range>\d+) *[EF](?:ast)',
    ]), re.IGNORECASE)


def parse(document_id, data):
    print(document_id)

    data = re.sub(r'[\s,.°_-]+', ' ', data)

    output = {
        'document_id': document_id,
        'details': [],
    }

    for expression in [Lot, Section]:
        for match in expression.finditer(data):
            print(repr(match))
            output['details'].append(match)

    print(output)
    print()

    return output


def strip_all_suffixes(path):
    old_path = path
    while True:
        path = path.with_suffix('')
        if path == old_path:
            return path.name
        old_path = path


if __name__ == '__main__':
    if len(sys.argv) > 1:
        data = []
        for filename in sys.argv[1:]:
            document_id = strip_all_suffixes(pathlib.Path(filename))
            data.append(parse(document_id, open(filename).read()))
    else:
        data =[parse(None, sys.stdin.read())]

