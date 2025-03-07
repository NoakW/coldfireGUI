############################
# See the overview.docx for information
############################

import parameterlist
import sequences

import socket
import queue
import threading
import time
import datetime
import tkinter as tk
import struct

UDP_IP_TEST_COMPUTER = "192.168.1.1"
UDP_IP_BLOCKMASTER = "192.168.1.2"
UDP_IP_RX = "192.168.1.101"
UDP_PORT = 0x555

SOFT_GREEN = "#CCFFCC"  # Soft Green
SOFT_RED = "#FFCCCC"  # Soft Red
GGEO_ORANGE = '#f15a22'  # GGEO Orange

BLOCKMASTER = "SOCKET1"
RX = "SOCKET2"

RX_ports_debounce = 0
RX_last_port_data = 0

stop_threads = False

############################
# Message Queues used to communicate between system threads
############################

UDP_RECIEVE_MESSAGE_QUEUE = queue.Queue()  # Used to t6ransmit raw UDP data to data handler thread. UDP_recieve_messages --> recieved_data_handler
UDP_TRANSMIT_MESSAGE_QUEUE = queue.Queue()  # Used to transmit raw UDP data to ethernet packages. ALL_THREADS --> UDP_transmit_messages
GUI_DATABASE_QUEUE = queue.Queue()  # Used to feed GUI with test database. recieved_data_handler -->  GUI
CONSOLE_QUEUE = queue.Queue()  # Used to print console messages in GUI. ALL_THREADS --> GUI.
RAW_DATA_QUEUE = queue.Queue()  # Used to print RAW UDP data in GUI. ALL_THREADS --> GUI.

SEQUENCER_MESSAGE_QUEUE = queue.Queue()  # Used to send control messages to request_data thread. GUI --> request_data.
RECIEVED_DATA_HANDLER_MESSAGE_QUEUE = queue.Queue()  # Used to send control messages to recieved_data_handler thread. GUI --> recieved_data_handler.
UDP_RECIEVE_STATE_QUEUE = queue.Queue()  # Used to send control messages to UDP_recieve_messages thread. GUI --> UDP_recieve_messages.
PLOTTER_QUEUE = queue.Queue()  # Used to send control messages to UDP_recieve_messages thread. GUI --> UDP_recieve_messages.
BATTERY_MESSAGE_QUEUE = queue.Queue()  # Used to send control messages to battery_test thread. GUI --> battery_test.

GUI_DATABASE_QUEUE


# ---------------------------------------------------------------------------------------------------------------------------------------

############################
# Function to handle recieved UDP packages.
############################

class PackageHeader:
    # Package header
    # I = unsigned int (size 4)
    # H = unsigned short (size 2)
    # B = unsigned char (size 1)
    _format = '!HHHHHHHH'

    def __init__(self, raw_data):
        self.protocol_id, self.package_number, self.dynamic_channel_id, self.payload_size, self.data_type, self.frame_number, self.number_of_frames, self.response_package_number = struct.unpack(
            self._format, raw_data[:16])


class BlockHeader:
    # Block header
    # I = unsigned int (size 4)
    # H = unsigned short (size 2)
    # B = unsigned char (size 1)
    _format = '!IHHBIHH'

    def __init__(self, raw_data):
        self.block_address, self.block_checksum, self.dynamic_channel_id, self.data_type, self.trace_number, self.payload_size, self.frame_number = struct.unpack(
            self._format, raw_data[:17])


class TraceHeader:
    # Block header
    # I = unsigned int (size 4)
    # H = unsigned short (size 2)
    # B = unsigned char (size 1)
    _format = '!BBBHI'

    def __init__(self, raw_data):
        self.unknown_1, self.unknown_2, self.unknown_3, self.channel_number, self.trace_number = struct.unpack(
            self._format, raw_data[:9])


import time
import struct
import socket
import queue
from threading import Thread

import time
import struct
import socket
import queue
from threading import Thread


def recieved_data_handler(CONSOLE_QUEUE,mysocket):

    recieved_traces = {
        "192.168.1.101": {1: {"trace": [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],  # Trace data
                              "recieved_frames": 0,  # Number of received frames
                              "packet_number": 0  # Packet number
                              }}}
    # --------------------------------------------------------

    CONSOLE_QUEUE.put("Starting thread recieved_data_handler")

    udp_socket_recv = mysocket
    print(udp_socket_recv)
    # Check if mysocket is a valid socket at the start
    if not isinstance(udp_socket_recv, socket.socket):
        print("Error: mysocket is not a valid socket!")
        return  # Stop execution if mysocket is invalid

    while not stop_threads:
        time.sleep(0.2)  # Run this function with defined minimum interval. This reduces load on CPU!!!

        try:
            # Receive data from the socket
            data, adress = udp_socket_recv.recvfrom(1024)  # Buffer size set to 4096 bytes
            message_PackageHeader = PackageHeader(data[:16])
            if not data:
                continue

            # Ensure we only process data from RX_IP
            if adress[0] != "192.168.1.101":  # Only process if the data comes from the RX_IP
                continue

            # Verify data length before processing headers
            if len(data) < 33:
                #print(f"⚠ Warning: Received packet is too short ({len(data)} bytes), skipping...")
                continue

            # Parse the BlockHeader from the received data
            block_header_size = 17  # Expected size of BlockHeader
            if len(data[16:33]) < block_header_size:
                print(
                    f"⚠ Error: Not enough data for BlockHeader! Expected {block_header_size} bytes, got {len(data[16:33])}")
                continue

            message_BlockHeader = BlockHeader(data[16:16 + block_header_size])  # Ensure exact slice

            # Append data to temporary buffer depending on frame number!
            if message_BlockHeader.frame_number == 1:
                if len(data) < 42:  # Ensure enough bytes for TraceHeader
                    print(f"⚠ Error: Packet too short for TraceHeader. Expected at least 42 bytes, got {len(data)}.")
                    continue

                message_TraceHeader = TraceHeader(data[33:42])  # Read TraceHeader only in the first frame
                raw_trace_buffer = data[42:]  # Append the data after the header
            else:
                raw_trace_buffer = data[33:]  # Append the data after the BlockHeader

            # Checking if new package received and reset or create a new placeholder
            if message_PackageHeader.dynamic_channel_id in recieved_traces.get(adress[0],
                                                                               {}):  # Check if the channel exists in the buffer
                if (recieved_traces[adress[0]][message_PackageHeader.dynamic_channel_id][
                    "packet_number"] != message_PackageHeader.package_number):
                    # Reset the data handler if new block message received
                    recieved_traces.update({adress[0]: {message_PackageHeader.dynamic_channel_id: {
                        "trace": [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
                        "recieved_frames": 0,
                        "packet_number": 0
                    }}})
            else:
                recieved_traces.update({adress[0]: {message_PackageHeader.dynamic_channel_id: {
                    "trace": [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
                    "recieved_frames": 0,
                    "packet_number": 0
                }}})

            # Add received data to the trace
            recieved_traces[adress[0]][message_PackageHeader.dynamic_channel_id]["trace"][
                message_PackageHeader.frame_number] = raw_trace_buffer
            recieved_traces[adress[0]][message_PackageHeader.dynamic_channel_id][
                "recieved_frames"] += 1  # Increase number of frames received
            recieved_traces[adress[0]][message_PackageHeader.dynamic_channel_id][
                "packet_number"] = message_PackageHeader.package_number

            # Check if the complete block is received and process it
            if recieved_traces[adress[0]][message_PackageHeader.dynamic_channel_id][
                "recieved_frames"] == message_PackageHeader.number_of_frames:
                trace = []
                for x in range(1, message_PackageHeader.number_of_frames + 1):
                    trace += recieved_traces[adress[0]][message_PackageHeader.dynamic_channel_id]["trace"][x]

                # Convert list to Uint32 instead of Uint8
                trace = [struct.unpack('!I', bytes(trace[i:i + 4]))[0] for i in range(0, len(trace), 4)]
                trace = [j - 0x80000000 for j in trace]  # Remove offset

                # Add trace to trace_container2.txt
                with open(f"trace_container2.txt", 'r') as read_trace_container:
                    trace_rows = read_trace_container.readlines()  # Read all existing rows from trace_container2.txt
                    trace_rows.append(
                        f"{adress[0]},{message_PackageHeader.dynamic_channel_id},{time.time()},empty1,empty2,empty3,{','.join([str(item) for item in trace])}\n")
                    last_rows = trace_rows[-8:]  # Get last 8 lines (traces), i.e., 4 traces from each channel

                time.sleep(0.01)

                with open(f"trace_container2.txt", 'w') as write_trace_container:
                    write_trace_container.writelines(trace_rows)

                time.sleep(0.01)

        except Exception:
            b = 1
    print("Stopped THREAD 'received_data_handler'")


# ---------------------------------------------------------------------------------------------------------------------------------------

############################
# Function to add stuff to database
############################

def add_recieved_data_to_database(database, parameterlist, message_id, value):
    global RX_ports_debounce
    global RX_last_port_data
    DEBOUNCE = 15

    parameterlist_message_id_index = parameterlist.index(message_id)
    parameterlist_test_name_index = parameterlist_message_id_index + 1
    test_name = parameterlist[parameterlist_message_id_index + 1]

    test_type = parameterlist[parameterlist_message_id_index + 4]

    # Convert deci-Kelvin to Celsius for battery temperature
    if test_type == "BAT" and "TEMP" in test_name:
        value = (value - 2722) / 10

    # Convert Analog value to negative if bigger than 32767 (for ADC voltage and Battery current)
    elif (test_type == "ADC" or (test_type == "BAT" and "SERIAL" not in test_name)) and value >= 32768:
        value = value - 65536  # Convert to negative numnber

    # Convert temperature and humidity data to real decimal values
    elif (test_type == "temp"):
        value = float(round(((value / 64) - 273.15), 2))

    elif (test_type == "humid"):
        value = float(round((value / 512), 2))

    # Add recieved data to database

    if (test_name in database):  # Update database if parameter already excist
        update_parameter_in_database(database, parameterlist, parameterlist_test_name_index, value)
    else:  # Add new parameter to database
        new_parameter_to_database(database, parameterlist, parameterlist_test_name_index, value)

    # # Add special parameters to database!

    # RX ports ID

    # if ("ID_" in test_name) and (test_type == "DIG"):

    # Check if all ID pins are read before processing data
    if ('ID0_MID_TEST' in database and 'ID1_MID_TEST' in database and 'ID2_MID_TEST' in database and
            'ID0_HIGH_TEST' in database and 'ID1_HIGH_TEST' in database and 'ID2_HIGH_TEST' in database):

        port_data = 0

        port_data = port_data + (database[database.index('ID2_HIGH_TEST') + 1] * 12)
        port_data = port_data + (database[database.index('ID2_MID_TEST') + 1] * 9)
        port_data = port_data + (database[database.index('ID1_HIGH_TEST') + 1] * 6)
        port_data = port_data + (database[database.index('ID1_MID_TEST') + 1] * 3)
        port_data = port_data + (database[database.index('ID0_HIGH_TEST') + 1] * 2)
        port_data = port_data + (database[database.index('ID0_MID_TEST') + 1] * 1)

        # Debounce data
        if (port_data == RX_last_port_data):
            RX_ports_debounce = RX_ports_debounce + 1
            RX_last_port_data = port_data
        else:
            RX_ports_debounce = 0
            RX_last_port_data = port_data

        # Add RX ID ports to database
        for x in range(1, 17):
            # port_name = ("%s_%d" % ('ID', x))
            port_name = f"ID_{x}"
            if (port_data == x and RX_ports_debounce > DEBOUNCE):
                value = 1
            else:
                value = 0

            parameterlist_test_name_index = parameterlist.index(port_name)

            if (port_name in database):
                update_parameter_in_database(database, parameterlist, parameterlist_test_name_index, value)
            else:
                new_parameter_to_database(database, parameterlist, parameterlist_test_name_index, value)

        # Add RX_CLK and T0 for each channel
        if ((port_data >= 1 and port_data <= 16) and RX_ports_debounce > DEBOUNCE):
            CLK_port_name = ("%s_%d" % ('CLK', port_data))
            T0_port_name = ("%s_%d" % ('T0', port_data))

            # Read value of T0 and RX from database
            if ('RX_TRIG_TEST' in database):
                RX_TRIG_TEST_index = database.index('RX_TRIG_TEST')
                RX_TRIG_VALUE = database[RX_TRIG_TEST_index + 1]

                # Add values to correspondning channel in database
                CLK_port_name_index = parameterlist.index(CLK_port_name)
                if (CLK_port_name in database):
                    update_parameter_in_database(database, parameterlist, CLK_port_name_index, RX_TRIG_VALUE)
                else:
                    new_parameter_to_database(database, parameterlist, CLK_port_name_index, RX_TRIG_VALUE)

            T0_port_name_index = parameterlist.index(T0_port_name)
            if ("RX_T0_TEST" in database):
                RX_T0_TEST_index = database.index('RX_T0_TEST')
                RX_T0_VALUE = database[RX_T0_TEST_index + 1]

                # Add values to correspondning channel in database
                if (T0_port_name in database):
                    update_parameter_in_database(database, parameterlist, T0_port_name_index, RX_T0_VALUE)
                else:
                    new_parameter_to_database(database, parameterlist, T0_port_name_index, RX_T0_VALUE)


############################
# Function to update parameter in database
############################

def update_parameter_in_database(database, parameterlist, parameterlist_test_name_index, value):
    test_name = parameterlist[parameterlist_test_name_index]
    test_limit_min = parameterlist[parameterlist_test_name_index + 1]
    test_limit_max = parameterlist[parameterlist_test_name_index + 2]
    test_type = parameterlist[parameterlist_test_name_index + 3]

    database_index = database.index(test_name)

    # Write current value to database!
    # print(f"Updating {test_name: <22} = {value: >16} in DATABASE (id: {id(database)})")
    database[database_index + 1] = value

    # Writing min and max values
    if (value <= database[database_index + 2]):
        database[database_index + 2] = value
    if (value >= database[database_index + 3]):
        database[database_index + 3] = value

    # Do checks on data and write:

    if (test_limit_min == '-' or test_limit_max == '-'):  # check if parameter should be tested
        database[database_index + 4] = 'Not Tested'
    else:
        test_limit_min = int(test_limit_min)
        test_limit_max = int(test_limit_max)

        # Inside min/max limit test:
        if (test_type == "ADC" or test_type == 'REV' or test_type == "DLY" or test_type == "COUNTER"):
            if (test_limit_min <= value and value <= test_limit_max):
                database[database_index + 4] = "True"
            else:
                database[database_index + 4] = "False"

        # Inside min/max limit test (keep if TRUE)
        elif (test_type == "ADC2" or test_type == 'BAT'):
            if (database[database_index + 4] == "True"):
                pass
            elif (test_limit_min <= value and value <= test_limit_max):
                database[database_index + 4] = "True"
            else:
                database[database_index + 4] = "False"


        # Min read value should be equal to min limit and max read value should be equal to max limit test:
        elif (test_type.startswith('in_exp') or test_type == 'DIG'):
            if (database[database_index + 2] == test_limit_min and database[database_index + 3] == test_limit_max):
                database[database_index + 4] = "True"
            else:
                database[database_index + 4] = "False"

        # Max wheel-tick value should be higher than min limit:
        # elif(test_type.startswith('COUNTER')):
        #     if(database[database_index+3] >= test_limit_min and database[database_index+3] <= test_limit_max):
        #         database[database_index+4] = "True"
        #     else:
        #         database[database_index+4] = "False"

        # No test
        else:
            database[database_index + 4] = 'Not Tested'

    # Add time
    database[database_index + 5] = time.time()


############################
# Function to add new parameter to database
############################

def new_parameter_to_database(database, parameterlist, parameterlist_test_name_index, value):
    # Recieve information from parameterlist
    message_id = parameterlist[parameterlist_test_name_index - 1]
    test_name = parameterlist[parameterlist_test_name_index]
    test_limit_min = parameterlist[parameterlist_test_name_index + 1]
    test_limit_max = parameterlist[parameterlist_test_name_index + 2]
    test_type = parameterlist[parameterlist_test_name_index + 3]

    print(f"Creating {test_name: <22} = {value: >16} in DATABASE (id: {id(database)})")

    # Write to database
    database.append(message_id)  # parameter number
    database.append(test_name)  # parameter name
    database.append(value)  # parameter current value
    database.append(value)  # parameter min value maesured
    database.append(value)  # parameter max value measured
    database.append('waiting')  # parameter test result
    database.append(time.time())  # system time
    database.append(test_limit_min)  # parameter low limit
    database.append(test_limit_max)  # parameter high limit
    database.append(test_type)  # parameter high limit

# ---------------------------------------------------------------------------------------------------------------------------------------

def UDP_recieve_messages(running_t1, UDP_RECIEVE_MESSAGE_QUEUE, CONSOLE_QUEUE, RAW_DATA_QUEUE, UDP_RECIEVE_STATE_QUEUE):
    UDP_recieve_state = "DISCONNECT"  # Default status

    # while running_t1.is_set():
    while not stop_threads:

        if (not UDP_RECIEVE_STATE_QUEUE.empty()):  # meddelande att sända i buffer!!
            UDP_recieve_parameter = UDP_RECIEVE_STATE_QUEUE.get()
            print(f"New UDP_receive_state: {UDP_recieve_parameter}]")

            # Stop UDP_recieve_message when disconnecting
            if UDP_recieve_parameter == "DISCONNECT":
                UDP_recieve_state = "DISCONNECT"
                print("- Disconnecting RX socket")

            if (UDP_recieve_parameter == "CONNECT"):
                UDP_recieve_state = "CONNECT"
                print("- Connecting RX socket")

            # Disconnect receive socket (and handle exception)
            elif (UDP_recieve_state == "DISCONNECT"):
                print('Shutting down UDP RX socket')
                CONSOLE_QUEUE.put('Shutting down UDP RX socket')
                try:
                    sock_recieve.shutdown(1)
                    sock_recieve.close()
                except Exception as e:
                    print("Cannot shutdown RX socket because:", e)
                time.sleep(0.1)

        # Recieve stuff
        elif (UDP_recieve_state == "CONNECT"):
            try:  # Check if message is recieved, create and bind socket if not existing (caught by exception)
                (data, addr) = sock_recieve.recvfrom(1024)  # Buffer size is 1024 bytes wait for message

                # Send message to 'recieve_data_handler' function!
                UDP_RECIEVE_MESSAGE_QUEUE.put((data, addr))
                latest_data_package = ("Recieve: %s %i" % addr, ",".join('%02x' % i for i in data))

                # Send message to GUI function to display incoming trafic!
                # print(latest_data_package)
                RAW_DATA_QUEUE.put(latest_data_package)

            except socket.timeout as timeout:
                time.sleep(0.01)
                pass

            except Exception as e:  # socket not existing start new socket!
                print("Creating RX socket because:", e)
                sock_recieve = socket.socket(socket.AF_INET,
                                             socket.SOCK_DGRAM)  # starts Internet Protocol v4 UDP socket

                try:
                    sock_recieve.bind((UDP_IP_TEST_COMPUTER, UDP_PORT))  # Listen to a ip adress and port
                    print_string = ("Binding RX socket: %s:%s" % (UDP_IP_TEST_COMPUTER, UDP_PORT))
                    sock_recieve.settimeout(0.010)
                    CONSOLE_QUEUE.put(print_string)
                    print(print_string)

                except socket.timeout as timeout:
                    pass

                # # except Exception as e:
                except Exception as e:
                    print("Cannot bind new RX socket because:", e)
                    print_string = ("FAIL, no IP adress: %s" % (UDP_IP_TEST_COMPUTER))
                    CONSOLE_QUEUE.put(print_string)
                    print(print_string)
                    # return
        time.sleep(0.002)  # Run this function with defined minimum interval. This reduce load on CPU!!!

    print("Stopped THREAD 'UDP_receive_messages'")


############################
# Function to send UDP messages on a specific IP adress and port
############################

def UDP_send_message(UDP_TRANSMIT_MESSAGE_QUEUE, RAW_DATA_QUEUE):
    UDP_send_status = "DISCONNECT"  # Default status

    while not stop_threads:
        time.sleep(0.01)  # Run this function with defined minimum interval. This reduce load on CPU!!!

        if (not UDP_TRANSMIT_MESSAGE_QUEUE.empty()):  # meddelande att sända i buffer!!
            UDP_message, UDP_send_parameter = UDP_TRANSMIT_MESSAGE_QUEUE.get()
            # Stop UDP_send_message when disconnecting
            if UDP_send_parameter == "DISCONNECT":
                UDP_send_status = "DISCONNECT"
                print("Disconnecting TX socket")

            if (UDP_send_parameter == "CONNECT"):
                UDP_send_status = "CONNECT"
                print("Connecting TX socket")

            elif (UDP_send_status == "CONNECT"):
                # Send stuff to BLOCKMASTER unit!
                if (UDP_send_parameter == BLOCKMASTER):
                    try:  # Try to send message on socket!
                        sock_send1.sendto(UDP_message, (UDP_IP_BLOCKMASTER, UDP_PORT))

                        latest_data_package = ("Send BM: %s" % ",".join('%02x' % i for i in UDP_message))
                        RAW_DATA_QUEUE.put(latest_data_package)

                    except Exception as e:  # Recreate the socket and reconnect if
                        print("Creating BM TX socket because:", e)
                        sock_send1 = socket.socket(socket.AF_INET,
                                                   socket.SOCK_DGRAM)  # starts Internet Protocol v4 UDP socket
                        sock_send1.sendto(UDP_message, (UDP_IP_BLOCKMASTER, UDP_PORT))

                        print_string = ("Sending BM data : %s:%s" % (UDP_IP_BLOCKMASTER, UDP_PORT))
                        CONSOLE_QUEUE.put(print_string)
                # Send stuff to RX unit!
                elif (UDP_send_parameter == RX):
                    try:  # Try to send message on socket!
                        sock_send2.sendto(UDP_message, (UDP_IP_RX, UDP_PORT))
                        print(f"HELLOOOOOOOOOOOOOOOOOOOOOOOOOOOO {UDP_message}\n")
                        latest_data_package = ("Send RX: %s" % ",".join('%02x' % i for i in UDP_message))
                        RAW_DATA_QUEUE.put(latest_data_package)


                    except Exception as e:  # Recreate the socket and reconnect if
                        print("Creating BM TX socket because:", e)
                        sock_send2 = socket.socket(socket.AF_INET,
                                                   socket.SOCK_DGRAM)  # starts Internet Protocol v4 UDP socket
                        sock_send2.sendto(UDP_message, (UDP_IP_RX, UDP_PORT))

                        print_string = ("Sending RX data : %s:%s" % (UDP_IP_RX, UDP_PORT))
                        CONSOLE_QUEUE.put(print_string)
                # Disconnect sockets!
                elif (UDP_send_parameter == "DISCONNECT"):
                    UDP_send_status = "DISCONNECT"
                    try:
                        sock_send1.shutdown(1)
                        sock_send1.close()
                        print("Shutting down socket 1")
                    except Exception as e:
                        print("Cannot shutdown TX BM socket because:", e)
                    try:
                        sock_send2.shutdown(1)
                        sock_send2.close()
                        print("Shutting down socket 2")
                    except Exception as e:
                        print("Cannot shutdown TX RX socket because:", e)
                else:
                    print("Wrong message type:", UDP_message, UDP_send_parameter)
    print("Stopped THREAD 'UDP_send_message'")


# ---------------------------------------------------------------------------------------------------------------------------------------

############################
# Functions to create a UDP messages in the correct format
# See HDR Communication MGSv3 document for information
############################

def create_UDP_command_packet(id, payload_size, cmd, rw, arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8):
    # ID is used to keep track of messages. The ID is returned in answear.
    upper_id_byte = (id >> 8) & 0xff
    lower_id_byte = id & 0xff

    # The CMD bytes are telling the test object which command to execute
    upper_CMD_byte = (cmd >> 8) & 0xff
    lower_CMD_byte = cmd & 0xff

    UDP_MESSAGE = bytearray([0x55, 0x56, upper_id_byte, lower_id_byte, 0x00, 0x00, 0x00  # default message header with:
                             # [uint16 protocol: 0x5556][uint16 packet nr: 0x0001][uint16 hw channel nr: 0x0000][uint16 payload size: 0x00 + first appended byte below]
                                , payload_size  # payload size (LSB)
                                , 0  # type: command (MSB)
                                , 0  # type: command (LSB)
                                , 0  # frame number (MSB)
                                , 1  # frame number (LSB)
                                , 0  # total frames (MSB)
                                , 1  # total frames (LSB)
                                , upper_CMD_byte  # command: uint16 0x003D = decimal 0061
                                , lower_CMD_byte  # cmd
                                , rw  # ARG[0] byte 0 read 1 is write
                                , arg1  # (CMD 377 I2C_operation: Chip address)
                                , arg2  # (CMD 377 I2C_operation: register address)
                                , arg3  # (CMD 377 I2C_operation: Data (MSB))
                                , arg4  # (CMD 377 I2C_operation: Data (LSB))
                                , arg5  # (CMD 377 I2C_operation: Data size (MSB))
                                , arg6  # (CMD 377 I2C_operation: Data size (LSB))
                                , arg7
                                , arg8
                             ])

    return UDP_MESSAGE


def reset_wheel_ticks(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index(parameter) - 1]
    cmd = int(parameterlist[parameterlist.index(parameter) + 4])
    CMD_PACKET = create_UDP_command_packet(id, 2, cmd, 1, 1, 0, 0, 0, 0, 0, 0,
                                           0)  # Command SET_MEAS_DIR (code 8), write (1) value: 1
    UDP_TRANSMIT_MESSAGE_QUEUE.put((CMD_PACKET, UDP_TRANSMIT_PARAMETER))


def set_delay(parameter, parameterlist, setvalue, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    delay = setvalue
    delay_byte3 = (delay >> 24) & 0xff
    delay_byte2 = (delay >> 16) & 0xff
    delay_byte1 = (delay >> 8) & 0xff
    delay_byte0 = delay & 0xff
    id = parameterlist[parameterlist.index(parameter) - 1]
    cmd = int(parameterlist[parameterlist.index(parameter) + 4])
    CMD_PACKET = create_UDP_command_packet(id, 4, cmd, 1, delay_byte3, delay_byte2, delay_byte1, delay_byte0, 0, 0, 0,
                                           0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((CMD_PACKET, UDP_TRANSMIT_PARAMETER))


def get_delay(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index(parameter) - 1]
    cmd = int(parameterlist[parameterlist.index(parameter) + 4])
    CMD_PACKET = create_UDP_command_packet(id, 4, cmd, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((CMD_PACKET, UDP_TRANSMIT_PARAMETER))


def get_trace(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index(parameter) - 1]
    cmd = int(parameterlist[parameterlist.index(parameter) + 4])
    CMD_PACKET = create_UDP_command_packet(id, 0, cmd, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((CMD_PACKET, UDP_TRANSMIT_PARAMETER))


def finalize_settings(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index(parameter) - 1]
    cmd = int(parameterlist[parameterlist.index(parameter) + 4])
    CMD_PACKET = create_UDP_command_packet(id, 2, cmd, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((CMD_PACKET, UDP_TRANSMIT_PARAMETER))


# Function
def shooting_table(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index(parameter) - 1]
    cmd = int(parameterlist[parameterlist.index(parameter) + 4])
    # CMD_PACKET = create_UDP_command_packet(id,32,cmd,1,1,192,168,1,101,1,0,1)

    upper_id_byte = (id >> 8) & 0xff
    lower_id_byte = id & 0xff

    upper_CMD_byte = (cmd >> 8) & 0xff
    lower_CMD_byte = cmd & 0xff

    CMD_PACKET = bytearray([0x55, 0x56, upper_id_byte, lower_id_byte, 0x00, 0x00, 0x00  # default message header with:
                            # [uint16 protocol: 0x5556][uint16 packet nr: 0x0001][uint16 hw channel nr: 0x0000][uint16 payload size: 0x00 + first appended byte below]
                               , 32  # payload size (LSB)
                               , 0  # type: command (MSB)
                               , 0  # type: command (LSB)
                               , 0  # frame number (MSB)
                               , 1  # frame number (LSB)
                               , 0  # total frames (MSB)
                               , 1  # total frames (LSB)
                               , upper_CMD_byte  # command: uint16 0x003D = decimal 0061
                               , lower_CMD_byte  # cmd
                               , 5  # numTx Uint8
                               , 2  # numRx Uint8
                               , 192  # IP Uint32
                               , 168  # IP Uint32
                               , 1  # IP   Uint32
                               , 101  # IP Uint32
                               , 1  # Channel ID Uint8
                               , 0  # Dynamic channel ID Uint16
                               , 1  # Dynamic channel ID Uint16
                               , 0
                               , 0
                               , 0
                               , 0
                               , 0
                               , 0
                               , 0
                               , 0
                               , 192
                               , 168
                               , 1
                               , 101
                               , 2
                               , 0
                               , 0
                               , 0
                               , 2
                               , 0
                               , 0
                               , 0
                               , 0
                               , 0
                               , 0
                            ])

    UDP_TRANSMIT_MESSAGE_QUEUE.put((CMD_PACKET, UDP_TRANSMIT_PARAMETER))


# Function
def set_runs(parameter, parameterlist, set_value, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    runs = set_value
    upper_runs_byte = (runs >> 8) & 0xff
    lower_runs_byte = runs & 0xff
    id = parameterlist[parameterlist.index(parameter) - 1]
    cmd = int(parameterlist[parameterlist.index(parameter) + 4])
    CMD_PACKET = create_UDP_command_packet(id, 3, cmd, 1, upper_runs_byte, lower_runs_byte, 0, 0, 0, 0, 0, 0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((CMD_PACKET, UDP_TRANSMIT_PARAMETER))


# Function
def set_samples(parameter, parameterlist, set_value, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    samples = set_value
    upper_samples_byte = (samples >> 8) & 0xff
    lower_samples_byte = samples & 0xff
    id = parameterlist[parameterlist.index(parameter) - 1]
    cmd = int(parameterlist[parameterlist.index(parameter) + 4])
    CMD_PACKET = create_UDP_command_packet(id, 3, cmd, 1, upper_samples_byte, lower_samples_byte, 0, 0, 0, 0, 0, 0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((CMD_PACKET, UDP_TRANSMIT_PARAMETER))


# Function
def set_stacks(parameter, parameterlist, set_value, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    stacks = set_value
    upper_stacks_byte = (stacks >> 8) & 0xff
    lower_stacks_byte = stacks & 0xff
    id = parameterlist[parameterlist.index(parameter) - 1]
    cmd = int(parameterlist[parameterlist.index(parameter) + 4])
    CMD_PACKET = create_UDP_command_packet(id, 3, cmd, 1, upper_stacks_byte, lower_stacks_byte, 0, 0, 0, 0, 0, 0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((CMD_PACKET, UDP_TRANSMIT_PARAMETER))


def discover(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index(parameter) - 1]
    cmd = int(parameterlist[parameterlist.index(parameter) + 4])
    CMD_PACKET = create_UDP_command_packet(id, 0, cmd, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((CMD_PACKET, UDP_TRANSMIT_PARAMETER))


# Function to
def get_recievers(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index(parameter) - 1]
    cmd = int(parameterlist[parameterlist.index(parameter) + 4])
    CMD_PACKET = create_UDP_command_packet(id, 0, cmd, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((CMD_PACKET, UDP_TRANSMIT_PARAMETER))


# Function to generate T0 pulse from Blockmaster (cmd_get_trace (14))
def generate_T0(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index(parameter) - 1]
    cmd = int(parameterlist[parameterlist.index(parameter) + 4])
    CMD_PACKET = create_UDP_command_packet(id, 4, cmd, 0, 0, 0, 0, 0, 0, 0, 0,
                                           0)  # CMD_GET_TRACE generates one T0 pulse from Blockmaster to all RX units
    UDP_TRANSMIT_MESSAGE_QUEUE.put((CMD_PACKET, UDP_TRANSMIT_PARAMETER))


# Function to
def set_host_IP(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index(parameter) - 1]
    cmd = int(parameterlist[parameterlist.index(parameter) + 4])
    CMD_PACKET = create_UDP_command_packet(id, 4, cmd, 1, 192, 168, 1, 1, 0, 0, 0, 0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((CMD_PACKET, UDP_TRANSMIT_PARAMETER))


# Function to
def get_channels(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index(parameter) - 1]
    cmd = int(parameterlist[parameterlist.index(parameter) + 4])
    CMD_PACKET = create_UDP_command_packet(id, 2, cmd, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((CMD_PACKET, UDP_TRANSMIT_PARAMETER))


# Function to recieve/write I2C registers
def send_read_I2C_8bitregister(id, cmd, adress_8bit, register_8bit, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    GET_I2C_MESSAGE = create_UDP_command_packet(id, 8, cmd, 0, adress_8bit, register_8bit, 0, 0, 0, 1, 0, 0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_I2C_MESSAGE, UDP_TRANSMIT_PARAMETER))


# Function to recieve/write I2C registers 1 or 2 bytes
def send_read_I2C_8or16bitregister(id, cmd, adress_8bit, register_8bit, data_size, UDP_TRANSMIT_MESSAGE_QUEUE,
                                   UDP_TRANSMIT_PARAMETER):
    GET_I2C_MESSAGE = create_UDP_command_packet(id, 8, cmd, 0, adress_8bit, register_8bit, 0, 0, 0, data_size, 0, 0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_I2C_MESSAGE, UDP_TRANSMIT_PARAMETER))


def send_write_I2C_8bitregister(id, cmd, adress_8bit, register_8bit, write_data_8bit, UDP_TRANSMIT_MESSAGE_QUEUE,
                                UDP_TRANSMIT_PARAMETER):
    GET_I2C_MESSAGE = create_UDP_command_packet(id, 8, cmd, 1, adress_8bit, register_8bit, 0, write_data_8bit, 0, 1, 0,
                                                0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_I2C_MESSAGE, UDP_TRANSMIT_PARAMETER))


def send_write_I2C_8or16bitregister(id, cmd, adress_8bit, register_8bit, data_MSB, data_LSB, data_size,
                                    UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    GET_I2C_MESSAGE = create_UDP_command_packet(id, 8, cmd, 1, adress_8bit, register_8bit, 0, data_MSB, data_LSB,
                                                data_size, 0, 0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_I2C_MESSAGE, UDP_TRANSMIT_PARAMETER))


# Function to recieve MCU FW
def send_get_MCU_FW_value(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index(parameter) - 1]

    GET_MCU_FW_MESSAGE = create_UDP_command_packet(id, 6, 61, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_MCU_FW_MESSAGE, UDP_TRANSMIT_PARAMETER))


# Function to get SYS FW version ("firmware blob version")
def get_SYS_FW_value(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index(parameter) - 1]

    GET_MCU_FW_MESSAGE = create_UDP_command_packet(id, 6, 61, 0, 0, 0, 0, 3, 0, 0, 0, 0)  # 3 = System "blob" firmware
    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_MCU_FW_MESSAGE, UDP_TRANSMIT_PARAMETER))


# Function to set SYS FW version ("firmware blob version")
def set_SYS_FW_value(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER, sys_fw_value):
    id = parameterlist[parameterlist.index(parameter) - 1]

    GET_MCU_FW_MESSAGE = create_UDP_command_packet(id, 6, 61, 1, 0, 0, 0, 3, 0, 0, 0,
                                                   sys_fw_value)  # 3 = System "blob" firmware
    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_MCU_FW_MESSAGE, UDP_TRANSMIT_PARAMETER))


# Function to recieve FPGA FW
def send_get_FPGA_FW_value(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index(parameter) - 1]

    GET_FPGA_FW_MESSAGE = create_UDP_command_packet(id, 6, 61, 0, 0, 0, 0, 1, 0, 0, 0, 0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_FPGA_FW_MESSAGE, UDP_TRANSMIT_PARAMETER))


# Function to recieve Board revision
def send_get_BOARD_REV_value(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index(parameter) - 1]

    GET_BOARD_REV_MESSAGE = create_UDP_command_packet(id, 6, 61, 0, 0, 0, 0, 2, 0, 0, 0, 0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_BOARD_REV_MESSAGE, UDP_TRANSMIT_PARAMETER))


# Function to recieve GET_WHEEL_TICK
def send_get_WHEEL_tick_value(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index(parameter) - 1]
    cmd = int(parameterlist[parameterlist.index(parameter) + 4])

    GET_WHEEL_MESSAGE = create_UDP_command_packet(id, 6, cmd, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_WHEEL_MESSAGE, UDP_TRANSMIT_PARAMETER))


# Function to recieve ADC messages
def send_get_ADC_value(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index(parameter) - 1]
    cmd = int(parameterlist[parameterlist.index(parameter) + 4])

    GET_ADC_MESSAGE = create_UDP_command_packet(id, 4, cmd, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_ADC_MESSAGE, UDP_TRANSMIT_PARAMETER))


# Function to start measurement
def send_start_meas_value(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index(parameter) - 1]
    cmd = int(parameterlist[parameterlist.index(parameter) + 4])

    START_MESSAGE = create_UDP_command_packet(id, 4, cmd, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((START_MESSAGE, UDP_TRANSMIT_PARAMETER))


# Function to turn off battery information
def send_battery_info_on_off(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index(parameter) - 1]
    cmd = int(parameterlist[parameterlist.index(parameter) + 4])

    if (parameter == "bat_info_on"):
        GET_MESSAGE = create_UDP_command_packet(id, 4, cmd, 1, 1, 0, 0, 0, 0, 0, 0, 0)
        print("Switching ON battery info sequence")
    else:
        GET_MESSAGE = create_UDP_command_packet(id, 4, cmd, 1, 0, 0, 0, 0, 0, 0, 0, 0)
        print("Switching OFF battery info sequence")

    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_MESSAGE, UDP_TRANSMIT_PARAMETER))


# Function to read parameterlist specified I2C registers:
def send_read_I2C_register_from_parameterlist(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                                              UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index(parameter) - 1]
    cmd = int(parameterlist[parameterlist.index(parameter) + 4])
    adress_7bit = int(parameterlist[parameterlist.index(parameter) + 5], 16)
    adress_8bit_read = adress_7bit << 1
    register = int(parameterlist[parameterlist.index(parameter) + 6], 16)
    data_size = int(parameterlist[parameterlist.index(parameter) + 7])

    send_read_I2C_8or16bitregister(id, cmd, adress_8bit_read, register, data_size, UDP_TRANSMIT_MESSAGE_QUEUE,
                                   UDP_TRANSMIT_PARAMETER)


# Function to read I2C registers:
def send_read_I2C1_8reg(parameterlist, adress_7bit, register_8bit, CONSOLE_QUEUE, UDP_TRANSMIT_MESSAGE_QUEUE,
                        UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index("I2C1_read_8bit") - 1]
    cmd = int(parameterlist[parameterlist.index("I2C1_read_8bit") + 4])
    adress_8bit = adress_7bit << 1

    print_string = ("Reading I2C1 reg: %s, %s" % (hex(adress_8bit), hex(register_8bit)))
    print(print_string)
    CONSOLE_QUEUE.put(print_string)

    send_read_I2C_8bitregister(id, cmd, adress_8bit, register_8bit, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER)


# Function to read I2C registers:
def send_read_I2C1_16reg(parameterlist, parameter, register_8bit, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index(parameter) - 1]
    cmd = int(parameterlist[parameterlist.index(parameter) + 4])
    adress_7bit = int(parameterlist[parameterlist.index(parameter) + 5], 16)
    adress_8bit = adress_7bit << 1
    data_size = int(parameterlist[parameterlist.index(parameter) + 7])

    send_read_I2C_8or16bitregister(id, cmd, adress_8bit, register_8bit, data_size, UDP_TRANSMIT_MESSAGE_QUEUE,
                                   UDP_TRANSMIT_PARAMETER)


# Function to write I2C registers:
def send_write_I2C1_8reg(parameterlist, adress_7bit, register_8bit, write_data_8bit, CONSOLE_QUEUE,
                         UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index("I2C1_write_8bit") - 1]
    cmd = int(parameterlist[parameterlist.index("I2C1_write_8bit") + 4])
    adress_8bit = adress_7bit << 1

    print_string = ("Writing to I2C1: %s, %s, %s" % (hex(adress_8bit), hex(register_8bit), hex(write_data_8bit)))
    print(print_string)
    CONSOLE_QUEUE.put(print_string)

    send_write_I2C_8bitregister(id, cmd, adress_8bit, register_8bit, write_data_8bit, UDP_TRANSMIT_MESSAGE_QUEUE,
                                UDP_TRANSMIT_PARAMETER)


# Function to write I2C registers:
def send_write_I2C1_16reg(parameterlist, adress_7bit, register_8bit, write_data_16bit, data_size, CONSOLE_QUEUE,
                          UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index("I2C1_write_16bit") - 1]
    cmd = int(parameterlist[parameterlist.index("I2C1_write_16bit") + 4])
    adress_8bit = adress_7bit << 1
    data_MSB = (write_data_16bit & 0xff00) >> 8
    data_LSB = write_data_16bit & 0xff

    # print_string = ("Writing to I2C1: %s, %s, %s" % (hex(adress_8bit), hex(register_8bit), hex(write_data_16bit)))
    # print(print_string)
    # CONSOLE_QUEUE.put(print_string)

    send_write_I2C_8or16bitregister(id, cmd, adress_8bit, register_8bit, data_MSB, data_LSB, data_size,
                                    UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER)


# Function to read FPGA registers:
def send_read_FPGA_register(register_adress, id):
    pass


# Function to write FPGA registers:
def send_write_FPGA_register(register_adress, data, id):
    pass


############################
# Function to create a text report file from database
############################

def write_recieved_data_to_file(filename, database, parameterlist, header_string, board_art, board_var, board_rev,
                                board_ser, CONSOLE_QUEUE, gui):
    report_list = []
    report_list_out = []

    # Open and write a textfile
    with open(filename, 'w+') as textfile:
        print_string = ("Writing data to textfile: %s" % (filename))
        print(print_string)
        CONSOLE_QUEUE.put(print_string)

        # Write file header in textfile
        textfile.write("Filename: %s\n" % filename.rsplit('/', 1)[-1])
        textfile.write("Date/Time: %s\n" % (datetime.datetime.now()))
        textfile.write("System time: %s\n\n" % (time.time()))
        textfile.write("Header info: %s\n" % header_string)
        textfile.write("\n")

        textfile.write(
            "[Number],\t[Name],\t[value],\t[min value],\t[max value],\t[test ok],\t[system time],\t[low limit],\t[high limit] ")

        textfile.write("\n")

        if (board_art == "15-002360"
                and "BM" in board_var):  # MCU Board, Blockmaster
            # All MCU related values from Blockmaster test
            low_range = 0
            high_range = 0x050

            # Some BM values
            report_list.append(0xD5)  # SW_PORT5_LED_TEST
            report_list.append(0xD6)  # SW_PORT1_LED_TEST

        elif (board_art == "15-002360"
              and "RX" in board_var):  # MCU Board, RX
            low_range = 0x0200
            high_range = 0x0300

            gui.trace_plot.save_plot(
                filename.rsplit('/', 1)[0],  # Folder (full path without filename)
                board_art,
                board_var,
                board_rev,
                board_ser)


        elif (board_art == "15-002361"):  # Blockmaster
            low_range = 0
            high_range = 0x0200

        elif (board_art == "15-002362"):  # RX Motherboard
            low_range = 0x0200
            high_range = 0x0300

            gui.trace_plot.save_plot(
                filename.rsplit('/', 1)[0],  # Folder (full path without filename)
                board_art,
                board_var,
                board_rev,
                board_ser)

        elif (board_art == "15-002312"  # ADC-board
              or board_art == "15-002363"):  # TX/HV-board
            # All RX values
            low_range = 0x0200
            high_range = 0x0300

            # Some BM values
            report_list.append(0x30)  # MCU_FW_BM
            report_list.append(0x31)  # FPGA_FW_BM

            gui.trace_plot.save_plot(
                filename.rsplit('/', 1)[0],  # Folder (full path without filename)
                board_art,
                board_var,
                board_rev,
                board_ser)

        elif (board_art == "15-002366"):  # Quad Battery Board
            low_range = 0x0303
            high_range = 0x0450

        else:
            low_range = 0
            high_range = 0xFFFF

        # Write database to textfile
        report_list_out.extend(range(low_range, high_range + 1))
        print(report_list_out)

        report_list_out.extend(report_list)
        print(report_list_out)

        # for x in range(low_range, high_range+1):  # Check all messages in parameterlist
        for x in report_list_out:
            if (x in parameterlist):
                parameterlist_object_index = parameterlist.index(x)
                parameterlist_object = parameterlist[parameterlist_object_index + 1]
                try:  # Check if parameter excist in database and write to file.
                    if (parameterlist_object in database):
                        database_object_index = database.index(parameterlist_object)
                        print_string = ("%s,\t%s,\t%s,\t%s,\t%s,\t%s,\t%s,\t%s,\t%s,\t%s\n" % (
                        database[database_object_index - 1], database[database_object_index],
                        database[database_object_index + 1], database[database_object_index + 2],
                        database[database_object_index + 3], database[database_object_index + 4],
                        database[database_object_index + 5], database[database_object_index + 6],
                        database[database_object_index + 7], database[database_object_index + 8]))
                        textfile.write(print_string)
                    else:
                        textfile.write("%s,\t%s,\tN/A\n" % (
                        parameterlist[parameterlist_object_index], parameterlist[parameterlist_object_index + 1]))
                except Exception as e:
                    print("Database ERROR")
                    print(e)
                    CONSOLE_QUEUE.put("Database ERROR")
                    break

        textfile.close()
        print("File created!")
        CONSOLE_QUEUE.put("File created!")


############################
# This function is requesting data from test object.
############################

def sequencer(UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE, CONSOLE_QUEUE, gui):
    prev_data_state = "STOP"
    request_data_state = "STOP"

    first_run = 1
    time.sleep(0.2)
    gui.test_info.load_config("LATEST")  # Load latest configuration data from config.ini at start-up

    CONSOLE_QUEUE.put("Starting thread sequencer")
    time.sleep(0.2)

    even = True  # Keep track of even/odd number of runs to control actions
    sequence_counter = 0

    while not stop_threads:

        time.sleep(0.05)  # Request data update time

        # if GUI_DATABASE_QUEUE.empty():
        # print(f"\t\t\t\t\t\tGUI_DATABASE_QUEUE size: {GUI_DATABASE_QUEUE.qsize()}")

        if (not SEQUENCER_MESSAGE_QUEUE.empty()):  # Check if there is any control messages.
            prev_data_state = request_data_state  # Store last RUN state
            request_data_state = SEQUENCER_MESSAGE_QUEUE.get()
            print(f"Prev. RUN state: {prev_data_state}")
            print(f"New RUN state:  {request_data_state}")
            if (sequences.conditional_wait(0.01, SEQUENCER_MESSAGE_QUEUE)): return

        elif (request_data_state == "GET_DELAY"):
            get_delay("DELAY_ADJ", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, RX)
            if (sequences.conditional_wait(0.1, SEQUENCER_MESSAGE_QUEUE)): return

            get_delay("DELAY", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, RX)
            time.sleep(0.4)

            request_data_state = "STOP"

        elif (request_data_state == "GET_TRACE"):

            get_delay("DELAY_ADJ", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, RX)
            if (sequences.conditional_wait(0.1, SEQUENCER_MESSAGE_QUEUE)): return

            get_delay("DELAY", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, RX)
            time.sleep(0.4)

            get_trace("GET_TRACE", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, BLOCKMASTER)
            time.sleep(0.1)

            # if(sequences.conditional_wait(0.4,SEQUENCER_MESSAGE_QUEUE)):return
            request_data_state = "STOP"

        elif (request_data_state == "RUN_BM_TEST" or request_data_state == "RUN_BM_ONCE"):
            # Increase counter
            sequence_counter += 1
            # Intitial, run only first time
            if sequence_counter == 1:
                reset_wheel_ticks("RESET_WHEEL", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, BLOCKMASTER)

            sequences.blockmaster_init(UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE, CONSOLE_QUEUE)
            sequences.blockmaster_init_gpio_values(UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE, CONSOLE_QUEUE)
            sequences.blockmaster_init_gpio_pins(UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE, CONSOLE_QUEUE)

            even = not even
            sequences.blockmaster_toggle_and_read_clock(even, UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE,
                                                        CONSOLE_QUEUE)
            sequences.blockmaster_toggle_gpio_values_A(UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE,
                                                       CONSOLE_QUEUE)
            sequences.blockmaster_read_internal_expanders(UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE,
                                                          CONSOLE_QUEUE)
            sequences.blockmaster_read_testboard_expanders(UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE,
                                                           CONSOLE_QUEUE)

            even = not even
            sequences.blockmaster_toggle_and_read_clock(even, UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE,
                                                        CONSOLE_QUEUE)
            sequences.blockmaster_toggle_gpio_values_B(UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE,
                                                       CONSOLE_QUEUE)
            sequences.blockmaster_read_internal_expanders(UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE,
                                                          CONSOLE_QUEUE)
            sequences.blockmaster_read_testboard_expanders(UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE,
                                                           CONSOLE_QUEUE)

            # even = not even
            # sequences.blockmaster_toggle_and_read_clock(even, UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE, CONSOLE_QUEUE)
            sequences.blockmaster_run_wheel_ticks(UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE, CONSOLE_QUEUE,
                                                  sequence_counter)
            sequences.blockmaster_read_values(UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE, CONSOLE_QUEUE)

            if (request_data_state == "RUN_BM_ONCE"):
                request_data_state = "STOP"

        elif (request_data_state == "RUN_RX_TEST" or request_data_state == "RUN_RX_ONCE"):
            # Increase counter
            sequence_counter += 1
            # Intitial, run only first time
            if sequence_counter == 1:
                sequences.set_RX_pwr_on(UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE,
                                        CONSOLE_QUEUE)  # Power on all RX ports
            sequences.RX_read_values(UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE, CONSOLE_QUEUE, gui)
            if (request_data_state == "RUN_RX_ONCE"):
                request_data_state = "STOP"

        elif (request_data_state == "SHOOT"):  # Get one trace
            CONSOLE_QUEUE.put("--SHOOT--")
            get_trace("GET_TRACE", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, BLOCKMASTER)
            # time.sleep(0.2)
            if (sequences.conditional_wait(0.2, SEQUENCER_MESSAGE_QUEUE)): return
            request_data_state = "STOP"


        elif request_data_state[0] == "SHOOTING_TABLE":

            CONSOLE_QUEUE.put("Sending shooting table to Blockmaster")

            print("Sending shooting table to Blockmaster")

            # Debugging Queues Safely

            print(f"request_data_state: {request_data_state}, type: {type(request_data_state)}")

            if not UDP_TRANSMIT_MESSAGE_QUEUE.empty():
                print("UDP Queue:", list(UDP_TRANSMIT_MESSAGE_QUEUE.queue))  # Don't remove items

            if not SEQUENCER_MESSAGE_QUEUE.empty():
                print("Sequencer Queue:", list(SEQUENCER_MESSAGE_QUEUE.queue))  # Don't remove items

            if not CONSOLE_QUEUE.empty():
                print("Console Queue:", list(CONSOLE_QUEUE.queue))  # Don't remove items

            # Call the shooting table function

            sequences.blockmaster_shooting_table(request_data_state, UDP_TRANSMIT_MESSAGE_QUEUE,
                                                 SEQUENCER_MESSAGE_QUEUE, CONSOLE_QUEUE)

            request_data_state = "STOP"

        # request_data_state = "RUN_BATTERY_TEST"
        elif (request_data_state == "RUN_BATTERY_TEST" or request_data_state == "RUN_BATTERY_TEST_ONCE"):
            # Increase counter
            sequence_counter += 1
            # Intitial, run only first time
            if sequence_counter == 1:
                sequences.blockmaster_init(UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE, CONSOLE_QUEUE)

            #batterytest.battery_test(CONSOLE_QUEUE, UDP_TRANSMIT_MESSAGE_QUEUE, BATTERY_MESSAGE_QUEUE,
            #                        SEQUENCER_MESSAGE_QUEUE)

            if (request_data_state == "RUN_BATTERY_TEST_ONCE"):
                request_data_state = "STOP"

        # Handle STOP commands,
        # - Empty UDP_TRANSMIT_MESSAGE_QUEUE
        if request_data_state == "STOP":
            UDP_TRANSMIT_MESSAGE_QUEUE.queue.clear()
            sequence_counter = 0
            request_data_state = "STOPPED"

    print("Stopped THREAD 'sequencer'")


# Starts all threads
def main():
    running_t1 = threading.Event()
    running_t1.set()

    # Create tkinter root window
    CONSOLE_QUEUE.put("Starting thread START_GUI")
    root = tk.Tk()
    root.title("MIRA HDR Rev2 - Production test application (v.0.18)")
    root.protocol('WM_DELETE_WINDOW', lambda: destroy(root, G))  # root is your root window
    root.configure(padx=5, pady=5)
    root.geometry("1920x1080")

    # root.state('zoomed')    # Start application in full-screen mode

    # Set ICON bitmap
    try:
        root.iconbitmap("GGEO_ICON_BLACK_32x32.ico")
    except:
        pass

    # Create GUI elements with GUI Class
    G = GUI.GUI(root, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_RECIEVE_STATE_QUEUE, GUI_DATABASE_QUEUE, SEQUENCER_MESSAGE_QUEUE,
                CONSOLE_QUEUE, RECIEVED_DATA_HANDLER_MESSAGE_QUEUE, RAW_DATA_QUEUE, PLOTTER_QUEUE)

    t1 = threading.Thread(target=UDP_recieve_messages,
                          args=[running_t1, UDP_RECIEVE_MESSAGE_QUEUE, CONSOLE_QUEUE, RAW_DATA_QUEUE,
                                UDP_RECIEVE_STATE_QUEUE])  # Start recieving UDP packages
    # t1 = threading.Thread(target=UDP_recieve_messages, args=[running_t1])       # Start recieving UDP packages
    t2 = threading.Thread(target=UDP_send_message,
                          args=[UDP_TRANSMIT_MESSAGE_QUEUE, RAW_DATA_QUEUE])  # This thread is sending UDP packages
    t3 = threading.Thread(target=recieved_data_handler,
                          args=[UDP_RECIEVE_MESSAGE_QUEUE, GUI_DATABASE_QUEUE, CONSOLE_QUEUE,
                                RECIEVED_DATA_HANDLER_MESSAGE_QUEUE, BATTERY_MESSAGE_QUEUE, PLOTTER_QUEUE,
                                parameterlist.parameterlist, G])  # This thread is unpacking the UDP packages
    # t4 = threading.Thread(target=GUI.START_GUI, args=[UDP_TRANSMIT_MESSAGE_QUEUE, UDP_RECIEVE_STATE_QUEUE, GUI_DATABASE_QUEUE, SEQUENCER_MESSAGE_QUEUE, CONSOLE_QUEUE, RECIEVED_DATA_HANDLER_MESSAGE_QUEUE, RAW_DATA_QUEUE, PLOTTER_QUEUE]) #This is the GUI thread

    t5 = threading.Thread(target=sequencer, args=[UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE, CONSOLE_QUEUE,
                                                  G])  # This thread is requesting data from test object.

    t1.start()
    t2.start()
    t3.start()
    # t4.start()
    t5.start()

    # Run tkinter window mainloop
    root.mainloop()

    # Message after exiting root.mainloop()
    print("Stopped 'GUI' window mainloop")
    print("-------TERMINATING---------")
    print(" ")


def destroy(root, gui):
    # check if saving
    # if not:
    global stop_threads

    print(" ")
    print("----Shutting down [1/3]----")
    gui.test_info.save_config("LATEST")
    time.sleep(0.1)
    print("Stoppings sockets...")
    UDP_RECIEVE_STATE_QUEUE.put("DISCONNECT")
    UDP_TRANSMIT_MESSAGE_QUEUE.put((0, "DISCONNECT"))
    print("Waiting for sockets to close..")
    time.sleep(0.5)
    print("----Shutting down [2/3]----")
    print("Closing other threads")
    stop_threads = True
    print('Waiting 1s for threads to stop...')
    time.sleep(0.2)
    print("----Shutting down [2/3]----")

    root.destroy()


# Read parameters-----------------------------------------------------------------------------------------
#

if __name__ == "__main__":
    print("Starting MAIN")
    main()