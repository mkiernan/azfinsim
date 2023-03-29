#! /usr/bin/env python3

# This is the main execution engine that runs on the pool nodes

import time
import sys
import logging
import pandas as pd

from . import utils, xmlutils, montecarlo, cache
from .metrics import Metrics

# config for metrics
_metrics_config = {
    "start_time": {
        "description": "Start time",
        "unit": "s",
        "type": "float",
        "aggregation": "last_value"
    },
    "end_time": {
        "description": "End time",
        "unit": "s",
        "type": "float",
        "aggregation": "last_value"
    },
    "task_time": {
        "description": "Task Execution time",
        "unit": "s",
        "type": "float",
        "aggregation": "last_value"
    },
    "io_read_time": {
        "description": "Time for IO reads",
        "unit": "s",
        "type": "float",
        "aggregation": "sum"
    },
    "io_write_time": {
        "description": "Time for IO writes",
        "unit": "s",
        "type": "float",
        "aggregation": "sum"
    },
    "num_trades": {
        "description": "Number of trades processed",
        "unit": "count",
        "type": "int",
        "aggregation": "last_value"
    },
    "compute_time": {
        "description": "Time to calculate PV, Delta, and Vega or Synthetic computation",
        "unit": "s",
        "type": "float",
        "aggregation": "sum"
    },
    "failed": {
        "description": "Calculation failed",
        "unit": "count",
        "type": "int",
        "aggregation": "last_value"
    }
}

log = logging.getLogger(__name__)

def execute(args):

    # start time
    start_ts = time.perf_counter()

    # setup metrics
    metrics = Metrics(_metrics_config,
                      tool="azfinsim.azfinsim",
                      trade_window=args.trade_window,
                      **args.tags)

    #-- log start time
    log.info("TRADE %10d: LAUNCH    : %d" % (args.start_trade, start_ts))
    metrics.put("start_time", start_ts)
    metrics.put("num_trades", args.trade_window)

    #-- open connection to conn
    log.info("Setting up cache connection ...")
    conn = cache.connect(args, as_input=True)
    log.info("... done.")

    # if cache_type is filesystem then we need a separate connection for output
    if args.cache_type == "filesystem":
        args.cache_path = args.cache_path + ".out"
        out_conn = cache.connect(args, as_input=False)
    else:
        out_conn = conn

    start_trade=args.start_trade
    stop_trade=start_trade+args.trade_window

    results = pd.DataFrame(columns = ['PV','PV_time', 'Delta', 'Vega'])
    out_pipe = out_conn.pipeline()

    out_batch_size = 10000 # number of trade results to write in a single batch

    for tradenum in range(start_trade,stop_trade):
        keyname = xmlutils.trade_key(tradenum)

        # start time for each trade
        start_trade_ts = time.perf_counter()

	    #-- read trade from cache
        log.debug("Retrieving Trade: %s", keyname)
        start_io_read_ts = time.perf_counter()
        xmlstring = conn.get(keyname)
        io_read_ts = time.perf_counter() - start_io_read_ts

        log.debug("XMLREAD: %s", xmlstring)
        log.info("TRADE %10d: REDISREAD : %.12f" % (tradenum, io_read_ts))
        metrics.put("io_read_time", io_read_ts)

        #-- Inject Random Failure 
        if utils.InjectRandomFail(args.failure):
            metrics.put("failed", 1)
            metrics.record()
            sys.exit(1)

        start_compute_ts = time.perf_counter()
        if args.algorithm == "synthetic":
	        #-- fake pricing computation - tunable duration - mainly for benchmarking schedulers
            if args.task_duration > 0:
                utils.DoFakeCompute(xmlstring, args.delay_start, args.task_duration, args.mem_usage)
            else:
                pass # should we do something?
            end_compute_ts = time.perf_counter()
        elif args.algorithm == "pvonly" or args.algorithm == "deltavega":
            #-- run a real pricing/monte-carlo simulation with EY Quant code
            input_file = xmlutils.ParseEYXML(xmlstring)
            log.debug("XMLPARSE: dataframe %d: %f", tradenum, input_file['fx1'])

            if args.algorithm == "pvonly": 
                log.debug("TRADE %10d: Start PV" % tradenum)
                pv, pv_time = montecarlo.price_option(input_file.loc[0].to_dict()) #- single row in dataframe TODO: save all & tab print
                end_compute_ts = time.perf_counter()
                results.loc[tradenum, 'PV'] = pv
                results.loc[tradenum, 'PV_time'] = pv_time
                log.info("TRADE %10d: PVTIME: = %f RESULT: PV (netSettlement) = %f", tradenum, pv_time, pv)

            elif args.algorithm == "deltavega":
                #--- Perform timedelta vega risk calculation
                log.debug("TRADE %10d: Start Delta Vega" % tradenum)
                results.loc[tradenum, 'Delta'] = montecarlo.risk('fx1', input_file.loc[0].to_dict())
                results.loc[tradenum, 'Vega'] = montecarlo.risk('sigma1', input_file.loc[0].to_dict())
                end_compute_ts = time.perf_counter()

                log.info("TRADE %10d: DELTA: %.12f", tradenum, results.loc[tradenum,'Delta'])
                log.info("TRADE %10d: VEGA: %.12f", tradenum, results.loc[tradenum,'Vega'])

            compute_ts = end_compute_ts - start_compute_ts
            log.info("TRADE %10d: COMPUTE : %.12f", tradenum, compute_ts)
            metrics.put("compute_time", compute_ts)

            #-- write result back to cache
            log.debug("Writing Trade: %s", keyname)
            out_pipe.set(f'{keyname}_results', results.to_xml())

            if (tradenum-start_trade) % out_batch_size == 0 or tradenum == stop_trade-1:
                start_io_write_ts = time.perf_counter()
                out_pipe.execute()
                io_write_ts = time.perf_counter() - start_io_write_ts
                log.info("TRADE %10d: WRITE: %.12f", tradenum, io_write_ts)
                metrics.put("io_write_time", io_write_ts)

    #-- log finish time
    end_ts =time.perf_counter()
    log.info("TRADE %10d: ENDTIME: %f", args.start_trade, end_ts)
    metrics.put("end_time", end_ts)
    
    timedelta = end_ts - start_ts
    log.info("TRADE %10d: TASKTIME  : %.12f", args.start_trade,timedelta)
    metrics.put("task_time", timedelta)

    # flush metrics
    metrics.record()
