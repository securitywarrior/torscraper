#!/usr/bin/python

import sys, os
import urllib2
import socket
import httplib
import re

import socks		# http://socksipy.sourceforge.net

import stem		# http://stem.torproject.org
import stem.process
from stem.util import term

def query(url):
	# urllib2 needs URLs to include http://, so if the user submits "example.com" this will prepend http://
	if not re.search("^http\:\/\/", url):
		url = "http://" + url
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

def main(url):
	socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', 9050)
	socket.socket = socks.socksocket


	print term.format("Starting Tor:\n", term.Attr.BOLD)

	tor_process = stem.process.launch_tor_with_config(
		config = {
			'SocksPort':str(9050),
			'ControlPort':str(9051),
			},
		init_msg_handler = print_bootstrap_lines,
		completion_percent = 100,
		timeout = 3600
	)

	#tor_process = stem.process.launch_tor()

	print term.format("\nChecking endpoints:\n", term.Attr.BOLD)
	print term.format(query(url).read(), term.Color.BLUE)

	tor_process.kill()
	print term.format("\nTor Instance Killed.", term.Attr.BOLD)
	

if __name__ == "__main__":
	if len(sys.argv) > 1:
		main(sys.argv[1])
	else:
		print "Please supply a URL to gather\n"
		print "python tor-scraper.py url\n"



