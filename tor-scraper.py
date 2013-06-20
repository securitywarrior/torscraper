#!/usr/bin/python

import sys, os
import urllib2
import socket
import httplib
import re
import argparse
#import sqlite3

import socks		# http://socksipy.sourceforge.net

import stem		# http://stem.torproject.org
import stem.process
from stem.util import term

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
		print "Unable to return %s" % url

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

def print_bootstrap_lines(line):
	if "Bootstrapped" in line:
		print term.format(line, term.Color.BLUE)

def check_http(url):
	# urllib2 needs URLs to include http://, so if the user submits "example.com" this will prepend http://
	if not re.search("^http[s]?\:\/\/", url):
		url = "http://" + url

	return url

def main():
	socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', 9050)
	socket.socket = socks.socksocket

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
			print "Error details:"
			print e
		# TODO: Remove this, make script try to connect to running instance
		sys.exit("Please kill all running Tor instances and try again")
			

	domains = []
	url = check_http(args.url)
	domains.append(url)

	# Prints endpoint information if debugging is enabled
	if DEBUG:
		print term.format("[I] Checking Endpoint:", term.Attr.BOLD)
		print query("http://www.atagar.com/echo.php").read()

	#tor_process = stem.process.launch_tor()

	print term.format("\nScraping for .ONION domains:\n", term.Attr.BOLD)
#	print term.format(query(url).read(), term.Color.BLUE)
#	db = sqlite3.connect('contents.db')

	for site in domains:
		if DEBUG:
			print term.format("Scraping %s\n" % site, term.Attr.BOLD)

		lines = query(site).readlines()

		for x in lines:
			m = re.search('\w+\.onion', x)
			if m and (m not in domains):
				domains.append(check_http(m.group(0)))
		if DEBUG:
			for x in domains:
				print x

	

	tor_process.kill()
	print term.format("\nTor Instance Killed.", term.Attr.BOLD)
	

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Tor-Scraper.py - Scrape sites using TOR and search for a keyword")
	parser.add_argument('-u', '--url', help="URL to scrape. Example: http://www.google.com", required=True)
	parser.add_argument('-k', '--keyword', help="Keyword to be searched on page")

	args = parser.parse_args()
	main()
	









