import sys

from polly import PollyPage

initial_url = sys.argv[1]

test_page = PollyPage(initial_url, allow_underscore=True)

print
print " ** Checking hreflang for: " + initial_url + " **"
print

print "Alternative URLs:"
print "\t" + "\n\t".join(test_page.alternate_urls_set())
print
print "No return tag error pages:"
print "\t" + "\n\t".join(test_page.no_return_tag_pages())
print
print "Non-retrievable pages:"
print "\t" + "\n\t".join(test_page.non_retrievable_pages())
print
print "Is this page the default:"
print "\t" + str(test_page.is_default)
print
print "Are there multiple defaults present:"
print "\t" + str(test_page.multiple_defaults)
print
print "hreflang values:"
print "\t" + ", ".join(test_page.hreflang_values)
print
print "Languages:"
print "\t" + ", ".join(test_page.languages)
print
print "Regions:"
print "\t" + ", ".join(test_page.regions)
print
