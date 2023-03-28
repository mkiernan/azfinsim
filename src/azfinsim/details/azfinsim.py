#! /usr/bin/env python3

# This is the main execution engine that runs on the pool nodes

import time
import sys
import logging
import pandas as pd

from . import utils, xmlutils, montecarlo
from opencensus.stats import measure as measure_module

#-- register the task absolute start time (for 3.7 use time.time_ns())
launch=time.time()

log = logging.getLogger(__name__)

def execute(args):
    m_task_time_s = measure_module.MeasureFloat("task_time", "Time for individual task/process", "s")
    m_get_trade_time_s = measure_module.MeasureFloat("get_trade_time", "Time to get trade from cache", "s")
    m_process_trade_time_s = measure_module.MeasureFloat("process_trade_time", "Time to process trade", "s")
    m_write_trade_time_s = measure_module.MeasureFloat("write_trade_time", "Time to write trade to cache", "s")

    if args.algorithm == "pvonly":
        m_pv_time_s = measure_module.MeasureFloat("pv_time", "Time to calculate PV", "s")
        


    # tc = TelemetryClient("%s" % args.appinsights_key) // FIXME:
    tc = TelemetryClient('%s' % None)
    #try:
    #except:
    #    logging.error("Telemetry Client Key %s is Invalid")
    #    tc.track_exception()

    # set up logging - STDOUT & Azure AppInsights EventLog
#    handler = LoggingHandler(args.appinsights_key)
#    logging.basicConfig(
#    format="%(asctime)s azfinsim: %(name)s %(threadName)-10.10s %(levelname)-5.5s %(message)s",
#    handlers=[
#	  LoggingHandler(args.appinsights_key), #-- send to AZURE
#	  logging.StreamHandler(stream=sys.stdout) #-- send to STDOUT
#          #logging.FileHandler("{0}/{1}.log".format(logPath, fileName)),
#    ],level=args.loglevel)
    #logging.info("%s" % args)

    #-- log start time
    log.info("TRADE %10d: LAUNCH    : %d" % (args.start_trade,launch))
    tc.track_metric('STARTTIME', launch)

    #-- open connection to cache
    if (args.cache_type == "redis" or args.cache_type == "hazelcast"):
        log.info('connect to cache')
        r = utils.SetupCacheConn(args.cache_type,args.cache_name,args.cache_port,args.cache_key,args.cache_ssl)
        if r is None:
             log.error("Cannot connect to Redis DB: %s, %s, %s" % args.cache_name,args.cache_port,args.cache_key)

    start_trade=args.start_trade
    stop_trade=start_trade+args.trade_window

    #results = pd.DataFrame(columns = ['netSettlement', 'Time'])
    results = pd.DataFrame(columns = ['PV','PV_time', 'Delta', 'Vega', 'Label'])
    #input_file = pd.DataFrame(columns=['fx1','start_date','end_date','drift','maturity',
    #                                  't_steps','trials','ro','v','sigma1','warrantsNo','notionalPerWarr','strike'])

    for tradenum in range(start_trade,stop_trade):

        trade_start_time=time.time()

        if (args.format == "varxml"): keyname = "var%007d.xml" % tradenum
        else: keyname = "ey%007d.xml" % tradenum

        log.debug("Retrieving Trade: %s" % keyname)
	    #-- read trade from cache
        start=time.perf_counter()
        xmlstring=utils.GetTrade(r,keyname)
        log.debug("XMLREAD: %s" % xmlstring)
        end=time.perf_counter()
        timedelta=end-start
        log.info("TRADE %10d: REDISREAD : %.12f" % (tradenum,timedelta))
        tc.track_metric('REDISREAD', timedelta)
        tc.flush()

        #-- Inject Random Failure 
        if (utils.InjectRandomFail(args.failure)):
            tc.track_metric('ERROR', timedelta)
            sys.exit(1)

        if (args.algorithm == "synthetic"): 
	    #-- fake pricing computation - tunable duration - mainly for benchmarking schedulers
            start=time.perf_counter()
            if (args.task_duration > 0):
                utils.DoFakeCompute(xmlstring,args.delay_start,args.task_duration,args.mem_usage)
            end=time.perf_counter()
            timedelta=end-start
            log.info("TRADE %10d: COMPUTE : %.12f" % (tradenum,timedelta))
            tc.track_metric('COMPUTE', timedelta)

        if (args.algorithm == "pvonly" or args.algorithm == "deltavega" ): 
            #-- other formats are legacy
            if (args.format != "eyxml"):
                log.error("ERROR - only eyxml format supported currently.")
                sys.exit(1)

            #-- If EY format, run a real pricing/monte-carlo simulation with EY Quant code
            input_file=xmlutils.ParseEYXML(xmlstring)
            log.debug("XMLPARSE: dataframe %d: %f" % (tradenum,input_file['fx1']))

            start=time.perf_counter()

            if (args.algorithm == "pvonly"): 
                #results.loc[tradenum] = montecarlo.price_option(tradenum,input_file)
                #out = montecarlo.price_option(input_file[tradenum].to_dict())
                out = montecarlo.price_option(input_file.loc[0].to_dict()) #- single row in dataframe TODO: save all & tab print
                results.loc[tradenum, 'PV'] = out[0]
                results.loc[tradenum, 'PV_time'] = out[1]
                #results.loc[tradenum, 'Label'] = 1 if out[0]!=0 else 0
                tc.track_metric('PVTIME', results.loc[tradenum,'PV_time'])
                tc.track_metric('PV', results.loc[tradenum,'PV'])
                #logging.info("TRADE %10d: RESULT: netSettlement = %f" % (tradenum,results.loc[tradenum,'netSettlement']))
                log.info("TRADE %10d: PVTIME: = %f" % (tradenum,results.loc[tradenum,'PV_time']))
                log.info("TRADE %10d: RESULT: PV (netSettlement) = %f" % (tradenum,results.loc[tradenum,'PV']))

            #--- Perform timedelta vega risk calculation
            if (args.algorithm == "deltavega"): 
                logging.debug("TRADE %10d: Start Delta Vega" % tradenum)
                #results.loc[tradenum, 'Delta'] = montecarlo.risk('fx1', input_file.loc[tradenum].to_dict())
                #results.loc[tradenum, 'Vega'] = montecarlo.risk('sigma1', input_file.loc[tradenum].to_dict())
                results.loc[tradenum, 'Delta'] = montecarlo.risk('fx1', input_file.loc[0].to_dict())
                results.loc[tradenum, 'Vega'] = montecarlo.risk('sigma1', input_file.loc[0].to_dict())
                end=time.perf_counter()
                timedelta=end-start
                log.info("TRADE %10d: DELTA: %.12f" % (tradenum,results.loc[tradenum,'Delta']))
                log.info("TRADE %10d: VEGA: %.12f" % (tradenum,results.loc[tradenum,'Vega']))
                #log.info("TRADE %10d: LABEL: %d" % (tradenum,results.loc[tradenum,'Label']))
                tc.track_metric('PV', results.loc[tradenum,'PV'])
                tc.track_metric('DELTA', results.loc[tradenum,'Delta'])
                tc.track_metric('VEGA', results.loc[tradenum,'Vega'])
                #tc.track_metric('LABEL', results.loc[tradenum,'Label'])
                tc.flush()

            end=time.perf_counter()
            timedelta=end-start
            log.info("TRADE %10d: COMPUTE : %.12f" % (tradenum,timedelta))
            tc.track_metric('COMPUTE', timedelta)

	#-- write result back to cache
        start=time.perf_counter()
        #utils.PutTrade("output",r,tradenum,xmlstring)
        utils.PutTrade(args.cache_type,"output",r,args.format,tradenum,xmlstring)
        end=time.perf_counter()
        timedelta=end-start
        log.info("TRADE %10d: REDISWRITE: %.12f" % (tradenum,timedelta))
        tc.track_metric('REDISWRITE', timedelta)

        #-- log time to process one trade
        timedelta = time.time() - trade_start_time
        log.info("TRADE %10d: TRADETIME : %.12f" % (tradenum,timedelta))
        tc.track_metric('TRADETIME', timedelta)

    #-- log finish time
    end=time.time()
    log.info("TRADE %10d: ENDTIME   : %d" % (args.start_trade,end))
    tc.track_metric('ENDTTIME', end)
    timedelta=end-launch
    log.info("TRADE %10d: TASKTIME  : %.12f" % (args.start_trade,timedelta))
    tc.track_metric('TASKTIME', timedelta)

    # flush all un-sent telemetry items
    tc.flush()
    #log.shutdown()
