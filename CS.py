import argparse
from entities import CS




def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address',  type=str, default='127.0.0.1')
    parser.add_argument('-p', '--port', type=int, default=8080)
    parser.add_argument('-f', '--filename', type=str, default='device.json')

    args = parser.parse_args()
    CS_l = CS()
    CS_l.load_from_file(args.filename)
    CS_l.init_with(args.address, args.port)
    CS_l.listen()

if __name__ == '__main__':
    main()