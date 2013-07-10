#!/usr/bin/python3
#
# NOTE: This version requires Python 3.x to run

import sys, os
import socket
import re
import argparse
import datetime
import queue
import concurrent.futures

import couchdb		# Running branch patched for Python 3
			# https://github.com/lilydjwg/couchdb-python3
from couchdb.mapping import Document, TextField, IntegerField, DateTimeField, BooleanField

import TorHandler

# Enable or disable debug messages
# Codes:
# [I] - Informational Messages
# [E] - Error Messages
DEBUG = True

class DB_Structure(Document):
	_id = TextField()
	url = TextField()
	ref = TextField()
	Discovered = DateTimeField()
	LastAccessed = DateTimeField()
	title = TextField()
	is_alive = BooleanField()

def check_http(url):
	# urllib needs URLs to include http://, so if the user submits "example.com" this will prepend http://
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

def scrape_site(site, domains, db, handler):
	doc = DB_Structure.load(db, check_http(site))
	if doc.LastAccessed is not None and (datetime.datetime.now() - doc.LastAccessed).total_seconds() < 300:
		if DEBUG:
			print('Site scraped within the last 5 minutes! Skipping...')		
		return

	alive = True
	if DEBUG:
		print("Scraping {0}".format(site))

	try:
		lines = handler.query(site).readlines()

	except AttributeError as e:
		print("[E] Site could not be read!")
		if DEBUG:
			print("Error message: {0}".format(e))
		lines = []
		alive = False

	lines = [x.decode('utf8', errors='replace') for x in lines]

	#Update the current site's entry

	doc.LastAccessed = datetime.datetime.now()
	doc.title = get_title(lines)
	doc.is_alive = alive
	doc.store(db)

	for x in lines:
		m = re.search('\w+\.onion', x)
		if m:
			full_url = check_http(m.group(0))
			domains.put(full_url)
			if full_url not in db:
				current_time = datetime.datetime.now()
				new_site = DB_Structure(_id = full_url, url = full_url, ref = site, Discovered=current_time, LastAccessed=None, title='', is_alive=False)
				new_site.store(db)

def main():

	# TODO: Add command line switch to set db server? Or config file?
	dbserv = couchdb.Server('http://localhost:5984/')

	# CouchDB connection and db creation
	try:
		db = dbserv['sites']
	except socket.error as e:
		print("[E] Could not connect to the database!")
		if DEBUG:
			print("Error message: {0}".format(e))
		sys.exit("Please make sure that the database has been started, and try again")
	except couchdb.http.ResourceNotFound:
		if DEBUG:
			print("[I] Building initial database...")
		db = dbserv.create('sites')

	# start the Tor process
	handler = TorHandler.TorHandler()
	if not handler.start_tor():
		print("[E] There was an error launching Tor. It may already be running.")

	if not handler.start_controller():
		print("[E] Could not connect to control port!")
		sys.exit("Please kill all running Tor instances and try again")
		
	domains = queue.Queue(0)
	url = check_http(args.url)
	domains.put(url)

	# Prints endpoint information if debugging is enabled
	if DEBUG:
		print(handler.check_endpoint())
		
	print("\nScraping for .ONION domains:\n")

	# Sets up DB entry for initial site being scraped
	if url not in db:	
		prev_site = 'N/A - Starting Domain'
		current_time = datetime.datetime.now()
		urldoc = DB_Structure(_id = check_http(url), url = check_http(url), ref = 'None', 
			Discovered=current_time, LastAccessed=None, title='')
		urldoc.store(db)

	# Main scraping loop
	# Gathers domains into the database, and continues to scrape through each subsequent domain

	with concurrent.futures.ThreadPoolExecutor(max_workers=5) as e:
		while domains.qsize() > 0:
			scrape_array = []
			if domains.qsize() > 4:
				for x in range(0,5):
					scrape_array.append(domains.get())
			else:
				for x in range(0,domains.qsize()):
					scrape_array.append(domains.get())	

			scraper = [e.submit(scrape_site, x, domains, db, handler) for x in scrape_array]
			
			# Hackish way to make the threads wait until the queue is populated again, or until all threads are done
			if domains.qsize() == 0:
				x = [s.result for s in concurrent.futures.as_completed(scraper)]
				
	print("\nScraping Complete.")

	if not handler.kill_tor():
		print("[E] Error killing the Tor process! It may already be dead.")
	else:
		print("\nTor Instance Killed.")

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Tor-Scraper.py - Scrape sites using TOR and searches for .onion domains")
	parser.add_argument('-u', '--url', help="URL to use as scraper origin. Example: http://www.google.com", required=True)
	# TODO: Implement in the future	
	#parser.add_argument('-k', '--keyword', help="Keyword to be searched on page")

	args = parser.parse_args()
	main()
	









