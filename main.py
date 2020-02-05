import multiprocessing
import random
import socket
# noinspection PyUnresolvedReferences
import mysql.connector
# noinspection PyUnresolvedReferences
from blspy import (PrivateKey, PublicKey, Signature, PrependSignature, AggregationInfo, ExtendedPrivateKey, Threshold,
                   Util)
from requests import get
import serialization_pb2
import utils
import socket

print(" " * 10 + "Pebble Node Program")
print("-" * 40)
print("-- Please Wait...")
cpucores = multiprocessing.cpu_count()
NODE_IP = get('https://api.ipify.org').text

TEST_FLAG = False
if (TEST_FLAG):
    NODE_IP = 'localhost'
    print("-- WARNING: TEST_FLAG IS ENABLED")
PORT = 2020
seed = bytes([random.randint(0, 255) for i in range(256)])
PRIVATE_KEY = PrivateKey.from_seed(seed)
PUBLIC_KEY = PRIVATE_KEY.get_public_key()
print("-- " + str(cpucores) + " CPU Cores detected.")
print("-- Deploying {} processes as workers.".format(cpucores - 2))
print("-- External IP: {}".format(NODE_IP))
print("-- Service Port: {}".format(PORT))
print("-- Node Public Key: {}".format(PUBLIC_KEY.serialize().hex()))
print("-- Starting service...")
workersQueue = []
nodes = {}
nodes[PUBLIC_KEY.serialize().hex()] = NODE_IP

sorted_nodekeys = sorted(nodes.keys()) # Error delayed call


class PeerConnectServer(multiprocessing.Process):
    global workersQueue, PUBLIC_KEY, NODE_IP

    def __init__(self, nodes):
        multiprocessing.Process.__init__(self)
        multiprocessing.Process.daemon = True

        self.nodes = nodes
        self.bootstrapnode = input("-- Enter Bootstrapping Node IP :")
        if self.bootstrapnode == "":
            print("-- Bootstrap Node Configured.")
            nodes = {}
        else:
            print("-- Connecting to Network...")
            tempnodes = utils.boostrapping(self.bootstrapnode, PUBLIC_KEY, NODE_IP)
            for i in tempnodes.keys():
                print("-- NODE FOUND: {}".format(tempnodes[i]))
                nodes[i] = tempnodes[i]
        self.serversockin = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.serversockin.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        self.serversockin.bind(('0.0.0.0', PORT + 1))
        while True:
            data, addr = self.serversockin.recvfrom(1024)
            incoming = serialization_pb2.incominghandshake()
            incoming.ParseFromString(data)
            if incoming.sendingpublickey not in self.nodes.keys():
                hello = serialization_pb2.outgoinghandshake()
                tempkey = hello.publickey
                for i in self.nodes.keys():
                    tempkey.append(i)
                tempip = hello.nodeip
                for i in nodes.values():
                    tempip.append(i)
                hello = hello.SerializeToString()
                self.nodes[incoming.sendingpublickey] = incoming.nodeip
                print("-- NODE_FOUND: {}".format(addr[0]))
                print(nodes)
                self.serversockin.sendto(hello, addr)


class UDPServer(multiprocessing.Process):
    global workersQueue, nodes, PUBLIC_KEY

    def __init__(self):
        multiprocessing.Process.__init__(self)
        multiprocessing.Process.daemon = True

        self.serversockin = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.serversockin.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.vectorClock = 0
        self.txHashlist = {}

    def run(self):
        self.serversockin.bind(('0.0.0.0', PORT))
        while True:
            data, addr = self.serversockin.recvfrom(1024)
            if self.vectorClock % 10 == 0 and self.vectorClock != 0:
                print("Created a commitment transaction.")
                """
                Create a commitment tx in all the queues. worker threads create the merkle root of last 10 transactions processed by the this node and send to other nodes.
                """
                self.vectorClock = self.vectorClock + 1  # Do commitment tx
            else:
                try:
                    transaction = serialization_pb2.Transaction()
                    transaction.ParseFromString(data)
                except Exception as e:
                    print("--Not transaction data ")
                    print(e)
                if transaction.txHash in self.txHashlist.keys():
                    workersQueue[self.txHashlist[transaction.txHash]].put(transaction)
                else:
                    timestamps = transaction.timestamp
                    timestamps[sorted_nodekeys.index(PUBLIC_KEY.serialize().hex())] = self.vectorClock
                    txhash = int(transaction.txHash, 16)
                    workerid = (txhash % (cpucores - 3))
                    print("Assigned to {}".format(workerid))
                    self.txHashlist[transaction.txHash] = workerid
                    workersQueue[workerid].put(transaction)
                    self.vectorClock = self.vectorClock + 1


class workerthread(multiprocessing.Process):  # This is where the processing happens
    global workersQueue, PUBLIC_KEY, PRIVATE_KEY

    def __init__(self, workerID):
        multiprocessing.Process.__init__(self)
        multiprocessing.Process.daemon = True
        self.workerID = workerID
        self.waitingTx = {}
        self.transaction = None
        self.conn = mysql.connector.connect(host='localhost', user='root', passwd='')
        self.autocommit = True
        self.cursor = self.conn.cursor()
        print("-- Worker {} started.".format(self.workerID))
        try:
            self.cursor.execute("USE blockchain;")
            self.cursor.execute(
                """SELECT txHash FROM worker{} ORDER BY vectorClock DESC LIMIT 1;""".format(str(self.workerID)))
            self.result = self.cursor.fetchall()
            self.prevtxHash = self.result[0][0]

        except mysql.connector.errors.ProgrammingError as e:
            self.prevtxHash = "GENESIS_HASH"
            self.cursor.execute(
                "CREATE TABLE {} (txHash text,vectorClock integer,tx_binary blob,time timestamp);".format(
                    'worker' + str(self.workerID)))
            self.cursor.execute(
                "INSERT INTO worker{} VALUES ('{}',0,'GENESIS_TX',NOW());".format(str(self.workerID),
                                                                                  self.prevtxHash))
            self.conn.commit()
            self.result = self.cursor.execute("SELECT * FROM worker{};".format(self.workerID))
            if self.result is not None:
                for i in self.result:
                    print(i)

    def run(self):
        while not workersQueue[self.workerID].empty():
            self.transaction = workersQueue[self.workerID].get()
            print("-- LOG: {} from worker-{}".format(self.transaction.txHash, self.workerID))
            #self.cursor.execute( """SELECT txHash FROM worker{} ORDER BY vectorClock DESC LIMIT 1;""".format(str(self.workerID)))
            #self.result = self.cursor.fetchall()
            #self.prevtxHash = self.result[0][0]
            #self.transaction.txHash = utils.txhash_generator(self.prevtxHash.encode('utf-8'),self.transaction.txHash)
            print(self.transaction.txHash)

    def __exit__(self):
        print("Destroying worker {} ".format(self.workerID))
        self.conn.close()

peerconnectServer = PeerConnectServer(nodes)
peerconnectServer.start()
print("-----Peer Server is running...")
for i in range(cpucores - 3):
    worker = workerthread(i)
    workerQueue = multiprocessing.Queue()
    workersQueue.append(workerQueue)
    worker.start()
print("-----Worker Processes deployed...")
server = UDPServer()
server.start()
print("-----UDP Server is running...")
while True:
    pass