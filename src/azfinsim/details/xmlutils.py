import pandas as pd
import numpy as np
import datetime as dt
import xml.etree.ElementTree as ET

def GenerateTradeEY(tradenum, N):
    # just use the time now
    today = dt.date.today()
    stoday = "%s" % (today)

    newFile = {}
    newFile['fx1'] = np.random.rand(N)*0.12+0.8285

    newFile['start_date'] = [dt.date(2017,12,29)]*N
    newFile['end_date'] = [dt.date(2018,8,28)]*N

    newFile['drift'] = np.random.rand(N)*0.2 - 0.1
    newFile['maturity'] = [0.20]*N

    t_steps = np.busday_count(dt.date(2017,12,29), dt.date(2018,8,28) )# number of working days between 29/12/2017 and 08/03/2018
    newFile['t_steps']  = [t_steps]*N
    #-- 10k vs 100k Monte Carlo Paths
    #newFile['trials'] = np.random.randint(10000,10000,N)
    #newFile['trials'] = np.random.randint(100000,100000,N)
    newFile['trials'] = np.repeat(10000,N)  
    #newFile['trials'] = np.repeat(100000,N)

    newFile['ro'] = [0.000038413221829]*N # calibration value: 0.000038413221829   Vega01 value: 0.0000387714624899
    newFile['v'] = [0.00154807378604]*N
    newFile['sigma1'] = np.random.rand(N) * 0.03 - 0.015 +  0.0808844481978

    newFile['warrantsNo'] = np.random.randint(30000,60000,N)
    newFile['notionalPerWarr'] = np.random.rand(N)*100 + 950
    #newFile['strike'] = np.random.rand(N)*0.2 + 0.9
    newFile['strike'] = np.random.rand(N)*0.12 + 0.7
 
    newFile = pd.DataFrame.from_dict(newFile)

    for i, row in newFile.iterrows():
        #print(row['fx1'],row['start_date'],row['drift'],row['maturity'],row['t_steps'],row['trials'])
        #print(row['ro'],row['v'],row['sigma1'],row['warrantsNo'],row['notionalPerWarr'],row['strike'])
        root = ET.Element("AZFINSIM")
        trade = ET.SubElement(root, "trade",
                              fx1 = "%.16f" % (row['fx1']), 
                              start_date = "%s" % (row['start_date']),
                              end_date = "%s" % (row['end_date']),
                              drift = "%2.17f" % (row['drift']),
                              maturity = "%.2f" % (row['maturity']),
                              t_steps = "%d" % (row["t_steps"]),
                              trials = "%d" % (row["trials"]),
                              ro = "%2.10e" % (row["ro"]),
                              v = "%2.16f" % (row["v"]),
                              sigma1 = "%2.17f" % (row["sigma1"]),
                              warrantsNo = "%d" % (row["warrantsNo"]),
                              notionalPerWarr = "%2.16f" % (row["notionalPerWarr"]),
                              strike = "%2.16f" % (row["strike"])
                             )
        trade.text = "%010d" % (tradenum + i)
        xml_data = ET.tostring(root, encoding="utf-8", method="xml")
        yield trade_key(tradenum +i ), xml_data

def xml_to_dataframe(elem):
    fx1 = float(elem.get('fx1'))
    start_date = elem.get('start_date')
    end_date = elem.get('end_date')
    drift = float(elem.get('drift'))
    maturity = float(elem.get('maturity'))
    t_steps = int(elem.get('t_steps'))
    trials = int(elem.get('trials'))
    ro = float(elem.get('ro'))
    v = float(elem.get('v'))
    sigma1 = float(elem.get('sigma1'))
    warrantsNo = int(elem.get('warrantsNo'))
    notionalPerWarr = float(elem.get('notionalPerWarr'))
    strike = float(elem.get('strike'))
    trade = elem.text
    return fx1, start_date, end_date, drift, maturity, t_steps, trials, ro, v, sigma1, warrantsNo, notionalPerWarr, strike
    

def ParseEYXML(xmlstring):
    root = ET.fromstring(xmlstring)
    #tree = ET.parse('trade2.xml')
    #root = tree.getroot()
    trade_elements = root.iter('trade')
    #print(trade_elements)
    trade_data = pd.DataFrame(list(map(xml_to_dataframe, trade_elements)),
                              columns=['fx1','start_date','end_date','drift','maturity',
                                      't_steps','trials','ro','v','sigma1','warrantsNo','notionalPerWarr','strike'])
    #trade_data = list(map(xml_to_dataframe, trade_elements))
    #print("xml trade data:")
    #print(trade_data.to_string())
    #drift = trade_data.loc[0,'drift']
    #print(drift)
    return(trade_data)

def trade_key(tradenum):
    return "ey%007d.xml" % (tradenum)

def results_key(tradenum):
    return "ey%007d_results.xml" % (tradenum)
