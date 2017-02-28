#!/usr/bin/env python3
import socket
import json
import os
import subprocess as sp
import sys
import argparse

def main(forceroot, tdir):
	if tdir is None:
		print('DIR NOT SET')
		return
	tdir = os.path.abspath(tdir)
	uname = sp.check_output(['whoami']).decode('utf8').strip()
	if uname == 'root' and not forceroot:
		print("SHIT!!! DON'T RUN ME FROM ROOT")
		print('if you REALY want to run it from root use flag --root')
		return
	sock = socket.socket()
	sock.bind( ('127.0.0.1', 28960) )
	sock.listen(1)
	while True:
		conn, _ = sock.accept()
		count = int(conn.recv(8).decode('utf8'), 16)
		data = conn.recv(count)
		try:
			data = data.decode('utf8')
			#print(data)
			data = json.loads(data)
			for fl in data['f']:
				if fl.startswith(tdir):
					os.remove(fl)
			for dr in data['d']:
				os.rmdir(dr)
			conn.send(b'y')
		except Exception as e:
			print(e)
			conn.send(b'n')

parser = argparse.ArgumentParser('remove files by request')
parser.add_argument('--daemon', default=False, action='store_true', help='run process as daemon')
parser.add_argument('--root', default=False, action='store_true', help='allow run from root')
parser.add_argument('--dir', help='target dir')

ans = parser.parse_args()

if ans.daemon:
	if os.fork() == 0:
		os.setsid()
		main(ans.root, ans.dir)
else:
	main(ans.root, ans.dir)
