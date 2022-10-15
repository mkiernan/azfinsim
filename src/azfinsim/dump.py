#! /usr/bin/env python3

# Dump the cache to dump.txt (used for faster manual injection to skip generation for demos)

import argparse
import time
import sys
import logging
import pandas as pd

from . import getargs, utils, xmlutils, montecarol, azlog

log = azlog.getLogger(__name__)
azlog.color=False

if __name__ == "__main__":

    #-- grab cli args
    args = getargs.getargs("dumpdb")

    #-- verbosity
    azlog.setDebug(args.verbose)

    #-- open connection to cache
    r = utils.SetupCacheConn(args.cache_type, args.cache_name, args.cache_port, args.cache_key, args.cache_ssl)
    if r is None:
             logging.error("Cannot connect to Redis DB: %s, %s, %s" % args.cache_name, args.cache_port, args.cache_key)

    with open("dump.txt", "a") as f:
        for tradenum in range(0,1000000):
            keyname = "ey%007d.xml" % tradenum
            #-- read trade from cache
            xmlstring=utils.GetTrade(r,keyname)
            xmlstr = xmlstring.decode('utf-8')
            xmlclean = xmlstr.replace("\n","") 
            x = xmlclean.replace('"','\\"')
        #   log.info("%s %s" % (keyname,xmlstring))
            str = 'SET %s "%s"' % (keyname,x)
            print(str, file=f) 
