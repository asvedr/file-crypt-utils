import socket
import json
import os

sock = socket.socket()
sock.bind( ('127.0.0.1', 28960) )
sock.listen(1)
while True:
	conn, addr = sock.accept()
	count = int(conn.recv(8).decode('utf8'), 16)
	data = conn.recv(count)
	try:
		data = data.decode('utf8')
		print(data)
		data = json.loads(data)
		for fl in data['f']:
			os.remove(fl)
		for dr in data['d']:
			os.rmdir(dr)
		conn.send(b'y')
	except Exception as e:
		print(e)
		conn.send(b'n')
