'''
Description: Simple local blockchain project which references previous blocks and clients
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
import collections
import Crypto.Random
import pickle
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
        if self.sender == "Genesis":
            identity = "Genesis"
        else:
            identity = self.sender.identity

        return collections.OrderedDict({
            'sender': identity,
            'recipient': self.recipient,
            'value': self.value,
            'time': self.time
        })

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
    def toDict(self) -> dict:
        return { }

# contains record of all transactions made
class Blockchain:
    def __init__(self):
        self.latestBlockHash = ""
        self.chainLength = 0
        self.chain = []
        self.difficulty = 2
    def add_block(self, newBlock, fromFile):
        # adds a block to the blockchain and appends it to file if it was not read from file
        self.chain.append(newBlock)
        self.latestBlockHash = hash(newBlock)
        self.chainLength += 1
        newBlock.blockHeight = self.chainLength
        # maybe add logic to check hashes (verify before adding?)
        if (fromFile == False):
            persist_block(newBlock)
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


memPool = MemPool()
blockchain = Blockchain()
blockchain_data = 'blockchain_data.txt'
client_data = 'client_data.txt'

def main():
    read_blockchain(blockchain_data)
    continueLoop = True
    clientList = read_clients(client_data)
    clientList.append(Client("Genesis"))


    while (continueLoop):

        choice = get_choice()

        if choice == '1':
            newClient = input ("Enter name of client: ")
            clientList.append(Client(newClient))
        elif choice == '2':
            sender = input ("Sender: ")
            recipient = input ("Recipient: ")
            amount = input ("Amount: ")

            sClient = None
            rClilent = None

            for client in clientList:
                if client == sender:
                    sClient = client
                if recipient == recipient:
                    rClient = client

            tempTransaction = Transaction(sClient, rClient.identity, amount)

            memPool.add_transaction(tempTransaction)
        elif choice == '3':
            # adds transactions from mempool into a block
            tempBlock = Block()
            forRange = 3 # determines number of transactions/block
            if memPool.get_size() < forRange:
                forRange = memPool.get_size()
            for i in range(forRange):
                tempTransaction = memPool.pull_transaction()
                # verification step would occur here
                tempBlock.add_transaction(tempTransaction)
            tempBlock.previous_block_hash = blockchain.get_last_hash()

            tempBlock.Nonce = Miner.mine(tempBlock, blockchain.difficulty)

            blockchain.add_block(tempBlock, False)

        elif choice == '4':
            memPool.display_mempool()
        elif choice == '5':
            blockchain.display_chain()
        elif choice == '6':
            continueLoop = False
            pickle_clients(clientList)
        else:
            print("Invalid option")


def get_choice():
    return input ("1. Create new Client\n"
                  "2. Create transaction\n"
                  "3. Mine block\n"
                  "4. Display mem pool\n"
                  "5. Display blockchain\n"
                  "6. Exit\n"
                  "Option: ")


def read_blockchain(blockchain_data):
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
                    blockchain.add_block(block, True)
    else:
        print ("No prior blockchain data found")


def persist_block(newBlock):
    # appends a pickled block to file
    with open(blockchain_data, 'ab') as file:
        pickle.dump(newBlock, file)


def pickle_clients(clientList):
    # writes pickled clients to file
    with open(client_data, 'wb') as file:
        for client in clientList:
            pickle.dump(client, file)


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


if __name__ == "__main__":
    main()