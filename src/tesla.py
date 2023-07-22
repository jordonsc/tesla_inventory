#!/usr/bin/env python3

import argparse
import logging

from tesla import Inventory, Notifier

# Arg parser
parser = argparse.ArgumentParser(description='Tesla Inventory Report')

# Market region (country)
parser.add_argument('-k', '--market', dest='market', action='store', default="AU",
                    help='Search market; default "AU"')

# Sub-region (normally state)
parser.add_argument('-r', '--region', dest='region', action='store', default="Victoria",
                    help='Market sub-region; eg "Victoria"')

# Model
parser.add_argument('-m', '--model', dest='model', action='store', required=True,
                    help='Vehicle model; valid options: m3, ms, my, mx')
# Trim
parser.add_argument('-t', '--trim', dest='trim', action='store',
                    help='Vehicle trim, comma delimited (optional); valid options: M3RWD, SRRWD, LRAWD, PAWD')

# Condition
parser.add_argument('-c', '--condition', dest='condition', action='store', default="new",
                    help='"new" or "used"; default "new"')

# Cache file
parser.add_argument('-f', '--cache', dest='cache', action='store', default="cache/inventory.json",
                    help='path to cache file for previous matches')

# ARN
parser.add_argument('-a', '--arn', dest='arn', action='store', required=True,
                    help='AWS SNS ARN to dispatch notifications to')

# Verbose/debug mode
parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                    help='increase logging verbosity')

if __name__ == "__main__":
    args = parser.parse_args()

    logging.basicConfig()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    # Get latest inventory..
    inv = Inventory(market=args.market, region=args.region)
    notifier = Notifier(cache_file=args.cache, arn=args.arn)

    trim = args.trim.replace(" ", "").split(",") if args.trim else None
    notifier.process_results(inv.fetch(args.model, trim))
