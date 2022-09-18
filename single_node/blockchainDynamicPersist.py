'''
Description: Script for running user-defined number of transactions and clients and references previous blocks
'''


import hashlib
import random
import string
import json
import binascii
import numpy as np
import pandas as pd
import pylab as pl
import logging
import datetime
import Crypto.Random
import pickle
import sys
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from os.path import exists

class Client:
    def __init__(self, name):
        random = Crypto.Random.new().read
        self._private_key = RSA.generate(1024, random)
        self._public_key = self._private_key.publickey()
        self._signer = PKCS1_v1_5.new(self._private_key)
        self.name = name
    
    def sign(self):
        return self._private_key

    @property
    def identity(self):
        return binascii.hexlify(self._public_key.exportKey(format='DER')).decode('ascii')
    
    def __eq__ (self, name):
        return self.name == name


class Transaction:
    def __init__(self, sender, recipient, value):
        self.sender = sender
        self.recipient = recipient
        self.value = value
        self.time = datetime.datetime.now()

    def to_dict(self):

        return {
            'sender': self.sender.name,
            'recipient': self.recipient.name,
            'value': self.value,
            'time': self.time
        }

    def sign_transaction(self, signer):
        # uses sender's private key to sign transaction
        if (signer.sign() == self.sender.sign()):
            private_key = self.sender._private_key
            signer = PKCS1_v1_5.new(private_key)
            h = SHA.new(str(self.to_dict()).encode('utf8'))
            return binascii.hexlify(signer.sign(h)).decode('ascii')

    def display_transaction(self):
        dict = self.to_dict()
        print ("Transaction Data")
        print ('----------------')
        print ("sender: " + dict['sender'])
        print ('-----')
        print ("recipient: " + dict['recipient'])
        print ('-----')
        print ("value: " + str(dict['value']))
        print ('-----')
        print ("time: " + str(dict['time']))
        print ('-----')


# acts as memory pool for transactions before getting added to a block
class MemPool:
    def __init__(self):
        self.transactions = []
    def display_mempool(self):
        if len(self.transactions) > 0:
            for transaction in self.transactions:
                transaction.display_transaction()
        else:
            print ("Mem Pool is empty")
    def add_transaction(self, transaction):
        self.transactions.append(transaction)
    def pull_transaction(self):
        nextTransaction = self.transactions[0]
        self.transactions.pop(0)
        return nextTransaction
    def get_size(self):
        return len(self.transactions)


# ensapsulates transactions to be added to blockchain
class Block:
    def __init__(self):
        self.verified_transactions = []
        self.previous_block_hash = ""
        self.Nonce = ""
        self.blockHeight = 0
    def display_block(self):
        print ("Block #" + str(self.blockHeight))
        print ("--------")
        for transaction in self.verified_transactions:
            transaction.display_transaction()
    def add_transaction(self, transaction):
        self.verified_transactions.append(transaction)
    def to_dict(self) -> dict:
        returnDict = {}
        for x, transaction in enumerate(self.verified_transactions):
            returnDict[x] = transaction.to_dict()
        return returnDict


# contains record of all transactions made
class Blockchain:
    def __init__(self):
        self.latestBlockHash = ""
        self.chainLength = 0
        self.chain = []
        self.difficulty = 2
    def add_block(self, newBlock, fromFile):
        # appends a block to the blockchain
        self.chain.append(newBlock)
        self.latestBlockHash = hash(newBlock)
        self.chainLength += 1
        newBlock.blockHeight = self.chainLength
        if fromFile is False:
            persist_block(newBlock)
        # maybe add logic to check hashes (verify before adding?)
    def get_chain_length(self):
        return self.chainLength
    def get_last_hash(self):
        return self.latestBlockHash
    def display_chain(self):
        print ("Number of blocks: " + str(self.get_chain_length()))
        for block in self.chain:
            print("========================")
            block.display_block()
    def verify_chain(self):
        # iterates over the blockchain from genesis to latest and checks hashes
        for i in range(0, self.chainLength-1):
            if (hash(self.chain[i]) != self.chain[i+1].previous_block_hash):
                return False
        return True
    def read_blockchain(self, blockchain_data):
    # reads pickled blocks if there are existing data
        if exists(blockchain_data):
            with open(blockchain_data, 'rb') as file:
                i = 0
                while i < 5:
                    try:
                        block = pickle.load(file)
                    except EOFError:
                        break
                    else:
                        self.add_block(block, True)
        else:
            print ("No prior blockchain data found")
    def to_dict(self) -> dict:
        returnDict = {}
        for x, block in enumerate(self.chain):
            returnDict[x] = block.to_dict()
        return returnDict


class Miner:
    def __init__(self) -> None:
        self.client = Client()
    def mine(message, difficulty = 1):
        # mines a block based on a given difficulty value
        assert difficulty >= 1, "Difficulty is invalid"
        prefix = '0' * difficulty
        for i in range(10000):
            digest = sha256(str(hash(message)) + str(i))
            if (digest.startswith(prefix)):
                # print ("after " + str(i) + " iterations found nonce: " + digest)
                return digest


def check_cla() -> bool:
    return len(sys.argv) == 3


def persist_block(newBlock):
    # appends a pickled block to file
    with open(blockchain_data, 'ab') as file:
        pickle.dump(newBlock, file)


def read_clients(client_data):
    # reads pickled clients from file
    clientList = []
    if exists(client_data):
        with open (client_data, 'rb') as file:
            while True:
                try:
                    client = pickle.load(file)
                except EOFError:
                    break
                else:
                    clientList.append(client)
    return clientList


def sha256(message):
    return hashlib.sha256(message.encode('ascii')).hexdigest()


memPool = MemPool()
blockchain = Blockchain()
blockchain_data = 'blockchain_data_DP.txt'
client_data = 'client_data_DP.txt'
json_file = 'output_DP.json'

def main():
    if (check_cla() is False):
        print ("Proper format: python3 BasicBlockchainDynamic.py #clients #transactions")
    else:
        blockchain.read_blockchain(blockchain_data)
        clientList = []
        numClients = sys.argv[1]
        numTransactions = int(sys.argv[2])

        # iterates over the number of clients and adds unique clients to a list
        for x in range(int(numClients)):
            clientList.append(Client(x))
        # iterates over number of transactions to create transactions without \
        #   sender and recipient being the same client
        for x in range(numTransactions):
            sender = random.choice(clientList)
            recipient = random.choice(clientList)
            while (sender == recipient):
                recipient = random.choice(clientList)
            memPool.add_transaction(Transaction(sender, recipient, 1))
        # mines blocks until no remaining transactions
        while memPool.get_size() > 0:
            newBlock = Block()
            forRange = 3 # determines max number of transactions/block
            if memPool.get_size() < forRange:
                forRange = memPool.get_size()
            for i in range(forRange):
                newBlock.add_transaction(memPool.pull_transaction())
            newBlock.nonce = Miner.mine(newBlock, difficulty=2)
            blockchain.add_block(newBlock, False)
        # converts blockchain to json object for file output
        json_object = json.dumps(blockchain.to_dict(), indent=4, sort_keys=True, default=str)
        with open(json_file, 'w') as file:
            file.write(json_object)
        print (f"Size of blockchain: {blockchain.chainLength}")


if __name__ == "__main__":
    main()