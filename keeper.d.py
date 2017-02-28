#!/usr/bin/env python3

import socket
import json
import os
import subprocess as sp
import sys
import argparse
import getpass
from Crypto import Random
from Crypto.Cipher import AES
import hashlib
import base64
from functools import reduce

PORT = 28961

# actions:
#	{'act': 'save', 'file': <file-to-save>, 'text': <text-to-enc>, 'pass': <password>}
#	{'act': 'load', 'file': <file-to-load>, 'pass': <password>}
#   {'act': 'del',  'file': <file-to-del>, 'pass': <password>}

class AESCipher(object):
    def __init__(self, key): 
        self.bs = 32
        self.key = hashlib.sha256(key.encode()).digest()
    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))
    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')
    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)
    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]

def send(conn, mess):
	raw = mess.encode('utf8')
	l = hex(len(raw))[2:].encode('utf8')
	conn.send(l)
	conn.send(raw)

def main(args,passwd):
	server = socket.socket()
	server.bind( ('127.0.0.1', PORT) )
	server.listen(1)
	while True:
		conn, _ = server.accept()
		count = int(conn.recv(8).decode('utf8'), 16)
		mess = conn.recv(count)
		try:
			req = json.loads(mess)
			if req['pass'] != passwd:
				send(conn, json.dumps({'mess': 'password error'}))
				continue
			if req['act'] == 'save':
				passwd = req['pass']
				name = req['file']
				path = os.path.join(args.dir, name)
				with open(path, 'wt') as h:
					cipher = AESCipher(req['pass'])
					mess = cipher.encrypt(req['text'])
	        	    chunks, chunk_size = len(mess), 64
    		        for line in [ mess[i:i+chunk_size] for i in range(0, chunks, chunk_size) ]:
	    	            h.write(line + '\n')
				os.path.chmod(path, 0o600)
			elif req['act'] == 'load':
				passwd = req['pass']
				name = req['file']
				path = os.path.join(args.dir, name)
				if os.path.isfile(path):
					with open(path, 'rt') as h:
						txt = reduce(lambda a,b: a if len(b) == 0 else a + b, h.read().split('\n'))
						cipher = AESCipher(req['pass'])
						mess = cipher.decrypt(txt)
						send(conn, json.dumps({'text': mess}))
						del mess
						del cipher
						del txt
				else:
					send(conn, json.dumps({'mess': 'file not exist'}))
			elif req['act'] == 'del':
				pass
			else:
				raise Exception('key error', req['act'])
		except Exception as e:
			send(conn, json.dumps({'error': str(e)}))

parser = argparse.ArgumentParser('remove files by request')
parser.add_argument('--daemon', default=False, action='store_true', help='run process as daemon')
parser.add_argument('--dir', help='root directory for cipher store')
args = parser.parse_args()

passwd = getpass.getpass()

if args.dir is None:
	print('no root dir')
	sys.exit(1)
if args.daemon:
	if os.fork() == 0:
		os.setsid()
		main(args,passwd)
else:
	main(args,passwd)

'''
parser.add_argument('--src')
parser.add_argument('--dst')

ans = parser.parse_args()
passwd = getpass.getpass()
with open(ans.src, 'rt') as h:
	acc = ''
	for line in h.read().split('\n'):
		if len(line) > 0:
			acc = acc + line
	mess = AESCipher(passwd).decrypt(acc)
	with open(ans.dst, 'wt') as h:
		h.write(mess)
'''
