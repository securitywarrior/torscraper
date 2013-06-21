#!/usr/bin/python

import sys, os
import urllib2
import socket
import httplib
import re
import argparse
import datetime

import socks		# http://socksipy.sourceforge.net

import stem		# http://stem.torproject.org
import stem.process
from stem.util import term

import couchdb		# https://code.google.com/p/couchdb-python/
from couchdb.mapping import Document, TextField, IntegerField, DateTimeField

from uuid import uuid4	# For generating CouchDB unique IDs client side, to avoid conflicts

# Enable or disable debug messages
# Codes:
# [I] - Informational Messages
# [E] - Error Messages
DEBUG = True

def query(url):
	try:
		opener = urllib2.build_opener(SocksiPyHandler(socks.PROXY_TYPE_SOCKS5, "localhost", 9050))
		h = opener.open(url)
		return h
	except:
		print "[E] Unable to return %s" % url

class SocksiPyConnection(httplib.HTTPConnection):
    def __init__(self, proxytype, proxyaddr, proxyport = None, rdns = True, username = None, password = None, *args, **kwargs):
        self.proxyargs = (proxytype, proxyaddr, proxyport, rdns, username, password)
        httplib.HTTPConnection.__init__(self, *args, **kwargs)

    def connect(self):
        self.sock = socks.socksocket()
        self.sock.setproxy(*self.proxyargs)
        if isinstance(self.timeout, float):
            self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))

class SocksiPyHandler(urllib2.HTTPHandler):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kw = kwargs
        urllib2.HTTPHandler.__init__(self)

    def http_open(self, req):
        def build(host, port=None, strict=None, timeout=0):
            conn = SocksiPyConnection(*self.args, host=host, port=port, strict=strict, timeout=timeout, **self.kw)
            return conn
        return self.do_open(build, req)

class DB_Structure(Document):
	_id = TextField()
	url = TextField()
	ref = TextField()
	Discovered = DateTimeField()
	LastAccessed = DateTimeField()
	title = TextField()


def print_bootstrap_lines(line):
	if "Bootstrapped" in line:
		print term.format(line, term.Color.BLUE)

def check_http(url):
	# urllib2 needs URLs to include http://, so if the user submits "example.com" this will prepend http://
	if not re.search("^http[s]?\:\/\/", url):
		url = "http://" + url

	return url

def get_title(lines):
	title = ''
	for x in lines:
		m = re.search("\<title\>.*\<\/title\>", x)
		if m:		
			title = m.group(0) 
	return title[7:-8]


def main():

	# TODO: Add command line switch to set db server? Or config file?
	dbserv = couchdb.Server('http://localhost:5984/')

	# CouchDB connection and db creation
	try:
		db = dbserv['sites']
	except socket.error as e:
		print "[E] Could not connect to the database!"
		if DEBUG:
			print "Error message: %s" % e
		sys.exit("Please make sure that the database has been started, and try again")
	except couchdb.http.ResourceNotFound:
		if DEBUG:
			print "[I] Building initial database..."
		db = dbserv.create('sites')

	print term.format("Starting Tor:\n", term.Attr.BOLD)
	try:
		tor_process = stem.process.launch_tor_with_config(
			config = {
				'SocksPort':str(9050),
				'ControlPort':str(9051),
				},
			init_msg_handler = print_bootstrap_lines,
			completion_percent = 100,
			timeout = 3600
		)

	# TODO: implement the ability to bind to existing Tor instance in the future
	# use stem.connection lib
	except OSError as e:
		print "[E] There was an error launching Tor"
		if DEBUG:
			print "Error message: %s" % e
		# TODO: Remove this, make script try to connect to running instance
		sys.exit("Please kill all running Tor instances and try again")
			

	domains = []
	url = check_http(args.url)
	domains.append(url)

	# Prints endpoint information if debugging is enabled
	if DEBUG:
		print term.format("[I] Checking Endpoint:", term.Attr.BOLD)
		print query("http://www.atagar.com/echo.php").read()

	print term.format("\nScraping for .ONION domains:\n", term.Attr.BOLD)

	# Main scraping loop
	# Gathers domains into the database, and continues to scrape through each subsequent domain
	prev_site = 'N/A - Starting Domain'
	current_time = datetime.datetime.now()
	urldoc = DB_Structure(_id = check_http(url), url = check_http(url), ref = 'None', Discovered=current_time, LastAccessed=current_time, title='')
	urldoc.store(db)
 		
#	try:	
#		db.save(urldoc)
#	except couchdb.http.ResourceConflict as e:
#		if DEBUG:
#			print "[I] Databse Record for %s already exists! Updating..." % url
#		# Update existing entry
#		db[site]['LastAccessed'] = '%s' % datetime.datetime.now()

	for site in domains:
		if DEBUG:
			print term.format("Scraping %s\n" % site, term.Attr.BOLD)

		try:
			lines = query(site).readlines()

		except AttributeError as e:
			print "[E] Site could not be read!"
			if DEBUG:
				print "Error message: %s" % e
			lines = []

		current_time = str(datetime.datetime.now())
		#urldoc = {'_id': site, 'URL': site, 'ref': prev_site, 'discovered': current_time, 
		#		'LastAccessed' : current_time, "Title": get_title(lines)}

		#Update the current site's entry
		doc = DB_Structure.load(db, check_http(site))
		doc.LastAccessed = datetime.datetime.now()
		doc.title = get_title(lines)
		doc.store(db)

		for x in lines:
			m = re.search('\w+\.onion', x)
			if m:
				full_url = check_http(m.group(0))
				domains.append(full_url)
				if full_url not in db:
					current_time = datetime.datetime.now()
					new_site = DB_Structure(_id = full_url, url = full_url, ref = site, Discovered=current_time, LastAccessed=current_time, title='')
					new_site.store(db)

		#prev_site = site

		#if DEBUG:
		#	for x in domains:
		#		print x

	
	print term.format("\nScraping Complete.", term.Attr.BOLD)
	tor_process.kill()
	print term.format("\nTor Instance Killed.", term.Attr.BOLD)
	

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Tor-Scraper.py - Scrape sites using TOR and searches for .onion domains")
	parser.add_argument('-u', '--url', help="URL to use as scraper origin. Example: http://www.google.com", required=True)
	# TODO: Implement in the future	
	#parser.add_argument('-k', '--keyword', help="Keyword to be searched on page")

	args = parser.parse_args()
	main()
	









