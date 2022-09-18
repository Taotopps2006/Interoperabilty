'''
Description: Multiple blockchains with multiple nodes to run user-defined number of clients and transactions.
Run code: mpirun -np <#nodes> python3 multiblockchainDP.py #clients #transactions
'''

import binascii
import Crypto.Random
import datetime
import hashlib
import json
import logging
import os
import pickle
import pylab as pl
import random
import string
import sys
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from mpi4py import MPI


class Client:
    """
    Class for the sender and recipients

    Attributes
    ----------
    _private_key : RSA
    _public_key : RSA
    _signer : PKCS1_v1_5
    name : str
        used to identify the Client

    Methods
    -------
    sign()
        Returns the Client's private key
    """

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
    """
    Class used to represent transactions to be included in blocks
    
    ...

    Attributes
    ----------
    sender : Client
        originator of the Transaction
    recipient : Client
        recipient of the Transaction
    value : bool, int, float
        the datatype changes based on the blockchain
    time : datetime
        the unique time the transaction was created

    Methods
    -------
    to_dict()
        Converts the Transaction's data to dictionary
    sign_transaction()
        Verifies the sender of the Transaction
    display_transaction()
        Prints the data in the Transaction
    """
    
    def __init__(self, sender, recipient, value):
        self.sender = sender
        self.recipient = recipient
        self.value = value
        self.time = datetime.datetime.now()

    def to_dict(self):
        return {
            'sender': self.sender.name,
            'recipient': self.recipient.identity,
            'value': self.value,
            'time': self.time
        }

    def sign_transaction(self, signer):
        """
        Uses sender's private key to sign transaction
        """
        if (signer.sign() == self.sender.sign()):
            private_key = self.sender._private_key
            signer = PKCS1_v1_5.new(private_key)
            h = SHA.new(str(self.to_dict()).encode('utf8'))
            return binascii.hexlify(signer.sign(h)).decode('ascii')

    def display_transaction(self):
        """
        Prints the Transaction data
        """
        dict = self.to_dict()
        print ("Transaction Data")
        print ('----------------')
        print ("sender: " + dict['sender'])
        print ('-----')
        print ("recipient: " + str(dict['recipient']))
        print ('-----')
        print ("value: " + str(dict['value']))
        print ('-----')
        print ("time: " + str(dict['time']))
        print ('-----')


class MemPool:
    """
    Class used to as a queue for transactions to be added to a block
    
    ...
    
    Attributes
    ----------
    transactions : list of Transactions
        the queue of transactions to be added

    Methods
    -------
    add_transaction(transaction)
        Queues a new Transaction
    pull_transaction()
        Removes and returns the first Transaction
    get_size()
        Returns the size of the queue
    """
    
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


class Block:
    """
    Class used to ensapsulates Transactions to be added to blockchain
    
    ...

    Attributes
    ----------
    verified_transactions : list of Transactions
        contains the Transactions within the Block
    previous_block_hash : str
        value which cryptographically links the Block to the previous Block
    nonce : str
        the mined value which satisfies the blockchain's difficulty value
    block_height : int
        the height of the Block to be added to the blockchain

    Methods
    -------
    display_block()
        Prints the Transactions within the Block
    add_transaction()
        Appends a transaction to the Block
    to_dict()
        Converts the transactions in the block to a dictionary
    """
    
    def __init__(self):
        self.verified_transactions = []
        self.previous_block_hash = ""
        self.nonce = ""
        self.block_height = 0
    def display_block(self):
        print ("Block #" + str(self.block_height))
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


class Blockchain:
    """
    Class to link together all mined Blocks

    ...

    Attrbiutes
    ----------
    latest_block_hash : str
    chain_length : int
    chain : list of Blocks
    difficulty : int

    Methods
    -------
    add_block(new_block, from_file)
        Adds a Block to the Blockchain list and persists to byte code if not read from file
    get_chain_length()
        Returns the length of the blockchain
    get_last_hash()
        Returns the hash of the most recent Block
    display_chain()
        Prints all the Blocks in the Blockchain
    verify_chain()
        Verifies all of the Blocks have the previous Block's hash
    read_blockchain()
        Reads Blockchain data from file if available
    to_dict()
        Converts all of the Blocks in the Blockchain to a dictionary
    persist()
        Iterates over the Blocks in the Blockchain and stores them to file
    """
    
    def __init__(self):
        self.latest_block_hash = ""
        self.chainLength = 0
        self.chain = []
        self.difficulty = 2
    def add_block(self, newBlock, fromFile):
        """
        Adds a block to the blockchain and appends it to file if it was not read from file
        """
        self.chain.append(newBlock)
        self.latest_block_hash = hash(newBlock)
        self.chainLength += 1
        newBlock.block_height = self.chainLength
        # maybe add logic to check hashes (verify before adding?)
        if (fromFile == False):
            persist_block(newBlock)
    def get_chain_length(self):
        return self.chainLength
    def get_last_hash(self):
        return self.latest_block_hash
    def display_chain(self):
        print ("Number of blocks: " + str(self.get_chain_length()))
        for block in self.chain:
            print("========================")
            block.display_block()
    def verify_chain(self):
        """
        Iterates over the blockchain from genesis to latest and checks hashes
        """
        for i in range(0, self.chainLength-1):
            if (hash(self.chain[i]) != self.chain[i+1].previous_block_hash):
                return False
        return True
    def read_blockchain(self, blockchain_data):
        """
        Reads pickled blocks if there are existing data
        """
        if os.path.exists(blockchain_data):
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
        """
        Converts blockchain data to a dictionary
        """
        returnDict = {}
        for x, block in enumerate(self.chain):
            returnDict[x] = block.to_dict()
        return returnDict
    def persist(self) -> None:
        """
        Writes all individual blocks to file
        """
        with open(blockchain_data, 'wb') as file:
            for i, block in enumerate(self.chain):
                pickle.dump(self.chain[i], file)


class Miner:
    """
    Class to encapsulate mining functions

    Attributes
    ----------
    client : Client
        Used if mining contained a "block reward"
    
    Methods
    -------
    mine(message, difficulty)
        Hashes a block until a valid (based on difficulty) nonce is found
    broadcast_block(block, local)
        Broadcasts or receives a new block based on it the node mined the block
    """
    
    def __init__(self) -> None:
        self.client = Client()
    def mine(message, difficulty = 1):
        """
        mines a block based on a given difficulty value
        """
        assert difficulty >= 1, "Difficulty is invalid"
        prefix = '0' * difficulty
        i = 0
        found = False
        foundLocal = False
        while found is False:
            # checks to see if other process has found digest
            probe = subcomm.iprobe()
            if probe:
                digest = subcomm.recv()
                found = True
            else:
                # if the digist/nonce has not been found, node tries mining it
                digest = sha256(str(hash(message)) + str(i))
                if (digest.startswith(prefix)):
                    found = True
                    foundLocal = True
                    # sends digest to all other processes
                    for j in range(subcommSize):
                        if j == subcommRank:
                            continue
                        subcomm.send(digest, dest=j, tag=NONCE_TAG)
            i += 1
        return digest, foundLocal
    def broadcast_block(block, local) -> None:
        """
        Broadcasts or receives a new block based on it the node mined the block
        """
        global blockchain
        if local is True:
            blockchain.add_block(block, False)
            # sends block to all blockchain nodes
            for node in range (subcommSize):
                if node == subcommRank:
                    continue
                subcomm.send(block, dest=node, tag=BLOCK_TAG)
        else:
            # wait for block message
            status = MPI.Status()
            receivedBlock = subcomm.recv(status=status, tag=BLOCK_TAG)
            blockchain.add_block(receivedBlock, False)
        subcomm.barrier() # waits until all nodes have received block


def sha256(message):
    return hashlib.sha256(message.encode('ascii')).hexdigest()


def check_cla() -> bool:
    return len(sys.argv) == 3


def persist_block(newBlock):
    """
    Appends a pickled block to file
    """
    with open(blockchain_data, 'ab') as file:
        pickle.dump(newBlock, file)


def pickle_clients(clientList):
    # not used in this implementation
    """
    Writes pickled clients to file
    """
    with open(client_data, 'wb') as file:
        for client in clientList:
            pickle.dump(client, file)


def read_clients(client_data):
    # not used in this implementation
    """
    Reads pickled clients from file
    """
    clientList = []
    if os.path.exists(client_data):
        with open (client_data, 'rb') as file:
            while True:
                try:
                    client = pickle.load(file)
                except EOFError:
                    break
                else:
                    clientList.append(client)
    return clientList


def persist_to_json(data):
    """
    Writes a dictionary object to the node's blockchain data file
    """
    json_object = json.dumps(data, indent=4, sort_keys=True, default=str)
    with open(blockchain_json, 'w') as file:
        file.write(json_object)


def synchronize_ledgers():
    """
    Node 0 sends its ledger to any node with a different blockchain length
    """
    global blockchain
    localLength = blockchain.get_chain_length()
    ledgerLengths = subcomm.allgather(localLength)
    maxLength = localLength
    maxLengthRank = subcommRank
    for i, length in enumerate(ledgerLengths): # compares all ledger lengths
        if (length > maxLength):
            maxLength = length
            maxLengthRank = i
    needSync = maxLengthRank != subcommRank
    syncList = subcomm.gather(needSync, 0) # assumes rank 0 always has longest ledger
    if subcommRank == 0:
        for i, sync in enumerate(syncList):
            if sync is True: # sending ledger to nodes with different length
                subcomm.send(blockchain, i, tag=BC_TAG)
    if needSync:
        blockchain = subcomm.recv(source=0, tag=BC_TAG)
        blockchain.persist()
    subcomm.barrier()


def make_folders(numBlockchains):
    """
    creates folders for blockchain node data to be stored
    this function is non-essential and is for organization
    """
    scriptOutputFolder = os.path.join(os.getcwd(), sys.argv[0].rsplit('.')[0])
    try:
        os.mkdir(scriptOutputFolder)
    except OSError as e:
        pass
    for i in range(numBlockchains):
        try:
            os.mkdir(os.path.join(scriptOutputFolder, "blockchain_"+str(i)))
        except OSError as e:
            pass

def create_subcomm(numBlockchains):
    """Creates subcommunications for the individual blockchains"""
    """Can be extended to take number of blockchains to run from CLA"""
    color = rank % numBlockchains
    return comm.Split(color, rank), color

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
subcomm, color = create_subcomm(numBlockchains=3)
comm.barrier()
subcommRank = subcomm.Get_rank()
commSize = comm.Get_size()
subcommSize = subcomm.Get_size()

memPool = MemPool()
blockchain = Blockchain()
if rank == 0:
    make_folders(numBlockchains=3)
blockchain_file_name = sys.argv[0].rsplit('.')[0]+'/blockchain_'+str(color)+'/miner_'
# file names: "miner_globalrank_subcommrank"
blockchain_data = blockchain_file_name + str(rank) + '_' + str(subcommRank) + '.txt'
blockchain_json = blockchain_file_name + str(rank) + '_' + str(subcommRank) + '.json'
client_data = 'client_data.txt'
clientList = []
# comm message tags
BLOCK_TAG = 0
NONCE_TAG = 1
BC_TAG = 2

# log = logging.getLogger(__name__)

def main():
    global blockchain
    global memPool
    global clientList

    if (check_cla() is False):
        print ("Proper format: mpirun -np <#nodes> python3 multiblockchainDP.py #clients #transactions")
    else:
        blockchain.read_blockchain(blockchain_data)
        synchronize_ledgers()
        numClients = sys.argv[1]
        numTransactions = int(sys.argv[2])
        if subcommRank == 0:
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
                if color == 0:
                    function = random.randrange(1,10)
                elif color == 1:
                    function = random.getrandbits(1)
                elif color == 2:
                    function = random.random()
                memPool.add_transaction(Transaction(sender, recipient, function))
        clientList = subcomm.bcast(clientList, root=0)
        memPool = subcomm.bcast(memPool, root=0)
        subcomm.barrier()
        # mines blocks until no remaining transactions
        while memPool.get_size() > 0:
            newBlock = Block()
            forRange = 3 # determines max number of transactions/block
            if memPool.get_size() < forRange:
                forRange = memPool.get_size()
            for i in range(forRange):
                newBlock.add_transaction(memPool.pull_transaction())
            newBlock.nonce, minedLocal = Miner.mine(newBlock, difficulty=5)
            Miner.broadcast_block(newBlock, minedLocal)
        persist_to_json(blockchain.to_dict())
        subcomm.Free()


if __name__ == '__main__':
    main()