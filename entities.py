from abc import abstractmethod
import random, numpy as np
import json
import string
import hashlib
from _thread import start_new_thread
from pypuf.simulation import PermutationPUF
from pypuf.io import random_inputs
from src.roles import Agg, IOT, KGC
from src.config import *
from server_client import ServerClient

class PUF():
    def __init__(self, id: int):
        self.puf = PermutationPUF(n=64, k=8, seed=id, noisiness=.05)
    def evaluate(self, challenge):
        return self.puf.eval(challenge)

def randInt(lower_bound = 2**30, upper_bound = 2**32-1):
    return random.randint(lower_bound, upper_bound)   

def save_object_to_file(obj, filename):
    with open(filename, 'w') as file:
        json.dump(obj, file)

def load_object_from_file(filename):
    with open(filename, 'r') as file:
        return json.load(file)


def generate_random_string(length):
    # Define the characters you want to include in the random string
    characters = string.ascii_letters + string.digits + string.punctuation

    # Use random.choice to pick random characters from the defined set
    random_string = ''.join(random.choice(characters) for _ in range(length))

    return random_string



class entity(ServerClient):
    def __init__(self, role):
        self.role = role
        # self.address = None
        # self.port = None
        self.info = None

    def generate_ID(self):
        self.id =  randInt()                
        self.puf = PUF(self.id)
    
    def compose_message(self, msg_type: str, contents):
        message = {}
        message['type'] = msg_type
        message['contents'] = contents
        return message

    def init_with(self, entity = None, address=None, port=None):
        if entity:
            if not address:
                address = entity.address
            if not port:
                port = entity.port
        destination = (address, port)
        identifiers = (self.id, self.address, self.port)
        message = self.compose_message('register', identifiers)
        encoded_msg = json.dumps(message)
        self.send_message(destination, encoded_msg)


    def save_to_file(self, filename):
        save_object_to_file({
            'info': self.info,
            'id': self.id,
            'role': self.role,
        }, filename)

    def load_from_file(self, filename):
        data = load_object_from_file(filename)
        self.id = data['id']
        self.role = data['role']
        self.info = data['info']

    




    @abstractmethod
    def message_processing(self, msg, src_addr):
        pass


class Device(entity):
    def __init__(self): 
        super().__init__(role=IOT)  
        try:     
            self.name = f'Device_{self.id}' 
        except:
            self.name = 'Device'
    
    def data_communication(self, C_i_k, data_i, destination):
        R_i_k = self.puf.evaluate(C_i_k)
        Msg = {'data': data_i, 'challenge': C_i_k, 'response': R_i_k}
        encoded_msg = json.dumps(Msg)
        # decoded_msg = json.loads(encoded_msg)
        sig_i = self.role.LSign(encoded_msg)
        M1_i = (self.id, C_i_k, data_i, R_i_k, sig_i)
        message = self.compose_message('M1_i', M1_i)
        message = json.dumps(message)
        self.send_message(destination, message)

    def message_processing(self, msg, src_addr):   #always receives the same message
        C_i_k = json.loads(msg)
        data_i = generate_random_string(4)
        self.data_communication(self, C_i_k, data_i, src_addr)


class LA(entity):
    def __init__(self, n_dr=1): 
        super().__init__(role=Agg)
        try:     
            self.name = f'LA_{self.id}' 
        except:
            self.name = 'LA'
        self.parallel_incomming = n_dr
        self.n_dr = n_dr
        self.address_book = {}
        self.CL = None

    def message_processing(self, msg, src_addr):   
        message = json.loads(msg)
        if message['type'] == 'register':
            id, address, port = message['contents']
            self.address_book[id] = (address, port)
            
        elif message['type'] == 'M1_i':
            self.Msgs.append(message['contents'])

            if(self.Msgs)==self.n_dr:
                start_new_thread(self.communicate_transaction, self.Msgs)
                self.Msgs = []  # empty the list

            elif message['type'] == 'C_LA':
                pass

    def challenge_device(self, ID_dev_i):
        _, C_i, _, c_r_idx = self.info[ID_dev_i]
        C_i_k = C_i[c_r_idx]
        encoded_challenge = json.dumps(C_i_k)
        destination = self.address_book[ID_dev_i]   # needs not specify message type
        self.send_message(destination, encoded_challenge)

    def data_verification(self, ID_dev_i, data_i, C_i_k, R_i_k, sig_i):
        pk_i, C_i, R_i, c_r_idx = self.info[ID_dev_i]
        if C_i_k != C_i[c_r_idx]:
            return False
        R_i_k_prime = R_i[c_r_idx]
        self.info[ID_dev_i] = (pk_i, C_i, R_i, c_r_idx-1)
        if R_i_k_prime == R_i_k:
            if self.role.LVer(data_i, sig_i, pk_i):
                return True
        return False

    def communicate_transaction(self, Msgs):
        data = []
        for i in range(self.n_dr):
            M1_i = Msgs[i]
            decoded_msg = json.loads(M1_i)
            ID_dev_i, C_i_k, data_i, R_i_k, sig_i = decoded_msg           
            
            if self.data_verification(ID_dev_i, data_i, C_i_k, R_i_k, sig_i):                
                data.append(data_i)
        
        data_LA_j = hashlib.sha256(str(data).encode()).hexdigest()
        self.sig_LA_j = self.role.AggSign(data_LA_j)
        M1_LA_j = {'ID_LA_j':self.id,'data': data, 'data_LA_j': data_LA_j, 'sig_LA_j': self.sig_LA_j}
        message = self.compose_message('M1_LA_j', M1_LA_j)
        encoded_msg = json.dumps(message)
        destination = self.address_book[self.Cl.id]
        self.send_message(destination, encoded_msg)

    def communicate_transaction_verify(self, C_LA_jk):
        R_LA_jk = self.puf.evaluate(C_LA_jk)
        cert = hashlib.sha256(str(R_LA_jk)+str(self.sig_LA_j).encode()).hexdigest()
        self.sig_LA_j = None
        message = self.compose_message('M2_LA_j', cert)
        encoded_msg = json.dumps(message)        
        destination = self.address_book[self.Cl.id]
        self.send_message(destination, encoded_msg)



class CS(entity):
    def __init__(self, n_la=1, n_tr = 10): 
        super().__init__(role=Agg)
        try:     
            self.name = f'CS_{self.id}' 
        except:
            self.name = 'SC' 
        self.parallel_incomming = n_la
        self.n_tr = n_tr
        self.address_book = {}
        self.CL = None
        self.TXN_CS_l = {}

    def message_processing(self, msg, src_addr):   
        message = json.loads(msg)
        if message['type'] == 'register':
            id, address, port = message['contents']
            self.address_book[id] = (address, port)
            
        elif message['type'] == 'M1_LA_j':
            M1_LA_j = message['contents']
            ID_LA_j = M1_LA_j['ID_LA_j']
            data = M1_LA_j['data'] 
            data_LA_j = M1_LA_j['data_LA_j'] 
            sig_LA_j  = M1_LA_j['sig_LA_j']
        
            self.aggregation_verify(ID_LA_j, data, data_LA_j, sig_LA_j )
        
        elif message['type'] == 'M2_LA_j':
            M2_LA_j = message['contents']
            cert = M2_LA_j['cert']
            self.aggregation_verify_cert( cert )

            if(self.TXN_CS_l)==self.n_tr:
                start_new_thread(self.mineBlock, self.Msgs)
                self.TXN_CS_l = {}  # empty the list


    def aggregation_verify(self,  ID_LA_j, data, data_LA_j, sig_LA_j  ):
        data_LA_j_hashed = hashlib.sha256(str(data).encode()).hexdigest()
        if data_LA_j == data_LA_j_hashed:
            _, C_LA_j, _, c_r_idx = self.info[ID_LA_j]
            C_LA_j_k = C_LA_j[c_r_idx]
            message = self.compose_message('C_LA', C_LA_j_k)
            encoded_challenge = json.dumps(message)
            destination = self.address_book[ID_LA_j]
            self.ID_LA_j = ID_LA_j
            self.sig_LA_j = sig_LA_j
            self.data = data
            self.data_LA_j = data_LA_j

            self.send_message(destination, encoded_challenge)


    def aggregation_verify_cert(self, cert):
            pk_LA_j, C_LA_j, R_LA_j, c_r_idx = self.info[self.ID_LA_j]
            R_LA_j_k_prime = R_LA_j[c_r_idx]
            cert_prime = hashlib.sha256(str(R_LA_j_k_prime)+str(self.sig_LA_j).encode()).hexdigest()
            if cert_prime == cert:
                if self.role.LVer(self.data_LA_j, self.sig_LA_j, pk_LA_j):
                    Txn = {'data': self.data, 'data_LA_j': self.data_LA_j, 'sig_LA_j': self.sig_LA_j}
                    self.TXN_CS_l.append(Txn)

    def mineBlock(self, TXN_CS_l):
        pass
        


class EC():
    def __init__(self):
        self.EC = KGC.KGC()
        self.devices = []
        self.n_dr = N-2 # from src/config.py
        for i in range(self.n_dr): 
            self.devices.append(Device())
        self.LA = LA()
        self.CS = CS()

    def entity_Registration(self):
        info = {}

        signers =  self.EC.KeyGen()
        c_r_idx = 3  # no of challenge response pairs 
        
        for i, dev_i in enumerate(self.devices):
            dev_i.generate_ID()
            sk_i = signers['priv'][i]  # s1, s2
            pk_i = signers['pub'][i]   # t, a, k
            dev_i.role(sk_i, pk_i)

            C_i = random_inputs(n=64, N=c_r_idx, seed=randInt())
            R_i = dev_i.puf.eval(C_i)
            
            info_entry = ( pk_i, C_i, R_i, c_r_idx)
            info[dev_i.id] = info_entry
            dev_i.save_to_file( f'devices_{dev_i.id}.json')
        
        self.LA.generate_ID()
        sk_aggr = signers['priv'][-2]  # s1, s2
        pk_aggr = signers['pub'][-2]   # t, a, k        
        self.LA.role(sk_aggr, pk_aggr)
        C_aggr = random_inputs(n=64, N=c_r_idx, seed=randInt())
        R_aggr = self.LA.puf.eval(C_aggr)
        self.LA.save_to_file( f'devices_{self.LA.id}.json')



        self.CS.info = info

        self.CS.generate_ID()
        sk_CS = signers['priv'][-1]  # s1, s2
        pk_CS = signers['pub'][-1]   # t, a, k
        self.CS.role(sk_CS, pk_CS)
        self.CS.info = {self.LA.id: (pk_aggr, C_aggr, R_aggr, c_r_idx)}
        self.CS.save_to_file( f'devices_{self.CS.id}.json')

    

    