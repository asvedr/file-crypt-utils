#!/usr/bin/env python3

import socket
import json
import argparse
import sys

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
    ans = client.recv(count).decode('utf8')
    return json.loads(ans)

def saveFile(pswd, name, src):
    with open(src, 'rt') as h:
        mess = h.read()
    return request({'act': 'save', 'file': name, 'pass': pswd, 'text': mess})

def loadFile(pswd, name, dst):
    ans = request({'act': 'load', 'file': name, 'pass': pswd})
    if dst is None:
        return ans
    elif 'text' in ans:
        with open(dst, 'wt') as h:
            h.write(ans['text'])
        return {'mess': 'ok'}
    else:
        return ans

def saveText(pswd, name, _):
    mess = sys.stdin.read()
    return request({'act': 'save', 'file': name, 'text': mess, 'pass': pswd})

def delete(pswd, name, _):
    return request({'act': 'del',  'file': name, 'pass': pswd})

def main():
    cmds = {'sf': saveFile, 'lf': loadFile, 'st': saveText, 'd' : delete}
    try:
        f = cmds[args.m]
    except:
        print('bad mode')
        return
    pswd = args.p
    if pswd is None:
        print('no pass')
        return
    sfile = args.n
    if sfile is None:
        print('no server filename')
        return
    ufile = args.f
    ans = f(pswd, sfile, ufile)
    if 'mess' in ans:
        print('MESS')
        print(ans['mess'])
    elif 'error' in ans:
        print('ERROR')
        print(ans['error'])
    elif 'text' in ans:
        print('TEXT')
        print(ans['text'])
    else:
        print('incorrect answer')

main()
