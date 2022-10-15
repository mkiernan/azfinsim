#! /usr/bin/env python3

r"""Common arg parser. It support parsing command line arguments or reading the same
from an optionally specified config file.
"""
import argparse
import json
from unicodedata import name

class ArgumentsAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        prefix = 'azfinsim-'
        prefix_length = len(prefix)
        with values as f:
            secrets = json.load(f)
            for key, value in secrets.items():
                key = key.lower()
                if key.startswith(prefix):
                    parser.parse_known_args(['--' + key[prefix_length:], value], namespace=namespace)
                elif key.startswith('-'):
                    parser.parse_known_args([key, value], namespace=namespace)
                else:
                    parser.parse_known_args(['--' + key, value], namespace=namespace)

def getargs(progname):

    parser = argparse.ArgumentParser(progname)

    #-- cli parsing
    parser.add_argument('--config', type=open, action=ArgumentsAction, help='read extra arguments from the config file (json)')
    parser.add_argument('--verbose', default=False, type=lambda x: (str(x).lower() == 'true'), help="verbose output: true or false")

    #-- Cache parameters
    cacheParser = parser.add_argument_group('Cache', 'Cache-specific options')
    cacheParser.add_argument("--cache-type", default="redis",
                             choices=['redis','filesystem','none'],
                             help="cache type (default: redis)"),
    cacheParser.add_argument("--cache-name", help="<redis or filesystem hostname/ip (port must be open)>")
    cacheParser.add_argument("--cache-port", default=6380, type=int, help="redis port number (default=6380 [SSL])")
    cacheParser.add_argument("--cache-key", help="cache access key")
    cacheParser.add_argument("--cache-ssl", default="yes", choices=['yes','no'], help="use SSL for redis cache access (default: yes)")
    cacheParser.add_argument("--cache-path", help="Cache Filesystem Path (not needed for redis")

    #-- algorithm/work per thread
    workParser = parser.add_argument_group('Trades', 'Trade-specific options')
    workParser.add_argument("-f", "--format", default="eyxml", choices=['varxml','eyxml'],help="format of trade data (default: eyxml)")
    workParser.add_argument("-s", "--start-trade", default=0, type=int, help="trade range to process: starting trade number (default: 0)")
    workParser.add_argument("-w", "--trade-window", default=0, type=int, help="number of trades to process (default: 0)")

    if progname == 'azfinsim':
        algoParser = parser.add_argument_group('Algorithm', 'Algorithm-specific options')
        algoParser.add_argument('--harvester', default=False, type=lambda x: (str(x).lower() == 'true'), help="use harvester scheduler: true or false")
        algoParser.add_argument("-a", "--algorithm", default="deltavega", choices=['deltavega','pvonly','synthetic'],help="pricing algorithm (default: deltavega)")

        #-- synthetic workload options
        algoParser.add_argument("-d", "--delay-start", type=int, default=0, help="delay startup time in seconds (default: 0)")
        algoParser.add_argument("-m", "--mem-usage", type=int, default=16, help="memory usage for task in MB (default: 16)")
        algoParser.add_argument("--task-duration", type=int, default=20, help="task duration in milliseconds (default: 20)")
        algoParser.add_argument("--failure", type=float, default=0.0, help="inject random task failure with this probability (default: 0.0)")

        #-- logs & metrics
        parser.add_argument("--appinsights-key", help="Azure Application Insights Key")

    return parser.parse_args()
