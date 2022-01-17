import datetime
import grequests
import os.path
import pprint
import re
import requests
from lxml import html
from urlparse import parse_qsl, urljoin, urlparse

# Dates I've inspected manually: 1/1/1971 - 1/31/1971

DATE_FORMAT = '%m/%d/%Y'
SEARCH_URL = 'http://or.occompt.com/recorder/eagleweb/docSearchPOST.jsp'
# This is as far as we've gotten in fetching *ALL* records. Beyond this it's just Disney
# START_DATE = datetime.date(year=1990, month=1, day=1)
START_DATE = datetime.date(year=2016, month=11, day=1)
TIMEFRAME = datetime.timedelta(days=366)
# END_DATE   = '03/31/1971'
END_DATE = START_DATE + TIMEFRAME - datetime.timedelta(days=1)
END_DATE = datetime.date(year=2016, month=12, day=31)
SEARCH_STR = 'disney'
DISNEY     = True  # Whether or not this query is known to return Disney docs
FILENAME_RE = re.compile(r'parent=(.+)$')

session = requests.Session()
session.post('http://or.occompt.com/recorder/web/loginPOST.jsp?guest=true')

response = session.post(SEARCH_URL, data={
    'RecordingDateIDStart': START_DATE.strftime(DATE_FORMAT),
    'RecordingDateIDEnd': END_DATE.strftime(DATE_FORMAT),
    'BothNamesIDSearchString': SEARCH_STR,
    'BothNamesIDSearchType': 'Wildcard Search',
    # NC - Notice of Commencement
    # D  - Deed
    '__search_select': 'NC',
}, allow_redirects=False)

results_url = response.headers['Location']

while True:
    tree = html.fromstring(session.get(results_url).text)
    queue = []
    for pdf_path in tree.xpath("//a[@oid][not(@class)]/@href"):
        parts = urlparse(pdf_path)
        args = dict(parse_qsl(parts.query))
        local_filename = '%(parent)s.pdf' % args
        disney_path = 'documents/%s' % local_filename
        incoming_path = 'incoming/pdf/%s' % local_filename
        remote_path = 'downloads/%(parent)s.pdf?parent=%(parent)s' % args

        # Prepare the requests
        if os.path.exists(disney_path) or os.path.exists(incoming_path):
            print 'Skipping %s' % local_filename
        else:
            req = grequests.get(urljoin(results_url, remote_path), session=session)
            queue.append(req)

    # Send the requests and write out the results
    for response in grequests.imap(queue, size=4, stream=True):
        local_filename = FILENAME_RE.search(response.request.url).group(1)
        disney_path = 'documents/%s.pdf' % local_filename
        incoming_path = 'incoming/pdf/%s.pdf' % local_filename
        local_path = disney_path if DISNEY else incoming_path
        with open(local_path, 'wb') as f:
            print ('Writing %s...' % local_path),
            for chunk in response.iter_content(chunk_size=1024): 
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
            f.flush()
            print 'done'

    next_url = tree.xpath("//a[text()='Next']/@href")
    if next_url:
        results_url = urljoin(results_url, next_url[0])
    else:
        break
