import ctypes, ctypes.util
import struct, os

class LLC():
    def __init__(self):
        super().__init__()
        self.wib_path = os.getcwd() + "/build/wib_util.so"
        self.wib = ctypes.CDLL(self.wib_path)

        #define C functions' argument types and return types
        self.wib.peek.argtypes = [ctypes.c_size_t]
        self.wib.peek.restype = ctypes.c_uint32
        
        self.wib.poke.argtypes = [ctypes.c_size_t, ctypes.c_uint32]
        self.wib.poke.restype = None

        self.wib.wib_peek.argtypes = [ctypes.c_size_t]
        self.wib.wib_peek.restype = ctypes.c_uint32
        
        self.wib.wib_poke.argtypes = [ctypes.c_size_t, ctypes.c_uint32]
        self.wib.wib_poke.restype = None
      
        self.wib.cdpeek.argtypes = [ctypes.c_uint8,  ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8]
        self.wib.cdpeek.restype = ctypes.c_uint8
        
        self.wib.cdpoke.argtypes = [ctypes.c_uint8,  ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8]
        self.wib.cdpoke.restype = None  
        
        self.wib.bufread.argtypes = [ctypes.POINTER(ctypes.c_char), ctypes.c_size_t]
        self.wib.bufread.restype = None

        self.wib.i2cread.argtypes = [ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8]
        self.wib.i2cread.restype = ctypes.c_uint8
    
        self.wib.i2cwrite.argtypes = [ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8]
        self.wib.i2cwrite.restype = None

        self.wib.read_ltc2990.argtypes = [ctypes.c_uint8, ctypes.c_bool, ctypes.c_uint8]
        self.wib.read_ltc2990.restype = ctypes.c_double
    
        self.wib.read_ltc2991.argtypes = [ctypes.c_uint8, ctypes.c_uint8, ctypes.c_bool, ctypes.c_uint8]
        self.wib.read_ltc2991.restype = ctypes.c_double    
    
        self.wib.read_ad7414.argtypes = [ctypes.c_uint8]
        self.wib.read_ad7414.restype = ctypes.c_double
    
        self.wib.read_ltc2499.argtypes = [ctypes.c_uint8]
        self.wib.read_ltc2499.restype = ctypes.c_double        

        self.wib.all_femb_bias_ctrl.argtypes = [ctypes.c_uint8 ]
        self.wib.all_femb_bias_ctrl.restype  = ctypes.c_bool

        self.wib.femb_power_en_ctrl.argtypes = [ctypes.c_int, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8]
        self.wib.femb_power_en_ctrl.restype  = ctypes.c_bool

        self.wib.femb_power_reg_ctrl.argtypes = [ctypes.c_uint8, ctypes.c_uint8, ctypes.c_double]
        self.wib.femb_power_reg_ctrl.restype = ctypes.c_bool
    
        self.wib.femb_power_config.argtypes = [ctypes.c_uint8, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double ]
        self.wib.femb_power_config.restype = ctypes.c_bool       

    def peek(self, regaddr):
        val = self.wib.peek(regaddr)
        return val

    def poke(self, regaddr, regval):
        self.wib.poke(regaddr, regval)
        return None

    def wib_peek(self, regaddr):
        val = self.wib.wib_peek(regaddr)
        return val

    def wib_poke(self, regaddr, regval):
        self.wib.wib_poke(regaddr, regval)
        return None

#    def poke_chk(self, regaddr, regval):
#        self.poke(regaddr, regval)
#        val = self.peek(regaddr)
#        if val == regval:
#            return val
#        else:
#            print ("Error: WIB reg addr 0x%x readback value (0x%x) is different from write value (0x%x)"%(regaddr, regval, val))
#            return None

    def cdpeek(self, femb_id, chip_addr, reg_page, reg_addr):
        val = self.wib.cdpeek(femb_id, chip_addr, reg_page, reg_addr)
        return val

    def cdpoke(self, femb_id, chip_addr, reg_page, reg_addr, data):
        self.wib.cdpoke(femb_id, chip_addr, reg_page, reg_addr, data)
   
#    def cdpoke_chk(self, femb_id, chip_addr, reg_page, reg_addr, data):
#        for i in range(10):
#            self.wib.cdpoke(femb_id, chip_addr, reg_page, reg_addr, data)
#            val = self.wib.cdpeek(femb_id, chip_addr, reg_page, reg_addr)
#            if val == data:
#                return val
#            else:
#                print ("Warning: FEMB%d_chipI2C0x%x_page0x%x_addr0x%x readback(0x%x) is different from write value (0x%x)"%(femb_id, chip_addr, reg_page, reg_addr, regval, val))
#                print ("Try again...")
#                if i > 5: 
#                    print ("Error: Failed to configurate FEMB, please check hardware connection...")
#                    exit()

    def fastcmd(self, cmd):
        fast_dict = { 'reset':1, 'act':2, 'sync':4, 'edge':8, 'idle':16, 'edge_act':32 }        
        self.wib.poke(0xA0030000, fast_dict[cmd]) #fast command

#    def fastcmd_act(self, femb_id, act_cmd="idle"):
#        if act_cmd == "idle":
#            wrdata = 0
#        elif act_cmd == "larasic_pls":
#            wrdata = 0x01
#        elif act_cmd == "save_timestamp":
#            wrdata = 0x02
#        elif act_cmd == "save_status":
#            wrdata = 0x03
#        elif act_cmd == "clr_saves":
#            wrdata = 0x04
#        elif act_cmd == "rst_adcs":
#            wrdata = 0x05
#        elif act_cmd == "rst_larasics":
#            wrdata = 0x06
#        elif act_cmd == "rst_larasic_spi":
#            wrdata = 0x07
#        elif act_cmd == "prm_larasics":
#            wrdata = 0x08
#        elif act_cmd == "relay_i2c_sda":
#            wrdata = 0x09
#        else:
#            wrdata = 0
#
#        self.cdpoke_chk(femb_id, chip_addr=3, reg_page=0, reg_addr=0x20, wrdata=wrdata)
#        self.cdpoke_chk(femb_id, chip_addr=2, reg_page=0, reg_addr=0x20, wrdata=wrdata)
#        self.fastcmd(cmd='act')
#        #return to "idle" in case other FEMB runs FC 
#        self.cdpoke_chk(femb_id, chip_addr=3, reg_page=0, reg_addr=0x20, wrdata=0)
#        self.cdpoke_chk(femb_id, chip_addr=2, reg_page=0, reg_addr=0x20, wrdata=0)


    def spybuf(self, fembs= [0, 1,2,3]):
        buf0 = True if 0 in fembs or 1 in fembs else False
        buf1 = True if 2 in fembs or 3 in fembs else False 

        DAQ_SPY_SIZE = 0x00100000
        buf = (ctypes.c_char*DAQ_SPY_SIZE)()
        #allocate memory in python
        buf0_bytes = bytearray(DAQ_SPY_SIZE)
        buf1_bytes = bytearray(DAQ_SPY_SIZE)

        if buf0:
            self.wib.bufread(buf, 0) #read buf0
            byte_ptr0 = (ctypes.c_char*DAQ_SPY_SIZE).from_buffer(buf0_bytes)
            if not ctypes.memmove(byte_ptr0, buf, DAQ_SPY_SIZE):
                print('memmove failed')
                exit()

        if buf1:
            self.wib.bufread(buf, 1) #read buf1    
            byte_ptr1 = (ctypes.c_char*DAQ_SPY_SIZE).from_buffer(buf1_bytes)
            if not ctypes.memmove(byte_ptr1, buf, DAQ_SPY_SIZE):
                print('memmove failed')
                exit()
        return buf0_bytes, buf1_bytes

        
    def femb_power_config(self, femb_id=0, vfe=3.0, vcd=3.0, vadc=3.5):
        self.wib.femb_power_config(femb_id, vfe, vcd, vadc, 0, 0, 0 )

    def all_femb_bias_ctrl(self, enable=0):
        self.wib.all_femb_bias_ctrl(enable )

    def femb_power_en_ctrl(self, femb_id=0, vfe_en=1, vcd_en=1, vadc_en=1, bias_en=0):
        self.wib.femb_power_en_ctrl(femb_id, vfe_en, vcd_en, vadc_en, 0, bias_en)


    def femb_power_set(self, femb_id=0, on=1, vfe=3.0, vcd=3.0, vadc=3.5, allon=1):
        self.femb_power_config(femb_id, vfe, vcd, vadc)
        self.all_femb_bias_ctrl(enable=allon)
        self.femb_power_en_ctrl(femb_id, vfe_en=on, vcd_en=on, vadc_en=on, bias_en=on)
            
