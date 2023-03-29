#! /usr/bin/env python3
#
# generator.py: Load the AzFinsim Cache with randomly generated trade data of specified length
#
import math
import time
import psutil
import logging
from multiprocessing.pool import ThreadPool

from . import xmlutils, cache
from .metrics import Metrics

log = logging.getLogger(__name__)

# config for metrics
_metrics_config = {
    "execution_time": {
        "description": "Execution time",
        "unit": "s",
        "type": "float",
        "aggregation": "last_value"
    },
    "io_time": {
        "description": "Time for IO",
        "unit": "s",
        "type": "float",
        "aggregation": "sum"
    }
}

#-- pipeline / batching method 
def create_trade_range(start_trade, batch_size, end_trade, conn, metrics: Metrics):
    start_ts = time.perf_counter()
    stop_trade = min(end_trade, start_trade + batch_size)
    log.info("Generating batch: %d-%d", start_trade, stop_trade-1)
    pipe = conn.pipeline()
    for keyname, trade in xmlutils.GenerateTradeEY(start_trade, stop_trade - start_trade):
        pipe.set(keyname, trade)
        # log.info(f'{trade_num}: {trade}')
    log.info("Executing batch: %d-%d", start_trade, stop_trade-1)
    start_io_ts = time.perf_counter()
    pipe.execute() 
    end_ts = time.perf_counter()

    # update metrics
    metrics.put("io_time", end_ts - start_io_ts)
    metrics.put("execution_time", end_ts - start_ts)

def execute(args):
    #-- verbosity
    log.info("Starting trade generator...")

    #-- set threads to vcore count unless specified
    vcores = psutil.cpu_count(logical=True)
    pcores = psutil.cpu_count(logical=False)
    log.info(f"System Info: Physical Cores: {pcores} Logical Cores: {vcores}")

    #-- open connection to conn
    log.info("Setting up cache connection ...")
    conn = cache.connect(args, as_input=False)
    log.info("... done.")

    # when writing to file, we don't suport writing out of order yet and hence we don't
    # use multiple threads.  When writing to redis, we can use multiple threads safely.
    threads = 1 if args.cache_type=='filesystem' else vcores

    if args.cache_type=='filesystem' and args.start_trade != 0:
        log.critical("Cannot start at a trade other than 0 when writing to file")

    start_trade = args.start_trade
    batch_size = min(10000, max(1, math.ceil(args.trade_window/threads)))
    stop_trade = start_trade + args.trade_window

    thread_pool = ThreadPool(threads)
    log.info(f'Starting the thread pool and filling the cache (%d threads)', threads)
    log.info(f'Generating %d trades in range %d to %d', args.trade_window, start_trade, stop_trade-1)
    log.info(f'Batch-size for pipeline to cache: %d', batch_size)

    metrics = Metrics(config=_metrics_config,
                # add tags to the metrics that can be used for
                # filtering and grouping in the Azure Application Insights portal
                tool="azfinsim.generator",
                trade_window=args.trade_window,
                threads=threads,
                **args.tags)

    start = time.perf_counter()
    thread_pool.map(lambda x: create_trade_range(x, batch_size, stop_trade, conn, metrics), range(start_trade, stop_trade, batch_size))
    end=time.perf_counter()

    timedelta=end-start
    log.info("Cache filled with %d trades in %.12f seconds" % (args.trade_window, timedelta))
    
    metrics.put("execution_time", timedelta)
    metrics.record()
