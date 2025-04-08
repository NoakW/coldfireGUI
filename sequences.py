import testengine
import parameterlist
import time

WAIT_TIME_1 = 0.05
WAIT_TIME_2 = 0.005

last_rx_time = 0
last_rx_time = 0


# Conditional wait used to skip steps if message recieved!
def conditional_wait(wait_time, queue_to_check):
    if (queue_to_check.empty()):  # Check if there is any control messages then wait
        time.sleep(wait_time)
        return 0
    else:  # Else do not wait and return 1 to break
        return 1


def blockmaster_init(UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE, CONSOLE_QUEUE):
    # Disable fetching of battery information
    testengine.send_battery_info_on_off("bat_info_off", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                        testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return

    # iniate temp/humidity sensor
    testengine.send_write_I2C1_8reg(parameterlist.parameterlist, 0x43, 0x21, 0x03, CONSOLE_QUEUE,
                                    UDP_TRANSMIT_MESSAGE_QUEUE, testengine.BLOCKMASTER)  # Sets sensor in continous mode
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_write_I2C1_8reg(parameterlist.parameterlist, 0x43, 0x22, 0x03, CONSOLE_QUEUE,
                                    UDP_TRANSMIT_MESSAGE_QUEUE, testengine.BLOCKMASTER)  # Start sensor measurment
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return


def set_RX_pwr_on(UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE, CONSOLE_QUEUE):
    # Set GPIO pins RX_EN_[16:1] to HIGH
    testengine.send_write_I2C1_8reg(parameterlist.parameterlist, 0x22, 0x01, 0xFF, CONSOLE_QUEUE,
                                    UDP_TRANSMIT_MESSAGE_QUEUE, testengine.BLOCKMASTER)  # Set RX_EN_[8:1], all HIGH
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_write_I2C1_8reg(parameterlist.parameterlist, 0x23, 0x01, 0xFF, CONSOLE_QUEUE,
                                    UDP_TRANSMIT_MESSAGE_QUEUE, testengine.BLOCKMASTER)  # Set RX_EN_[16:9], all HIGH
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return

    # Set GPIO pins RX_EN_[16:1] pins to Outputs
    testengine.send_write_I2C1_8reg(parameterlist.parameterlist, 0x22, 0x03, 0x00, CONSOLE_QUEUE,
                                    UDP_TRANSMIT_MESSAGE_QUEUE,
                                    testengine.BLOCKMASTER)  # Set all pins as outputs (RX_EN_[8:1])
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_write_I2C1_8reg(parameterlist.parameterlist, 0x23, 0x03, 0x00, CONSOLE_QUEUE,
                                    UDP_TRANSMIT_MESSAGE_QUEUE,
                                    testengine.BLOCKMASTER)  # Set all pins as outputs (RX_EN_[16:9])
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return


def blockmaster_read_values(UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE, CONSOLE_QUEUE):
    # Read voltages in blockmaster
    testengine.send_get_ADC_value("3v3_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                  testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_get_ADC_value("3v3_FPGA_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                  testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_get_ADC_value("2v5_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                  testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_get_ADC_value("VBAT_MCU_BM_12V", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                  testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_get_ADC_value("VBAT_MCU_BM_24V", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                  testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_get_ADC_value("1v8_FPGA_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                  testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_get_ADC_value("1v0_FPGA_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                  testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_get_ADC_value("1v2_ETHSW_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                  testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_get_ADC_value("MB_REV_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                  testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_get_ADC_value("5V_MB_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                  testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_get_ADC_value("2v5_MB_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                  testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_get_ADC_value("1v2_MB_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                  testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_get_ADC_value("-3v3_MB_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                  testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_get_ADC_value("3v3_MB_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                  testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_get_ADC_value("3v8_MB_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                  testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_get_ADC_value("1v25_REF_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                  testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_get_ADC_value("ID0_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                  testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_get_ADC_value("ID1_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                  testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_get_ADC_value("ID2_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                  testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return

    # Read wheelticks
    testengine.send_get_WHEEL_tick_value("WHEEL1", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                         testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_get_WHEEL_tick_value("WHEEL2", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                         testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return

    # Read version strings in blockmaster
    testengine.send_get_BOARD_REV_value("MCU_REV_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                        testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_get_MCU_FW_value("MCU_FW_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                     testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_get_FPGA_FW_value("FPGA_FW_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                      testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return

    testengine.get_SYS_FW_value("SYS_FW_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return

    # Read BM temp/humidity chip
    testengine.send_read_I2C_register_from_parameterlist("BM_Temp", parameterlist.parameterlist,
                                                         UDP_TRANSMIT_MESSAGE_QUEUE, testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.send_read_I2C_register_from_parameterlist("BM_Humid", parameterlist.parameterlist,
                                                         UDP_TRANSMIT_MESSAGE_QUEUE, testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return


def blockmaster_shooting_table(request_data_state, UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE, CONSOLE_QUEUE):
    consol_text = ("--Setting shooting table-- Runs:%i Samples:%i Stacks:%i " % (
    request_data_state[1], request_data_state[2], request_data_state[3]))
    CONSOLE_QUEUE.put(consol_text)

    # Connect to BM and send measurement settings (distributed by Blockmaster to available RX-units)
    testengine.discover("DISCOVER", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_1, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.set_host_IP("SET_HOST_IP", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                           testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_1, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.get_recievers("GET_RECIEVERS", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                             testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_1, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.get_channels("GET_CHANNELS", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                            testengine.BLOCKMASTER)  # Sätt istället till antal channels!
    if (conditional_wait(WAIT_TIME_1, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.set_runs("SET_RUNS", parameterlist.parameterlist, request_data_state[1], UDP_TRANSMIT_MESSAGE_QUEUE,
                        testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_1, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.set_samples("SET_SAMPLES", parameterlist.parameterlist, request_data_state[2],
                           UDP_TRANSMIT_MESSAGE_QUEUE, testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_1, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.set_stacks("SET_STACKS", parameterlist.parameterlist, request_data_state[3], UDP_TRANSMIT_MESSAGE_QUEUE,
                          testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_1, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.trig_src_time(UDP_TRANSMIT_MESSAGE_QUEUE, testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_1, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.trig_cond(request_data_state[4],UDP_TRANSMIT_MESSAGE_QUEUE, testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_1, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.meas_dir(UDP_TRANSMIT_MESSAGE_QUEUE, testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_1, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.shooting_table("SHOOTING_TABLE", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                              testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_1, SEQUENCER_MESSAGE_QUEUE)): return
    testengine.finalize_settings("FINALIZE_SETTINGS", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                 testengine.BLOCKMASTER)
    if (conditional_wait(WAIT_TIME_1, SEQUENCER_MESSAGE_QUEUE)): return


def RX_read_values(UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE, CONSOLE_QUEUE):
    global last_rx_time
    time_between_traces = 1.5
    # delay_not_ok = not gui.delay_element.delay_ok
    time_for_trace = True if ((time.time() - last_rx_time) > time_between_traces) else False
    # force_trace = gui.delay_element.force_trace_checked.get()
    if (conditional_wait(0.05, SEQUENCER_MESSAGE_QUEUE)): return
    # Get trace at a regular interval - until delay value ok (or force new traces)
    if (time_for_trace):
        if (conditional_wait(0.1, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.get_delay("DELAY_ADJ", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, testengine.RX)
        if (conditional_wait(0.1, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.get_delay("DELAY", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, testengine.RX)
        if (conditional_wait(0.2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.get_trace("GET_TRACE", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                             testengine.BLOCKMASTER)
        if (conditional_wait(0.9, SEQUENCER_MESSAGE_QUEUE)): return

        last_rx_time = time.time()

    else:
        if (conditional_wait(0.2, SEQUENCER_MESSAGE_QUEUE)): return
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.send_get_ADC_value("3v3_RX", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.send_get_ADC_value("3v3_FPGA_RX", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                      testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.send_get_ADC_value("2v5_RX", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.send_get_ADC_value("VBAT_MCU_RX", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                      testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.send_get_ADC_value("1v8_FPGA_RX", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                      testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.send_get_ADC_value("1v0_FPGA_RX", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                      testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.send_get_ADC_value("1v2_ETHSW_RX", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                      testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.send_get_ADC_value("MB_REV_RX", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                      testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.send_get_ADC_value("5V_MB_RX", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                      testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.send_get_ADC_value("2v5_MB_RX", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                      testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.send_get_ADC_value("1v2_MB_RX", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                      testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.send_get_ADC_value("-3v3_MB_RX", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                      testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.send_get_ADC_value("3v3_MB_RX", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                      testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.send_get_ADC_value("3v8_MB_RX", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                      testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.send_get_ADC_value("1v25_REF_RX", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                      testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.send_get_ADC_value("ID0_RX", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.send_get_ADC_value("ID1_RX", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.send_get_ADC_value("ID2_RX", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.send_get_MCU_FW_value("MCU_FW_RX", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                         testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.send_get_FPGA_FW_value("FPGA_FW_RX", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                          testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.get_SYS_FW_value("SYS_FW_RX", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return

        testengine.send_get_MCU_FW_value("MCU_FW_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                         testengine.BLOCKMASTER)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.send_get_FPGA_FW_value("FPGA_FW_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                          testengine.BLOCKMASTER)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        testengine.get_SYS_FW_value("SYS_FW_BM", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                    testengine.BLOCKMASTER)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return

        testengine.send_get_BOARD_REV_value("MCU_REV_RX", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                            testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return

        testengine.get_delay("DELAY_ADJ", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, testengine.RX)
        if (conditional_wait(WAIT_TIME_2, SEQUENCER_MESSAGE_QUEUE)): return
        if (conditional_wait(0.2, SEQUENCER_MESSAGE_QUEUE)): return



