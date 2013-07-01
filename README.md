TOR-SCRAPER.PY

Instructions:

This script is in its early stages of development. As such, there are certain system dependences that must be set up before beginning.

1) CouchDB must be running on http://localhost:5984 (Learn more about CouchDB at http://couchdb.apache.org)
2) CouchDB python library must be installed (https://code.google.com/p/couchdb-python/)
3) SocksiPy library must be installed (http://socksipy.sourceforge.net)
4) Python STEM library must be installed (http://stem.torproject.org)

Running:
python tor-scraper.py -u http://example.com

the scraping will begin with the given URL and grab all *.onion sites, and then scrape each of those sites in turn

Viewing Results:

There is currently no built-in results viewer. To view the database, please use the CouchDB web interface (http://localhost:5984/_utils/database.html?sites)
