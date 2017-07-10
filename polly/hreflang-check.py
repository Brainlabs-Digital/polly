import sys

from polly import PollyPage

initial_url = sys.argv[1]

test_page = PollyPage(initial_url, allow_underscore=True)
test_page.detect_errors()

print
print " ** Checking hreflang for: " + initial_url + " **"
print

print "Alternative URLs:"
print "\t" + "\n\t".join(test_page.alternate_urls())
print
print "No return tag error pages:"
print "\t" + "\n\t".join(test_page.no_return_tag_pages())
print
print "Non-retrievable pages:"
print "\t" + "\n\t".join(test_page.non_retrievable_pages())
print
print "Codes with multiple entries:"
print "\t" + "\n\t".join(test_page.hreflang_keys_with_multiple_entries)
print
print "Is this page the default:"
print "\t" + str(test_page.is_default)
print
print "Are there multiple defaults present:"
print "\t" + str(test_page.has_multiple_defaults)
print
print "hreflang keys:"
print "\t" + ", ".join(test_page.hreflang_keys)
print
print "Languages:"
print "\t" + ", ".join(test_page.languages)
print
print "Regions:"
print "\t" + ", ".join(test_page.regions)
print

print "Errors by hreflang_key:"
for hreflang_key in test_page.hreflang_keys:
    print "\t" + hreflang_key + " = " + str(test_page.issues_for_key[hreflang_key]['has_errors'])
print

print "Errors by url:"
for url in test_page.alternate_urls():
    print "\t" + url + " = " + str(test_page.issues_for_url[url]['has_errors'] )
print
