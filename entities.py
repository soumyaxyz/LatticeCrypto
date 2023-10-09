from abc import abstractmethod
import random, numpy as np
import json
import string
import hashlib
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


def generate_random_string(length):
    # Define the characters you want to include in the random string
    characters = string.ascii_letters + string.digits + string.punctuation

    # Use random.choice to pick random characters from the defined set
    random_string = ''.join(random.choice(characters) for _ in range(length))

    return random_string

def keyLoader(filename = 'keys0.json'):
    # f = open(filename, 'r')
    with open(filename, 'r') as f:
        obj = json.load(f)
    # obj = json.load(f)
    # f.close()

    sk = np.array([obj['priv']['s1'], obj['priv']['s2']])
    pk = (np.array(obj['pub']['t']), obj['pub']['a'], obj['pub']['k'])
    return(sk, pk)

class entity(ServerClient):
    def __init__(self, role):
        self.role = role
        self.address = None
        self.port = None
        self.info = None

    def generate_ID(self):
        self.id =  randInt()                
        self.puf = PUF(self.id)

    @abstractmethod
    def message_processing(self, msg, src_addr):
        pass

class Device(entity):
    def __init__(self): 
        super().__init__(role=IOT)  

    def data_communication(self, C_i_k, data_i, destination):
        R_i_k = self.puf.evaluate(C_i_k)
        Msg = {'data': data_i, 'challenge': C_i_k, 'response': R_i_k}
        encoded_msg = json.dumps(Msg)
        # decoded_msg = json.loads(encoded_msg)
        sig_i = self.role.LSign(encoded_msg)
        M1_i = json.dumps(self.id, C_i_k, data_i, R_i_k, sig_i)
        self.send_message(destination, M1_i)

    def message_processing(self, msg, src_addr):
        C_i_k = json.loads(msg)
        data_i = generate_random_string(4)
        self.data_communication(self, C_i_k, data_i, src_addr)



class LA(entity):
    def __init__(self, n_dr): 
        super().__init__(role=Agg)
        self.n_dr = n_dr


    def challenge_device(self, ID_dev_i):
        _, C_i, _, c_r_idx = self.info[ID_dev_i]
        C_i_k = C_i[c_r_idx]
        encoded_challenge = json.dumps(C_i_k)
        destination = 
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
        sig_LA_j = self.role.AggSign(data_LA_j)
        M1_LA_j = {'data': data, 'data_LA_j': data_LA_j, 'sig_LA_j': sig_LA_j}
        encoded_msg = json.dumps(M1_LA_j)
        send_message_to_CS(encoded_msg)










class CS(entity):
    def __init__(self): 
        super().__init__(role=Agg)


class EC():
    def __init__(self, n_dr):
        self.EC = KGC.KGC()
        self.devices = {}
        self.n_dr = N-2 # from src/config.py
        for i in range(n_dr): 
            self.devices.append(Device())
        self.LA = LA()
        self.CS = CS()

    def Entity_Registration(self):
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
        
        self.LA.generate_ID()
        sk_aggr = signers['priv'][-2]  # s1, s2
        pk_aggr = signers['pub'][-2]   # t, a, k        
        self.LA.role(sk_aggr, pk_aggr)
        C_aggr = random_inputs(n=64, N=c_r_idx, seed=randInt())
        R_aggr = self.LA.puf.eval(C_aggr)
        self.CS.info = info

        self.CS.generate_ID()
        sk_CS = signers['priv'][-1]  # s1, s2
        pk_CS = signers['pub'][-1]   # t, a, k
        self.CS.role(sk_CS, pk_CS)
        self.CS.info = {self.LA.id: (pk_aggr, C_aggr, R_aggr, c_r_idx)}

    

    