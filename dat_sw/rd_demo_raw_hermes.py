import sys 
import numpy as np
import pickle
import time, datetime, random, statistics
import matplotlib.pyplot as plt
import copy

import struct
from spymemory_decode_hermes import wib_spy_dec_syn

fp = sys.argv[1]
if "/" in fp:
    sfn = fp.split("/")
elif "\\" in fp:
    sfn = fp.split("\\")
p = fp.find(sfn[-1])
fdir = fp[0:p]

with open(fp, 'rb') as fn:
    raw = pickle.load(fn)
    
rawdata = raw[0]
pwr_meas = raw[1]
runi = 0

#buf0 = rawdata[runi][0][0]
#buf1 = rawdata[runi][0][1]
bufs = [[],[],[],[],[],[],[],[]]

for i in range(8):
    bufs[i] = rawdata[runi][0][i]

buf_end_addr = rawdata[runi][1] 
trigger_rec_ticks = rawdata[runi][2]
if rawdata[runi][3] != 0:
    trigmode = 'HW'; 
else:
    trigmode = 'SW'; 
    
dec_data = wib_spy_dec_syn(bufs, trigmode, buf_end_addr, trigger_rec_ticks)

flen = len(dec_data[0])

tmts = []
#sfs0 = [] #not in new format?
#sfs1 = []
cdts_0 = [[],[],[],[],[],[],[],[]]
cdts_1 = [[],[],[],[],[],[],[],[]]
femb0 = [[] for ch in range(128)]
femb1 = [[] for ch in range(128)]
femb2 = [[] for ch in range(128)]
femb3 = [[] for ch in range(128)]

for i in range(flen):
    tmts.append(dec_data[0][i]["TMTS"])
    for cd in range(8):
        cdts0[cd].append(dec_data[cd][i]["FEMB_CD0TS"])
        cdts1[cd].append(dec_data[cd][i]["FEMB_CD1TS"])
        
    chdata_64ticks = dec_data[0][i]["CD_data"] + dec_data[1][i]["CD_data"]
    femb0 = [femb0[ch] + chdata_64ticks[ch] for ch in range(128)] #append new data to each channels
    
    chdata_64ticks = dec_data[2][i]["CD_data"] + dec_data[3][i]["CD_data"] 
    femb1 = [femb1[ch] + chdata_64ticks[ch] for ch in range(128)]
    
    chdata_64ticks = dec_data[4][i]["CD_data"] + dec_data[5][i]["CD_data"]
    femb2 = [femb2[ch] + chdata_64ticks[ch] for ch in range(128)]
    
    chdata_64ticks = dec_data[6][i]["CD_data"] + dec_data[7][i]["CD_data"]
    femb3 = [femb3[ch] + chdata_64ticks[ch] for ch in range(128)]
       
print (f"timestampe of first 10 events {tmts[0:10]}")

#no zip needed

wib = [femb0, femb1, femb2, femb3]

x = np.arange(len(tmts))

if True:
    fig = plt.figure(figsize=(10,6))
    plt.plot(x, np.array(tmts)-tmts[0], label ="Time Master Timestamp")
    plt.plot(x, np.array(cdts_0[0])-cdts_0[0][0], label ="Coldata Timestamp (FEMB0 CD0)")
    plt.plot(x, np.array(cdts_l[0])-cdts_l[0][0], label ="Coldata Timestamp (FEMB0 CD1)")
    plt.legend()
    #plt.show()
    plt.savefig(fdir + "timestamp.jpg")
    plt.close()

    for fembi in range(4):
        #maxpos = np.where(wib[fembi][0][0:1500] == np.max(wib[fembi][0][0:1500]))[0][0] #not used?
        fig = plt.figure(figsize=(10,6))
        for chip in range(8): #coldata
            for chn in range(16):
                i = chip*16 + chn
                #if chn == 0:
                #    plt.plot(x, wib[fembi][i],color = 'C%d'%chip, label = "Chip%dCH0"%chip )
                #else:
                plt.plot(x, wib[fembi][i],color = 'C%d'%chip )        
        plt.title(f"Waveform of FEMB{fembi}")
        #plt.legend()
        ##plt.show()
        plt.savefig(fdir + f"{fembi}_wf.jpg")
        plt.close()    
    