import argparse
from entities import LA



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address',  type=str, default='127.0.0.1')
    parser.add_argument('-p', '--port', type=int, default=8080)
    parser.add_argument('-f', '--filename', type=str, default='device.json')

    args = parser.parse_args()
    LA_j = LA()
    LA_j.load_from_file(args.filename)
    LA_j.init_with(args.address, args.port)
    LA_j.listen()

if __name__ == '__main__':
    main()