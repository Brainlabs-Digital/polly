# Introduction

polly is a library to help you parse and check rel-alternate-hreflang directives on a page.

Using polly you can fetch a page and quickly access information about how many rel-alternate-hreflang entries are on a page, and which countries and languages they cover:

	my_page = PollyPage(initial_url)
	print my_page.hreflang_values
	print my_page.languages
	print my_page.regions

You can also check various aspects of a page, see whether the pages it includes in its rel-alternate-hreflang entries point back, or whether there are entries that do not see retrievable (due to 404 or 500 etc. errors:

	print my_page.is_default
	print my_page.non_reciprocal_pages()
	print my_page.non_retrievable_pages()

# Using polly

Simply install it with pip:

	pip install polly

# To Do

- handle hreflang via XML sitemap
- handle hreflang via HTTP headers
- cross check with rel-canonical directives
- cross check with the other language indicators on a page
- handle script variations (https://support.google.com/webmasters/answer/189077?hl=en)

# Why Polly?

Polyglot. Get it?!

# Contributing

See CONTRIBUTING file.

# License

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License

See LICENSE file.