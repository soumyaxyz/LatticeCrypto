# LatticeCrypto

## About
This project is an implementation of a paper submited IEEE ICC 24  

It involves communication between laptop running one or more Cloud Server (SC) and Local Aggregertors (LA) and Raspberry Pi simulating Medical Devices.

The code implemets the PUF enabled post quantum data aggreation scheme proposed in the paper

## Setup Config.py (src)

- (N) Total number of entities in the system
- (f) degree of polynomial - power of 2
- (p) large prime number
- (K_min, K_max) range of positive integer < sqrt(p)


## How to Run

1. Generate Keys  
`python Main.py`  
Move CS_id.json the SC. 
Move LA_id.json the LA.  
Move Device_id.json the medicical device.

2. Run CS, LA and N-2  devices indepently
   `python <filename>.py -f <relavent>.json`



