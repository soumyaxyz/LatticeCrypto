import json
import argparse
from entities import Device


def main():    
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address',  type=str, default='127.0.0.1')
    parser.add_argument('-p', '--port', type=int, default=8080)
    parser.add_argument('-f', '--filename', type=str, default='device.json')

    

    args = parser.parse_args()
    D = Device()
    D.load_from_file(args.filename)
    D.init_with(args.address, args.port)
    D.listen()

if __name__ == '__main__':
    main()