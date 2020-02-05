import serialization_pb2
import socket, hashlib, string, random


def boostrapping(bootstranode, PUBLICKEY, NODE_IP):
    serversockin = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serversockin.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # serversockin.bind(('0.0.0.0', 2020))
    hi = serialization_pb2.incominghandshake()
    hi.sendingpublickey = PUBLICKEY.serialize().hex()
    hi.nodeip = NODE_IP
    hi = hi.SerializeToString()
    serversockin.sendto(hi, (bootstranode, 2021))
    data = ""
    while data is "":
        data, addr = serversockin.recvfrom(1024)
        # print(data)
    hello = serialization_pb2.outgoinghandshake()
    hello.ParseFromString(data)
    keys = hello.publickey
    ips = hello.nodeip
    nodes = dict(zip(keys, ips))
    for i in nodes.values():
        serversockin.sendto(hi, (i, 2021))
    serversockin.close()
    return nodes


def txhash_generator(signature, payload):
    hasher = hashlib.md5()
    hasher.update(signature)
    hasher.update(payload)
    txhash = hasher.hexdigest()
    return txhash


def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))
