# 1. Introduction
DAT functions include: []
## 1.1. GitHub
The source code for the DAT firmware is located in the DUNE_DAT_FPGA_V2B subfolder of this repository: https://github.com/jdonohue-bnl/bnl-dat-fw-sw.
In addition to the firmware, the repository contains associated software ([dat_sw](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/tree/main/dat_sw)) meant to be used on the WIB to control and communicate with the DAT, and a README giving quick-start instructions.
## 1.2 FPGA info
The DAT FPGA is an Altera Cyclone IV. Development on it has been with Quartus Prime 17.1, and it can be programmed with Quartus Programmer. The resulting bitfiles from a compilation always go in the DUNE_DAT_FPGA_V2B/output_files folder. Besides the latest compilated bitfiles, the output_files folder on Github also contains a .pof file called DUNE_DAT_FPGA_femb.pof with the base functionality allowing the DAT to act like an FEMB.
#### To compile new bitfiles:

1.  Open DUNE_DAT_FPGA_V2B/DUNE_DAT_FPGA.qpf in Quartus Prime 17.1.
2.  Click Start Compilation.

#### To program using the .sof file (needs to be reprogrammed after power cycle):

1.  Plug the JTAG into header  **P4**  with the ribbon cable coming towards the FPGA.
2.  Open Quartus Prime (any version) or Quartus Programmer.  [Here are instructions for downloading Quartus Programmer](http://www.terasic.com.tw/wiki/Chapter_1_Download_and_install_Quartus_Programmer).
3.  Click Programmer.
4.  Click Hardware Setup to select your JTAG blaster.
5.  Click Add Files to add the .sof file if not already present and select the file.
6.  Under mode, select  **JTAG**.
7.  Check Program/Configure if not checked already, and click Start.

#### To program using the .pof file (remains after power cycle):

1.  Plug the JTAG into header  **P5**  with the ribbon cable coming towards the FPGA.
2.  Open Quartus Programmer.
3.  Click Hardware Setup to select your JTAG blaster.
4.  Click Add Files to add the .pof file if not already present and select the file.
5.  Under mode, select  **Active Serial Programming**.
6.  Check Program/Configure if not checked already, and click Start.
# 2. Firmware structure
[Block diagram]

[RTL diagram]

[Most (all?) entities were already used on the DUT]

## 2.1 I2C target
Allows the WIB to read and write the DAT registers in the same way that it reads and writes other chips on the board. The DAT FPGA has I2C address 0xC. 
### Instructions for use:
 - Use [cdpeek/cdpoke](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/wib_util.cc#L78) [femb_idx = the connector the DAT is plugged into - goes from 0 on the right to 3; **chip_addr = 0xC**, reg_page = 0, reg_addr = desired register number (see map)] or a wrapped version thereof.

See the appendix for the map of DAT registers.

## 2.2 Socket selection

To reduce the total number of registers, some signals which have 8 "copies" (because of the nature of the DAT) are the inputs to a mux controlled by the register SOCKET_SEL. The output of that mux goes to a read-only register. Likewise, for writeable signals (e.g. INA226 read strobes), the register goes to a demux and SOCKET_SEL determines which of the 8 signals (e.g. LArASIC 2's INA226 controller's read strobe) receives the data (by default they are assigned 0x0). 
SOCKET_SEL is a 3-bit signal from 0x0 to 0x7: regardless of the value of CD_SEL (which changes the I2C addresses of the ADCs), the leftmost LArASIC/ColdADC's (when viewing the board with the COLDATAs at the top) associated signals will be selected with value 0x0 and the rightmost will be selected with the value 0x7. 

**Registers that utilize SOCKET_SEL**:
Writeable registers:

 - INA226_STRB
 - FE_DAC_TP_DATA_LSB, FE_DAC_TP_DATA_MSB

Read-only registers:

 - INA226_FE_DOUT_MSB, INA226_FE_DOUT_LSB
 - ADC_MONADC_DATA_LSB, ADC_MONADC_DATA_MSB_BUSY
 - FE_MONADC_DATA_LSB, FE_MONADC_DATA_MSB_BUSY
 - ADC_RING_OSC_COUNT_B0, ADC_RING_OSC_COUNT_B1, ADC_RING_OSC_COUNT_B2, ADC_RING_OSC_COUNT_B3

Note: in the DAT schematic and in the toplevel VHDL file, the leftmost LArASIC/ColdADC and their associated chips are referred to as FE1/ADC1 despite being selected with SOCKET_SEL value 0x0, FE8/ADC8 with 0x7, etc.

See also: [toplevel DAT file](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/DUNE_DAT_FPGA_V2B/SRC/DUNE_DAT_FPGA.vhd#L697).

## 2.3 Power monitors (INA226)
All chips on the board have power rails that need to be monitored. Each COLDATA has 5 INA226s on one I2C bus (CD1/2_FPGA_CD_INA_SCL/SDA) and each LArASIC/ADC pair has 7 INA226s on its own I2C bus (FE_INA_SCL/SDA[0-7]). Each bus is managed by an I2C controller instance, whose inputs (device address to contact, register within the device, number of bytes, data to write, and read and write strobes) are controlled by DAT registers, and each I2C controller has two assigned registers for the 16-bit result of a read operation.

[Note about I2c controller not working correctly and me compensating for that]

The INA226 has a built-in current calculator so that you can program its calibration register ahead of time and then simply read the current register instead of reading the shunt register and then having to divide it by the shunt resistor value.

calib_value = 0.00512/(I_LSB*R)

...where I_LSB is your desired maximum possible current divided by 2^15 (in amps) and R = 0.1 ohms. See section 7.5 of the datasheet (linked below) for more details.
| COLDATA power rail name | Address | Voltage | Description
|--|--|--|--|
| CD_VDDA | 0x40 | 1.1 V | PLL analog circuits
| FE_VDDA | 0x41 | 1.8 V | (a.k.a VDD_LArASIC) I/O to/from LArASICs
| CD_VDDCORE | 0x43* | 1.1 V | Core digital logic
| CD_VDDIO | 0x44 | 2.25 V | All I/O except to/from LArASICs
| CD_VDDD | 0x45 | 1.1 V | Digital logic in PLL, serializers, and line drivers

(Rail info source: COLDATA datasheet, section "Power Domains")

*The CD_VDDCORE address was supposed to be 0x42 (A1 = GND, A0 = SDA), but the CD1_FPGA_CD_INA_SCL & CD1_FPGA_CD_INA_SDA FPGA pin assignments had to be swapped due to a schematic error and thus the chip's address changed.

| LArASIC/ADC Power rail name | Address |  Voltage | Description
|--|--|--|--|
| FE: |
| VDD | 0x40 | 1.8 V | Analog supply
| VDDO | 0x41 | 1.8 V | Analog supply for output buffer
| VPPP | 0x42 | 1.8 V | (a.k.a. VDDP) Analog supply for the 1st stage of the charge amplifiers |
| ADC: |
| VDDA2P5 | 0x43 | 2.25 V (+/- 5%) | Analog power
| VDDD1P2 | 0x44 | 1.1 V (+/- 5%), max voltage is nominal +10% | Digital logic power
| VDDD2P5 | 0x45 | 2.25 V (+/- 5%) | Digital ADC power
| VDDIO | 0x46 | 2.25 V | ESD ring/CMOS I/O power

(Rail info sources: LArASIC datasheet, table 5; COLDADC datasheet, table 1)

#### Strobe value to write to INA226_STRB:
| INA226 type | Write strobe | Read strobe
|--|--|--|
| CD1 | 0x1 | 0x2
| CD2 | 0x4 | 0x8
| FE (set SOCKET_SEL first) | 0x10 | 0x20

### Reading an INA226 register:
1. **If the INA226 device is associated with the LArASIC or the ColdADC**, write the 0-7 number of the chip to SOCKET_SEL. 
2. Write the address of the device to INA226_DEVICE_ADDR (see the table above).
3. Write the number of bytes to write (0 to 2) to INA226_NUM_BYTES (see the table below).
4. Write the register to write to to INA226_REG_ADDR.
5. (If not doing a dummy write) Write the less significant byte of the data you wish to write to DAT_INA226_DIN_LSB.
6. (If not doing a dummy write or a 1 byte write) Write the more significant byte of the data you wish to write to DAT_INA226_DIN_MSB.
7. Write the appropriate write strobe to INA226_STRB (see the table above).
8. Write 0x0 to INA226_STRB.

See for an example: [datpower_poke](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/dat_util.cc#L8).
### Reading an INA226 register:
1. **If the INA226 device is associated with the LArASIC or the ColdADC**, write the 0-7 number of the chip to SOCKET_SEL. 
2. Perform a 0 byte dummy write to the register you wish to read (see write instructions above). If the register is read-only (see the datasheet, section 7.6), it doesn't matter what you write.
3. Write the number of bytes to read to INA226_NUM_BYTES (the other I2C parameters should already be in the DAT registers from the dummy write).
4. Write the appropriate read strobe to INA226_STRB.
5. Write 0x0 to INA226_STRB.
6. Read the appropriate register (INA226_CD1_DOUT_MSB, INA226_CD2_DOUT_MSB, or INA226_FE_DOUT_MSB) for the more significant byte of the data.
7. Read the appropriate register (INA226_CD1_DOUT_LSB, INA226_CD2_DOUT_LSB, or INA226_FE_DOUT_LSB) for the less significant byte of the data.
8. If multiple reads in a row are required (e.g. checking for a flag), you don't need to repeat steps 1 through 3.

The I2C operations are fairly slow relative to the clock (12.5 MHz), but this shouldn't be noticeable when using the WIB to communicate with the DAT. 

See for an example: [datpower_peek](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/dat_util.cc#L38), [datpower_getvoltage](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/dat_util.cc#L70).

| I2C number of bytes| Writing | Reading |
|--:|--|--|
| 0 | Dummy write (only sets device's register pointer to prepare for a read)  | Reads 1 byte (half a register) |
| 1 | Writes 1 byte (half a register) and sets register pointer  | Reads 1 byte (half a register) |
| 2 | Writes 2 bytes (one register) and sets register pointer  | Reads 2 bytes (one register) |

###  Reading a voltage or current:
1. **If you want a current reading:** program INA226 register 0x5 with your calculated calibration value.
2. Program INA226 register 0x0 with the desired configuration value (see datasheet section 7.6.1). If not configured to shutdown mode, a conversion will begin immediately.
3. Keep checking INA226 register 0x6 until the ready flag (result & 0x8 = 0x8) appears. Depending on the configuration settings, this may take as many as 10-20 reads (from C). 
4. The bus voltage (voltage measured to ground) reading can now be accessed in INA226 register 0x2. Multiply the integer by 1.25 mV to get the actual reading.
5. The current reading can now be accessed in INA226 register 0x4. Multiply the integer by the I_LSB you used to calculate the calibration value to get the current value.

See for an example: [datpower_getvoltage](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/dat_util.cc#L70), [datpower_getcurrent](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/dat_util.cc#L113).

See also: the entity source code [I2c_master.vhd](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/DUNE_DAT_FPGA_V2B/SRC/I2c_master.vhd), [dat_util.h](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/dat_util.h) for INA226 internal register mapping, [INA226 datasheet](https://www.ti.com/lit/ds/symlink/ina226.pdf).

## 2.4 Monitoring ADCs (AD7274)
The ADCs on the DAT board monitor analog input & output pins on all three chips, such as the LArASIC bandgap reference voltage. SN74LV4051 analog muxes allows 1 ADC to monitor 8 voltages from a chip. The chips are controlled over SPI. Each "type" of monitoring ADC (COLDATA, LArASIC, or ColdADC) share an SPI bus: they share both the clock and CS lines, but each chip has their own separate SDO (MISO) line. 

Within the FPGA, SPI controller instances control one ADC each. Writing 0x1 to MONADC_START causes all the SPI controllers to trigger the chips to start a conversion. The SPI controllers receive the 12-bit voltage data over the SDO lines and stores it in a signal, then turns the corresponding busy flag off. The ADCs' data can then be accessed via the registers. If you are reading a LArASIC or ColdADC ADC, you must first write the 0-7 socket number of the ADC to register SOCKET_SEL.

The analog muxes which control the output to the ADCs are in turn controlled by registers CD_AMON_SEL, ADC_FE_TEST_SEL, ADC_TEST_SEL_INHIBIT, FE_TEST_SEL_INHIBIT; "inhibit" signals turn the mux off entirely. See section 2.6 for more info.

### 2.4.1 Triggering and reading ADCs
1. Trigger all ADCs by writing 0x1 to MONADC_START.
2. Conversion takes at most 600 ns (14 SCLK periods * 1/(25MHz)). **If the AD7274 is associated with the LArASIC or the ColdADC**, take the time to write the 0-7 number of the chip to SOCKET_SEL. 
3. Check if the SPI controller is still busy by checking if the highest bit of the MSB/busy register (DAT_CD1_MONADC_DATA_MSB_BUSY, DAT_CD2_MONADC_DATA_MSB_BUSY, DAT_ADC_MONADC_DATA_MSB_BUSY, or DAT_FE_MONADC_DATA_MSB_BUSY) is set or not.
4. Once the busy flag is 0, the LSB of the data is in the corresponding register (DAT_CD1_MONADC_DATA_LSB, DAT_CD2_MONADC_DATA_LSB, DAT_ADC_MONADC_DATA_LSB, or DAT_FE_MONADC_DATA_LSB), and the upper 4 bits are in bits 3:0 of the MSB/busy register (see step 3).
5. The voltage value of the LSB depends on the external reference Vref applied to the ADC - in this case, that reference is 2.257 V (labeled as P2.5V on the datasheet). When I measured it with a multimeter, it read 2.27 V. Multiply the 12-bit output data by Vref/4096 for your result.
6. If you want to get multiple results from one trigger, simply change SOCKET_SEL and the data registers you're reading as needed.

See for an example: [dat_monadc_trigger](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/dat_util.cc#L146), [dat_monadc_busy](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/dat_util.cc#L152), [dat_monadc_getdata](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/dat_util.cc#L171), [dat_test.py](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/dat_test.py#L343).

See also: [the SPI controller source code](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/DUNE_DAT_FPGA_V2B/SRC/COTS_AD7274.vhd), [AD7274 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/AD7273_7274.pdf).
## 2.5 Test pulse generation
A central function of the DAT is the ability to configure external test pulses and send them to either the LArASIC or directly into the ColdADC in order to calibrate them (as opposed to just using the LArASIC's internal pulse generator). 

### 2.5.1 DACs (AD5683R)
There are 11 DACs on the DAT:

 - 8 local LArASIC DACs
 - 1 common P/N pair of DACs for the ColdADCs
 - 1 common LArASIC DAC

The DACs will output a constant voltage once programmed. To create the test pulse, the test pulse generator (see section 2.5.2) will toggle switches on the DAT between the DAT constant voltage (or another source) and ground or another constant voltage. 
To calculate the appropriate 16-bit integer for a desired voltage value: Data_int = Voltage*65536/2.5. The 2.5 value is from an internal voltage reference. 

#### Programming a DAC to output a set voltage:
1.   **If the AD5683R is local to a particular LArASIC**, write the LArASIC's socket number to SOCKET_SEL.
2. Write the MSB of the calculated 16-bit integer to the appropriate data register (see the table below).
3. Write the LSB of the integer to the appropriate data register.
4. Write the appropriate strobe value to the appropriate strobe register.
5. Write 0x0 to the strobe register.

See for an example: [dat_set_dac](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/dat_util.cc#L198). 

| DAC | MSB data register | LSB data register | Strobe register | Strobe value
|--|--|--|--|--|
| Local LArASIC | FE_DAC_TP_DATA_MSB | FE_DAC_TP_DATA_LSB | FE_DAC_TP_SET | 0x1 << [LArASIC socket #]
| ColdADC (positive) | DAC_ADC_P_DATA_MSB | DAC_ADC_P_DATA_LSB | DAC_OTHER_SET | 0x1
| ColdADC (negative) | DAC_ADC_N_DATA_MSB | DAC_ADC_N_DATA_LSB | DAC_OTHER_SET | 0x2
| Common LArASIC | DAC_TP_DATA_MSB | DAC_TP_DATA_LSB | DAC_OTHER_SET | 0x4

See also: [AD5683R datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/ad5683r_5682r_5681r_5683.pdf).
### 2.5.2 FPGA test pulse generator


## 2.6 Analog muxes/demuxes and switches

### 2.4.2 Selecting a voltage to read [edit]
The analog muxes [which control the output to the ADCs] are in turn controlled by registers CD_AMON_SEL, ADC_FE_TEST_SEL, ADC_TEST_SEL_INHIBIT, FE_TEST_SEL_INHIBIT; "inhibit" signals turn the mux off entirely. The signals in ADC_FE_TEST_SEL control multiple types of muxes: bits 2:0 control control the 8 ColdADCs' muxes and bits 6:4 control the 8 LArASICs' muxes as well as the common mux that supplies the voltage FE_COMMON_DAC to the LArASICs' muxes (the fact that the local & common FE muxes share select lines is an error and will be fixed in later DAT revisions). 

[MUX_NAME]_CSC is the most significant bit in each CSC/CSB/CSA group of bits, as is the mux datasheet convention.

Todo fix and make simpler: in terms of integers written to registers

**COLDATA muxes:** Control register CD_AMON_SEL
| Select | Output | Description
|--:|--|:--|
| 0 | GND |
| 1 | CD_VCEXT | ?
| 2 | CD_LOCK | Interface_LOCK (equal to COLDATA register 0x23, bit 6)
| 3 | CD_ATO | Analog Test Output (see COLDATA register 0x43)
| 4 | CD_VDDIO | See INA226 COLDATA table
| 5 | CD_VDDA | ..
| 6 | CD_VDDCORE | ..
| 7 | CD_VDDD | ..
Select = CD[1/2]_AMON_CSC & CD[1/2]_AMON_CSB & CD[1/2]_AMON_CSA
Inhibit = CD[1/2]_AMON_INH
(Voltage info source: COLDATA datasheet, "Non-Writable Registers", "PLL Control Registers")

**ColdADC muxes:** Control register ADC_FE_TEST_SEL bits 2:0, ADC_TEST_SEL_INHIBIT (bit 0 inhibits ColdADC 1's MonADC, etc.)
| Select | Output | Description
|--:|--|:--|
| 0 | VOLTAGE_MONITOR_MUX | Internal voltage monitor (see ADC register 0xAF)
| 1 | CURRENT_MONITOR_MUX | Internal current monitor (ADC register 0xAF)
| 2 | VREFP | ADC positive reference voltage (1.95 V)
| 3 | VREFN | ADC negative reference voltage (0.45 V)
| 4 | VCMI | Common-mode input voltage (0.9 V)
| 5 | VCMO | ADC Core Common-mode voltage (1.2 V)
| 6 | AUX_ISINK_MUX | (a.k.a. aux 2) Reference current sink monitor (ADC register 0x95)
| 7 | AUX_ISOURCE_MUX | (a.k.a. aux 3) Reference current source monitor (ADC registers 0x94, 0x95)
Select = ADC_TEST_CSC & ADC_TEST_CSB & ADC_TEST_CSA
(Voltage info sources: ColdADC datasheet, "Monitor Output Configuration", Table 3, "Bandgap Reference Configuration")


**LArASIC muxes:** Control register ADC_FE_TEST_SEL bits 6:4, FE_TEST_SEL_INHIBIT (bit 0 inhibits LArASIC 1's MonADC, etc.)
| Select | Output | Description
|--:|--|:--|
| 0 | GND |
| 1 | Ext_Test | Local SMA port
| 2 | DAC | Output of local DAC
| 3 | FE_COMMON_DAC | Output of common mux
| 4 | VBGR | Bandgap reference monitor, ~1.18V at room temp
| 5 | To_AmpADC (Disconnected by default) | Input to amp preceding the LArASIC ADC
| 6 | GND | 
| 7 | AUX_VOLTAGE_MUX | From the corresponding ColdADC, (a.k.a. aux 1) reference voltage monitor (see ADC registers 0x94, 0x95)
Select = FE_TEST_CSC & FE_TEST_CSB & FE_TEST_CSA
(Voltage info sources: LArASIC datasheet, table 5; ColdADC datasheet, "Bandgap Reference Configuration")

See also: [SN74LV4051AD Analog mux datasheet](https://www.ti.com/lit/ds/symlink/sn74lv4051a.pdf), 

## 2.7 ADC Ring Oscillator counter


## 2.8 Clocks, PLLs, etc.
[CLK_64MHZ_SYS_P comes from WIB]
[CLK_DAQ_P is from onboard oscillator, not currently used]
### 2.8.1 PLLs
### 2.8.2 Reset manager
# Appendix: DAT Register Map
**Bolded** registers are read-only, *italicized* registers or signals are associated with a SOCKET_SEL mux or demux. A signal's bits are 7:0 unless noted otherwise. 

See also: [dat_util.h](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/dat_util.h), [toplevel VHDL file](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/DUNE_DAT_FPGA_V2B/SRC/DUNE_DAT_FPGA.vhd).
[Todo add descriptions]
| Reg # | Register name |Bit(s) |  Signal name (in toplevel VHDL file)|  Description  |
|--:|:--:|:--:|:--|:--|
| 1 | CD_CONFIG | 0 |  CD_SEL |  0 selects COLDATA 1 as the I2C controller, 1 selects COLDATA 2 as the I2C controller. 
| 1 |  | 4 |  CD1_PAD_RESET |  Set this bit high to drive this COLDATA's PAD_RESET pin low.
| 1 |  | 5 | CD2_PAD_RESET |  
| 2 | **CD1_CONTROL** | 5:0 | CD1_CONTROL |  
| 3 | **CD2_CONTROL** | 5:0 | CD2_CONTROL | 
| 4 | SOCKET_SEL | 2:0 | SOCKET_RDOUT_SEL | Socket select |
| 5 | INA226_REG_ADDR |  | I2C_ADDRESS | INA226 register address |
| 6 | INA226_DEVICE_ADDR | 6:0 | I2C_DEV_ADDR | INA226 device I2C address |
| 7 | INA226_NUM_BYTES | 3:0 | I2C_NUM_BYTES |  |
| 8 | INA226_DIN_MSB | | I2C_DIN | INA226 data in |
| 9 | INA226_DIN_LSB | |  |  |
| 10 | INA226_STRB | 0 | I2C_WR_STRB_S1 | COLDATA 1 INA226 write strobe |
| 10 |  | 1 | I2C_RD_STRB_S1 |  COLDATA 1 INA226 read strobe
| 10 |  | 2 | I2C_WR_STRB_S2 | COLDATA 2 INA226 write strobe |
| 10 |  | 3 | I2C_RD_STRB_S2 | COLDATA 2 INA226 read strobe |
| 10 |  | 4 | *I2C_WR_STRB_FE* | LArASIC INA226 write strobe |
| 10 |  | 5 | *I2C_RD_STRB_FE* | LArASIC INA226 read strobe |
| 11 | **INA226_CD1_DOUT_MSB** |  | I2C_DOUT_S1 | COLDATA 1 INA226 output data
| 12 | **INA226_CD1_DOUT_LSB** |  |  | 
| 13 | **INA226_CD2_DOUT_MSB** |  | I2C_DOUT_S2 | COLDATA 2 INA226 output data
| 14 | **INA226_CD2_DOUT_LSB** |  |  | 
| 15 | ***INA226_FE_DOUT_MSB*** |  | *I2C_DOUT_FE* | LArASIC INA226 output data
| 16 | ***INA226_FE_DOUT_LSB*** |  |  | 
| 17 | MONADC_START | 0 | cots_adc_start |  Monitoring ADCs start
| 18 | **CD1_MONADC_DATA_LSB** |  | CD1_MonADC_data | COLDATA 1 Monitoring ADC data
| 19 | **CD1_MONADC_DATA_MSB_BUSY** | 3:0 |  | 
| 19 |  | 7 | CD1_MonADC_busy | COLDATA 1 Monitoring ADC busy flag
| 20 | **CD2_MONADC_DATA_LSB** |  | CD2_MonADC_data | COLDATA 2 Monitoring ADC data
| 21 | **CD2_MONADC_DATA_MSB_BUSY** | 3:0 |  | 
| 21 |  | 7 | CD2_MonADC_busy | COLDATA 2 Monitoring ADC busy flag
| 22 | ***ADC_MONADC_DATA_LSB*** |  | *ADC_MonADC_data* | ColdADC Monitoring ADC data
| 23 | ***ADC_MONADC_DATA_MSB_BUSY*** | 3:0 |  | 
| 23 |  | 7 | *ADC_MonADC_busy* | ColdADC Monitoring ADC busy flag
| 24 | ***FE_MONADC_DATA_LSB*** |  | *FE_MonADC_data* | LArASIC Monitoring ADC data
| 25 | ***FE_MONADC_DATA_MSB_BUSY*** | 3:0 |  | 
| 25 |  | 7 | *FE_MonADC_busy* | LArASIC Monitoring ADC busy flag
| 26 | CD_AMON_SEL | 0 | CD1_AMON_CSA |  |
| 26 |  | 1 | CD1_AMON_CSB |  |
| 26 |  | 2 | CD1_AMON_CSC |  |
| 26 |  | 3 | CD1_AMON_INH |  |
| 26 |  | 4 | CD2_AMON_CSA |  |
| 26 |  | 5 | CD2_AMON_CSB |  |
| 26 |  | 6 | CD2_AMON_CSC |  |
| 26 |  | 7 | CD2_AMON_INH |  |
| 27 | ADC_FE_TEST_SEL| 0 | ADC_TEST_CSA |  |
| 27 | | 1 | ADC_TEST_CSB |  |
| 27 | | 2 | ADC_TEST_CSC |  |
| 27 | | 4 | FE_TEST_CSA |  |
| 27 | | 5 | FE_TEST_CSB |  |
| 27 | | 6 | FE_TEST_CSC |  |
| 27 | | 7 | FE_TEST_INH |  |
| 28 | ADC_TEST_SEL_INHIBIT |  | ADC_TEST_INH |  |
| 29 | FE_TEST_SEL_INHIBIT |  | FE_TEST_INH_ARR |  |
| 30 | FE_IN_TST_SEL_LSB |  | FE_IN_TST_SEL |  |
| 31 | FE_IN_TST_SEL_MSB |  |  |  |
| 32 | FE_CALI_CS |  | FE_CALI_CS |  |
| 33 | ADC_TST_SEL |  | ADC_TST_SEL |  |
| 34 | ADC_SRC_CS_P_LSB |  |  |  | Unused in first DAT version due to mis-assigned signals
| 35 | ADC_SRC_CS_P_MSB |  |  |  | 
| 36 | ADC_PN_TST_SEL| 0 | ADC_P_TST_CSA |  |
| 36 | | 1 | ADC_P_TST_CSB |  |
| 36 | | 2 | ADC_P_TST_CSC |  |
| 36 | | 3 | ADC_P_TST_AMON_INH |  |
| 36 | | 4 | ADC_N_TST_CSA |  |
| 36 | | 5 | ADC_N_TST_CSB |  |
| 36 | | 6 | ADC_N_TST_CSC |  |
| 36 | | 7 | ADC_N_TST_AMON_INH |  |
| 37 | ADC_TEST_IN_SEL | 0 | ADC_TEST_IN_SEL |  |
| 38 | EXT_PULSE_CNTL | 0 | EXT_PULSE_CNTL |  |
| 39 | FE_DAC_TP_SET |  | FE_DAC_TP_set |  |
| 40 | *FE_DAC_TP_DATA_LSB* |  | *FE_DAC_TP_data* |  |
| 41 | *FE_DAC_TP_DATA_MSB* |  |  |  |
| 42 | DAC_OTHER_SET | 0 |  | DAC_ADC_P start |
| 42 |  | 1 |  | DAC_ADC_N start |
| 42 |  | 2 |  | DAC_TP start |
| 43 | DAC_ADC_P_DATA_LSB |  | DAC_ADC_P_data |  |
| 44 | DAC_ADC_P_DATA_MSB |  |  |  |
| 45 | DAC_ADC_N_DATA_LSB |  | DAC_ADC_N_data |  |
| 46 | DAC_ADC_N_DATA_MSB |  |  |  |
| 47 | DAC_TP_DATA_LSB | | DAC_TP_data |  |
| 48 | DAC_TP_DATA_MSB |  |  |  |
| 49 | **ADC_RING_OSC_COUNT_B0** |  | ro_cnt |
| 50 | **ADC_RING_OSC_COUNT_B1** |  |  | 
| 51 | **ADC_RING_OSC_COUNT_B2** |  |  | 
| 52 | **ADC_RING_OSC_COUNT_B3** |  |  | 
| 53 | ADC_POR_NAND |  | ADC_POR_NAND |  |
| 54 | ADC_CHIP_ACTIVE |  | ADC_CHIP_ACTIVE |  |
| 55 | TEST_PULSE_EN | 0 | FPGA_TP_EN |  |
| 55 |  | 1 | ASIC_TP_EN |  |
| 55 |  | 2 | INT_TP_EN |  |
| 55 |  | 3 | EXT_TP_EN |  |
| 56 | TEST_PULSE_SOCKET_EN |  | TP_SOCKET_EN |  |
| 57 | TEST_PULSE_WIDTH_LSB |  | Test_PULSE_WIDTH |  |
| 58 | TEST_PULSE_WIDTH_MSB |  |  |  |
| 59 | TEST_PULSE_DELAY |  | TP_DLY |  |
| 60 | TEST_PULSE_PERIOD_LSB |  | TP_PERIOD |  |
| 61 | TEST_PULSE_PERIOD_MSB |  |  |  |




