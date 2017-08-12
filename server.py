#!/usr/bin/env python3
from struct import pack, unpack
from collections import defaultdict
import sys, socketserver, socket, threading

uploadDict = defaultdict(list)
downloadDict = defaultdict(list)
transmitThreadLst = []

def terminateServer():
	global server
	server.shutdown()

def transmit(uploadSocket, downloadSocket, key):
	while True:
		pkt = uploadSocket.recv(512)
		if not pkt: break
		downloadSocket.send(pkt)
	downloadSocket.close()

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
	def handle(self):
		global cv, uploadDict, downloadDict, transmitThreadLst, socketKeeper, termination, transmit, terminateServer
		instruction = self.request.recv(9).decode("utf-8")
		command = instruction[0]
		key = instruction[1:9]
		# print(key, command)

		if command == "F": # termination
			termination = True
			for thread in transmitThreadLst:
				thread.join()
			with cv:
				cv.notify_all()
			with socketKeeper:
				socketKeeper.notify_all()
			terminationThread = threading.Thread(name="terminationThread", target=terminateServer)
			terminationThread.start()
			terminationThread.join()
			return

		elif command == "G" and not termination: # download
			downloadDict[key].append(self.request)
			# print("========= G ========")
			# print("upload dict")
			# for key in uploadDict: print(key)
			# print("--------------------")
			# print("download dict")
			# for key in downloadDict: print(key)
			# print("========= G ========")
			if key not in uploadDict:
				with cv:
					while key not in uploadDict:
						cv.wait()
						if termination:
							# print("G"+key+" will be cut down")
							return
					uploadSocket = uploadDict[key].pop()
					if len(uploadDict[key]) == 0:
						del uploadDict[key]
					downloadSocket = downloadDict[key].pop()
					if len(downloadDict[key]) == 0:
						del downloadDict[key]
				transmitThread = threading.Thread(name="transmitThread", target=transmit, args=(uploadSocket, downloadSocket, key))
				transmitThreadLst.append(transmitThread)
				transmitThread.start()
			else:
				with cv:
					cv.notify_all()

		elif command == "P" and not termination: # upload
			uploadDict[key].append(self.request)
			# print("========= P ========")
			# print("upload dict")
			# for key in uploadDict: print(key)
			# print("--------------------")
			# print("download dict")
			# for key in downloadDict: print(key)
			# print("========= P ========")
			if key not in downloadDict:
				with cv:
					while key not in downloadDict:
						cv.wait()
						if termination:
							# print("P"+key+" will be cut down")
							return
					uploadSocket = uploadDict[key].pop()
					if len(uploadDict[key]) == 0:
						del uploadDict[key]
					downloadSocket = downloadDict[key].pop()
					if len(downloadDict[key]) == 0:
						del downloadDict[key]
				transmitThread = threading.Thread(name="transmitThread", target=transmit, args=(uploadSocket, downloadSocket, key))
				transmitThreadLst.append(transmitThread)
				transmitThread.start()
			else:
				with cv:
					cv.notify_all()

		with socketKeeper:
			socketKeeper.wait()


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


HOST, PORT = "", 0

server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
print(server.server_address[1])
portFile = open("port", "w+")
portFile.write(str(server.server_address[1]))
portFile.close()

termination = False
cv = threading.Condition()
socketKeeper = threading.Condition()
server.serve_forever()