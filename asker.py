#!/usr/bin/env python3

import socket
import json
import argparse

PORT = 28961

parser = argparse.ArgumentParser('control panel for cipher daemon')
parser.add_argument('-m', help='mode (sf|lf|st|d) - save file, load file, save text, del')
parser.add_argument('-n', help='filename in store')
parser.add_argument('-f', help='file')
parser.add_argument('-p', help='password')

args = parser.parse_args()

def to8(s):
    for _ in range(0, 8 - len(s)):
        s = '0' + s
    return s
def request(js):
	client = socket.socket()
	client.connect( ('127.0.0.1', PORT) )
	mess = json.dumps(js).encode('utf8')
	client.send(to8(hex(len(mess))[2:]).encode('utf8'))
	client.send(mess)
	count = int(client.recv(8).decode('utf8'), 16)
	ans = client.recv(count)
	return ans
