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
#print (reg_read)
reg_read = chk.peek(0xA00C0004)
print (hex(reg_read))
reg_read = chk.wib_peek(0xA00C0004)
print (hex(reg_read))
reg_read = chk.poke(0xA00C0004, 2)
reg_read = chk.peek(0xA00C0004)
print (hex(reg_read))
reg_read = chk.wib_peek(0xA00C0004)
print (hex(reg_read))
reg_read = chk.wib_poke(0xA00C0004, 3)
reg_read = chk.peek(0xA00C0004)
print (hex(reg_read))
reg_read = chk.wib_peek(0xA00C0004)
print (hex(reg_read))

#chk.femb_power_en_ctrl(femb_id=2, enable=1)
#chk.femb_power_set(0,1)

