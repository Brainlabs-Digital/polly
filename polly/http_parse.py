import re


def http_headers_to_dict(headers):
    hreflang_entries = {}
    if 'link' in headers:
        heads = headers['link'].split(',')
        iheads = [head.split(';') for head in heads]
        for ihead in iheads:
            if len(ihead) >= 3:
                r = re.search(r'hreflang=(.*)', ihead[2])
                hreflang = r.group(1).strip("'")
                url = ihead[0].strip()[1:-2]
                hreflang_entries[hreflang] = url
    return hreflang_entries
