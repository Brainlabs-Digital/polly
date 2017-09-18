from distutils.core import setup
setup(
    name='polly',
    packages=['polly'],
    version='0.6.4',
    description='A library for parsing and validating rel-alternate-hreflang entries on a page.',
    author='Tom Anthony',
    author_email='tom.anthony@distilled.net',
    url='https://github.com/DistilledLtd/polly',
    download_url='https://github.com/DistilledLtd/polly/tarball/0.6.4',
    keywords=['hreflang', 'rel-alternate-hreflang'],
    classifiers=[],
    install_requires=[
        'language-tags',
        'lxml',
        'requests',
        'pyopenssl',
        'ndg-httpsclient',
        'pyasn1'
    ]
)
