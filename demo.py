from wib_cfgs import WIB_CFGS
import time
import sys
import numpy as np
import pickle
import copy
import time, datetime, random, statistics


chk = WIB_CFGS()
#reg_read = chk.poke(0xA00C0004, 1)
#reg_read = chk.peek(0xA00C0004)
chk.femb_power_en_ctrl(femb=0, enable=0)
print (reg_read)

