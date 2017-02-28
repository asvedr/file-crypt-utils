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

parser = argparse.ArgumentParser('remove files by request')
parser.add_argument('--daemon', default=False, action='store_true', help='run process as daemon')
parser.add_argument('--root', default=False, action='store_true', help='allow run from root')
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
