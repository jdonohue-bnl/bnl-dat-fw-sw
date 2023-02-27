# 1. Introduction
DAT functions include: []
## 1.1. GitHub
The source code for the DAT firmware is located in the DUNE_DAT_FPGA_V2B subfolder of this repository: https://github.com/jdonohue-bnl/bnl-dat-fw-sw
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

## 2.1 I2C slave
Allows the WIB to read and write the DAT registers in the same way that it reads and writes other chips on the board. The DAT FPGA has I2C address 0xC. 
### Instructions for use:
 - Use [cdpeek/cdpoke](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/wib_util.cc#L78) [femb_idx = the connector the DAT is plugged into - goes from 0 on the right to 3; **chip_addr = 0xC**, reg_page = 0, reg_addr = desired register number (see map)] or a wrapped version thereof.

See the appendix for the map of DAT registers.

## 2.2 Socket selection

## 2.3 Power monitors (INA226)
Each chip has several power rails that need to be monitored. Each COLDATA has 5 INA226s on one I2C bus (CD1_FPGA_CD_INA_SCL/SDA) and each LArASIC/ADC pair has 7 INA226s on one I2C bus (FE_INA_SCL/SDA[0-7]). Each bus is managed by an I2C master instance, whose inputs (device address to contact, register within the device, number of bytes, data to write, and read and write strobes) are controlled by DAT registers, and each I2C master has two assigned registers for the 16-bit result of a read operation.

[Note about I2c master not working correctly and me compensating for that]

The INA226 has a built-in current calculator so that you can program its calibration register ahead of time and then simply read the current register instead of reading the shunt register and then having to divide it by the shunt resistor value.

calib_value = 0.00512/(I_LSB*R)

...where I_LSB is your desired maximum possible current divided by 2^15 (in amps) and R = 0.1 ohms. See section 7.5 of the datasheet (linked below) for more details.
| COLDATA Power rail name | Address |
|--|--|
| CD_VDDA | 0x40 |
| FE_VDDA | 0x41 |
| CD_VDDCORE | 0x43* |
| CD_VDDD | 0x45 |
| CD_VDDIO | 0x44 |
*The CD_VDDCORE address was supposed to be 0x42 (A1 = GND, A0 = SDA), but the CD1_FPGA_CD_INA_SCL & CD1_FPGA_CD_INA_SDA FPGA pin assignments had to be swapped due to a schematic error and thus the chip's address changed.

| LArASIC/ADC Power rail name | Address |
|--|--|
| FE: |
| VDD | 0x40 |
| VDDO | 0x41 |
| VPPP [VDDP?] | 0x42 |
| ADC: |
| VDDA2P5 | 0x43 |
| VDDD2P5 | 0x45 |
| VDDIO | 0x46 |
| VDDD1P2 | 0x44 |

#### Strobe value to write to INA226_STRB:
| INA226 type | Write strobe | Read strobe
|--|--|--|
| CD1 | 0x1 | 0x2
| CD2 | 0x4 | 0x8
| FE (set SOCKET_SEL first) | 0x10 | 0x20

### To write an INA226 register:
1. **If the INA226 device is associated with the LArASIC or the ADC**, write the 0-7 number of the chip to SOCKET_SEL. 
2. Write the address of the device to INA226_DEVICE_ADDR (see the table above).
3. Write the number of bytes to write (0 to 2) to INA226_NUM_BYTES (see the table below).
4. Write the register to write to to INA226_REG_ADDR.
5. (If not doing a dummy write) Write the less significant byte of the data you wish to write to DAT_INA226_DIN_LSB.
6. (If not doing a dummy write or a 1 byte write) Write the more significant byte of the data you wish to write to DAT_INA226_DIN_MSB.
7. Write the appropriate write strobe to INA226_STRB (see the table above).
8. Write 0x0 to INA226_STRB.

See for an example: [datpower_poke](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/dat_util.cc#L8)
### To read an INA226 register:
1. **If the INA226 device is associated with the LArASIC or the ADC**, write the 0-7 number of the chip to SOCKET_SEL. 
2. Perform a 0 byte dummy write to the register you wish to read (see write instructions above). If the register is read-only (see the datasheet, section 7.6), it doesn't matter what you write.
3. Write the number of bytes to read to INA226_NUM_BYTES (the other I2C parameters should already be in the DAT registers from the dummy write).
4. Write the appropriate read strobe to INA226_STRB.
5. Write 0x0 to INA226_STRB.
6. Read the appropriate register (INA226_CD1_DOUT_MSB, INA226_CD2_DOUT_MSB, or INA226_FE_DOUT_MSB) for the more significant byte of the data.
7. Read the appropriate register (INA226_CD1_DOUT_LSB, INA226_CD2_DOUT_LSB, or INA226_FE_DOUT_LSB) for the less significant byte of the data.
8. If multiple reads in a row are required (e.g. checking for a flag), you don't need to repeat steps 1 through 3.

The I2C operations are fairly slow relative to the clock (12.5 MHz), but this shouldn't be noticeable when using the WIB to communicate with the DAT. 

See for an example: [datpower_peek](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/dat_util.cc#L38).

| I2C number of bytes| Writing | Reading |
|--:|--|--|
| 0 | Dummy write (only sets device's register pointer to prepare for a read)  | Reads 1 byte (half a register) |
| 1 | Writes 1 byte (half a register) and sets register pointer  | Reads 1 byte (half a register) |
| 2 | Writes 2 bytes (one register) and sets register pointer  | Reads 2 bytes (one register) |

### To get a voltage or current reading:
1. **If you want a current reading:** program INA226 register 0x5 with your calculated calibration value.
2. Program INA226 register 0x0 with the desired configuration value (see datasheet section 7.6.1). If not configured to shutdown mode, a conversion will begin immediately.
3. Keep checking INA226 register 0x6 until the ready flag (result & 0x8 = 0x8) appears. Depending on the configuration settings, this may take as many as 10-20 reads (from C). 
4. The bus voltage (voltage measured to ground) reading can now be accessed in INA226 register 0x2. Multiply the integer by 1.25 mV to get the actual reading.
5. The current reading can now be accessed in INA226 register 0x4. Multiply the integer by the I_LSB you used to calculate the calibration value to get the .

See for an example: [datpower_getvoltage](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/dat_util.cc#L70), [datpower_getcurrent](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/dat_util.cc#L113) 

See also: the entity source code [I2c_master.vhd](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/DUNE_DAT_FPGA_V2B/SRC/I2c_master.vhd), [dat_util.h](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/dat_util.h) for INA226 internal register map constants, [INA226 datasheet](https://www.ti.com/lit/ds/symlink/ina226.pdf).

## 2.4 Monitoring ADCs (AD7274)


## 2.5 Test pulse generation

### 2.5.1 DACs (DAC8411)

### 2.5.2 FPGA test pulse generator

## 2.7 ADC Ring Oscillator counter


# 3. Clocks, PLLs, etc.
[CLK_64MHZ_SYS_P comes from WIB]
[CLK_DAQ_P is from onboard oscillator, not currently used]
## 3.1 PLLs
## 3.2 Reset manager
# Appendix: DAT Register Map
See also: [dat_util.h](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/dat_sw/src/dat_util.h), [toplevel VHDL file](https://github.com/jdonohue-bnl/bnl-dat-fw-sw/blob/main/DUNE_DAT_FPGA_V2B/SRC/DUNE_DAT_FPGA.vhd)
[Todo add descriptions]
| Reg # | Reg. name |Bit(s) |  Signal name |  Read-only? | Description  |
|--:|:--:|:--:|:--|:--:|--|
| 1 | CD_CONFIG | 0 |  CD_SEL: COLDATA select |  | 0 selects COLDATA 1 as the I2C master, 1 selects COLDATA 2 as the I2C master. 
| 1 |  | 4 |  CD1_PAD_RESET: COLDATA 1 reset |  | Set this bit high to drive this COLDATA's PAD_RESET pin low.
| 1 |  | 5 | CD2_PAD_RESET: COLDATA 2 reset |  | 
| 2 | CD1_CONTROL | 5:0 | CD1_CONTROL | ✔ | 
| 3 | CD2_CONTROL | 5:0 | CD2_CONTROL | ✔ |
| 4 | SOCKET_SEL | 2:0 | Socket select |  |
| 5 | INA226_REG_ADDR |  | INA226 register address |  |
| 6 | INA226_DEVICE_ADDR | 6:0 | INA226 device I2C address |  |
| 7 | INA226_NUM_BYTES | 3:0 | INA226 device I2C address |  |
| 8 | INA226_DIN_MSB | | INA226 data in |  |
| 9 | INA226_DIN_LSB | |  |  |
| 10 | INA226_STRB | 0 | COLDATA 1 INA226 write strobe |  |
| 10 |  | 1 | COLDATA 1 INA226 read strobe |  |
| 10 |  | 2 | COLDATA 2 INA226 write strobe |  |
| 10 |  | 3 | COLDATA 2 INA226 read strobe |  |
| 10 |  | 4 | LArASIC INA226 write strobe |  |
| 10 |  | 5 | LArASIC INA226 read strobe |  |
| 11 | INA226_CD1_DOUT_MSB |  | COLDATA 1 INA226 output data | ✔ |
| 12 | INA226_CD1_DOUT_LSB |  |  | ✔ |
| 13 | INA226_CD2_DOUT_MSB |  | COLDATA 2 INA226 output data | ✔ |
| 14 | INA226_CD2_DOUT_LSB |  |  | ✔ |
| 15 | INA226_FE_DOUT_MSB |  | LArASIC INA226 output data | ✔ |
| 16 | INA226_FE_DOUT_LSB |  |  | ✔ |
| 17 | MONADC_START | 0 | Monitoring ADCs start |  |
| 18 | CD1_MONADC_DATA_LSB |  | COLDATA 1 Monitoring ADC data | ✔ |
| 19 | CD1_MONADC_DATA_MSB_BUSY | 3:0 |  | ✔ |
| 19 |  | 7 | COLDATA 1 Monitoring ADC busy flag | ✔ |
| 20 | CD1_MONADC_DATA_LSB |  | COLDATA 1 Monitoring ADC data | ✔ |
| 21 | CD2_MONADC_DATA_MSB_BUSY | 3:0 |  | ✔ |
| 21 |  | 7 | COLDATA 2 Monitoring ADC busy flag | ✔ |
| 22 | ADC_MONADC_DATA_LSB |  | ADC Monitoring ADC data | ✔ |
| 23 | ADC_MONADC_DATA_MSB_BUSY | 3:0 |  | ✔ |
| 23 |  | 7 | ADC Monitoring ADC busy flag | ✔ |
| 24 | FE_MONADC_DATA_LSB |  | LArASIC Monitoring ADC data | ✔ |
| 25 | FE_MONADC_DATA_MSB_BUSY | 3:0 |  | ✔ |
| 25 |  | 7 | FE Monitoring ADC busy flag | ✔ |
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
| 39 | FE_DAC_TP_SET |  | FE_DAC_TP_SET |  |
| 40 | FE_DAC_TP_DATA_LSB |  | FE_DAC_TP_data |  |
| 41 | FE_DAC_TP_DATA_MSB |  |  |  |
| 42 | DAC_OTHER_SET | 0 | DAC_ADC_P start |  |
| 42 |  | 1 | DAC_ADC_N start |  |
| 42 |  | 2 | DAC_TP start |  |
| 43 | DAC_ADC_P_DATA_LSB |  | DAC_ADC_P_data |  |
| 44 | DAC_ADC_P_DATA_MSB |  |  |  |
| 45 | DAC_ADC_N_DATA_LSB |  | DAC_ADC_N_data |  |
| 46 | DAC_ADC_N_DATA_MSB |  |  |  |
| 47 | DAC_TP_DATA_LSB | | DAC_TP_data |  |
| 48 | DAC_TP_DATA_MSB |  |  |  |
| 49 | ADC_RING_OSC_COUNT_B0 |  | ro_cnt | ✔ |
| 50 | ADC_RING_OSC_COUNT_B1 |  |  | ✔ |
| 51 | ADC_RING_OSC_COUNT_B2 |  |  | ✔ |
| 52 | ADC_RING_OSC_COUNT_B3 |  |  | ✔ |
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




