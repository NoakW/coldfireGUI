############################
# Read only database. Specific parameters describing the test object.
############################

parameterlist = [

    # "-" marks no test for parameter.
    # ADC and REV type test inside min/max limit test.
    # in_exp and DIG type is min read value should be equal to min limit and max read value should be equal to max limit test.
    # Counter type Max value should be higher than max limit:

    #        [Number]     [Name]     [min limit]    [max limit]    [Type]   [Type specific data]...

    # Blockmaster related messages

    0x01, "1v25_REF_BM", "1210", "1288", "ADC", "379",  # +/- 3%
    0x02, "3v3_BM", "3200", "3400", "ADC", "357",  # +/- 3%
    0x03, "3v3_FPGA_BM", "3200", "3400", "ADC", "358",  # +/- 3%
    0x04, "2v5_BM", "2375", "2625", "ADC", "359",  # +/- 5%
    0x05, "VBAT_MCU_BM_12V", "11000", "13000", "ADC2", "383",
    0x06, "1v8_FPGA_BM", "1746", "1854", "ADC", "360",  # +/- 3%
    0x07, "1v0_FPGA_BM", "950", "1050", "ADC", "361",  # +/- 50 mV
    0x08, "1v2_ETHSW_BM", "1164", "1236", "ADC", "362",  # +/- 3%

    0x09, "MB_REV_BM", "300", "500", "ADC", "363",
    # Expecting 410 mV for Blockmaster rev 1.x or calculate as: [REV(main number) * 400mV +/- 100 mV]
    0x0A, "5V_MB_BM", "4850", "5150", "ADC", "364",  # +/- 3%
    0x0B, "2v5_MB_BM", "2375", "2625", "ADC", "365",  # +/- 5%
    0x0C, "1v2_MB_BM", "1140", "1260", "ADC", "366",  # +/- 5%
    0x0D, "-3v3_MB_BM", "3200", "3400", "ADC", "367",
    # Expecting value 3300mV in Blockmaster because no negative voltage present
    0x0E, "3v3_MB_BM", "3135", "3465", "ADC", "368",  # +/- 5%
    0x0F, "3v8_MB_BM", "-", "-", "ADC", "380",  # Expecting small value in Blockmaster because no voltage connected

    0x10, "ID0_BM", "3250", "3300", "ADC", "384",  # Always HIGH in Blockmaster
    0x11, "ID1_BM", "3250", "3300", "ADC", "385",  # Always HIGH in Blockmaster
    0x12, "ID2_BM", "3250", "3300", "ADC", "387",  # Always HIGH in Blockmaster
    0x13, "VBAT_MCU_BM_24V", "23000", "25000", "ADC2", "383",
    # Second VBAT test to guide user to test both 12V and 24V input

    0x30, "MCU_FW_BM", "1610613012", "1610613012", "REV", "61",
    0x31, "FPGA_FW_BM", "64", "64", "REV", "61",
    0x32, "MCU_REV_BM", "-", "-", "REV", "61",
    0x33, "SYS_FW_BM", "8", "8", "REV", "61",

    0x40, "WHEEL1", "8", "12", "COUNTER", "500",
    0x41, "WHEEL2", "8", "12", "COUNTER", "501",

    0x50, "in_exp1", "-", "-", "IO_exp_8", "377", "0x20", "0x00", "1",
    0x51, "out_exp1", "-", "-", "IO_exp_8", "377", "0x20", "0x01", "1",
    0x52, "3V3_IO_EXP1", "0", "1", "in_exp1_0", "0", "IN",
    0x53, "AUX_OUT_EN", "0", "1", "in_exp1_1", "1", "OUT",
    0x54, "REMOTE_nON", "0", "1", "in_exp1_2", "2", "IN",
    0x55, "GNSS_RF_SEL", "0", "1", "in_exp1_3", "3", "OUT",
    0x56, "FAN_CONTROL", "0", "1", "in_exp1_4", "4", "OUT",
    0x57, "CH_CON", "0", "1", "in_exp1_5", "5", "OUT",
    0x58, "I2C_MUX_EN", "0", "1", "in_exp1_6", "6", "OUT",
    0x59, "I2C_MUX_SEL", "0", "1", "in_exp1_7", "7", "OUT",

    0x60, "in_exp2", "-", "-", "IO_exp_8", "377", "0x21", "0x00", "1",
    0x61, "out_exp2", "-", "-", "IO_exp_8", "377", "0x21", "0x01", "1",
    0x62, "AUX_OUT_ST1", "0", "1", "in_exp2_0", "0", "IN",
    0x63, "AUX_OUT_ST2", "0", "1", "in_exp2_1", "1", "IN",
    0x64, "AUX_IN_ST1", "0", "1", "in_exp2_2", "2", "IN",
    0x65, "AUX_IN_ST2", "0", "1", "in_exp2_3", "3", "IN",
    0x66, "RPi_GLOBAL_EN", "-", "-", "in_exp2_4", "4", "OUT",
    0x67, "RPi_RUN_PG", "-", "-", "in_exp2_5", "5", "IN",  # Power-good not tested
    0x68, "ETH_OPTO_nINT", "-", "-", "in_exp2_6", "6", "IN",  # Not tested since SFP-module not populated
    0x69, "ETH_OPTO_TX_DIS", "-", "-", "in_exp2_7", "7", "OUT",

    0x70, "in_exp3", "-", "-", "IO_exp_8", "377", "0x22", "0x00", "1",
    0x71, "out_exp3", "-", "-", "IO_exp_8", "377", "0x22", "0x01", "1",
    0x72, "RX1_EN", "0", "1", "in_exp3_0", "0", "OUT",
    0x73, "RX2_EN", "0", "1", "in_exp3_1", "1", "OUT",
    0x74, "RX3_EN", "0", "1", "in_exp3_2", "2", "OUT",
    0x75, "RX4_EN", "0", "1", "in_exp3_3", "3", "OUT",
    0x76, "RX5_EN", "0", "1", "in_exp3_4", "4", "OUT",
    0x77, "RX6_EN", "0", "1", "in_exp3_5", "5", "OUT",
    0x78, "RX7_EN", "0", "1", "in_exp3_6", "6", "OUT",
    0x79, "RX8_EN", "0", "1", "in_exp3_7", "7", "OUT",

    0x80, "in_exp4", "-", "-", "IO_exp_8", "377", "0x23", "0x00", "1",
    0x81, "out_exp4", "-", "-", "IO_exp_8", "377", "0x23", "0x01", "1",
    0x82, "RX9_EN", "0", "1", "in_exp4_0", "0", "OUT",
    0x83, "RX10_EN", "0", "1", "in_exp4_1", "1", "OUT",
    0x84, "RX11_EN", "0", "1", "in_exp4_2", "2", "OUT",
    0x85, "RX12_EN", "0", "1", "in_exp4_3", "3", "OUT",
    0x86, "RX13_EN", "0", "1", "in_exp4_4", "4", "OUT",
    0x87, "RX14_EN", "0", "1", "in_exp4_5", "5", "OUT",
    0x88, "RX15_EN", "0", "1", "in_exp4_6", "6", "OUT",
    0x89, "RX16_EN", "0", "1", "in_exp4_7", "7", "OUT",

    0x90, "in_exp5", "-", "-", "IO_exp_8", "377", "0x24", "0x00", "1",
    0x91, "out_exp5", "-", "-", "IO_exp_8", "377", "0x24", "0x01", "1",
    0x92, "OUT_ST1", "0", "1", "in_exp5_0", "0", "IN",
    0x93, "OUT_ST2", "-", "-", "in_exp5_1", "1", "IN",
    0x94, "OUT_ST3", "0", "1", "in_exp5_2", "2", "IN",
    0x95, "OUT_ST4", "-", "-", "in_exp5_3", "3", "IN",
    0x96, "OUT_ST5", "0", "1", "in_exp5_4", "4", "IN",
    0x97, "OUT_ST6", "-", "-", "in_exp5_5", "5", "IN",
    0x98, "OUT_ST7", "0", "1", "in_exp5_6", "6", "IN",
    0x99, "OUT_ST8", "-", "-", "in_exp5_7", "7", "IN",

    0xA0, "in_exp6", "-", "-", "IO_exp_8", "377", "0x25", "0x00", "1",
    0xA1, "out_exp6", "-", "-", "IO_exp_8", "377", "0x25", "0x01", "1",
    0xA2, "OUT_ST9", "0", "1", "in_exp6_0", "0", "IN",
    0xA3, "OUT_ST10", "-", "-", "in_exp6_1", "1", "IN",
    0xA4, "OUT_ST11", "0", "1", "in_exp6_2", "2", "IN",
    0xA5, "OUT_ST12", "-", "-", "in_exp6_3", "3", "IN",
    0xA6, "OUT_ST13", "0", "1", "in_exp6_4", "4", "IN",
    0xA7, "OUT_ST14", "-", "-", "in_exp6_5", "5", "IN",
    0xA8, "OUT_ST15", "0", "1", "in_exp6_6", "6", "IN",
    0xA9, "OUT_ST16", "-", "-", "in_exp6_7", "7", "IN",

    0xB0, "in_exp_led", "-", "-", "IO_exp_8", "377", "0x60", "0x00", "1",
    0xB1, "out_exp_led", "-", "-", "IO_exp_8", "377", "0x60", "0x01", "1",
    0xB2, "LED0", "-", "-", "in_exp_led_0", "0", "OUT",
    0xB3, "LED1", "0", "1", "in_exp_led_1", "1", "OUT",
    0xB4, "LED2", "0", "1", "in_exp_led_2", "2", "OUT",
    0xB5, "LED3", "0", "1", "in_exp_led_3", "3", "OUT",
    0xB6, "LED4", "0", "1", "in_exp_led_4", "4", "OUT",
    0xB7, "LED5", "0", "1", "in_exp_led_5", "5", "OUT",
    0xB8, "LED6", "0", "1", "in_exp_led_6", "6", "OUT",

    # Test board!!
    0xC0, "in_exp1_testbord_low", "-", "-", "IO_exp_8", "377", "0x74", "0x00", "1",
    0xC1, "out_exp1_testbord_low", "-", "-", "IO_exp_8", "377", "0x74", "0x02", "1",
    0xC2, "I2C_MUX_EN_TEST", "0", "1", "in_exp1_testbord_low_0", "0", "IN",
    0xC3, "I2C_MUX_SEL_TEST", "0", "1", "in_exp1_testbord_low_1", "1", "IN",
    0xC4, "CH_CON_TEST", "0", "1", "in_exp1_testbord_low_2", "2", "IN",
    0xC5, "LED0_TEST", "0", "1", "in_exp1_testbord_low_3", "3", "IN",
    0xC6, "LED1_TEST", "0", "1", "in_exp1_testbord_low_4", "4", "IN",
    0xC7, "AUX1_OUT_TEST", "0", "1", "in_exp1_testbord_low_5", "5", "IN",
    0xC8, "LED2_TEST", "0", "1", "in_exp1_testbord_low_6", "6", "IN",
    0xC9, "AUX2_OUT_TEST", "0", "1", "in_exp1_testbord_low_7", "7", "IN",

    0xD0, "in_exp1_testbord_high", "-", "-", "IO_exp_8", "377", "0x74", "0x01", "1",
    0xD1, "out_exp1_testbord_high", "-", "-", "IO_exp_8", "377", "0x74", "0x03", "1",
    0xD2, "ENC1_5V_TEST", "1", "1", "in_exp1_testbord_high_0", "0", "IN",  # ENC_5V is assumed to be always high
    0xD3, "ENC2_5V_TEST", "1", "1", "in_exp1_testbord_high_1", "1", "IN",  # ENC_5V is assumed to be always high
    0xD4, "LED3_TEST", "0", "1", "in_exp1_testbord_high_2", "2", "IN",
    0xD5, "SPARE_ETH_LED", "0", "1", "in_exp1_testbord_high_3", "3", "IN",  # SW_PORT5_LED_TEST ("SPARE" Ethernet port)
    0xD6, "MAIN_ETH_LED", "0", "1", "in_exp1_testbord_high_4", "4", "IN",  # SW_PORT1_LED_TEST ("MAIN" Ethernet port)
    0xD7, "SPARE_LED_2", "-", "-", "in_exp1_testbord_high_5", "5", "IN",
    # SPARE_LED_2 not connected in Blockmaster, therefore not tested
    0xD8, "LED4_TEST", "0", "1", "in_exp1_testbord_high_6", "6", "IN",
    0xD9, "LED5_TEST", "0", "1", "in_exp1_testbord_high_7", "7", "IN",

    0xE0, "in_exp2_testbord_low", "-", "-", "IO_exp_8", "377", "0x75", "0x00", "1",
    0xE1, "out_exp2_testbord_low", "-", "-", "IO_exp_8", "377", "0x75", "0x02", "1",
    0xE2, "LED6_TEST", "0", "1", "in_exp2_testbord_low_0", "0", "IN",
    0xE3, "RX_PWR_TEST", "0", "1", "in_exp2_testbord_low_1", "1", "IN",
    0xE4, "RX_TRIG_TEST", "0", "1", "in_exp2_testbord_low_2", "2", "IN",
    0xE5, "RX_T0_TEST", "0", "1", "in_exp2_testbord_low_3", "3", "IN",
    0xE6, "ID2_HIGH_TEST", "0", "1", "in_exp2_testbord_low_4", "4", "IN",
    0xE7, "ID2_MID_TEST", "0", "1", "in_exp2_testbord_low_5", "5", "IN",
    0xE8, "ID1_HIGH_TEST", "0", "1", "in_exp2_testbord_low_6", "6", "IN",
    0xE9, "ID1_MID_TEST", "0", "1", "in_exp2_testbord_low_7", "7", "IN",

    0xF0, "in_exp2_testbord_high", "-", "-", "IO_exp_8", "377", "0x75", "0x01", "1",
    0xF1, "out_exp2_testbord_high", "-", "-", "IO_exp_8", "377", "0x75", "0x03", "1",
    0xF2, "ID0_HIGH_TEST", "0", "1", "in_exp2_testbord_high_0", "0", "IN",
    0xF3, "ID0_MID_TEST", "0", "1", "in_exp2_testbord_high_1", "1", "IN",

    0x0100, "in_exp3_testbord_low", "-", "-", "IO_exp_8", "377", "0x76", "0x00", "1",
    0x0101, "out_exp3_testbord_low", "-", "-", "IO_exp_8", "377", "0x76", "0x02", "1",
    0x0102, "REMOTE_ON1_TEST", "0", "1", "in_exp3_testbord_low_0", "0", "OUT",
    0x0103, "CH_LED_EN_TEST", "0", "1", "in_exp3_testbord_low_1", "1", "OUT",
    0x0104, "REMOTE_ON2_TEST", "0", "1", "in_exp3_testbord_low_2", "2", "OUT",
    0x0105, "AUX1_IN_TEST", "0", "1", "in_exp3_testbord_low_3", "3", "OUT",
    0x0106, "AUX2_IN_TEST", "0", "1", "in_exp3_testbord_low_4", "4", "OUT",
    0x0107, "ENC1_A", "0", "1", "in_exp3_testbord_low_5", "5", "OUT",
    0x0108, "ENC1_B", "0", "1", "in_exp3_testbord_low_6", "6", "OUT",
    0x0109, "ENC2_A", "0", "1", "in_exp3_testbord_low_7", "7", "OUT",

    0x0111, "in_exp3_testbord_high", "-", "-", "IO_exp_8", "377", "0x76", "0x01", "1",
    0x0112, "out_exp3_testbord_high", "-", "-", "IO_exp_8", "377", "0x76", "0x03", "1",
    0x0113, "ENC2_B", "0", "1", "in_exp3_testbord_high_0", "0", "OUT",
    0x0114, "EN_PWR_BTN", "-", "-", "in_exp3_testbord_high_1", "1", "OUT",
    # EN_PWR_BTN not read by MCU-firmware, therefore not tested

    # Other messages

    0x0120, "ID_1", "0", "1", "DIG",
    0x0121, "T0_1", "0", "1", "DIG",
    0x0122, "CLK_1", "0", "1", "DIG",
    0x0123, "ID_2", "0", "1", "DIG",
    0x0124, "T0_2", "0", "1", "DIG",
    0x0125, "CLK_2", "0", "1", "DIG",
    0x0126, "ID_3", "0", "1", "DIG",
    0x0127, "T0_3", "0", "1", "DIG",
    0x0128, "CLK_3", "0", "1", "DIG",
    0x0129, "ID_4", "0", "1", "DIG",
    0x012A, "T0_4", "0", "1", "DIG",
    0x012B, "CLK_4", "0", "1", "DIG",
    0x012C, "ID_5", "0", "1", "DIG",
    0x012D, "T0_5", "0", "1", "DIG",
    0x012E, "CLK_5", "0", "1", "DIG",
    0x012F, "ID_6", "0", "1", "DIG",
    0x0130, "T0_6", "0", "1", "DIG",
    0x0131, "CLK_6", "0", "1", "DIG",
    0x0132, "ID_7", "0", "1", "DIG",
    0x0133, "T0_7", "0", "1", "DIG",
    0x0134, "CLK_7", "0", "1", "DIG",
    0x0135, "ID_8", "0", "1", "DIG",
    0x0136, "T0_8", "0", "1", "DIG",
    0x0137, "CLK_8", "0", "1", "DIG",
    0x0138, "ID_9", "0", "1", "DIG",
    0x0139, "T0_9", "0", "1", "DIG",
    0x013A, "CLK_9", "0", "1", "DIG",
    0x013B, "ID_10", "0", "1", "DIG",
    0x013C, "T0_10", "0", "1", "DIG",
    0x013D, "CLK_10", "0", "1", "DIG",
    0x013E, "ID_11", "0", "1", "DIG",
    0x013F, "T0_11", "0", "1", "DIG",
    0x0140, "CLK_11", "0", "1", "DIG",
    0x0141, "ID_12", "0", "1", "DIG",
    0x0142, "T0_12", "0", "1", "DIG",
    0x0143, "CLK_12", "0", "1", "DIG",
    0x0144, "ID_13", "0", "1", "DIG",
    0x0145, "T0_13", "0", "1", "DIG",
    0x0146, "CLK_13", "0", "1", "DIG",
    0x0147, "ID_14", "0", "1", "DIG",
    0x0148, "T0_14", "0", "1", "DIG",
    0x0149, "CLK_14", "0", "1", "DIG",
    0x014A, "ID_15", "0", "1", "DIG",
    0x014B, "T0_15", "0", "1", "DIG",
    0x014C, "CLK_15", "0", "1", "DIG",
    0x014D, "ID_16", "0", "1", "DIG",
    0x014E, "T0_16", "0", "1", "DIG",
    0x014F, "CLK_16", "0", "1", "DIG",

    #        [Number]     [Name]     [min limit]    [max limit]    [Type]               [CMD]   [7bit address]  [Register]  [Data_size]
    0x0150, "BM_Temp", "15", "35", "temp", "377", "0x43", "0x30", "2",
    0x0151, "BM_Humid", "0", "100", "humid", "377", "0x43", "0x33", "2",

    0x0152, "MCU_PCB_Temp", "-", "-", "MCU_PCB_T", "377", "0x76", "0x33", "2",
    0x0153, "FPGA_Temp", "-", "-", "FPGA_T", "377", "0x76", "0x33", "2",

    # RX/TX related messages

    0x0201, "1v25_REF_RX", "1210", "1288", "ADC", "379",  # +/- 3%
    0x0202, "3v3_RX", "3200", "3400", "ADC", "357",  # +/- 3%
    0x0203, "3v3_FPGA_RX", "2800", "3400", "ADC", "358",  # +/- 3%
    0x0204, "2v5_RX", "2375", "2625", "ADC", "359",  # +/- 5%
    0x0205, "VBAT_MCU_RX", "11000", "25000", "ADC", "383",  # 11-25 V assumed for production test
    0x0206, "1v8_FPGA_RX", "1746", "1854", "ADC", "360",  # +/- 3%
    0x0207, "1v0_FPGA_RX", "950", "1050", "ADC", "361",  # +/- 50 mV
    0x0208, "1v2_ETHSW_RX", "1164", "1236", "ADC", "362",  # +/- 3%

    0x0209, "MB_REV_RX", "0", "100", "ADC", "363",
    0x020A, "5V_MB_RX", "-", "-", "ADC", "364",
    0x020B, "2v5_MB_RX", "-", "-", "ADC", "365",
    0x020C, "1v2_MB_RX", "-", "-", "ADC", "366",
    0x020D, "-3v3_MB_RX", "-3465", "-3135", "ADC", "367",  # -3.3V +/- 5%
    0x020E, "3v3_MB_RX", "3200", "3400", "ADC", "368",
    0x020F, "3v8_MB_RX", "3600", "3900", "ADC", "380",
    0x020A, "5V_MB_RX", "-", "-", "ADC", "364",
    0x020B, "2v5_MB_RX", "-", "-", "ADC", "365",
    0x020C, "1v2_MB_RX", "-", "-", "ADC", "366",
    0x020D, "-3v3_MB_RX", "-3465", "-3135", "ADC", "367",  # -3.3V +/- 5%
    0x020E, "3v3_MB_RX", "3200", "3400", "ADC", "368",
    0x020F, "3v8_MB_RX", "3600", "3900", "ADC", "380",

    0x0210, "ID0_RX", "1800", "1900", "ADC", "384",  # Assumed RX connected to CLK/ID port 1
    0x0211, "ID1_RX", "300", "400", "ADC", "385",  # Assumed RX connected to CLK/ID port 1
    0x0212, "ID2_RX", "300", "400", "ADC", "387",  # Assumed RX connected to CLK/ID port 1
    0x0210, "ID0_RX", "1800", "1900", "ADC", "384",  # Assumed RX connected to CLK/ID port 1
    0x0211, "ID1_RX", "300", "400", "ADC", "385",  # Assumed RX connected to CLK/ID port 1
    0x0212, "ID2_RX", "300", "400", "ADC", "387",  # Assumed RX connected to CLK/ID port 1

    0x0230, "MCU_FW_RX", "1610613012", "1610613012", "REV", "61",  # 1610613012 = 0x60000114
    0x0231, "FPGA_FW_RX", "65", "65", "REV", "61",
    0x0232, "MCU_REV_RX", "-", "-", "REV", "61",
    0x0234, "SYS_FW_RX", "8", "8", "REV", "61",

    0x0240, "DELAY_ADJ", "701", "1100", "DLY", "105",  # Read delay value from RX-unit
    0x0241, "DELAY_ERR", "-15", "15", "DLY", "14",  # 'get_trace command', calculates delay error when received

    # Battery related messages
    #           [Number]    [Name]                     min limit] [max limit] [Type]   [CMD]    [7bit address]    [Register]  [Data_size]
    0x0301, "Charger", "-", "-", "BAT", "377", "0xA", "", "2",
    0x0302, "Battery", "-", "-", "BAT", "377", "0xB", "", "2",

    0x0303, "C1_SYSTEM_STATE", "-", "-", "BAT", "377", "0xA", "0x01", "2",
    0x0304, "C1_SYSTEM_STATE_CONT", "-", "-", "BAT", "377", "0xA", "0x02", "2",
    0x0305, "C1_SYSTEM_INFO", "-", "-", "BAT", "377", "0xA", "0x04", "2",

    0x0306, "B1_PRESENT", "1", "1", "BAT", "377", "", "", "2",
    0x0307, "B1_CHARGING", "1", "1", "BAT", "377", "", "", "2",
    0x0308, "B1_SUPPLYING", "1", "1", "BAT", "377", "", "", "2",

    0x0309, "B1_REM_CAP_ALARM_THRESHOLD", "-", "-", "BAT", "377", "0xB", "0x01", "2",
    # 0x01 Sets or gets the Low Capacity alarm threshold value
    0x0310, "B1_REM_TIME_ALARM_THRESHOLD", "-", "-", "BAT", "377", "0xB", "0x02", "2",
    # 0x02 Sets or gets the Remaining Time alarm value
    0x0311, "B1_MODE", "-", "-", "BAT", "377", "0xB", "0x03", "2",
    # 0x03 selects various battery modes and reports the battery’s capabilities, modes, flags minor conditions requiring attention
    0x0312, "B1_AT_RATE", "-", "-", "BAT", "377", "0xB", "0x04", "2",
    # 0x04 used to set the AtRate value used in calculations made by the AtRateTimeToFull(), AtRateTimeToEmpty(), and AtRateOK() functions
    0x0313, "B1_AT_RATE_TIME_FULL", "-", "-", "BAT", "377", "0xB", "0x05", "2",
    # 0x05 Returns the predicted remaining time to fully charge the battery at the previously written AtRate value in mA
    0x0314, "B1_AT_RATE_TIME_EMPTY", "-", "-", "BAT", "377", "0xB", "0x06", "2",
    # 0x06 Returns the predicted remaining operating time if the battery is discharged at the previously written AtRate value.
    0x0315, "B1_AT_RATE_OK", "-", "-", "BAT", "377", "0xB", "0x07", "2",
    # 0x07 Returns a Boolean value that indicates whether or not the battery can deliver the previously written AtRate value of additional energy for 10 seconds (Boolean).
    0x0316, "B1_TEMP", "-", "-", "BAT", "377", "0xB", "0x08", "2",
    # 0x08 Returns the cell-pack's internal temperature (°K).
    0x0317, "B1_VOLTAGE", "-", "-", "BAT", "377", "0xB", "0x09", "2",  # 0x09 Returns the cell-pack voltage (mV).
    0x0318, "B1_CURRENT", "-", "-", "BAT", "377", "0xB", "0x0a", "2",
    # 0x0A Returns the current being supplied (or accepted) through the battery's terminals (mA).
    0x0319, "B1_AVARAGE_CURRENT", "-", "-", "BAT", "377", "0xB", "0x0b", "2",
    # 0x0B Returns a one-minute rolling average based on the current being supplied (or accepted) through the battery's terminals (mA)
    0x0320, "B1_MAX_ERROR", "-", "-", "BAT", "377", "0xB", "0x0c", "2",
    # 0x0C Returns the expected margin of error (%) in the state of charge calculation
    0x0321, "B1_REL_CHARGE_STATE", "-", "-", "BAT", "377", "0xB", "0x0d", "2",
    # 0x0D Returns the predicted remaining battery capacity expressed as a percentage of FullChargeCapacity() (%).
    0x0322, "B1_ABS_CHARGE_STATE", "-", "-", "BAT", "377", "0xB", "0x0e", "2",
    # 0x0E Returns the predicted remaining battery capacity expressed as a percentage of DesignCapacity() (%)
    0x0323, "B1_REMAINING_CAPACITY", "-", "-", "BAT", "377", "0xB", "0x0f", "2",
    # 0x0F Returns the predicted remaining battery capacity.
    0x0324, "B1_FULL_CHARGE_CAPACITY", "-", "-", "BAT", "377", "0xB", "0x10", "2",
    # 0x10 Returns the predicted pack capacity when it is fully charged.
    0x0325, "B1_RUN_TIME_EMPTY", "-", "-", "BAT", "377", "0xB", "0x11", "2",
    # 0x11 Returns the predicted remaining battery life at the present rate of discharge (minutes)
    0x0326, "B1_AVARAGE_TIME_EMPTY", "-", "-", "BAT", "377", "0xB", "0x12", "2",
    # 0x12 Returns a one-minute rolling average of the predicted remaining battery life (minutes).
    0x0327, "B1_AVARAGE_TIME_FULL", "-", "-", "BAT", "377", "0xB", "0x13", "2",
    # 0x13 Returns a one minute rolling average of the predicted remaining time until the Smart Battery reaches full charge (minutes).
    0x0328, "B1_CHARGING_CURRENT", "-", "-", "BAT", "377", "0xB", "0x14", "2",
    # 0x14 Sends the desired charging rate to the Smart Battery Charger (mA).
    0x0329, "B1_CHARGING_VOLTAGE", "-", "-", "BAT", "377", "0xB", "0x15", "2",
    # 0x15 Sends the desired charging voltage to the Smart Battery Charger (mV)
    0x0330, "B1_ALARM_WARNING", "-", "-", "BAT", "377", "0xB", "0x16", "2",
    # 0x16 Returns the Smart Battery's status word which contains Alarm and Status bit flags
    0x0331, "B1_CYCLE_COUNT", "-", "-", "BAT", "377", "0xB", "0x17", "2",
    # 0x17 Returns the number of cycles the battery has experienced
    0x0332, "B1_DESIGN_CAPACITY", "-", "-", "BAT", "377", "0xB", "0x18", "2",
    # 0x18 Returns the theoretical capacity of a new pack.
    0x0333, "B1_DESIGN_VOLTAGE", "-", "-", "BAT", "377", "0xB", "0x19", "2",
    # 0x19 Returns the theoretical voltage of a new pack (mV)
    0x0334, "B1_SPECIFICATION_INFO", "-", "-", "BAT", "377", "0xB", "0x1A", "2",
    # 0x1A Returns the version number of the Smart Battery specification the battery pack supports, as well as voltage and current and capacity scaling information in a packed unsigned integer.
    0x0335, "B1_MANUFACTURE_DATE", "-", "-", "BAT", "377", "0xB", "0x1B", "2",
    # 0x1B This function returns the date the cell pack was manufactured in a packed integer. The date is packed in the following fashion: (year-1980) * 512 + month * 32 + day.
    0x0336, "B1_SERIAL_NO", "-", "-", "BAT", "377", "0xB", "0x1C", "2",
    # 0x1C This function is used to return a serial number.
    0x0337, "B1_MANUFACTURER_NAME", "-", "-", "BAT", "377", "0xB", "0x20", "2",
    # 0x20 This function returns a character array containing the battery's manufacturer's name
    0x0338, "B1_DEVICE_NAME", "-", "-", "BAT", "377", "0xB", "0x21", "2",
    # 0x21 This function returns a character string that contains the battery's name
    0x0339, "B1_DEVICE_CHEMISTRY", "-", "-", "BAT", "377", "0xB", "0x22", "2",
    # 0x22 This function returns a character string that contains the battery's chemistry
    0x0340, "B1_MANUFACTURER_DATA", "-", "-", "BAT", "377", "0xB", "0x23", "2",
    # 0x23 This function allows access to the manufacturer data contained in the battery (data).

    0x0341, "B2_PRESENT", "1", "1", "BAT", "377", "", "", "2",
    0x0342, "B2_CHARGING", "1", "1", "BAT", "377", "", "", "2",
    0x0343, "B2_SUPPLYING", "1", "1", "BAT", "377", "", "", "2",

    0x0344, "B2_REM_CAP_ALARM_THRESHOLD", "-", "-", "BAT", "377", "0xB", "0x01", "2",
    # 0x01 Sets or gets the Low Capacity alarm threshold value
    0x0345, "B2_REM_TIME_ALARM_THRESHOLD", "-", "-", "BAT", "377", "0xB", "0x02", "2",
    # 0x02 Sets or gets the Remaining Time alarm value
    0x0346, "B2_MODE", "-", "-", "BAT", "377", "0xB", "0x03", "2",
    # 0x03 selects various battery modes and reports the battery’s capabilities, modes, flags minor conditions requiring attention
    0x0347, "B2_AT_RATE", "-", "-", "BAT", "377", "0xB", "0x04", "2",
    # 0x04 used to set the AtRate value used in calculations made by the AtRateTimeToFull(), AtRateTimeToEmpty(), and AtRateOK() functions
    0x0348, "B2_AT_RATE_TIME_FULL", "-", "-", "BAT", "377", "0xB", "0x05", "2",
    # 0x05 Returns the predicted remaining time to fully charge the battery at the previously written AtRate value in mA
    0x0349, "B2_AT_RATE_TIME_EMPTY", "-", "-", "BAT", "377", "0xB", "0x06", "2",
    # 0x06 Returns the predicted remaining operating time if the battery is discharged at the previously written AtRate value.
    0x0350, "B2_AT_RATE_OK", "-", "-", "BAT", "377", "0xB", "0x07", "2",
    # 0x07 Returns a Boolean value that indicates whether or not the battery can deliver the previously written AtRate value of additional energy for 10 seconds (Boolean).
    0x0351, "B2_TEMP", "-", "-", "BAT", "377", "0xB", "0x08", "2",
    # 0x08 Returns the cell-pack's internal temperature (°K).
    0x0352, "B2_VOLTAGE", "-", "-", "BAT", "377", "0xB", "0x09", "2",  # 0x09 Returns the cell-pack voltage (mV).
    0x0353, "B2_CURRENT", "-", "-", "BAT", "377", "0xB", "0x0a", "2",
    # 0x0A Returns the current being supplied (or accepted) through the battery's terminals (mA).
    0x0354, "B2_AVARAGE_CURRENT", "-", "-", "BAT", "377", "0xB", "0x0b", "2",
    # 0x0B Returns a one-minute rolling average based on the current being supplied (or accepted) through the battery's terminals (mA)
    0x0355, "B2_MAX_ERROR", "-", "-", "BAT", "377", "0xB", "0x0c", "2",
    # 0x0C Returns the expected margin of error (%) in the state of charge calculation
    0x0356, "B2_REL_CHARGE_STATE", "-", "-", "BAT", "377", "0xB", "0x0d", "2",
    # 0x0D Returns the predicted remaining battery capacity expressed as a percentage of FullChargeCapacity() (%).
    0x0357, "B2_ABS_CHARGE_STATE", "-", "-", "BAT", "377", "0xB", "0x0e", "2",
    # 0x0E Returns the predicted remaining battery capacity expressed as a percentage of DesignCapacity() (%)
    0x0358, "B2_REMAINING_CAPACITY", "-", "-", "BAT", "377", "0xB", "0x0f", "2",
    # 0x0F Returns the predicted remaining battery capacity.
    0x0359, "B2_FULL_CHARGE_CAPACITY", "-", "-", "BAT", "377", "0xB", "0x10", "2",
    # 0x10 Returns the predicted pack capacity when it is fully charged.
    0x0360, "B2_RUN_TIME_EMPTY", "-", "-", "BAT", "377", "0xB", "0x11", "2",
    # 0x11 Returns the predicted remaining battery life at the present rate of discharge (minutes)
    0x0361, "B2_AVARAGE_TIME_EMPTY", "-", "-", "BAT", "377", "0xB", "0x12", "2",
    # 0x12 Returns a one-minute rolling average of the predicted remaining battery life (minutes).
    0x0362, "B2_AVARAGE_TIME_FULL", "-", "-", "BAT", "377", "0xB", "0x13", "2",
    # 0x13 Returns a one minute rolling average of the predicted remaining time until the Smart Battery reaches full charge (minutes).
    0x0363, "B2_CHARGING_CURRENT", "-", "-", "BAT", "377", "0xB", "0x14", "2",
    # 0x14 Sends the desired charging rate to the Smart Battery Charger (mA).
    0x0364, "B2_CHARGING_VOLTAGE", "-", "-", "BAT", "377", "0xB", "0x15", "2",
    # 0x15 Sends the desired charging voltage to the Smart Battery Charger (mV)
    0x0365, "B2_ALARM_WARNING", "-", "-", "BAT", "377", "0xB", "0x16", "2",
    # 0x16 Returns the Smart Battery's status word which contains Alarm and Status bit flags
    0x0366, "B2_CYCLE_COUNT", "-", "-", "BAT", "377", "0xB", "0x17", "2",
    # 0x17 Returns the number of cycles the battery has experienced
    0x0367, "B2_DESIGN_CAPACITY", "-", "-", "BAT", "377", "0xB", "0x18", "2",
    # 0x18 Returns the theoretical capacity of a new pack.
    0x0368, "B2_DESIGN_VOLTAGE", "-", "-", "BAT", "377", "0xB", "0x19", "2",
    # 0x19 Returns the theoretical voltage of a new pack (mV)
    0x0369, "B2_SPECIFICATION_INFO", "-", "-", "BAT", "377", "0xB", "0x1A", "2",
    # 0x1A Returns the version number of the Smart Battery specification the battery pack supports, as well as voltage and current and capacity scaling information in a packed unsigned integer.
    0x0370, "B2_MANUFACTURE_DATE", "-", "-", "BAT", "377", "0xB", "0x1B", "2",
    # 0x1B This function returns the date the cell pack was manufactured in a packed integer. The date is packed in the following fashion: (year-1980) * 512 + month * 32 + day.
    0x0371, "B2_SERIAL_NO", "-", "-", "BAT", "377", "0xB", "0x1C", "2",
    # 0x1C This function is used to return a serial number.
    0x0372, "B2_MANUFACTURER_NAME", "-", "-", "BAT", "377", "0xB", "0x20", "2",
    # 0x20 This function returns a character array containing the battery's manufacturer's name
    0x0373, "B2_DEVICE_NAME", "-", "-", "BAT", "377", "0xB", "0x21", "2",
    # 0x21 This function returns a character string that contains the battery's name
    0x0374, "B2_DEVICE_CHEMISTRY", "-", "-", "BAT", "377", "0xB", "0x22", "2",
    # 0x22 This function returns a character string that contains the battery's chemistry
    0x0375, "B2_MANUFACTURER_DATA", "-", "-", "BAT", "377", "0xB", "0x23", "2",
    # 0x23 This function allows access to the manufacturer data contained in the battery (data).

    0x0376, "C2_SYSTEM_STATE", "-", "-", "BAT", "377", "0xA", "0x01", "2",
    0x0377, "C2_SYSTEM_STATE_CONT", "-", "-", "BAT", "377", "0xA", "0x02", "2",
    0x0378, "C2_SYSTEM_INFO", "-", "-", "BAT", "377", "0xA", "0x04", "2",

    0x0379, "B3_PRESENT", "1", "1", "BAT", "377", "", "", "2",
    0x0380, "B3_CHARGING", "1", "1", "BAT", "377", "", "", "2",
    0x0381, "B3_SUPPLYING", "1", "1", "BAT", "377", "", "", "2",

    0x0382, "B3_REM_CAP_ALARM_THRESHOLD", "-", "-", "BAT", "377", "0xB", "0x01", "2",
    # 0x01 Sets or gets the Low Capacity alarm threshold value
    0x0383, "B3_REM_TIME_ALARM_THRESHOLD", "-", "-", "BAT", "377", "0xB", "0x02", "2",
    # 0x02 Sets or gets the Remaining Time alarm value
    0x0384, "B3_MODE", "-", "-", "BAT", "377", "0xB", "0x03", "2",
    # 0x03 selects various battery modes and reports the battery’s capabilities, modes, flags minor conditions requiring attention
    0x0385, "B3_AT_RATE", "-", "-", "BAT", "377", "0xB", "0x04", "2",
    # 0x04 used to set the AtRate value used in calculations made by the AtRateTimeToFull(), AtRateTimeToEmpty(), and AtRateOK() functions
    0x0386, "B3_AT_RATE_TIME_FULL", "-", "-", "BAT", "377", "0xB", "0x05", "2",
    # 0x05 Returns the predicted remaining time to fully charge the battery at the previously written AtRate value in mA
    0x0387, "B3_AT_RATE_TIME_EMPTY", "-", "-", "BAT", "377", "0xB", "0x06", "2",
    # 0x06 Returns the predicted remaining operating time if the battery is discharged at the previously written AtRate value.
    0x0388, "B3_AT_RATE_OK", "-", "-", "BAT", "377", "0xB", "0x07", "2",
    # 0x07 Returns a Boolean value that indicates whether or not the battery can deliver the previously written AtRate value of additional energy for 10 seconds (Boolean).
    0x0389, "B3_TEMP", "-", "-", "BAT", "377", "0xB", "0x08", "2",
    # 0x08 Returns the cell-pack's internal temperature (°K).
    0x0390, "B3_VOLTAGE", "-", "-", "BAT", "377", "0xB", "0x09", "2",  # 0x09 Returns the cell-pack voltage (mV).
    0x0391, "B3_CURRENT", "-", "-", "BAT", "377", "0xB", "0x0a", "2",
    # 0x0A Returns the current being supplied (or accepted) through the battery's terminals (mA).
    0x0392, "B3_AVARAGE_CURRENT", "-", "-", "BAT", "377", "0xB", "0x0b", "2",
    # 0x0B Returns a one-minute rolling average based on the current being supplied (or accepted) through the battery's terminals (mA)
    0x0393, "B3_MAX_ERROR", "-", "-", "BAT", "377", "0xB", "0x0c", "2",
    # 0x0C Returns the expected margin of error (%) in the state of charge calculation
    0x0394, "B3_REL_CHARGE_STATE", "-", "-", "BAT", "377", "0xB", "0x0d", "2",
    # 0x0D Returns the predicted remaining battery capacity expressed as a percentage of FullChargeCapacity() (%).
    0x0395, "B3_ABS_CHARGE_STATE", "-", "-", "BAT", "377", "0xB", "0x0e", "2",
    # 0x0E Returns the predicted remaining battery capacity expressed as a percentage of DesignCapacity() (%)
    0x0396, "B3_REMAINING_CAPACITY", "-", "-", "BAT", "377", "0xB", "0x0f", "2",
    # 0x0F Returns the predicted remaining battery capacity.
    0x0397, "B3_FULL_CHARGE_CAPACITY", "-", "-", "BAT", "377", "0xB", "0x10", "2",
    # 0x10 Returns the predicted pack capacity when it is fully charged.
    0x0398, "B3_RUN_TIME_EMPTY", "-", "-", "BAT", "377", "0xB", "0x11", "2",
    # 0x11 Returns the predicted remaining battery life at the present rate of discharge (minutes)
    0x0399, "B3_AVARAGE_TIME_EMPTY", "-", "-", "BAT", "377", "0xB", "0x12", "2",
    # 0x12 Returns a one-minute rolling average of the predicted remaining battery life (minutes).
    0x0400, "B3_AVARAGE_TIME_FULL", "-", "-", "BAT", "377", "0xB", "0x13", "2",
    # 0x13 Returns a one minute rolling average of the predicted remaining time until the Smart Battery reaches full charge (minutes).
    0x0401, "B3_CHARGING_CURRENT", "-", "-", "BAT", "377", "0xB", "0x14", "2",
    # 0x14 Sends the desired charging rate to the Smart Battery Charger (mA).
    0x0402, "B3_CHARGING_VOLTAGE", "-", "-", "BAT", "377", "0xB", "0x15", "2",
    # 0x15 Sends the desired charging voltage to the Smart Battery Charger (mV)
    0x0403, "B3_ALARM_WARNING", "-", "-", "BAT", "377", "0xB", "0x16", "2",
    # 0x16 Returns the Smart Battery's status word which contains Alarm and Status bit flags
    0x0404, "B3_CYCLE_COUNT", "-", "-", "BAT", "377", "0xB", "0x17", "2",
    # 0x17 Returns the number of cycles the battery has experienced
    0x0405, "B3_DESIGN_CAPACITY", "-", "-", "BAT", "377", "0xB", "0x18", "2",
    # 0x18 Returns the theoretical capacity of a new pack.
    0x0406, "B3_DESIGN_VOLTAGE", "-", "-", "BAT", "377", "0xB", "0x19", "2",
    # 0x19 Returns the theoretical voltage of a new pack (mV)
    0x0407, "B3_SPECIFICATION_INFO", "-", "-", "BAT", "377", "0xB", "0x1A", "2",
    # 0x1A Returns the version number of the Smart Battery specification the battery pack supports, as well as voltage and current and capacity scaling information in a packed unsigned integer.
    0x0408, "B3_MANUFACTURE_DATE", "-", "-", "BAT", "377", "0xB", "0x1B", "2",
    # 0x1B This function returns the date the cell pack was manufactured in a packed integer. The date is packed in the following fashion: (year-1980) * 512 + month * 32 + day.
    0x0409, "B3_SERIAL_NO", "-", "-", "BAT", "377", "0xB", "0x1C", "2",
    # 0x1C This function is used to return a serial number.
    0x0410, "B3_MANUFACTURER_NAME", "-", "-", "BAT", "377", "0xB", "0x20", "2",
    # 0x20 This function returns a character array containing the battery's manufacturer's name
    0x0411, "B3_DEVICE_NAME", "-", "-", "BAT", "377", "0xB", "0x21", "2",
    # 0x21 This function returns a character string that contains the battery's name
    0x0412, "B3_DEVICE_CHEMISTRY", "-", "-", "BAT", "377", "0xB", "0x22", "2",
    # 0x22 This function returns a character string that contains the battery's chemistry
    0x0413, "B3_MANUFACTURER_DATA", "-", "-", "BAT", "377", "0xB", "0x23", "2",
    # 0x23 This function allows access to the manufacturer data contained in the battery (data).

    0x0414, "B4_PRESENT", "1", "1", "BAT", "377", "", "", "2",
    0x0415, "B4_CHARGING", "1", "1", "BAT", "377", "", "", "2",
    0x0416, "B4_SUPPLYING", "1", "1", "BAT", "377", "", "", "2",

    0x0417, "B4_REM_CAP_ALARM_THRESHOLD", "-", "-", "BAT", "377", "0xB", "0x01", "2",
    # 0x01 Sets or gets the Low Capacity alarm threshold value
    0x0418, "B4_REM_TIME_ALARM_THRESHOLD", "-", "-", "BAT", "377", "0xB", "0x02", "2",
    # 0x02 Sets or gets the Remaining Time alarm value
    0x0419, "B4_MODE", "-", "-", "BAT", "377", "0xB", "0x03", "2",
    # 0x03 selects various battery modes and reports the battery’s capabilities, modes, flags minor conditions requiring attention
    0x0420, "B4_AT_RATE", "-", "-", "BAT", "377", "0xB", "0x04", "2",
    # 0x04 used to set the AtRate value used in calculations made by the AtRateTimeToFull(), AtRateTimeToEmpty(), and AtRateOK() functions
    0x0421, "B4_AT_RATE_TIME_FULL", "-", "-", "BAT", "377", "0xB", "0x05", "2",
    # 0x05 Returns the predicted remaining time to fully charge the battery at the previously written AtRate value in mA
    0x0422, "B4_AT_RATE_TIME_EMPTY", "-", "-", "BAT", "377", "0xB", "0x06", "2",
    # 0x06 Returns the predicted remaining operating time if the battery is discharged at the previously written AtRate value.
    0x0423, "B4_AT_RATE_OK", "-", "-", "BAT", "377", "0xB", "0x07", "2",
    # 0x07 Returns a Boolean value that indicates whether or not the battery can deliver the previously written AtRate value of additional energy for 10 seconds (Boolean).
    0x0424, "B4_TEMP", "-", "-", "BAT", "377", "0xB", "0x08", "2",
    # 0x08 Returns the cell-pack's internal temperature (°K).
    0x0425, "B4_VOLTAGE", "-", "-", "BAT", "377", "0xB", "0x09", "2",  # 0x09 Returns the cell-pack voltage (mV).
    0x0426, "B4_CURRENT", "-", "-", "BAT", "377", "0xB", "0x0a", "2",
    # 0x0A Returns the current being supplied (or accepted) through the battery's terminals (mA).
    0x0427, "B4_AVARAGE_CURRENT", "-", "-", "BAT", "377", "0xB", "0x0b", "2",
    # 0x0B Returns a one-minute rolling average based on the current being supplied (or accepted) through the battery's terminals (mA)
    0x0428, "B4_MAX_ERROR", "-", "-", "BAT", "377", "0xB", "0x0c", "2",
    # 0x0C Returns the expected margin of error (%) in the state of charge calculation
    0x0429, "B4_REL_CHARGE_STATE", "-", "-", "BAT", "377", "0xB", "0x0d", "2",
    # 0x0D Returns the predicted remaining battery capacity expressed as a percentage of FullChargeCapacity() (%).
    0x0430, "B4_ABS_CHARGE_STATE", "-", "-", "BAT", "377", "0xB", "0x0e", "2",
    # 0x0E Returns the predicted remaining battery capacity expressed as a percentage of DesignCapacity() (%)
    0x0431, "B4_REMAINING_CAPACITY", "-", "-", "BAT", "377", "0xB", "0x0f", "2",
    # 0x0F Returns the predicted remaining battery capacity.
    0x0432, "B4_FULL_CHARGE_CAPACITY", "-", "-", "BAT", "377", "0xB", "0x10", "2",
    # 0x10 Returns the predicted pack capacity when it is fully charged.
    0x0433, "B4_RUN_TIME_EMPTY", "-", "-", "BAT", "377", "0xB", "0x11", "2",
    # 0x11 Returns the predicted remaining battery life at the present rate of discharge (minutes)
    0x0434, "B4_AVARAGE_TIME_EMPTY", "-", "-", "BAT", "377", "0xB", "0x12", "2",
    # 0x12 Returns a one-minute rolling average of the predicted remaining battery life (minutes).
    0x0435, "B4_AVARAGE_TIME_FULL", "-", "-", "BAT", "377", "0xB", "0x13", "2",
    # 0x13 Returns a one minute rolling average of the predicted remaining time until the Smart Battery reaches full charge (minutes).
    0x0436, "B4_CHARGING_CURRENT", "-", "-", "BAT", "377", "0xB", "0x14", "2",
    # 0x14 Sends the desired charging rate to the Smart Battery Charger (mA).
    0x0437, "B4_CHARGING_VOLTAGE", "-", "-", "BAT", "377", "0xB", "0x15", "2",
    # 0x15 Sends the desired charging voltage to the Smart Battery Charger (mV)
    0x0438, "B4_ALARM_WARNING", "-", "-", "BAT", "377", "0xB", "0x16", "2",
    # 0x16 Returns the Smart Battery's status word which contains Alarm and Status bit flags
    0x0439, "B4_CYCLE_COUNT", "-", "-", "BAT", "377", "0xB", "0x17", "2",
    # 0x17 Returns the number of cycles the battery has experienced
    0x0440, "B4_DESIGN_CAPACITY", "-", "-", "BAT", "377", "0xB", "0x18", "2",
    # 0x18 Returns the theoretical capacity of a new pack.
    0x0441, "B4_DESIGN_VOLTAGE", "-", "-", "BAT", "377", "0xB", "0x19", "2",
    # 0x19 Returns the theoretical voltage of a new pack (mV)
    0x0442, "B4_SPECIFICATION_INFO", "-", "-", "BAT", "377", "0xB", "0x1A", "2",
    # 0x1A Returns the version number of the Smart Battery specification the battery pack supports, as well as voltage and current and capacity scaling information in a packed unsigned integer.
    0x0443, "B4_MANUFACTURE_DATE", "-", "-", "BAT", "377", "0xB", "0x1B", "2",
    # 0x1B This function returns the date the cell pack was manufactured in a packed integer. The date is packed in the following fashion: (year-1980) * 512 + month * 32 + day.
    0x0444, "B4_SERIAL_NO", "-", "-", "BAT", "377", "0xB", "0x1C", "2",
    # 0x1C This function is used to return a serial number.
    0x0445, "B4_MANUFACTURER_NAME", "-", "-", "BAT", "377", "0xB", "0x20", "2",
    # 0x20 This function returns a character array containing the battery's manufacturer's name
    0x0446, "B4_DEVICE_NAME", "-", "-", "BAT", "377", "0xB", "0x21", "2",
    # 0x21 This function returns a character string that contains the battery's name
    0x0447, "B4_DEVICE_CHEMISTRY", "-", "-", "BAT", "377", "0xB", "0x22", "2",
    # 0x22 This function returns a character string that contains the battery's chemistry
    0x0448, "B4_MANUFACTURER_DATA", "-", "-", "BAT", "377", "0xB", "0x23", "2",
    # 0x23 This function allows access to the manufacturer data contained in the battery (data).

    0x0449, "C1_AC_PRESENT", "1", "1", "BAT", "377", "", "", "2",
    0x0450, "C2_AC_PRESENT", "1", "1", "BAT", "377", "", "", "2",

    # System related messages

    0x0900, "bat_info_on", "0", "1", "SYS", "378",
    0x0901, "bat_info_off", "0", "1", "SYS_NOPRINT", "378",

    0x0902, "I2C1_write_8bit", "0", "1", "SYS", "377",
    0x0903, "I2C1_read_8bit", "0", "1", "SYS", "377",

    0x0904, "START_MEAS", "0", "1", "SYS", "12",
    0x0905, "GEN_T0", "0", "1", "SYS_NOPRINT", "14",
    0x0906, "GET_TRACE", "0", "1", "SYS", "14",
    0x0907, "DISCOVER", "0", "1", "SYS", "214",
    0x0908, "SHOOTING_TABLE", "0", "1", "SYS", "204",
    0x0909, "GET_RECIEVERS", "0", "1", "SYS", "206",
    0x090A, "SET_SAMPLES", "0", "1", "SYS", "1",
    0x090B, "SET_RUNS", "0", "1", "SYS", "104",
    0x090C, "SET_STACKS", "0", "1", "SYS", "2",
    0x090D, "FINALIZE_SETTINGS", "0", "1", "SYS", "209",
    0x090E, "SET_HOST_IP", "0", "1", "SYS", "83",
    0x090F, "GET_CHANNELS", "0", "1", "SYS", "50",
    0x0910, "TRACE_DATA", "0", "1", "SYS", "102",
    0x0911, "DELAY", "0", "1", "", "105",
    0x0912, "RESET_WHEEL", "-", "-", "SYS", "8",  # Command SET_MEAS_DIR re-initializes wheel ticks

    0x0920, "config_0x22", "-", "-", "IO_exp_8", "377",
    0x0921, "read_0x22", "-", "-", "IO_exp_8", "377",
    0x0922, "read_0x22_2", "-", "-", "IO_exp_8", "377",

    0x0923, "I2C1_write_16bit", "0", "1", "", "377",
    0x0924, "I2C1_read_16bit", "0", "1", "SYS", "377"
]
