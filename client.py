#!/usr/bin/env python3
from struct import pack, unpack
import socket, sys, os, io, math, time

# terminate server: client <host> <port> F
# download: client <host> <port> G<key> <file name> <recv size>
# upload: client <host> <port> P<key> <file name> <send size> <wait time>

def tryInt(s):
	try:
		int(s)
		return True
	except ValueError:
		return False


HOST, PORT, instruction = sys.argv[1:4]
PORT = int(PORT)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
if (instruction[0] == "F"):
	instruction = instruction + "\0\0\0\0\0\0\0\0"
	s.send(str.encode(instruction))

elif (instruction[0] == "G"):
	while len(instruction) < 9:
		instruction = instruction + "\0"
	s.send(str.encode(instruction))
	fileName, payloadSize = sys.argv[4:]
	payloadSize = int(payloadSize)
	fd = open(fileName, "wb+")
	while True:
		pkt = s.recv(payloadSize)
		if not pkt: break
		fd.write(pkt)
	fd.close()

elif (instruction[0] == "P"):
	while len(instruction) < 9:
		instruction = instruction + "\0"
	s.send(str.encode(instruction))
	fileName, payloadSize, waitTime = sys.argv[4:]
	payloadSize, waitTime = int(payloadSize), int(waitTime)
	if (tryInt(fileName)):
		fileSize = int(fileName)
		fd = io.BytesIO(bytes(fileSize))
	else:
		fd = open(fileName, "rb")
		fileSize = os.path.getsize(fileName)
	while True:
		chunk = fd.read(payloadSize)
		if not chunk: break
		s.send(bytes(chunk))
		time.sleep(waitTime / 1000.0)
	fd.close()




