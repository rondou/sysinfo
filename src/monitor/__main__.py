# -*- coding: utf-8 -*-

import argparse
import json

from . import monitor


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path', default='', help='json script path')
    return parser.parse_args(), parser


def main():
    args, argsrser = parse_args()

    data = monitor.load_json_data_from_json_file(path=args.path)
    result = monitor.monitor_generator(data=data)

    j = json.dumps(result)

    print(j)

if __name__ == '__main__':
    main()
