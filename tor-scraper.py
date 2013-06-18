#!/usr/bin/python

import sys, os
import urllib2
import socket

import socks		# http://socksipy.sourceforge.net

import stem		# http://stem.torproject.org
import stem.process
from stem.util import term

def query(url):
	try:
		return urllib2.urlopen(url).read()
	except:
		print "Unable to return %s" % url


def print_bootstrap_lines(line):
	if "Bootstrapped" in line:
		print term.format(line, term.Color.BLUE)

def main():
	socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', 9050)
	socket.socket = socks.socksocket

	print term.format("Starting Tor:\n", term.Attr.BOLD)

#	tor_process = stem.process.launch_tor_with_config(
#		config = {
#			'SocksPort':str(9050),
#			'ControlPort':str(9051),
#			},
#		init_msg_handler = print_bootstrap_lines,
#		completion_percent = 100,
#		timeout = 3600
#	)

	tor_process = stem.process.launch_tor()

	print term.format("\nChecking endpoints:\n", term.Attr.BOLD)
	print term.format(query("http://atagar.com/echo.php"), term.Color.BLUE)

	tor_process.kill()
	

if __name__ == "__main__":
	main()


