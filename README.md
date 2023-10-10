# PUF secured Post Quantum Aggregate Signature Scheme for Secure Dissemination of Medical Data 

## About
This project is an implementation of a paper submitted to IEEE ICC 24  

It involves communication between laptops running one or more cloud servers (SC) and local aggregators (LA) and Raspberry Pi-simulated medical devices.

The code implements the PUF-enabled post-quantum data aggregation scheme proposed in the paper


## How to Run

1. Generate Keys  
`python Main.py`  
Move CS_id.json the SC. 
Move LA_id.json the LA.  
Move Device_id.json the medicical device.

2. Run CS, LA and N-2  devices independently
   `python <filename>.py -f <relavent>.json`



