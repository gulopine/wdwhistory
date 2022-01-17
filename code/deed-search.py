import datetime
import functools
import grequests
import json
import os.path
import pprint
import re
import requests
from collections import defaultdict
from lxml import html
from urllib.parse import parse_qsl, urljoin, urlparse

DATE_FORMAT = '%m/%d/%Y'
OUTPUT_DIRECTORY = '../maps.documents/deeds.new'
SEARCH_URL = 'https://or.occompt.com/recorder/eagleweb/docSearchPOST.jsp'
FILENAME_RE = re.compile(r'parent=(.+)$')
SCRIPT_DIR = os.path.dirname(__file__)
VALID_PERSON = re.compile(r'^[A-Za-z]+')
TODAY = datetime.date.today()

# Load in a cache of prior results
RESULTS_PATH = os.path.join(SCRIPT_DIR, OUTPUT_DIRECTORY, 'deed-results.json')
try:
    with open(RESULTS_PATH) as input_file:
        prior_results = json.load(input_file)
except:
    prior_results = {"searches": [], "documents": []}

START_OVER = not prior_results["searches"]
START_OVER = True

# Accept the usage terms
session = requests.Session()
response = session.post('https://or.occompt.com/recorder/web/loginPOST.jsp?guest=true')


def json_converter(o):
    if isinstance(o, datetime.date):
        return o.strftime('%Y-%m-%d')
    if isinstance(o, set):
        return list(o)


def strpdate(date_string, date_format=DATE_FORMAT):
    return datetime.datetime.strptime(date_string, date_format).date()


prior_results = prior_results["searches"]
deferred_searches = []
if START_OVER:
    prior_results = []
prior_searches = []
for search, results in prior_results:
    if results == 'DEFERRED':
        deferred_searches.append((search, results))
        continue
    search = search.copy()
    start_date = search.get('start_date')
    end_date = search.get('end_date')
    if start_date:
        search['start_date'] = strpdate(start_date, date_format='%Y-%m-%d')
    if end_date:
        search['end_date'] = strpdate(end_date, date_format='%Y-%m-%d')
    prior_searches.append(search)


def search_params_for_value(value, field=''):
    if value.startswith('*'):
        value = value[1:]
        search_type = 'Wildcard Search'
    else:
        search_type = 'Exact Match'

    return {
        f'{field}SearchString': value,
        f'{field}SearchType': search_type,
    }


def search(
    start_date,
    end_date,
    grantor=None,
    grantee=None,
    both=None,
    legal=None,
    prior_results=prior_results,
):
    params = {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
    }
    if grantor:
        params['grantor'] = grantor
    if grantee:
        params['grantee'] = grantee
    if both:
        params['both'] = both
    if legal:
        params['legal'] = legal

    raw_params = {
        # NC - Notice of Commencement
        # D  - Deed
        '__search_select': 'D',
        'RecordingDateIDStart': start_date.strftime(DATE_FORMAT),
        'RecordingDateIDEnd': end_date.strftime(DATE_FORMAT),
    }

    if grantor:
        raw_params.update(search_params_for_value(grantor, field='GrantorID'))
    if grantee:
        raw_params.update(search_params_for_value(grantee, field='GranteeID'))
    if both:
        raw_params.update(search_params_for_value(both, field='BothNamesID'))

    if legal:
        raw_params['LegalRemarks'] = legal

    if len(raw_params) == 1:
        # No dates were added
        raise ValueError("Must supply additional parameters")

    for p, results in prior_results:
        if p == params:
            if results == 'TODO':
                # These were determined previously and need to be run this time, so pretend it didn't exist
                pass
            else:
                return False, raw_params, results

    return True, raw_params, get_results(raw_params)


def get_results(params):
    # Search for records
    response = session.post(SEARCH_URL, data=params, allow_redirects=False)
    results_url = urljoin(SEARCH_URL, response.headers['Location'])
    results = []

    while True:
        content = session.get(results_url).text
        tree = html.fromstring(content.replace('><', '>\n<'))
        for result in tree.xpath("//tr[@class]"):
            doc_type, doc_number = result.xpath(".//strong")[0].text_content().split()
            parent = result.xpath(".//a[@oid][not(@class)]/@oid")[0]
            attrs = dict(re.findall(r'\b(.+?): +(.*?) *\n+', re.sub('\xa0|&nbsp;?', '\n', result.text_content())))

            local_filename = f'{parent}.pdf'
            remote_path = f'downloads/{local_filename}?parent={parent}'
            remote_url = urljoin(results_url, remote_path)

            try:
                yield {
                    'doc_type': doc_type,
                    'number': doc_number,
                    'parent': parent,
                    'filename': local_filename,
                    'url': remote_url,
                    'recorded_date': str(strpdate(attrs['Rec Date'].split()[0])),
                    'book_page': re.findall('.: ([0-9]+)', attrs['BookPage']),
                    'related': attrs['Related'],
                    'related_book_page': re.findall('.: ([0-9]+)', attrs['Related BP']),
                    'grantors': attrs['Grantor'].split(', '),
                    'grantees': attrs['Grantee'].split(', '),
                    'location': attrs.get('Legal'),
                    'doc_deed_tax': attrs['Doc Deed Tax'],
                }
            except KeyError as e:
                print(result.text_content())
                print(attrs)
                raise

        next_url = tree.xpath("//a[text()='Next']/@href")
        if next_url:
            results_url = urljoin(results_url, next_url[0])
        else:
            break



def download_files(filenames):
    queue = []
    for local_path, remote_url in filenames:
        # Prepare the requests
        if os.path.exists(local_path):
            print('Skipping %s' % os.path.basename(local_path))
        else:
            req = grequests.get(remote_url, session=session)
            queue.append(req)

    # Send the requests and write out the results
    for response in grequests.imap(queue, size=4, stream=True):
        local_filename = '%s.pdf' % FILENAME_RE.search(response.request.url).group(1)
        local_path = os.path.join(OUTPUT_DIRECTORY, local_filename)
        with open(local_path, 'wb') as f:
            print('Writing %s...' % local_path, end='')
            for chunk in response.iter_content(chunk_size=1024): 
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
            f.flush()
            print('done')


if __name__ == '__main__':
    founding = {
        'start_date': datetime.date(year=1964, month=1, day=1),
        'end_date': datetime.date(year=1971, month=12, day=31),
    }
    searches = [
        # dict(founding, grantor='demetree'),  # 12,400 acres, to "Bob Price"?
        # dict(founding, grantor='jenkins bill'),  # 12,400 acres, to "Bob Price"?
        # # ^^ find mineral rights from tufts?
        # dict(founding, grantor='bronson irlo'),  # 8,500 acres
        # dict(founding, grantor='hall brothers'),  # 1,800 acres, purchased with help from Florida Ranch Lands, 0 records

        # # dict(founding, grantee='florida ranch lands'),  # calls to out-of-state owners, 0 records

        # dict(founding, grantee='helliwell paul'),  # definitely disney properties
        # dict(founding, grantee='smith philip n'),  # definitely disney properties
        # # dict(founding, grantee='foster robert'),  # many records look unrelated, needs more digging
        # # dict(founding, grantee='price bob'),  # 2 records that look unrelated
        # # dict(founding, grantee='davis roy'),  # 3 records that look unrelated
        # # haven't (yet?) found any records for Roy Hawkins

        # dict(founding, grantee='ayefour corp'),  # Ayefour Corporation, Robert Foster
        # dict(founding, grantee='bay lk prop'),  # Bay Lake Properties, Bob Price
        # dict(founding, grantee='tomahawk prop'),  # Tomahawk Properties, Bob Price
        # dict(founding, grantee='compass e'),  # Compass East, Roy Davis
        # dict(founding, grantee='reedy crk ranch'),  # Reedy Creek Ranch Lands, M.T. Lott
        # # # can't (yet?) find any records for Latin American Development & Management, Roy Davis

        # # dict(founding, grantor='ayefour corp'),  # Ayefour Corporation, Robert Foster, 0 records
        # # dict(founding, grantor='bay lk prop'),  # Bay Lake Properties, Bob Price, 0 records
        # dict(founding, grantor='tomahawk prop'),  # Tomahawk Properties, Bob Price
        # dict(founding, grantor='compass e'),  # Compass East, Roy Davis
        # dict(founding, grantor='reedy crk ranch'),  # Reedy Creek Ranch Lands, M.T. Lott
        # # can't (yet?) find any records for Latin American Development & Management, Roy Davis

        # dict(founding, grantee='*disney'),
        dict(founding, grantee='bay lk prop'),  # Bay Lake Properties, Bob Price
        dict(founding, grantor='reedy creek ranch'),  # Reedy Creek Ranch Lands, M.T. Lott
    ]
    # searches = [
    #     # dict(founding, grantee='helliwell paul'),  # definitely disney properties
    #     dict(founding, grantee='smith philip n'),  # definitely disney properties
    # ]
    # if not START_OVER:
    #     searches = prior_searches
    update_cache = False

    fresh_count = 0
    document_ids = set()
    processed = 0
    depth = 1
    new_searches = []
    new_results = []
    result_pdfs = []
    while depth and searches:
        unprocessed = len(searches)
        total = processed + unprocessed
        print('%2.2f%% %4d / %4d' % (processed / total * 100, processed, total))
        params = searches.pop(0)
        records = []

        related_people = defaultdict(int)
        if 'grantor' in params and 'grantee' in params:
            related_field = None
        elif 'grantor' in params:
            related_field = 'grantees'
        elif 'grantee' in params:
            related_field = 'grantors'
        else:
            related_field = None

        # print('Search', params)
        fresh, raw_params, results = search(**params)

        if True or fresh:
            for result in sorted(results, key=lambda r: '' if isinstance(r, str) else r['recorded_date']):
                try:
                    base_path = os.path.join(OUTPUT_DIRECTORY, result['filename'])
                except Exception as e:
                    print('Result', result)
                    raise
                result_pdfs.append((
                    base_path,
                    result['url'],
                ))
                with open(f'{base_path}.json', 'w') as json_file:
                    json.dump(result, json_file, indent=2, sort_keys=True)
                if depth > 1 and related_field is not None:
                    related_people[tuple(result[related_field])] += 1
                    for related_person in result[related_field]:
                        if related_field == 'grantors' and related_person and related_person[0].isalpha():
                            recorded_date = strpdate(result['recorded_date'], date_format='%Y-%m-%d')
                            # print(recorded_date, related_person)
                            new_search = {
                                'start_date': datetime.date(year=1800, month=1, day=1),
                                'end_date': recorded_date - datetime.timedelta(days=1),
                                'grantee': related_person,
                            }
                            print('Result', new_search)
                            new_searches.append((new_search, 'TODO'))
                            # searches.append(new_search)
                            # searches.sort(key=lambda p: TODAY - p['end_date'])

                            # For now, only process the first grantor. It significantly reduce the number of
                            # searches to perform, but might theoretically miss some deeds along the way.
                            break

                document_ids.add(f"{result['number']}:{result['parent']}")
                fresh_count += 1

                # print("{icon} {recorded_date} {grantors} -> {grantees}".format(icon='+' if fresh else ' ', **result))
                records.append(result)

            # Temporary break after the first result, just to see if this goes back in time the way I think it should
            # break

        # if fresh:
        #     new_results.append((params, records))
        new_results.append((params, records))

        # for people in related_people:
        #     print('  %4d %s' % (len(people), people))
        # print('%4d %s records' % (len(records), 'new' if fresh else 'cached'))
        # break
        processed += 1
        # depth -= 1


    if update_cache:
        new_results.extend(new_searches)
        new_results.extend(deferred_searches)
        with open(RESULTS_PATH, 'w') as output_file:
            json.dump({
                "searches": new_results,
                "documents": document_ids
            }, output_file, indent=2, default=json_converter)

    print('%2.2f%% %4d / %4d' % (processed / total * 100, processed, total))
    print('Found %d new records' % fresh_count)

    download_files(result_pdfs)


if False:# results:
    searches = json.load(open(os.path.join(OUTPUT_DIRECTORY, 'searches.json'), 'r'))
    searches.append({
        'params': search_params,
        'date': str(datetime.date.today()),
        'results': results,
    })
    json.dump(searches, open(os.path.join(OUTPUT_DIRECTORY, 'searches.json'), 'w'))
