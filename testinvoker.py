import random
import serialization_pb2
import requests,utils,boto3

# noinspection PyUnresolvedReferences
from blspy import (PrivateKey, PublicKey, Signature, PrependSignature, AggregationInfo, ExtendedPrivateKey, Threshold,
                   Util)

from utils import txhash_generator
import socket
import sys


if __name__ == '__main__':
    seed = bytes([random.randint(0, 255) for i in range(256)])
    PRIVATE_KEY = PrivateKey.from_seed(seed)
    PUBLIC_KEY = PRIVATE_KEY.get_public_key()
    TESTKEY = PrivateKey.from_seed(seed)
    TESTPKEY = PRIVATE_KEY.get_public_key()
    sqs = boto3.client('sqs',region_name='ap-south-1')
    queue_url = "https://sqs.ap-south-1.amazonaws.com/876703040586/PebbleMumbaiServer"

    #print("-- Configured for {} at {}".format(serverip, 2020))
    print("-- PUBLIC KEY: {}".format(PUBLIC_KEY.serialize().hex()))
    #print("-- Sending transactions from {} ".format(2021))
    #API_ENDPOINT="http://{}:5000/newtransaction".format(serverip)
    #serversockin = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #serversockin.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    while True:
        print("-- Enter 1 to create and send a empty transaction ")
        print("-- Enter 2 to create and send N transactions ")
        a = int(input("Enter Option: "))
        if a == 1:
            payload = ""
            transaction = serialization_pb2.Transaction()
            transaction.payload = payload.encode('utf-8')  # Payload set
            transaction.UserPublicKey = PUBLIC_KEY.serialize().hex()  # User PKey set
            signature = PRIVATE_KEY.sign(payload.encode('utf-8'))
            transaction.MultiSignature = signature.serialize().hex()  # Signature Set
            transaction.txHash = txhash_generator(signature.serialize(), payload.encode('utf-8'))
            timestamps = transaction.timestamp # Fixing the timestamps
            transaction.RecipientPublickey = TESTPKEY.serialize().hex()
            transaction.NodeListSeed = 28 # Node list seed
            transaction.commitment = False # Commitment Flag
            for i in range(5):
                timestamps.append(-1)
            tx_bytes = transaction.SerializeToString()
            #sock.sendall(tx_bytes)
            print(tx_bytes)
            print(len(tx_bytes))
            response = sqs.send_message(
                QueueUrl=queue_url,
                DelaySeconds=0,
                MessageAttributes={'Transaction':{'DataType':'Binary','BinaryValue':tx_bytes}},
                MessageBody=(" Pebble Transactions"))
            print(response['MessageId'])
            #r = requests.post(url=API_ENDPOINT, data=tx_bytes)
            #print(r.text)
            #serversockin.sendto(tx_bytes, (serverip, 2020))
        if a==2:
            N = int(input("Enter number of transactions to create : "))
            for i in range(N):
                payload = utils.randomString()
                transaction = serialization_pb2.Transaction()
                transaction.payload = payload.encode('utf-8')  # Payload set
                transaction.UserPublicKey = PUBLIC_KEY.serialize().hex()  # User PKey set
                signature = PRIVATE_KEY.sign(payload.encode('utf-8'))
                transaction.MultiSignature = signature.serialize().hex()  # Signature Set
                transaction.txHash = txhash_generator(signature.serialize(), payload.encode('utf-8'))
                timestamps = transaction.timestamp  # Fixing the timestamps
                transaction.RecipientPublickey = TESTPKEY.serialize().hex()
                transaction.NodeListSeed = 28  # Node list seed
                transaction.commitment = False  # Commitment Flag
                for i in range(5):
                    timestamps.append(-1)
                tx_bytes = transaction.SerializeToString()
                print(tx_bytes)
                print(len(tx_bytes))
                response = sqs.send_message(
                    QueueUrl=queue_url,
                    DelaySeconds=0,
                    MessageAttributes={'Transaction': {'DataType': 'Binary', 'BinaryValue': tx_bytes}},
                    MessageBody=(" Pebble Transactions"))
                print(response['MessageId'])
                #r = requests.post(url=API_ENDPOINT, data=tx_bytes)
                #print(r.text)
                #sock.sendall(tx_bytes)
                #serversockin.sendto(tx_bytes, (serverip, 2020))
                #print("-- Tx Hash {} is sent.".format(transaction.txHash))
        if a==3:
            break

