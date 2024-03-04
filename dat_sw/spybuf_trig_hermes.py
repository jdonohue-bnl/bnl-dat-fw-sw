##wib_cfgs.py:
def spybuf_trig(self, fembs, num_samples=1, trig_cmd=0x08, spy_rec_ticks=0x3f00): 
    #spy_rec_ticks subject to change
    #(spy_rec_ticks register now only 15 bits instead of 18)
    if trig_cmd == 0x00:
        print (f"Data collection for FEMB {fembs} with software trigger")
    else:
        print (f"Data collection for FEMB {fembs} with trigger operations") 

    data = []    
    for i in range(num_samples):
        if trig_cmd == 0x00: #SW
            self.poke(0xA00C0024, spy_rec_ticks) #spy rec time
            rdreg = self.peek(0xA00C0004)
            wrreg = (rdreg&0xffffffbf)|0x40 #NEW FW
            self.poke(0xA00C0004, wrreg) #reset spy buffer
            wrreg = (rdreg&0xffffffbf)|0x00 #NEW FW
            self.poke(0xA00C0004, wrreg) #release spy buffer
            time.sleep(0.001) #NEW FW
            rdreg = self.peek(0xA00C0004)
            wrreg = (rdreg&0xffffffbf)|0x40 #NEW FW
            self.poke(0xA00C0004, wrreg) #reset spy buffer
            rawdata = self.spybuf(fembs)
            data.append((rawdata, 0, 0x3ffff, 0x00))    
        else: #HW
            print ("DTS trigger mode only supports 4 FEMBs attached")
            rdreg = self.peek(0xA00C0004)   
            wrreg = (rdreg&0xffffffbf)|0x40 #NEW FW
            self.poke(0xA00C0004, wrreg)
            wrreg = (rdreg&0xffffffbf)|0x40 #NEW FW
            self.poke(0xA00C0004, wrreg) #release spy buffer
            
            self.poke(0xA00C0024, spy_rec_ticks) #spy rec time
            rdreg = self.peek(0xA00C0014)
            wrreg = (rdreg&0xff00ffff)|(trig_cmd<<16)|0x40000000
            self.poke(0xA00C0014, wrreg) #program cmd_code_trigger     

            while True:
                spy_full_flgs = False
                rdreg = self.peek(0xA00C0080)
                if rdreg&0x1fb == 0x1fb:
                    print ("Recived %d of %d triggers"%((i+1), num_samples))
                    spy_full_flgs = True
                    spy_addr_regs = [0xA00C0094, 0xA00C0098, 0xA00C00CC, 0xA00C00D0]
                    buf_end_addrs = []                   
                    for femb in range(4):
                        buf_end_addrs.append(self.peek(spy_addr_regs[femb*2]))
                        buf_end_addrs.append(self.peek(spy_addr_regs[femb*2+1]))                         
                    if abs(max(buf_end_addrs) - min(buf_end_addrs)) < 32:
                        rawdata = self.spybuf(fembs)
                        data0 = (rawdata, buf_end_addrs[0], spy_rec_ticks, trig_cmd)
                        data.append(data0)
                    else:
                        print("Two buffers out of sync")
                        pass
                else:
                    spy_full_flgs = False
                if spy_full_flgs:
                    break
                else:
                    print ("No external trigger received, Wait a second ")
                    time.sleep(1)                
    return data

##llc.py:
def spybuf(self, fembs): 
    DAQ_SPY_SIZE = 0x40000 #256KB
    buf = (ctypes.c_char*DAQ_SPY_SIZE)()
    bufs_bytes = [bytearray(DAQ_SPY_SIZE) for coldata in range(8)]
    
    
    for femb in range(4):
        if femb in fembs:
            self.wib.bufread(buf,femb*2) #read first COLDATA's buffer
            byte_ptr = (ctypes.c_char*DAQ_SPY_SIZE).from_buffer(bufs_bytes[femb*2])            
            if not ctypes.memmove(byte_ptr, buf, DAQ_SPY_SIZE):
                print('memmove failed')
                exit()
                
            self.wib.bufread(buf,femb*2+1) #read first COLDATA's buffer
            byte_ptr = (ctypes.c_char*DAQ_SPY_SIZE).from_buffer(bufs_bytes[femb*2+1])            
            if not ctypes.memmove(byte_ptr, buf, DAQ_SPY_SIZE):
                print('memmove failed')
                exit()

    return bufs_bytes 
            
