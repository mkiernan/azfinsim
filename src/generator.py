#! /usr/bin/env python3
#
# generator.py: Load the AzFinsim Cache with randomly generated trade data of specified length
#
import argparse
import time
import psutil
import logging
from multiprocessing.pool import ThreadPool
from azure.identity import DefaultAzureCredential

from config import *
import config
import azlog 
import xmlutils
import utils
import secrets
from getargs import getargs

log = azlog.getLogger(__name__)

#-- todo: fix nbytes for var, and fold these variables into create_trades
format=""
tradenum=0

#def create_trades(cache_type,format,tradenum):
def create_trades(tradenum):
        if (args.format == "eyxml"): 
            xmlstring = xmlutils.GenerateTradeEY(tradenum,1)
        elif (format == "varxml"):
            nbytes=1 #-- TBD need to pass this
            xmlstring = xmlutils.GenerateTrade(tradenum,nbytes)
        utils.PutTrade(cache_type,"input",r,format,tradenum,xmlstring)


if __name__ == "__main__":

    #-- grab cli args
    args = getargs("generator")

    #-- verbosity
    azlog.setDebug(args.verbose)
    log.info("Starting trade generator...")

    #-- pull keys/passwords from the keyvault
    log.info("Reading kevault secrets")
    secrets.ReadKVSecrets()
    log.info("Done.")

    #-- set threads to vcore count unless specified
    if (args.threads): threads = args.threads
    else: threads = psutil.cpu_count(logical=True)
     
    #nbytes=args.nbytes

    #-- open connection to cache
    log.info("Setting up cache connection")
    if (args.cache_type == "redis" or args.cache_type == "hazelcast"):
        r = utils.SetupCacheConn(args.cache_type,args.cache_name,args.cache_port,config.AZFINSIM_REDISKEY,args.cache_ssl)
        if r is None:
             log.error("Cannot connect to Cache DB: %s, %s, %s" % args.cache_name,args.cache_port,args.cache_key,args.cache_ssl)
    log.info("Done.")

    cache_type = args.cache_type
    format = args.format

    start_trade=args.start_trade
    stop_trade=start_trade+args.trade_window

    thread_pool = ThreadPool(threads)
    log.info(f'Starting the thread pool and filling the cache (%d threads)', threads)
    start=time.perf_counter()
    thread_pool.map(create_trades, range(start_trade,stop_trade))
    end=time.perf_counter()
    timedelta=end-start
    log.info("Done.")
    log.info("Cache filled with %d trades in %.12f seconds" % (args.trade_window,timedelta)) 
