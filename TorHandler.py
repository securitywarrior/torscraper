#!/usr/bin/python3
#
# Tor Handler class for Tor scraper 

import sys, os
import urllib
import socket
import http

import socks		# Now using branch version for compatibility with Python 3.x
			# https://code.google.com/p/socksipy-branch/

import stem		# http://stem.torproject.org
import stem.process
import stem.control
from stem.util import term

class TorHandler():
	def __init__(self):
		self.SocksPort = str(9050)
		self.ControlPort = str(9051)
		self.tor_process = None

	def start_tor(self):
		print(term.format("Starting Tor:\n", term.Attr.BOLD))
		try:
			self.tor_process = stem.process.launch_tor_with_config(
				config = {
					'SocksPort':self.SocksPort,
					'ControlPort':self.ControlPort,
					},
				init_msg_handler = self.print_bootstrap_lines,
				completion_percent = 100,
				timeout = 3600,
				take_ownership = True
			)
			return True
		except OSError:
			return False
	
	def kill_tor(self):
		try:	
			self.tor_process.kill()
			print(term.format("\nTor Instance Killed.", term.Attr.BOLD))
			return True
		except NameError as e:
			return False

	def start_controller(self):
		try:
			control = stem.control.Controller.from_port(address='127.0.0.1', port=9051)
			control.authenticate()
			return True
		except stem.SocketError:
			return False

	def query(self, url):
		opener = urllib.request.build_opener(SocksiPyHandler(socks.PROXY_TYPE_SOCKS5, "localhost", int(self.SocksPort)))
		h = opener.open(url)
		return h

	def print_bootstrap_lines(self, line):
		if "Bootstrapped" in line:
			print(term.format(line, term.Color.BLUE))

	def check_endpoint(self):
		print(term.format("[I] Checking Endpoint:", term.Attr.BOLD))
		return((self.query("http://www.atagar.com/echo.php").read()).decode('utf8'))


class SocksiPyConnection(http.client.HTTPConnection):
    def __init__(self, proxytype, proxyaddr, proxyport = None, rdns = True, username = None, password = None, *args, **kwargs):
        self.proxyargs = (proxytype, proxyaddr, proxyport, rdns, username, password)
        http.client.HTTPConnection.__init__(self, *args, **kwargs)

    def connect(self):
        self.sock = socks.socksocket()
        self.sock.setproxy(*self.proxyargs)
        if isinstance(self.timeout, float):
            self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))

class SocksiPyHandler(urllib.request.HTTPHandler):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kw = kwargs
        urllib.request.HTTPHandler.__init__(self)

    def http_open(self, req):
        def build(host, port=None, strict=None, timeout=0):
            conn = SocksiPyConnection(*self.args, host=host, port=port, strict=strict, timeout=timeout, **self.kw)
            return conn
        return self.do_open(build, req)

	
