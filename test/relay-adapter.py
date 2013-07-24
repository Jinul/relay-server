
# Set these values for your relay and servers.

RELAY_SERVER = ('localhost', 8082)

SERVERS = [
    ('localhost', 8088)
    ,('localhost', 8089)
    #,('localhost', 8113)
    ]

VERBOSE = 1



# BEWARE: a blank request (eg. only a newline) signals an end to that whole cilent-server conversation

import socket
import threading

SHUTDOWN_COMMAND = "shutdown adapter"

# Read from the sockets, looking for "\n" (one character at a time).
def readLine(s):
    return s.makefile().readline().rstrip("\n")
'''
    # another approach
    ret = ''
    while True:
        c = s.recv(1)
        if c == '\n' or c == '':
            break
        else:
            ret += c
    return ret
'''


def hostAndPortTuple(hostAndPort):
    hostPortList = hostAndPort.split(":")
    return (hostPortList[0], int(hostPortList[1]))

socketsToShutdown = []
def shutdownAllSockets():
    print "Shutting it all down."
    for sock in socketsToShutdown:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        finally:
            pass # don't care about errors; just want to close them all
    exit(0)


class CopyFromSockToSock(threading.Thread):
    def __init__(self, clientSock, serverSock):
        super(CopyFromSockToSock, self).__init__()
        self.clientSock = clientSock
        self.serverSock = serverSock
    def run(self):
        try:
            request = readLine(self.clientSock)
            while (request != ''):
               if (request == SHUTDOWN_COMMAND):
                   shutdownAllSockets()
               else:
                    self.serverSock.sendall(request + "\n")
                    response = readLine(self.serverSock)
                    self.clientSock.sendall(response + "\n")
                    request = readLine(self.clientSock)
        finally:
            self.clientSock.close()
            self.serverSock.close()






class RouteThroughRelay(threading.Thread):
    def __init__(self, publicHostAndPort, relaySock, serverHostAndPort):
        super(RouteThroughRelay, self).__init__()
        self.publicHostAndPort = publicHostAndPort
        self.serverHostAndPort = serverHostAndPort
        self.relaySock = relaySock
    def run(self):

        # This is the part of the program where you'll want to customize behavior for this server.

        newClientHostPortStr = readLine(self.relaySock)
        while (newClientHostPortStr != ''):
            if (VERBOSE):
                print "New client now available at {} going to {}".format(newClientHostPortStr,
                                                                          self.serverHostAndPort)
            newClientHostAndPort = hostAndPortTuple(newClientHostPortStr)
            
            clientRelaySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            clientRelaySock.connect(newClientHostAndPort)
            socketsToShutdown.append(clientRelaySock)
            
            serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            serverSock.connect(self.serverHostAndPort)
            socketsToShutdown.append(serverSock)
            
            CopyFromSockToSock(clientRelaySock, serverSock).start()

            newClientHostPortStr = readLine(self.relaySock)




class RouteThroughOldRelay(threading.Thread):
    def __init__(self, publicHostAndPort, relaySock, serverHostAndPort):
        super(RouteThroughOldRelay, self).__init__()
        self.publicHostAndPort = publicHostAndPort
        self.serverHostAndPort = serverHostAndPort
        self.relaySock = relaySock
    def run(self):

        # This is the part of the program where you'll want to customize behavior for this server.

        serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSock.connect(self.serverHostAndPort)
        socketsToShutdown.append(serverSock)
            
        CopyFromSockToSock(self.relaySock, serverSock).start()








print "To shutdown, connect to any public port and enter:", SHUTDOWN_COMMAND

# For each server, get a connection to the relay.
for idx, serverHostAndPort in enumerate(SERVERS):
    relaySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    relaySock.connect(RELAY_SERVER)
    socketsToShutdown.append(relaySock)

    # get the HOST:PORT for this server's public address
    publicHostAndPort = hostAndPortTuple(readLine(relaySock))
    if (VERBOSE):
        print "server {}={} is public at {}".format(idx, serverHostAndPort, publicHostAndPort)

    RouteThroughRelay(publicHostAndPort, relaySock, serverHostAndPort).start()
    #RouteThroughOldRelay(publicHostAndPort, relaySock, serverHostAndPort).start()
    
