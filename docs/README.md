# 1. Introduction
The DAT was created in order to:
 - Test 1 FEMB's worth of ASICs (2 COLDATAs, 8 ColdADCs, 8 LArASICs) at once
	 - This includes having programmable external pulses that can be injected into either the LArASICs or the ColdADCs.
 - Have a testing device fully compatible with current WIB production firmware, requiring only a superset of the current WIB software for QC tests
 - Enable full monitoring of ASIC power rails and I/O functions

## 1.1. GitHub
The source code for the DAT firmware is located in the DUNE_DAT_FPGA_V2B subfolder of this repository: https://github.com/jdonohue-bnl/bnl-dat-fw-sw.
In addition to the firmware, the repository contains associated software ([dat_sw](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/tree/main/dat_sw)) meant to be used on the WIB to control and communicate with the DAT, and a README giving quick-start instructions.
## 1.2 FPGA info
The DAT FPGA is an Altera Cyclone IV. Development on it has been with Quartus Prime 17.1, and it can be programmed with Quartus Programmer. The resulting bitfiles from a compilation always go in the DUNE_DAT_FPGA_V2B/output_files folder. Besides the latest compilated bitfiles, the output_files folder on Github also contains a .pof file called DUNE_DAT_FPGA_femb.pof with the base functionality allowing the DAT to function like an FEMB.
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
All of the entities used in the DAT firmware (besides the toplevel file) were copied from the DUT  (its predecessor) and at most slightly altered for device compatibility or timing. 

![Block diagram of DAT FPGA firmware](https://raw.githubusercontent.com/jdonohue-bnl/bnl-dat-fw-sw/main/docs/DAT%20diagram%20expanded.png)


## 2.1 I2C target
Allows the WIB to read and write the DAT registers in the same way that it reads and writes other chips on the board. The DAT FPGA has I2C address 0xC. 
### Instructions for use:
 - Use [cdpeek/cdpoke](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/wib_util.cc#L78) [femb_idx = the connector the DAT is plugged into - goes from 0 on the right to 3; **chip_addr = 0xC**, reg_page = 0, reg_addr = desired register number (see map)] or a wrapped version thereof.

See the appendix for the map of DAT registers.

## 2.2 Socket selection

To reduce the total number of registers, some signals which have 8 "copies" (because of the nature of the DAT) are the inputs to a mux controlled by the register SOCKET_SEL. The output of that mux goes to a read-only register. Likewise, for writeable signals (e.g. INA226 read strobes), the register goes to a demux and SOCKET_SEL determines which of the 8 signals (e.g. LArASIC 2's INA226 controller's read strobe) receives the data (by default they are assigned 0x0). 
SOCKET_SEL is a 3-bit signal from 0x0 to 0x7: regardless of the value of CD_SEL (which changes the I2C addresses of the ColdADCs), the leftmost LArASIC/ColdADC's (when viewing the board with the COLDATAs at the top) associated signals will be selected with value 0x0 and the rightmost will be selected with the value 0x7. 

**Registers that utilize SOCKET_SEL**:
Writeable registers:

 - INA226_STRB

Read-only registers:

 - INA226_FE_DOUT_MSB, INA226_FE_DOUT_LSB
 - ADC_MONADC_DATA_LSB, ADC_MONADC_DATA_MSB_BUSY
 - FE_MONADC_DATA_LSB, FE_MONADC_DATA_MSB_BUSY
 - ADC_RING_OSC_COUNT_B0, ADC_RING_OSC_COUNT_B1, ADC_RING_OSC_COUNT_B2, ADC_RING_OSC_COUNT_B3

Note: in the DAT schematic and in the toplevel VHDL file, the leftmost LArASIC/ColdADC and their associated chips are referred to as FE1/ADC1 despite being selected with SOCKET_SEL value 0x0, FE8/ADC8 with 0x7, etc.

See also: [toplevel DAT file](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/DUNE_DAT_FPGA_V2B/SRC/DUNE_DAT_FPGA.vhd#L697).

## 2.3 Power monitors (INA226)
All chips on the board have power rails that need to be monitored. Each COLDATA has 5 INA226s on one I2C bus (CD1/2_FPGA_CD_INA_SCL/SDA) and each LArASIC/ColdADC pair has 7 INA226s on its own I2C bus (FE_INA_SCL/SDA[0-7]). Each bus is managed by an I2C controller instance, whose inputs (device address to contact, register within the device, number of bytes, data to write, and read and write strobes) are controlled by DAT registers, and each I2C controller has two assigned registers for the 16-bit result of a read operation.

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

| LArASIC/ColdADC Power rail name | Address |  Voltage | Description
|--|--|--|--|
| FE: |
| VDD | 0x40 | 1.8 V | Analog supply
| VDDO | 0x41 | 1.8 V | Analog supply for output buffer
| VPPP | 0x42 | 1.8 V | (a.k.a. VDDP) Analog supply for the 1st stage of the charge amplifiers |
| ADC: |
| VDDA2P5 | 0x43 | 2.25 V (+/- 5%) | Analog power
| VDDD1P2 | 0x44 | 1.1 V (+/- 5%), max voltage is nominal +10% | Digital logic power
| VDDD2P5 | 0x45 | 2.25 V (+/- 5%) | Digital ColdADC power
| VDDIO | 0x46 | 2.25 V | ESD ring/CMOS I/O power

(Rail info sources: LArASIC datasheet, table 5; ColdADC datasheet, table 1)

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

| I2C number of bytes | Writing | Reading |
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

Note: The I2c controller entity writes and reads bytes in the reverse order as intended, which is not made obvious at all in the firmware (to be fixed?). This is why unlike the other types of controllers, the I2c controllers have MSB of input or output data listed before LSB in the official register mapping (while appearing to be LSB-first in the firmware).

See also: the INA226 I2c controller source code [I2c_master.vhd](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/DUNE_DAT_FPGA_V2B/SRC/I2c_master.vhd), [dat_util.h](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/dat_util.h) for INA226 internal register mapping, [INA226 datasheet](https://www.ti.com/lit/ds/symlink/ina226.pdf).

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

See also: [AD7274 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/AD7273_7274.pdf), the SPI controller source code [COTS_AD7274.vhd](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/DUNE_DAT_FPGA_V2B/SRC/COTS_AD7274.vhd).
## 2.5 Test pulse generation
A central function of the DAT is the ability to configure external test pulses and send them to either the LArASIC or directly into the ColdADC in order to calibrate them (as opposed to just using the LArASIC's internal pulse generator). To create the test pulse, the test pulse generator toggles switches on the DAT between the DAC constant voltage (or another source of constant voltage) and ground or another constant voltage.

### 2.5.1 DACs (AD5683R)
There are 11 DACs on the DAT:

 - 8 local LArASIC DACs
 - A common P/N pair of DACs for the ColdADCs [currently disconnected from direct register control, connected to DAC ramp - see section 2.5.2]
 - 1 common LArASIC DAC

The DACs will output a constant voltage once programmed.  
To calculate the appropriate 16-bit integer for a desired voltage value: 

    Data_int = Voltage*65536/2.5 

The 2.5V value is from an internal voltage reference. 

#### Programming a DAC to output a set voltage:
1. Write the MSB of the calculated 16-bit integer to the appropriate data register (see the table below).
2. Write the LSB of the integer to the appropriate data register.
3. Write the appropriate strobe value to the appropriate strobe register.
4. Write 0x0 to the strobe register.

See for an example: [dat_set_dac](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/dat_util.cc#L198). 

| DAC | MSB data register | LSB data register | Strobe register | Strobe value
|--|--|--|--|--|
| Local LArASIC | FE_DAC_TP_DATA_MSB | FE_DAC_TP_DATA_LSB | FE_DAC_TP_SET | 0x1 << [LArASIC socket #]
| ColdADC (positive) | DAC_ADC_P_DATA_MSB [disconnected] | DAC_ADC_P_DATA_LSB [disconnected] | DAC_OTHER_SET [disconnected] | 0x1 [disconnected]
| ColdADC (negative) | DAC_ADC_N_DATA_MSB [disconnected] | DAC_ADC_N_DATA_LSB [disconnected] | DAC_OTHER_SET [disconnected] | 0x2 [disconnected]
| Common LArASIC | DAC_TP_DATA_MSB | DAC_TP_DATA_LSB | DAC_OTHER_SET | 0x4
See also: [AD5683R datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/ad5683r_5682r_5681r_5683.pdf), SPI controller source code [DAC8411.vhd](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/DUNE_DAT_FPGA_V2B/SRC/DAC8411.vhd).

### 2.5.2 ColdADC DAC ramp
In order to test the ColdADCs' functionality, a firmware entity was designed to program the ColdADC common DACs with every possible voltage in their range (0 to 2.5V, 2^16 possible voltages) and compare each nominal voltage step with the voltage measured by the ADCs. This results in a sawtooth-type output waveform. At present, the DAC_ADC_P and DAC_ADC_N SPI controllers' input ports are connected to this counter instead of directly to the registers;  DAC_ADC_P is programmed with the ramp voltage and DAC_ADC_N is set to 0 V. 

The length of time the DAC output voltage stays at each step in 25MHz clock ticks (and therefore the "slope" of the ramp) is configurable via the DAC_ADC_RAMP_DELAY register. This takes into account the number of clock cycles it takes to program the DAC, so programmed delay values below 0x1C will default to 0x1C. Note that this does *not* take into account the amount of time it takes the DAC output voltage to settle (5-7 us). If this module ends up being used, the delay may need to be either allocated more than 8 bits or have the delay increment in more than one 25MHz clock tick.

#### Setting up the ColdADC DAC ramp generator and connecting it to all ColdADC input channels:
1. Set ADC_PN_TST_SEL to 0x33 to select the positive and negative ColdADC DAC voltage inputs to the ColdADC positive and negative muxes, respectively. 
2. Set ADC_TEST_IN_SEL to 0x0 to connect the ColdADC positive and negative mux outputs to ADC_P and ADC_N, respectively.
3. Set ADC_SRC_CS_P_MSB and ADC_SRC_CS_P_LSB both to 0x0 to connect all ColdADC positive and negative input channels to ADC_P and ADC_N, respectively.
4. Divide the amount of time you wish the DAC to spend on each "step" by 40 ns (the minimum amount of time is 0x1C = 1.12 us, the maximum amount is 0xff = 10.2 us), and write the resulting integer to DAC_ADC_RAMP_DELAY.
5. Write 0x1 to DAC_ADC_RAMP_EN to turn on the ramp generator.

See for an example: [dat_test.py](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/dat_test.py).

### 2.5.3 FPGA test pulse generator
To calculate what value to program for a desired test pulse frequency, first convert the frequency to a period in microseconds (maximum ~5.12 ms or 195 Hz). Then,

    Tp_period ~= Period_us / 0.07814 us
Likewise, the width parameter can be determined from the desired width of the pulse (max 1.04 ms):

    Tp_width = Width_ns / 16 ns

An additional parameter TEST_PULSE_DELAY allows you to delay the test pulse signal in case you want it to appear in a particular place in a sampling window. See the BNL Cold ASIC User Guide linked below for more information.

Currently one instance of the test pulse generator exists in the firmware, and its output is connected to FE_INS_PLS_CS (individually gated with the register TEST_PULSE_SOCKET_EN), which switches between PLS_FE and an unpopulated resistor that normally connects to ground. 

#### Generating a local DAC pulse for LArASIC X (0-7):
1. Set the voltage of the corresponding DAC (see the next section) to the desired amplitude of the pulse.
2. Set the top 4 bits of register ADC_FE_TEST_SEL to 0x2 in order to connect the DAC output to the mux output FE_TEST.
3. Clear bit X of FE_CALI_CS to connect FE_TEST to PLS_FE.
4. Set FE_IN_TST_SEL_MSB and FE_IN_TST_SEL_LSB to 0x0 to connect all input channels of all LArASICs to (each) FE_INS_PLS.
5. Write the LSB of the period (see equation above) to TEST_PULSE_PERIOD_LSB.
6. Write the MSB of the period to TEST_PULSE_PERIOD_MSB.
7. Write the LSB of the width to TEST_PULSE_WIDTH_LSB.
8. Write the MSB of the width TEST_PULSE_WIDTH_MSB.
9. Enable bit X of TEST_PULSE_SOCKET_EN to enable a pulse output for this socket.
10. Finally, turn on the pulse generator by writing 0x6 to TEST_PULSE_EN.

See for an example: [dat_set_pulse](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/dat_util.cc#L239).

See also: [SBND_TEST_PULSE.vhd](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/DUNE_DAT_FPGA_V2B/SRC/SBND_TST_PULSE.vhd), [BNL Cold ASIC User Guide](https://brookhavenlab-my.sharepoint.com/personal/jdonohue_bnl_gov/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fjdonohue%5Fbnl%5Fgov%2FDocuments%2FDocuments%2FEric%20example%20documentation%2FASIC%5FUser%5FGuide%20%281%29%20%281%29%2Epdf&parent=%2Fpersonal%2Fjdonohue%5Fbnl%5Fgov%2FDocuments%2FDocuments%2FEric%20example%20documentation&ga=1) section 5, which also uses SBND_TEST_PULSE.vhd.

## 2.6 Analog muxes/demuxes and switches

The analog signals going to LArASIC frontend & test inputs, LArASIC MonADCs, and ColdADC frontend & test inputs are selected via analog muxes and switches. They are re-illustrated together below.

[MUX_NAME]_CSC is the most significant bit in each CSC/CSB/CSA group of bits, as is the mux datasheet convention. The inhibit signal [MUX_NAME]_INH connects the mux output to ground.

In the first version of the DAT, the common LArASIC mux is assigned the same control signals as the local LArASIC muxes (other than the inhibit signals), in error.

![Block diagram of the interconnected switches and muxes on the DAT (first version).](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/docs/DAT%20mux%20diagram.png?raw=true)


### COLDATA MonADC mux:
| Select (CD[1/2]_AMON_CSC:CSA) | Output | Description
|--:|--|:--|
| 0 | GND |
| 1 | CD_VCEXT | ?
| 2 | CD_LOCK | Interface_LOCK (equal to COLDATA register 0x23, bit 6)
| 3 | CD_ATO | Analog Test Output (see COLDATA register 0x43)
| 4 | CD_VDDIO | See INA226 COLDATA table
| 5 | CD_VDDA | ..
| 6 | CD_VDDCORE | ..
| 7 | CD_VDDD | ..
(Voltage info source: COLDATA datasheet, sections "Non-Writable Registers" & "PLL Control Registers")

**COLDATA 1&2 mux outputs** based on CD_AMON_SEL register value:
| CD_AMON_SEL bit 7 | 6:4 | 3 | 2:0 | CD1 mux output | CD2 mux output |
|--:|--|--|--|--|--|
| X | X | 0 | 0 | GND | -
| X | X | 0 | 1 | VC_EXT | -
| X | X | 0 | 2 | CD_LOCK | -
| X | X | 0 | 3 | CD_ATO | -
| X | X | 0 | 4 | CD_VDDIO | -
| X | X | 0 | 5 | CD_VDDA | -
| X | X | 0 | 6 | CD_VDDCORE | -
| X | X | 0 | 7 | CD_VDDD | -
| X | X | 1 | X | GND | -
| 0 | 0 | X | X | - | GND
| 0 | 1 | X | X | - | VC_EXT
| 0 | 2 | X | X | - | CD_LOCK
| 0 | 3 | X | X | - | CD_ATO
| 0 | 4 | X | X | - | CD_VDDIO
| 0 | 5 | X | X | - | CD_VDDA
| 0 | 6 | X | X | - | CD_VDDCORE
| 0 | 7 | X | X | - | CD_VDDD
| 1 | 0 | X | X | - | GND





### ColdADC positive mux:
| Select (ADC_P_TST_CSC:CSA) | Output | Description
|--:|--|:--|
| 0 | GND |
| 1 | TST_PULSE_AMON | WIB-generated test pulse
| 2 | ADC_EXT_P | ColdADC positive SMA port
| 3 | DAC_OUT_P | Output of ColdADC positive DAC
| 4 | ADC_EXT_N | ColdADC negative SMA port
| 5 | DAC_OUT_N | Output of ColdADC negative DAC
| 6 | Open |
| 7 | Open |


### ColdADC negative mux:
| Select (ADC_N_TST_CSC:CSA) | Output | Description
|--:|--|:--|
| 0 | GND |
| 1 | TST_PULSE_AMON | WIB-generated test pulse
| 2 | ADC_EXT_N | ColdADC negative SMA port
| 3 | DAC_OUT_N | Output of ColdADC negative DAC
| 4 | ADC_EXT_P | ColdADC positive SMA port
| 5 | DAC_OUT_P | Output of ColdADC positive DAC
| 6 | Open |
| 7 | Open |

**ColdADC P&N mux outputs** based on ADC_PN_TST_SEL register value:
| ADC_PN_TST_SEL bit 7 | 6:4 | 3 | 2:0 | P mux output | N mux output |
|--:|--|--|--|--|--|
| X | X | 0 | 0 | GND | -
| X | X | 0 | 1 | TST_PULSE_AMON | -
| X | X | 0 | 2 | ADC_EXT_P | -
| X | X | 0 | 3 | DAC_OUT_P | -
| X | X | 0 | 4 | ADC_EXT_N | -
| X | X | 0 | 5 | DAC_OUT_N | -
| X | X | 0 | 6 | Open | -
| X | X | 0 | 7 | Open | -
| X | X | 1 | X | GND | -
| 0 | 0 | X | X | - | GND
| 0 | 1 | X | X | - | TST_PULSE_AMON
| 0 | 2 | X | X | - | ADC_EXT_N
| 0 | 3 | X | X | - | DAC_OUT_N
| 0 | 4 | X | X | - | ADC_EXT_P
| 0 | 5 | X | X | - | DAC_OUT_P
| 0 | 6 | X | X | - | Open
| 0 | 7 | X | X | - | Open
| 1 | X | X | X | - | GND

### ColdADC MonADC mux:
| Select (ADC_TEST_CSC:CSA) | Output | Description
|--:|--|:--|
| 0 | VOLTAGE_MONITOR_MUX | Internal voltage monitor (see ColdADC register 0xAF)
| 1 | CURRENT_MONITOR_MUX | Internal current monitor (ColdADC register 0xAF)
| 2 | VREFP | ColdADC positive reference voltage (1.95 V)
| 3 | VREFN | ColdADC negative reference voltage (0.45 V)
| 4 | VCMI | Common-mode input voltage (0.9 V)
| 5 | VCMO | ColdADC Core Common-mode voltage (1.2 V)
| 6 | AUX_ISINK_MUX | (a.k.a. aux 2) Reference current sink monitor (ColdADC register 0x95)
| 7 | AUX_ISOURCE_MUX | (a.k.a. aux 3) Reference current source monitor (ColdADC registers 0x94, 0x95)
(Voltage info sources: ColdADC datasheet, section "Monitor Output Configuration", table 3, & section "Bandgap Reference Configuration")

### LArASIC local mux:
| Select (FE_TEST_CSC:CSA)| Output | Description
|--:|--|:--|
| 0 | GND |
| 1 | Ext_Test | Local SMA port
| 2 | DAC | Output of local DAC
| 3 | FE_COMMON_DAC | Output of common mux (FE_TEST_CMN), buffered
| 4 | VBGR | Bandgap reference monitor, ~1.18V at room temp
| 5 | To_AmpADC (Disconnected by default) | Input to amp preceding the LArASIC ADC
| 6 | GND | 
| 7 | AUX_VOLTAGE_MUX | From the corresponding ColdADC, (a.k.a. aux 1) reference voltage monitor (see ColdADC registers 0x94, 0x95)
(Voltage info sources: LArASIC datasheet, table 5; ColdADC datasheet, "Bandgap Reference Configuration")

### LArASIC common mux:
| Select (FE_TEST_CSC:CSA)| Output | Description
|--:|--|:--|
| 0 | GND |
| 1 | DAC_OUT | Output of common DAC
| 2 | TST_PULSE_AMON | WIB-generated test pulse
| 3 | Ext_TEST | Common SMA port
| 4 | DAC_OUT_WIB_SWTCH | Output of a switch (controlled by EXT_PULSE_CNTL) that can connect to either DAC_OUT (see above) or GND
| 5 | P1.8V | [Ask Jack, used with diodes] 2.26V
| 6 | Open |
| 7 | Open |

**ColdADC & LArASIC (local & common) mux outputs** based on ADC_FE_TEST_SEL register value:
| ADC_FE_TEST_SEL bit 7 | 6:4 | 3 | 2:0 | ADC_TEST | FE_TEST | FE_TEST_CMN
|--:|--|--|--|--|--|--|
| X | X | X | 0 | VOLTAGE_MONITOR_MUX | - | -
| X | X | X | 1 | CURRENT_MONITOR_MUX | - | -
| X | X | X | 2 | VREFP | - | -
| X | X | X | 3 | VREFN | - | -
| X | X | X | 4 | VCMI | - | -
| X | X | X | 5 | VCMO | - | -
| X | X | X | 6 | AUX_ISINK_MUX | - | -
| X | X | X | 7 | AUX_ISOURCE_MUX | - | -
| 0 | 0 | X | X | - | GND | GND
| 0 | 1 | X | X | - | Ext_Test | DAC_OUT
| 0 | 2 | X | X | - | DAC | TST_PULSE_AMON
| 0 | 3 | X | X | - | FE_COMMON_DAC | Ext_TEST
| 0 | 4 | X | X | - | VBGR | DAC_OUT_WIB_SWTCH
| 0 | 5 | X | X | - | (Disconnected) To_AmpADC | P1.8V
| 0 | 6 | X | X | - | GND | Open
| 0 | 7 | X | X | - | AUX_VOLTAGE_MUX | Open
| 1 | X | X | X | - | - | GND






See also: [SN74LV4051AD Analog mux datasheet](https://www.ti.com/lit/ds/symlink/sn74lv4051a.pdf), 

## 2.7 ColdADC ring oscillator counter
Each ColdADC includes a process monitor "intended to help characterize the process variations associated with different wafers and different fabrication lots." This consists of a [ring oscillator circuit](https://en.wikipedia.org/wiki/Ring_oscillator), whose output is connected to the FPGA and is expected to have a certain frequency depending on its process corner and the temperature. The FPGA has 8 ring oscillator counting instances which continuously count the number of ring oscillator pulses. Each instance's 32-bit ro_cnt output represent the number of pulses it has counted in 1 second. 

### Accessing a ColdADC's ring oscillator count:
1. Write the ColdADC's 0-7 socket ID to SOCKET_SEL.
2. The 32-bit count is located across (from MSB to LSB) registers ADC_RING_OSC_COUNT_B3, ADC_RING_OSC_COUNT_B2, ADC_RING_OSC_COUNT_B1, & ADC_RING_OSC_COUNT_B0.

See also: ColdADC datasheet, sections "Process Monitor" & "Ring Oscillator Configuration"; [ring oscillator counter source code](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/DUNE_DAT_FPGA_V2B/SRC/coldadc_ro_cnt.vhd).

## 2.8 Clocks, PLLs, etc.

The DAT receives its primary clock, CLK_64MHZ_SYS_P, from the WIB over the data cable. This clock is the input to a few PLLs which generate the rest of its clocks.
The DAT also has an onboard oscillator, CLK_DAQ_P, available for future applications, but it's not currently used.


### 2.8.1 PLLs
CLK_64MHZ_SYS_P is the input to  phase-locked loops (DAT_PLL) which generate the clocks for the rest of the FPGA. Their frequencies are described in their names.

| PLL output | Instances using clock |
|--|--|
| CLK_100MHz | Ring oscillator counters (ro_inst[7:0]) |
| CLK_62_5MHz | I2c target (I2CSLAVE), Test pulse generator (TST_PULSE_GEN_inst) |
| CLK_50MHz | Reset manager (sys_rst_inst) |
| CLK_25MHz | AD7274 SPI controllers (CD1_MonADC_inst, CD2_MonADC_inst, ADC1_MonADC_inst, ADC_MonADC_inst[7:1], FE1_MonADC_inst, FE_MonADC_inst[7:1]), AD5683R SPI controllers (FE1_DAC_TP_inst, FE_DAC_TP_inst[7:1], DAC_ADC_P_inst, DAC_ADC_N_inst, DAC_TP_inst) |
| CLK_12_5MHz | INA226 I2C controllers (CD1_INA226_master, CD2_INA226_master, FE_INA226_master[7:0])  |


### 2.8.2 Reset manager
The sys_rst entity is a simple power-on-reset (POR) that resets the rest of the firmware upon power-up for 0x1000 50MHz clock ticks (20 us). There is also a manual reset port, reset_in, but it is not tied to a register at the moment.

See also: [reset manager source code](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/DUNE_DAT_FPGA_V2B/SRC/sys_rst.vhd).

# Appendix: DAT Register Map
**Bolded** registers are read-only, *italicized* registers or signals are associated with a SOCKET_SEL mux or demux. A signal's bits are 7:0 unless noted otherwise. 

See also: [dat_util.h](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/dat_util.h), [toplevel VHDL file](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/DUNE_DAT_FPGA_V2B/SRC/DUNE_DAT_FPGA.vhd).
[Todo add descriptions]
| Reg # | Register name |Bit(s) |  Signal name (in toplevel VHDL file)|  Description  |
|--:|:--:|:--:|:--|:--|
| 1 | CD_CONFIG | 0 |  CD_SEL |  0 selects COLDATA 1 as the I2C controller, 1 selects COLDATA 2 as the I2C controller. 
| 1 |  | 4 |  CD1_PAD_RESET |  Set this bit high to drive this COLDATA's PAD_RESET pin low.
| 1 |  | 5 | CD2_PAD_RESET |  
| 2 | **CD1_CONTROL** | 4:0 | CD1_CONTROL |  Each COLDATA outputs what is in register 0x26 on 5 pins which the FPGA reads and makes available in these registers. See COLDATA datasheet, "Control Registers - Main Page".
| 3 | **CD2_CONTROL** | 4:0 | CD2_CONTROL | 
| 4 | SOCKET_SEL | 2:0 | SOCKET_RDOUT_SEL | Socket select. See section 2.2. |
| 5 | INA226_REG_ADDR |  | I2C_ADDRESS | INA226 register address |
| 6 | INA226_DEVICE_ADDR | 6:0 | I2C_DEV_ADDR | INA226 device I2C address |
| 7 | INA226_NUM_BYTES | 3:0 | I2C_NUM_BYTES | See INA226 "I2C number of bytes" table. |
| 8 | INA226_DIN_MSB | | I2C_DIN | INA226 data in (to send to the device) |
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
| 26 | CD_AMON_SEL | 0 | CD1_AMON_CSA | Control signals for COLDATA 1 analog mux which outputs to its monitoring ADC. See CD_AMON table. Least significant bit of select signal. |
| 26 |  | 1 | CD1_AMON_CSB |  |
| 26 |  | 2 | CD1_AMON_CSC | Most significant bit of select signal. |
| 26 |  | 3 | CD1_AMON_INH | Inhibit the output of this mux. |
| 26 |  | 4 | CD2_AMON_CSA | COLDATA 2 analog mux. See CD_AMON table. Least significant bit of select signal. |
| 26 |  | 5 | CD2_AMON_CSB |  |
| 26 |  | 6 | CD2_AMON_CSC | Most significant bit of select signal. |
| 26 |  | 7 | CD2_AMON_INH | Inhibit the output of this mux. |
| 27 | ADC_FE_TEST_SEL| 0 | ADC_TEST_CSA |  Select signals for all ColdADC analog muxes which outputs to their monitoring ADCs. See ADC_TEST table. Least significant bit of select signal. |
| 27 | | 1 | ADC_TEST_CSB |  |
| 27 | | 2 | ADC_TEST_CSC | Most significant bit of select signal. |
| 27 | | 4 | FE_TEST_CSA | Select signals for all local LArASIC analog muxes, and also the common LArASIC mux (to be fixed) (**see section**). Least significant bit of select signal. |
| 27 | | 5 | FE_TEST_CSB |  |
| 27 | | 6 | FE_TEST_CSC | Most significant bit of select signal. |
| 27 | | 7 | FE_TEST_INH | Inhibits the output of the common LArASIC mux. |  
| 28 | ADC_TEST_SEL_INHIBIT |  | ADC_TEST_INH | Bit X of this register inhibits the output of the analog mux for ADC X's monitoring ADC. |
| 29 | FE_TEST_SEL_INHIBIT |  | FE_TEST_INH_ARR | Bit X of this register inhibits the output of the analog mux for LArASIC X. |
| 30 | FE_IN_TST_SEL_LSB |  | FE_IN_TST_SEL | Bit Y of this signal determines whether input channel Y of all LArASICs connects to that LArASIC's FE_INS_PLS signal (0) or its PLS_FE signal (1). |
| 31 | FE_IN_TST_SEL_MSB |  |  |  |
| 32 | FE_CALI_CS |  | FE_CALI_CS | Bit X of this signal determines whether the output of LArASIC X's local analog mux is connected to that LArASIC's PLS_FE signal (0) or FE_CALI (1). |
| 33 | ADC_TST_SEL |  | ADC_TST_SEL | Bit X controls the input to ColdADC X's ADC_TEST_P & ADC_TEST_N pins. 0 selects the local P&N SMA ports, 1 selects ADC_TEST_IN_P & ADC_TEST_IN_N (common).  |
| 34 | ADC_SRC_CS_P_LSB |  | ADC_SRC_CS_P | Bit Y of this signal determines whether input channels Y+ & Y- of all ColdADCs connect to the common ColdADC DAC P & N outputs (0) or to the corresponding LArASIC output channels Y+ & Y- (1). | 
| 35 | ADC_SRC_CS_P_MSB |  |  |  | 
| 36 | ADC_PN_TST_SEL| 0 | ADC_P_TST_CSA | Select signal for ColdADC's positive common analog mux. Least significant bit of select signal.|
| 36 | | 1 | ADC_P_TST_CSB |  |
| 36 | | 2 | ADC_P_TST_CSC | Most significant bit of select signal. |
| 36 | | 3 | ADC_P_TST_AMON_INH | Inhibits the output of the positive common ColdADC mux. |
| 36 | | 4 | ADC_N_TST_CSA | Select signal for ColdADC's negative common analog mux. Least significant bit of select signal. |
| 36 | | 5 | ADC_N_TST_CSB |  |
| 36 | | 6 | ADC_N_TST_CSC | Most significant bit of select signal. |
| 36 | | 7 | ADC_N_TST_AMON_INH | Inhibits the output of the negative common ColdADC mux. |
| 37 | ADC_TEST_IN_SEL | 0 | ADC_TEST_IN_SEL | Determines whether the outputs of the P&N common ColdADC muxes connect to ADC_[P&N] (0) or ADC_TEST_IN_[P&N] (1). |
| 38 | EXT_PULSE_CNTL | 0 | EXT_PULSE_CNTL | Goes out to WIB to control a WIB-generated test pulse (which comes back on TST_PULSE_AMON).  |
| 39 | FE_DAC_TP_SET |  | FE_DAC_TP_set | Bit X sets LArASIC X's DAC to the voltage encoded in  FE_DAC_TP_data (via its SPI controller).
| 40 | FE_DAC_TP_DATA_LSB |  | FE_DAC_TP_data | See section 2.5.1 for more info. |
| 41 | FE_DAC_TP_DATA_MSB |  |  |  |
| 42 | DAC_OTHER_SET | 0 |  | DAC_ADC_P start | Sets the ColdADCs' positive common DAC to the voltage encoded in DAC_ADC_P_data (via its SPI controller).
| 42 |  | 1 |  | DAC_ADC_N start | Sets the ColdADCs' negative common DAC to the voltage encoded in DAC_ADC_N_data (via its SPI controller).
| 42 |  | 2 |  | DAC_TP start | Sets the LArASICs' common DAC to the voltage encoded in DAC_TP_data (via its SPI controller).
| 43 | DAC_ADC_RAMP_DELAY |  | DAC_ADC_ramp_delay | Duration of each step on the ColdADC DAC ramp in 25 MHz clock ticks (40 ns). See section 2.5.2 for more info. |
| 44 | DAC_ADC_RAMP_EN | 0 | DAC_ADC_ramp_enable | Enables the ColdADC DAC ramp. |
| 45 | DAC_ADC_N_DATA_LSB |  | DAC_ADC_N_data | See section 2.5.1 for more info. |
| 46 | DAC_ADC_N_DATA_MSB |  |  |  |
| 47 | DAC_TP_DATA_LSB | | DAC_TP_data | See section 2.5.1 for more info. |
| 48 | DAC_TP_DATA_MSB |  |  |  |
| 49 | **ADC_RING_OSC_COUNT_B0** |  | ro_cnt | LSB of ring oscillator count
| 50 | **ADC_RING_OSC_COUNT_B1** |  |  | 
| 51 | **ADC_RING_OSC_COUNT_B2** |  |  | 
| 52 | **ADC_RING_OSC_COUNT_B3** |  |  | MSB of ring oscillator count
| 53 | ADC_POR_NAND |  | ADC_POR_NAND | Bit X sets ColdADC X's POR_NAND input. "The power on reset circuit is intended to initialize all control variables to their default values. The POR_NAND input will disable the power on reset circuit if tied to 0V" - ColdADC datasheet | 
| 54 | ADC_CHIP_ACTIVE |  | ADC_CHIP_ACTIVE | Bit X sets ColdADC X's CHIP_ACTIVE input. |
| 55 | TEST_PULSE_EN | 0 | FPGA_TP_EN | Enabling inputs to the test pulse generator. |
| 55 |  | 1 | ASIC_TP_EN | This bit must be enabled to get an output on Test_pulse. |
| 55 |  | 2 | INT_TP_EN | This bit must be enabled to get an output on Test_pulse. |
| 55 |  | 3 | EXT_TP_EN |  |
| 56 | TEST_PULSE_SOCKET_EN |  | TP_SOCKET_EN | Bit X will enable the test pulse generator to toggle LArASIC X's FE_INS_PLS_CS select signal, thus generating a pulse on FE_INS_PLS. |
| 57 | TEST_PULSE_WIDTH_LSB |  | Test_PULSE_WIDTH | See section 2.5.3 for more info. |
| 58 | TEST_PULSE_WIDTH_MSB |  |  |  |
| 59 | TEST_PULSE_DELAY |  | TP_DLY | See section 2.5.3 for more info. |
| 60 | TEST_PULSE_PERIOD_LSB |  | TP_PERIOD | See section 2.5.3 for more info. |
| 61 | TEST_PULSE_PERIOD_MSB |  |  |  |
| 62 | FE_CMN_SEL | 0 | FE_CMN_CSA | Select signal for LArASIC’s common analog mux (signal to be implemented in upcoming DAT revision). Least significant bit of select signal.|
| 62 |  | 1 | FE_CMN_CSB |  |
| 62 |  | 2 | FE_CMN_CSC | Most significant bit of select signal. |
| 62 |  | 3 | FE_CMN_INH | Inhibits the output of the common LArASIC mux. |
| 63 | MISC_U1_IO | 2:0 | MISC_U1_IO | Miscellaneous digital output pins that appear on header P3 pins 5:3 (see DAT schematic). |




