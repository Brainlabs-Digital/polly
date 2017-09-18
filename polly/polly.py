from collections import defaultdict
from urlparse import urljoin
from http_parse import http_headers_to_dict

import lxml.html
import requests

from language_tags import tags


class PollyPage(object):
    """ A class that contains the functions and structures to
        retrieve and store all of the various aspects of the
        hreflang entries of a page and of those pages it refers
        to via those hreflang entries.
    """

    def __init__(self,
                 url,
                 allow_underscore=False,
                 fetch_page=True,
                 fuzzy_match_trailing_slash=True):

        if url[:4] != "http":
            url = "http://" + url

        self.base_url = url
        self.headers = {}
        self.hreflang_entries = {}
        self.hreflang_entries_from_html = {}
        self.hreflang_entries_from_http = {}
        self.issues_for_key = {}
        self.issues_for_url = {}
        self.alternate_pages = {}
        self.alternate_languages = set()
        self.alternate_regions = set()
        self.allow_underscore = allow_underscore
        self.alternate_pages_fetched = False
        self.fuzzy_match_trailing_slash = fuzzy_match_trailing_slash

        try:
            if fetch_page:
                self.fetch_page()
        except ValueError:
            raise

    def __repr__(self):
        return self.base_url

    @property
    def url(self):
        return self.base_url

    @property
    def hreflang_keys(self):
        return sorted(self.hreflang_entries.keys())

    @property
    def languages(self):
        return sorted(self.alternate_languages)

    @property
    def regions(self):
        return sorted(self.alternate_regions)

    def parse_hreflang_value(self, hreflang_value):
        """ NBED
        """

        # Replace underscores if desired
        if self.allow_underscore:
            hreflang_value = hreflang_value.replace("_", "-")

        # Handle the x-default special case
        if hreflang_value.lower() == "x-default":
            return ("x-default", "default", "default")

        # Try to parse the IETF language/region tag.
        parsed_tag = tags.tag(hreflang_value)

        # Extract the language
        language = str(parsed_tag.language.description[0].encode('ascii',
                                                                 errors='xmlcharrefreplace')
                       if parsed_tag.language else "Unknown")

        # Extract the region
        # Differentiate between none being specified and one not
        # being recognised
        region = (str(parsed_tag.region.description[0].encode('ascii',
                                                              errors='xmlcharrefreplace'))
                  if parsed_tag.region else "Unknown"
                  if len(str(parsed_tag)) > 3 else None)

        # Return cleaned version of the tag
        return (str(parsed_tag), language, region)

    def format_hreflang_value(self, hreflang_value):
        formatted_hreflang_value, l, r = self.parse_hreflang_value(
            hreflang_value)
        return formatted_hreflang_value

    def hreflang_value_language(self, hreflang_value):
        c, language, r = self.parse_hreflang_value(hreflang_value)
        return language

    def hreflang_value_region(self, hreflang_value):
        c, l, region = self.parse_hreflang_value(hreflang_value)
        return region

    def fetch_page(self):
        """ Fetch the page's HTML and parse it for hreflang entries
            and then parse each of these entries.
        """

        # Clear the current internal links
        self.hreflang_entries = {}

        # Grab the page and pull out the hreflang <link> elements
        try:
            r = requests.get(self.base_url, allow_redirects=False, timeout=5)
            self.headers = r.headers
        except Exception as e:
            raise ValueError(str(e))

        self.status_code = r.status_code
        if r.status_code != 200:
            raise ValueError("HTTP Response Code was not 200.")

        tree = lxml.html.fromstring(r.text)
        elements = tree.xpath("//link[@hreflang]")

        # concert a link element into a tuple of the clean language
        # code and the alternate url link
        def element_hreflang_value_and_url(element):
            """ Get the attributes of the element """

            language_code = element.get('hreflang', '')
            alternate_url = element.get('href', '')

            formatted_hreflang_value = self.format_hreflang_value(
                language_code)

            return formatted_hreflang_value, alternate_url

        # group the links by country code
        hreflang_entries = defaultdict(list)
        for element in elements:
            hreflang_value, alternate_url = element_hreflang_value_and_url(
                element)
            hreflang_entries[hreflang_value].append(alternate_url)
            self.alternate_languages.add(
                self.hreflang_value_language(hreflang_value))
            region = self.hreflang_value_region(hreflang_value)
            if region:
                self.alternate_regions.add(region)

        self.hreflang_entries_from_html = dict(hreflang_entries)
        self.get_http_headers()
        self.combine_sources()

    def get_http_headers(self):
        http_headers = defaultdict(list)
        for headers, values in http_headers_to_dict(self.headers).iteritems():
            http_headers[self.format_hreflang_value(headers)].append(values)
            self.alternate_languages.add(self.hreflang_value_language(headers))
            region = self.hreflang_value_region(headers)
            if region:
                self.alternate_regions.add(region)
        self.hreflang_entries_from_http = dict(http_headers)

    def combine_sources(self):
        hreflang_entries = defaultdict(set)
        html_hreflangs = self.hreflang_entries_from_html
        http_hreflangs = self.hreflang_entries_from_http
        for hreflang_value, urls in html_hreflangs.iteritems():
            hreflang_entries[hreflang_value].update(urls)
        for hreflang_value, urls in http_hreflangs.iteritems():
            hreflang_entries[hreflang_value].update(urls)

        self.hreflang_entries = dict(hreflang_entries)

    def fetch_alternate_pages(self):
        """ Iterate over all the URLs we have encountered on the current
            page, and then download and parse each of them in turn.
        """

        # Only do fetch if we have not already done so
        if self.alternate_pages_fetched:
            return

        self.alternate_pages_fetched = True

        # Loop each of the URLs from the current page's hreflang
        # entries and create PollyPage objects to fetch and parse them.
        for url in self.alternate_urls():
            # We resolve relative URLs. This is permitted (see 'mistake #2':
            # http://googlewebmastercentral.blogspot.co.uk/2013/04/5-common-mistakes-with-relcanonical.html)
            resolved_url = urljoin(self.base_url, url)
            self.alternate_pages[url] = PollyPage(resolved_url,
                                                  allow_underscore=self.allow_underscore,
                                                  fetch_page=False)

            # Fetch the pages manually such that the constructor always
            # returns an object even when there is a problem with the URL.
            try:
                self.alternate_pages[url].fetch_page()
            except:
                pass

    def detect_errors(self):

        self.fetch_alternate_pages()

        self.issues_for_key = {}
        self.issues_for_url = {}

        non_retrievable_pages = list(self.non_retrievable_pages())
        no_return_tag_pages = list(self.no_return_tag_pages())
        hreflang_keys_with_multiple_entries = self.hreflang_keys_with_multiple_entries

        for key in self.hreflang_keys:
            self.issues_for_key[key] = {
                "has_errors": False,
                "has_warnings": False,
                "multiple_entries": False,
                "unknown_language": False,
                "unknown_region": False
            }

        for url in self.alternate_urls():
            self.issues_for_url[url] = {
                "has_errors": False,
                "non_retrievable": False,
                "no_return_tag": False,
            }

        for key, urls in self.hreflang_entries.iteritems():

            if self.hreflang_value_language(key) == "Unknown":
                self.issues_for_key[key]['has_errors'] = True
                self.issues_for_url[url]['unknown_language'] = True

            if self.hreflang_value_language(key) in self.languages_missing_standalone_entry:
                self.issues_for_key[key]['has_warnings'] = True

            if self.hreflang_value_region(key) == "Unknown":
                self.issues_for_key[key]['has_errors'] = True
                self.issues_for_url[url]['unknown_region'] = True

            if hreflang_keys_with_multiple_entries:
                if key in hreflang_keys_with_multiple_entries:
                    self.issues_for_key[key]['multiple_entries'] = True
                    self.issues_for_key[key]['has_errors'] = True

            for url in urls:
                if url in non_retrievable_pages:
                    self.issues_for_url[url]['non_retrievable'] = True
                    self.issues_for_url[url]['has_errors'] = True

                if url in no_return_tag_pages:
                    self.issues_for_url[url]['no_return_tag'] = True
                    self.issues_for_url[url]['has_errors'] = True

    def alternate_urls(self, include_x_default=True):
        """ Returns a set of all the alternate URLs encountered.
        """

        hreflang_entries = self.hreflang_entries

        if not include_x_default:
            hreflang_entries['x-default'] = []

        return set(
            link
            for hreflang_value in hreflang_entries
            for link in hreflang_entries[hreflang_value]
        )

    def links_back_to(self, url, include_x_default=False):

        alternative_urls = self.alternate_urls(
            include_x_default=include_x_default)

        if self.fuzzy_match_trailing_slash:
            if url[-1] == '/':
                alternate_base_url = url[:-1]
            elif url[-1] != '/':
                alternate_base_url = url + '/'

            return url in alternative_urls or alternate_base_url in alternative_urls

        else:
            return url in alternative_urls

    @property
    def is_default(self):

        if 'x-default' in self.hreflang_entries:
            return self.base_url in self.hreflang_entries['x-default']

        return False

    @property
    def has_multiple_defaults(self):

        if 'x-default' in self.hreflang_entries:
            return len(self.hreflang_entries['x-default']) > 1

        return False

    @property
    def hreflang_keys_with_multiple_entries(self):

        hreflang_keys = set()

        for hreflang_value in self.hreflang_entries:
            if len(self.hreflang_entries[hreflang_value]) > 1:
                hreflang_keys.add(hreflang_value)

        return hreflang_keys

    def no_return_tag_pages(self, include_x_default=False):

        self.fetch_alternate_pages()
        urls = set()

        for url, page in self.alternate_pages.iteritems():

            if url == self.base_url:
                continue

            if not page.links_back_to(self.base_url, include_x_default=include_x_default):
                urls.add(page.url)

        return urls

    def non_retrievable_pages(self):

        self.fetch_alternate_pages()
        urls = set()

        for url, page in self.alternate_pages.iteritems():

            if url == self.base_url:
                continue

            if page.status_code != 200:
                urls.add(page.url)

        return urls

    @property
    def hreflang_entries_to_tuples(self):
        """ Splits hreflang_keys into a dictionary containing with hreflang_keys
            as the keys and a tuple of (language, region) as the value.
        """
        hreflang_entries_to_tuples = {}
        for key in self.hreflang_keys:
            formatted_hreflang_value, language, region = self.parse_hreflang_value(
                key)
            hreflang_entries_to_tuples[key] = (language, region)

        return hreflang_entries_to_tuples

    @property
    def languages_missing_standalone_entry(self):
        """ Takes hreflang_entries and returns a set of the languages with a
            linked country but without that language by itself.
        """
        associated = set()
        unassociated = set()
        for key, value in self.hreflang_entries_to_tuples.items():
            if not value[1]:
                unassociated.add(value[0])
            elif value[1] == 'default':
                continue
            else:
                associated.add(value[0])

        return associated.difference(unassociated)
