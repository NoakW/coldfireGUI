import parameterlist
import socket
import queue
import threading
import time
import tkinter as tk
import struct
import traceback
from queue import Empty

UDP_IP_TEST_COMPUTER = "192.168.1.1"
UDP_IP_BLOCKMASTER = "192.168.1.2"
UDP_IP_RX = "192.168.1.101"
UDP_PORT = 0x555

BLOCKMASTER = "SOCKET1"
RX = "SOCKET2"

RX_ports_debounce = 0
RX_last_port_data = 0

stop_threads = False
PACKET_QUEUE = queue.Queue(maxsize=5000)

UDP_RECIEVE_MESSAGE_QUEUE = queue.Queue()  # Used to transmit raw UDP data to data handler thread. UDP_recieve_messages --> recieved_data_handler
UDP_TRANSMIT_MESSAGE_QUEUE = queue.Queue()  # Used to transmit raw UDP data to ethernet packages. ALL_THREADS --> UDP_transmit_messages
GUI_DATABASE_QUEUE = queue.Queue()  # Used to feed GUI with test database. recieved_data_handler -->  GUI
CONSOLE_QUEUE = queue.Queue()  # Used to print console messages in GUI. ALL_THREADS --> GUI.
RAW_DATA_QUEUE = queue.Queue()  # Used to print RAW UDP data in GUI. ALL_THREADS --> GUI.

SEQUENCER_MESSAGE_QUEUE = queue.Queue()  # Used to send control messages to request_data thread. GUI --> request_data.
RECIEVED_DATA_HANDLER_MESSAGE_QUEUE = queue.Queue()  # Used to send control messages to recieved_data_handler thread. GUI --> recieved_data_handler.
UDP_RECIEVE_STATE_QUEUE = queue.Queue()  # Used to send control messages to UDP_recieve_messages thread. GUI --> UDP_recieve_messages.
PLOTTER_QUEUE = queue.Queue()  # Used to send control messages to UDP_recieve_messages thread. GUI --> UDP_recieve_messages.
BATTERY_MESSAGE_QUEUE = queue.Queue()  # Used to send control messages to battery_test thread. GUI --> battery_test.

receiver_thread_instance = None
processor_thread_instance = None
run_thread = None

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


def stop_run(udp_socket, response_text, mode):
    global run_thread, stop_threads, receiver_thread_instance, processor_thread_instance

    if run_thread and run_thread.is_alive():
        # Signal threads to stop
        stop_threads = True

        if mode == "RUN":
            response_text.insert(tk.END,f"Stopping {mode}...\n")
            try:
                stop_measurement(UDP_TRANSMIT_MESSAGE_QUEUE, BLOCKMASTER)
                udp_message, _ = UDP_TRANSMIT_MESSAGE_QUEUE.get()
                udp_socket.sendto(udp_message, (UDP_IP_BLOCKMASTER, UDP_PORT))
            except Exception as e:
                response_text.insert(tk.END,f"Error stopping the measurement: {e}\n")
        elif mode == "TRACE":
            response_text.insert(tk.END,f"Stopping {mode}...")

        # Clean up threads
        if receiver_thread_instance and receiver_thread_instance.is_alive():
            receiver_thread_instance.join()
        if processor_thread_instance and processor_thread_instance.is_alive():
            processor_thread_instance.join()
        if run_thread and run_thread.is_alive():
            run_thread.join()

        run_thread = None
        stop_threads = False

    else:
        response_text.insert(tk.END,f"Unexpected error: no active threads\n")


def start_run(udp_socket, order, repeat, runs,data_file,response_text,mode):
    global run_thread, stop_threads, receiver_thread_instance, processor_thread_instance

    if run_thread and run_thread.is_alive():
        return

    stop_threads = False

    # Start the run thread for received data handler
    run_thread = threading.Thread(target=received_rundata_handler,
                                  args=[udp_socket,response_text],
                                  daemon=True)
    run_thread.start()

    # Start the receiver thread to listen for incoming UDP packets
    receiver_thread_instance = threading.Thread(target=receiver_thread, args=[udp_socket,response_text], daemon=True)
    receiver_thread_instance.start()

    # Start the processor thread to process the data from the queue
    processor_thread_instance = threading.Thread(target=processor_thread, args=[order, repeat, runs,data_file], daemon=True)
    processor_thread_instance.start()
    if mode == "RUN":
        try:
            send_start_meas_value("START_MEAS", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, BLOCKMASTER)
            udp_message, _ = UDP_TRANSMIT_MESSAGE_QUEUE.get()
            udp_socket.sendto(udp_message, (UDP_IP_BLOCKMASTER, UDP_PORT))
            response_text.insert(tk.END,"Run active...")
        except Exception as e:
            response_text.insert(tk.END, f"Error {e}\n")

    elif mode == "TRACE":
        try:
            send_start_meas_value("GET_TRACE", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, BLOCKMASTER)
            udp_message, _ = UDP_TRANSMIT_MESSAGE_QUEUE.get()
            udp_socket.sendto(udp_message, (UDP_IP_BLOCKMASTER, UDP_PORT))
        except Exception as e:
            response_text.insert(tk.END,f"Error {e}\n")

def receiver_thread(mysocket,response_text):
    """ Receives UDP packets and pushes them into a queue """
    while not stop_threads:
        try:
            # Add timeout for non-blocking behavior
            mysocket.settimeout(0.2)  # Timeout of 0.5 seconds for checking stop_threads flag
            data, address = mysocket.recvfrom(1024)
            if address[0] == "192.168.1.101":
                PACKET_QUEUE.put((time.time(), data))  # Add timestamp for debugging
        except socket.timeout:
            # Timeout is used to periodically check stop_threads flag
            continue
        except Exception as e:
            response_text.insert(tk.END,f"Receiver Error: {e}\n")


def received_rundata_handler(mysocket,response_text):
    """ This is where the thread will run its operations, and it checks for stop_threads flag """
    while not stop_threads:
        try:
            # Add timeout for non-blocking behavior
            mysocket.settimeout(0.5)  # Timeout of 0.5 seconds for checking stop_threads flag
            data, address = mysocket.recvfrom(1024)
            if address[0] == UDP_IP_RX:
                PACKET_QUEUE.put((time.time(), data))  # Add timestamp for debugging
        except socket.timeout:
            # Timeout is used to periodically check stop_threads flag
            continue
        except Exception as e:
            response_text.insert(tk.END,f"Receiver Error: {e}\n")


def processor_thread(order, reps, runs, data_file):
    """Processes UDP packets from queue and writes to file only if dynamic_channel_id == 2"""
    received_traces = {}
    address = UDP_IP_RX

    while not stop_threads:
        try:
            timestamp, data = PACKET_QUEUE.get(timeout=0.5)
            if not data:
                continue

            package_header = PackageHeader(data[:16])
            block_header = BlockHeader(data[16:33])

            # Extract trace data
            if block_header.frame_number == 1:
                if len(data) < 42:
                    print(f"Error: Packet too short for TraceHeader. Got {len(data)} bytes.")
                    continue
                _ = TraceHeader(data[33:42])  # Unused in this snippet, but parsed for completeness
                raw_trace = data[42:]
            else:
                raw_trace = data[33:]

            channel_id = package_header.dynamic_channel_id
            frame_num = package_header.frame_number
            packet_num = package_header.package_number
            total_frames = package_header.number_of_frames

            # Init or reset channel trace buffer
            if channel_id not in received_traces.get(address, {}):
                received_traces[address] = {
                    channel_id: {
                        "trace": [[] for _ in range(16)],
                        "received_frames": 0,
                        "packet_number": 0
                    }
                }

            trace_entry = received_traces[address][channel_id]

            if trace_entry["packet_number"] != packet_num:
                trace_entry["trace"] = [[] for _ in range(16)]
                trace_entry["received_frames"] = 0

            trace_entry["trace"][frame_num] = raw_trace
            trace_entry["received_frames"] += 1
            trace_entry["packet_number"] = packet_num

            # Process complete trace
            if trace_entry["received_frames"] == total_frames:
                full_trace = []
                for i in range(1, total_frames + 1):
                    full_trace += trace_entry["trace"][i]

                # Convert to signed uint32
                full_trace = [struct.unpack('!I', bytes(full_trace[i:i + 4]))[0] for i in range(0, len(full_trace), 4)]
                full_trace = [val - 0x80000000 for val in full_trace]

                # Only store if channel ID is 2
                if channel_id == 2:
                    new_row = f"{order},{reps},{runs},{address},{channel_id},{time.time()},empty1,empty2,empty3,{','.join(map(str, full_trace))}\n"

                    try:
                        with open(data_file, 'r') as f:
                            trace_rows = f.readlines()
                    except FileNotFoundError:
                        trace_rows = []

                    trace_rows.append(new_row)

                    with open(data_file, 'w') as f:
                        f.writelines(trace_rows)

                    time.sleep(0.01)

        except Empty:
            continue
        except Exception as e:
            print(f"[ProcessorThread ERROR] {e}")
            traceback.print_exc()


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

def trig_src_time(UDP_TRANSMIT_MESSAGE_QUEUE,UDP_TRANSMIT_PARAMETER):
    MESSAGE = bytearray([
        0x55, 0x56,  # Protocol ID (0x5556)
        0x00, 0x01,  # Packet Number (0x0001)
        0x00, 0x00,
        0x00  # Hardware Channel Number (0x0000)
    ])

    MESSAGE.append(2)  # len #
    MESSAGE.append(0)
    MESSAGE.append(0)  # type: command
    MESSAGE.append(0)  # frame num
    MESSAGE.append(1)  # frame num
    MESSAGE.append(0)  # num frames
    MESSAGE.append(1)  # numframes
    MESSAGE.append(0)  # command
    MESSAGE.append(5)  # command
    MESSAGE.append(1)
    MESSAGE.append(2)

    UDP_TRANSMIT_MESSAGE_QUEUE.put((MESSAGE,UDP_TRANSMIT_PARAMETER))

def trig_cond(delay,UDP_TRANSMIT_MESSAGE_QUEUE,UDP_TRANSMIT_PARAMETER):
    MESSAGE = bytearray([
        0x55, 0x56,  # Protocol ID (0x5556)
        0x00, 0x01,  # Packet Number (0x0001)
        0x00, 0x00,
        0x00  # Hardware Channel Number (0x0000)
    ])

    MESSAGE.append(5)
    MESSAGE.append(0)
    MESSAGE.append(0)  # type: command
    MESSAGE.append(0)
    MESSAGE.append(1)
    MESSAGE.append(0)  # total frames
    MESSAGE.append(1)  # total frames
    MESSAGE.append(0)
    MESSAGE.append(6)
    MESSAGE.append(1)
    MESSAGE.append(0)
    MESSAGE.append(0)
    MESSAGE.append(0)
    MESSAGE.append(delay)

    UDP_TRANSMIT_MESSAGE_QUEUE.put((MESSAGE, UDP_TRANSMIT_PARAMETER))

def stop_measurement(UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    MESSAGE = bytearray([
        0x55, 0x56,  # Protocol ID (0x5556)
        0x00, 0x01,  # Packet Number (0x0001)
        0x00, 0x00,
        0x00  # Hardware Channel Number (0x0000)
    ])

    MESSAGE.append(2)
    MESSAGE.append(0)
    MESSAGE.append(0)
    MESSAGE.append(0)
    MESSAGE.append(1)  # frame number
    MESSAGE.append(0)  # total frames
    MESSAGE.append(1)  # total frames
    MESSAGE.append(0)
    MESSAGE.append(13)

    UDP_TRANSMIT_MESSAGE_QUEUE.put((MESSAGE, UDP_TRANSMIT_PARAMETER))

def meas_dir(UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    MESSAGE = bytearray([
        0x55, 0x56,  # Protocol ID (0x5556)
        0x00, 0x01,  # Packet Number (0x0001)
        0x00, 0x00,
        0x00  # Hardware Channel Number (0x0000)
    ])

    MESSAGE.append(5)
    MESSAGE.append(0)
    MESSAGE.append(0)  # type: command
    MESSAGE.append(0)
    MESSAGE.append(1)
    MESSAGE.append(0)
    MESSAGE.append(1)  # total frames
    MESSAGE.append(0)
    MESSAGE.append(8)
    MESSAGE.append(1)
    MESSAGE.append(1)

    UDP_TRANSMIT_MESSAGE_QUEUE.put((MESSAGE, UDP_TRANSMIT_PARAMETER))

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
    GET_I2C_MESSAGE = create_UDP_command_packet(id,8,cmd,0,adress_8bit,register_8bit,0,0,0,1,0,0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_I2C_MESSAGE, UDP_TRANSMIT_PARAMETER))

# Function to recieve/write I2C registers 1 or 2 bytes
def send_read_I2C_8or16bitregister(id, cmd, adress_8bit, register_8bit,data_size,UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    GET_I2C_MESSAGE = create_UDP_command_packet(id,8,cmd,0,adress_8bit,register_8bit,0,0,0,data_size,0,0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_I2C_MESSAGE, UDP_TRANSMIT_PARAMETER))

def send_write_I2C_8bitregister(id, cmd, adress_8bit, register_8bit, write_data_8bit, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    GET_I2C_MESSAGE = create_UDP_command_packet(id,8,cmd,1,adress_8bit,register_8bit,0,write_data_8bit,0,1,0,0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_I2C_MESSAGE, UDP_TRANSMIT_PARAMETER))

def send_write_I2C_8or16bitregister(id, cmd, adress_8bit, register_8bit, data_MSB, data_LSB, data_size, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    GET_I2C_MESSAGE = create_UDP_command_packet(id,8,cmd,1,adress_8bit,register_8bit,0,data_MSB,data_LSB,data_size,0,0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_I2C_MESSAGE, UDP_TRANSMIT_PARAMETER))

# Function to recieve MCU FW
def send_get_MCU_FW_value(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):

    id = parameterlist[parameterlist.index(parameter)-1]

    GET_MCU_FW_MESSAGE = create_UDP_command_packet(id,6,61,0,0,0,0,0,0,0,0,0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_MCU_FW_MESSAGE, UDP_TRANSMIT_PARAMETER))

# Function to get SYS FW version ("firmware blob version")
def get_SYS_FW_value(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):

    id = parameterlist[parameterlist.index(parameter)-1]

    GET_MCU_FW_MESSAGE = create_UDP_command_packet(id,6,61,0,0,0,0,3,0,0,0,0) # 3 = System "blob" firmware
    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_MCU_FW_MESSAGE, UDP_TRANSMIT_PARAMETER))

# Function to set SYS FW version ("firmware blob version")
def set_SYS_FW_value(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER, sys_fw_value):

    id = parameterlist[parameterlist.index(parameter)-1]

    GET_MCU_FW_MESSAGE = create_UDP_command_packet(id,6,61,1,0,0,0,3,0,0,0,sys_fw_value) # 3 = System "blob" firmware
    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_MCU_FW_MESSAGE, UDP_TRANSMIT_PARAMETER))

# Function to recieve FPGA FW
def send_get_FPGA_FW_value(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):

    id = parameterlist[parameterlist.index(parameter)-1]

    GET_FPGA_FW_MESSAGE = create_UDP_command_packet(id,6,61,0,0,0,0,1,0,0,0,0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_FPGA_FW_MESSAGE, UDP_TRANSMIT_PARAMETER))

# Function to recieve Board revision
def send_get_BOARD_REV_value(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):

    id = parameterlist[parameterlist.index(parameter)-1]

    GET_BOARD_REV_MESSAGE = create_UDP_command_packet(id,6,61,0,0,0,0,2,0,0,0,0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_BOARD_REV_MESSAGE, UDP_TRANSMIT_PARAMETER))

# Function to recieve GET_WHEEL_TICK
def send_get_WHEEL_tick_value(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):

    id = parameterlist[parameterlist.index(parameter)-1]
    cmd = int(parameterlist[parameterlist.index(parameter)+4])

    GET_WHEEL_MESSAGE = create_UDP_command_packet(id,6,cmd,0,0,0,0,0,0,0,0,0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_WHEEL_MESSAGE, UDP_TRANSMIT_PARAMETER))

# Function to recieve ADC messages
def send_get_ADC_value(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):

    id = parameterlist[parameterlist.index(parameter)-1]
    cmd = int(parameterlist[parameterlist.index(parameter)+4])

    GET_ADC_MESSAGE = create_UDP_command_packet(id,4,cmd,0,0,0,0,0,0,0,0,0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((GET_ADC_MESSAGE, UDP_TRANSMIT_PARAMETER))


# Function to start measurement
def send_start_meas_value(parameter, parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER):
    id = parameterlist[parameterlist.index(parameter) - 1]
    cmd = int(parameterlist[parameterlist.index(parameter) + 4])

    START_MESSAGE = create_UDP_command_packet(id, 4, cmd, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    UDP_TRANSMIT_MESSAGE_QUEUE.put((START_MESSAGE, UDP_TRANSMIT_PARAMETER))


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


    send_write_I2C_8or16bitregister(id, cmd, adress_8bit, register_8bit, data_MSB, data_LSB, data_size,
                                    UDP_TRANSMIT_MESSAGE_QUEUE, UDP_TRANSMIT_PARAMETER)

