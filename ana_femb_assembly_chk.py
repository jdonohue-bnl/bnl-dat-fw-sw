import time
import sys
import numpy as np
import pickle
import copy
import os
import time, datetime, random, statistics
from QC_tools import ana_tools
from fpdf import FPDF
import matplotlib.pyplot as plt


def CreateFolders(fembs, fembNo, env, toytpc):

    reportdir = "reports/"
    PLOTDIR = {}

    for ifemb in fembs:
        femb_no = fembNo['femb%d'%ifemb]
        plotdir = reportdir + "FEMB{}_{}_{}".format(femb_no, env, toytpc)

        n=1
        while (os.path.exists(plotdir)):
            if n==1:
                plotdir = plotdir + "_R{:03d}".format(n)
            else:
                plotdir = plotdir[:-3] + "{:03d}".format(n)
            n=n+1
            if n>20:
                raise Exception("There are more than 20 folders for FEMB %d..."%femb_no)

        try:
            os.makedirs(plotdir)
        except OSError:
            print ("Error to create folder %s"%plotdir)
            sys.exit()
           
        plotdir = plotdir+"/"


        PLOTDIR[ifemb] = plotdir+'/'

    return PLOTDIR

###### Main ######

if len(sys.argv) < 2:
    print('Please specify the folder to analyze')
    exit()

if len(sys.argv) > 2:
    print('Too many arguments!')
    exit()

datadir = sys.argv[1]
fdata = "tmp_data/"+datadir+"/"

###### load logs and create report folder ######
flog = fdata+"logs_env.bin"
with open(flog, 'rb') as fn:
    evlog = pickle.load(fn)

tester = evlog['tester']
env = evlog['env']
toytpc = evlog['toytpc']
note = evlog['note']
fembNo = evlog['femb id']
date = evlog['date']

###### analyze RMS Raw Data ######

frms = fdata+"Raw_SE_200mVBL_14_0mVfC_2_0us_0x00.bin"
with open(frms, 'rb') as fn:
    raw = pickle.load(fn)

rmsdata = raw[0]
fembs = raw[2]

PLOTDIR=CreateFolders(fembs, fembNo, env, toytpc)

qc_tools = ana_tools()

pldata,_ = qc_tools.data_decode(rmsdata, fembs)
pldata = np.array(pldata)

for ifemb in fembs:
    fp = PLOTDIR[ifemb]
    ped,rms=qc_tools.GetRMS(pldata, ifemb, fp, "SE_200mVBL_14_0mVfC_2_0us")
#    qc_tools.ChkRMS(env, fp, "SE_200mVBL_14_0mVfC_2_0us", 1, 0, 3)

fpulse = fdata+"Raw_SE_900mVBL_14_0mVfC_2_0us_0x10.bin"
with open(fpulse, 'rb') as fn:
    raw = pickle.load(fn)

sedata = raw[0]

pldata,tmst = qc_tools.data_decode(sedata, fembs)
pldata = np.array(pldata)
tmst = np.array(tmst)

for ifemb in fembs:
    fp = PLOTDIR[ifemb]
    ppk,npk,bl=qc_tools.GetPeaks(pldata, tmst, ifemb, fp, "SE_900mVBL_14_0mVfC_2_0us_0x10")

#    fig,ax = plt.subplots(figsize=(6,4))
#    ax.plot(range(128), ppk, marker='.',label='pos')
#    ax.plot(range(128), npk, marker='.',label='neg')
#    ax.plot(range(128), bl, marker='.',label='ped')
#    ax.set_title("SE_900mVBL_14_0mVfC_2_0us")
#    ax.set_xlabel("chan")
#    ax.set_ylabel("ADC")
#    plt.legend()
#    fp_fig = fp+"pulse_{}.png".format("SE_900mVBL_14_0mVfC_2_0us")
#    plt.savefig(fp_fig)
#    plt.close(fig)

#fpulse_diff = fdata+"Raw_DIFF_900mVBL_14_0mVfC_2_0us_0x20.bin"
#with open(fpulse_diff, 'rb') as fn:
#    raw = pickle.load(fn)
#
#diff_data = raw[0]
#
#pldata = qc_tools.data_decode(diff_data, fembs)
#pldata = np.array(pldata)
#
#for ifemb in fembs:
#    fp = PLOTDIR[ifemb]
#    ppk,npk,bl=qc_tools.GetPeaks(pldata, ifemb, fp, "DIFF_900mVBL_14_0mVfC_2_0us")
#
#    fig,ax = plt.subplots(figsize=(6,4))
#    ax.plot(range(128), ppk, marker='.',label='pos')
#    ax.plot(range(128), npk, marker='.',label='neg')
#    ax.plot(range(128), bl, marker='.',label='ped')
#    ax.set_title(fname)
#    ax.set_xlabel("chan")
#    ax.set_ylabel("ADC")
#    plt.legend()
#    fp_fig = fp+"pulse_{}.png".format("DIFF_900mVBL_14_0mVfC_2_0us")
#    plt.savefig(fp_fig)
#    plt.close(fig)

#fmon = fdata+"Mon_200mVBL_14_0mVfC.bin"
#with open(fmon, 'rb') as fn:
#    rawmon = pickle.load(fn)
#
#mon_refs = rawmon[0]
#mon_temps = rawmon[1]
#mon_adcs = rawmon[2]
#
#fpwr = fdata+"PWR_SE_200mVBL_14_0mVfC_2_0us_0x00.bin"
#with open(fpwr, 'rb') as fn:
#    rawpwr = pickle.load(fn)
#
#pwr_meas=rawpwr[0]
#for ifemb in fembs:
#    fp_pwr = PLOTDIR[ifemb]+"pwr_meas"
#    qc_tools.PrintPWR(pwr_meas, ifemb, fp_pwr)
#
#nchips=range(8)
#makeplot=True
#qc_tools.PrintMON(fembs, nchips, mon_refs, mon_temps, mon_adcs, PLOTDIR, makeplot)

####### Generate Report ######

#for ifemb in fembs:
#    plotdir = PLOTDIR[ifemb]
#
#    pdf = FPDF(orientation = 'P', unit = 'mm', format='Letter')
#    pdf.alias_nb_pages()
#    pdf.add_page()
#    pdf.set_auto_page_break(False,0)
#    pdf.set_font('Times', 'B', 20)
#    pdf.cell(85)
#    pdf.l_margin = pdf.l_margin*2
#    pdf.cell(30, 5, 'FEMB#{:04d} Checkout Test Report'.format(int(fembNo['femb%d'%ifemb])), 0, 1, 'C')
#    pdf.ln(2)
#
#    pdf.set_font('Times', '', 12)
#    pdf.cell(30, 5, 'Tester: {}'.format(tester), 0, 0)
#    pdf.cell(80)
#    pdf.cell(30, 5, 'Date: {}'.format(date), 0, 1)
#
#
#    pdf.cell(30, 5, 'Temperature: {}'.format(env), 0, 0)
#    pdf.cell(80)
#    pdf.cell(30, 5, 'Input Capacitor(Cd): {}'.format(toytpc), 0, 1)
#    pdf.cell(30, 5, 'Note: {}'.format(note[0:80]), 0, 1)
#    pdf.cell(30, 5, 'FEMB configuration: {}, {}, {}, {}, DAC=0x{:02x}'.format("200mVBL","14_0mVfC","2_0us","500pA",0x20), 0, 1)
#
#    pwr_image = fp_pwr+".png"
#    pdf.image(pwr_image,0,40,200,40)
#
#    if makeplot:
#       mon_image = plotdir+"mon_meas_plot.png"
#       pdf.image(mon_image,10,85,180,72)
#    else:
#       mon_image = plotdir+"mon_meas.png"
#       pdf.image(mon_image,0,77,200,95)
#
##    rms_image = plotdir+
##    pdf.image(chk_image,3,158,200,120)
#
#    outfile = plotdir+'report.pdf'
#    pdf.output(outfile, "F")
#