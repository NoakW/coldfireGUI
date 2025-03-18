import socket
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import correlate
import time
import parameterlist
import queue
import sequences
import testengine
import threading
from bscan import bscan_main
from matplotlib import gridspec

UDP_TRANSMIT_MESSAGE_QUEUE = queue.Queue()
SEQUENCER_MESSAGE_QUEUE = queue.Queue()
CONSOLE_QUEUE = queue.Queue()
UDP_RECEIVE_MESSAGE_QUEUE = queue.Queue()

TRACE_FILE = "trace_container2.txt"
COLDFIRE_IP = "192.168.1.2"  # Coldfire device IP
RX_IP = "192.168.1.101"
UDP_PORT: int = 0x555  # Port
udp_socket = None  # Global socket variable
all_traces = []

flipper = True

clock_freq = 160e6 # Hz
interval = 1.6e-6 # s

# Function to establish an udp connection
def connect_udp():
    MESSAGE = bytearray([0x55, 0x56, 0x00, 0x01, 0x00, 0x00, 0x00])
    global udp_socket
    try:
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind((socket.gethostbyname(socket.gethostname()), UDP_PORT))
        udp_socket.settimeout(1)  # Set a timeout to prevent blocking

        MESSAGE.append(6)  # payload size (LSB)
        MESSAGE.append(0)
        MESSAGE.append(0)  # type command
        MESSAGE.append(0)
        MESSAGE.append(1)  # frame number
        MESSAGE.append(0)  # total frames
        MESSAGE.append(1)  # total frames
        MESSAGE.append(0)  # command: uint16 0x003D = decimal 0061
        MESSAGE.append(61)
        MESSAGE.append(0)  # cmd
        MESSAGE.append(0)
        MESSAGE.append(0)
        MESSAGE.append(0)
        MESSAGE.append(0)

        udp_socket.sendto(MESSAGE, (RX_IP, UDP_PORT))
        data, adr = udp_socket.recvfrom(1024)

        response_text.insert(tk.END, f"Connected on local port {socket.gethostbyname(socket.gethostname())}.\n")

        if data:
            payload = data[16:]
            payload_str = ""
            for i, h in enumerate(payload):
                payload_str += str(h) + " "
                if i % 4 == 3:
                    payload_str += "\n"
            print(f"response data: {payload_str}\n")
            response_text.insert(tk.END, f"Version: {payload_str}")
            connect_button.configure(state=tk.DISABLED, background="#8cde83", foreground="white")
    except Exception as e:
        udp_socket = None
        response_text.insert(tk.END, f"Connection failed: {e}\n")

def close_udp():
    global udp_socket

    if udp_socket:
        try:
            udp_socket.close()
        except Exception as e:
            print(f"Unknown error {e}\n")
            pass

    response_text.insert(tk.END, "UDP connection closed.\n")
    root.destroy()

def plot_and_send_command():
    global interval, clock_freq

    chip_time = 1/(2*clock_freq)
    error_list = []
    order = []
    repetitions = []

    if not udp_socket:
        response_text.insert(tk.END, "Error: Not connected to Coldfire.\n")
        return

    try:
        # Validate repetitions input
        order_input = command_input.get().strip()
        if not order_input:
            error_list.append("Enter M-sequence order.")
        elif not order_input.isdigit():
            error_list.append("M-sequence order must be an integer.")
        else:
            order = int(order_input)
            if not (5 <= order <= 12):
                error_list.append("M-sequence order must be between 5 and 12.")

        total_time = 0.000000001
        #total_time = (2**order-1) * chip_time

        if total_time > interval:
            error_list.append("Sequence too long.")

        repetitions_input = repeat_input.get().strip()
        if not repetitions_input:
            error_list.append("Enter number of repetitions.")
        elif not repetitions_input.isdigit():
            error_list.append("Repetitions must be a number.")
        else:
            repetitions = int(repetitions_input)

        max_reps = np.floor(interval/total_time)
        total_time *= repetitions

        if total_time > interval:
            error_list.append(f"Too many repetitions for signal order: {order}. \nMax reps: {max_reps}")
        # Validate M-sequence order input

        # Stop execution if there are validation errors
        if error_list:
            response_text.insert(tk.END, "Error: " + " | ".join(error_list) + "\n")
            return

        # Generate M-sequence data
        data = plot(order)
        data[data == -1] = 0  # Convert -1 to 0
        data = data.astype(np.uint8)

        response_text.insert(tk.END, f"\nSENT: M-sequence order = {order}, repetitions = {repetitions}.")

        time.sleep(0.2)
        send_ctrl(order)
        time.sleep(0.1)
        send_reps(repetitions)
        time.sleep(0.1)
        send_sequence(data)

    except Exception as e:
        response_text.insert(tk.END, f"Unexpected error: {e}\n")

def send_reps(repetitions):

    print(repetitions)
    # Construct the message with correct header
    MESSAGE = bytearray([
        0x55, 0x56,  # Protocol ID (0x5556)
        0x00, 0x01,  # Packet Number (0x0001)
        0x00, 0x00,
        0x00  # Hardware Channel Number (0x0000)
    ])

    MESSAGE.append(4)  # payload size (LSB)
    MESSAGE.append(0)
    MESSAGE.append(0)  # type command
    MESSAGE.append(0)
    MESSAGE.append(1)  # frame number
    MESSAGE.append(0)  # total frames
    MESSAGE.append(1)
    MESSAGE.append(1)
    MESSAGE.append(137)
    MESSAGE.append(0)
    MESSAGE.extend(repetitions.to_bytes(2,byteorder='big'))
    MESSAGE.append(0)

    hex_representation = MESSAGE.hex(sep="|")

    try:
        udp_socket.sendto(MESSAGE, (RX_IP, UDP_PORT))  # Send packed message
        if enable_MESSAGE_debug_var.get():
            response_text.insert(tk.END, f"Repetitions message 16-bit stream:\n {MESSAGE}\n")
        if enable_HEX_debug_var.get():
            response_text.insert(tk.END, f"Hex: {hex_representation}\n")

        udp_socket.settimeout(5)
        while True:
            try:
                data, adr = udp_socket.recvfrom(1024)
                if adr[0] == RX_IP:
                    break  # Exit loop if response is from RX_IP
            except Exception as e:
                response_text.insert(tk.END, f"Timeout or error: {e}\n")
                return

        if data:
            payload = data[16:]
            payload_str = ""
            for i, h in enumerate(payload):
                payload_str += str(h) + " "
                if i % 4 == 3:
                    payload_str += "\n"
            print(f"response data: {payload_str}\n")
            if enable_RESPONSE_debug_var.get():
                response_text.insert(tk.END, f"\nRepetitions: {payload_str}")

    except Exception as e:
        response_text.insert(tk.END, f"Error sending message: {e}\n")

def send_sequence(data):
    bit_string = "".join(str(bit) for bit in data)

    # Ensure length is a multiple of 16 by padding at the end
    padding = (16 - (len(bit_string) % 16)) % 16  # Avoid adding extra 16 if already aligned
    bit_string += "0" * padding

    # Convert to 16-bit words
    packed_16bit_words = [int(bit_string[i:i + 16], 2) for i in range(0, len(bit_string), 16)]
    for word in packed_16bit_words:

        # Construct the header
        MESSAGE = bytearray([
            0x55, 0x56,  # Protocol ID (0x5556)
            0x00, 0x01,  # Packet Number (0x0001)
            0x00, 0x00,  # Hardware Channel Number (0x0000)
            0x00])

        MESSAGE.append(4)  # payload size (LSB)
        MESSAGE.append(0)
        MESSAGE.append(0)  # type: command
        MESSAGE.append(0)
        MESSAGE.append(1)  # frame number
        MESSAGE.append(0)  # total frames
        MESSAGE.append(1)
        MESSAGE.append(1)
        MESSAGE.append(136)
        MESSAGE.append(0)
        MESSAGE.extend(word.to_bytes(2, byteorder='big'))
        MESSAGE.append(0)

        print(f"DATA message {MESSAGE}")

        # Convert to hex for debugging
        hex_representation = MESSAGE.hex(sep="|")

        try:
            time.sleep(0.2)
            udp_socket.sendto(MESSAGE, (RX_IP, UDP_PORT))  # Send packed message

            if enable_MESSAGE_debug_var.get():
                response_text.insert(tk.END, f"Sequence message 16-bit stream:\n {MESSAGE}\n")
            if enable_HEX_debug_var.get():
                response_text.insert(tk.END, f"Hex: {hex_representation}\n")

        # Receive response
            udp_socket.settimeout(1)
            while True:
                try:
                    data, adr = udp_socket.recvfrom(1024)
                    if adr[0] == RX_IP:
                        break  # Exit loop if response is from RX_IP
                except Exception as e:
                    response_text.insert(tk.END, f"Timeout or error: {e}\n")
                    return

            if data:
                payload = data[16:]
                payload_str = " ".join(str(h) for h in payload)
                print(f"Response data: {payload_str}\n")
                if enable_RESPONSE_debug_var.get():
                    response_text.insert(tk.END, f"\nSequence response: {payload_str}")
        except Exception as e:
            response_text.insert(tk.END, f"Error sending message: {e}\n")

    response_text.insert(tk.END, "\n")

def send_ctrl(order):

    MESSAGE_CTRL = bytearray([
        0x55, 0x56,  # Protocol ID (0x5556)
        0x00, 0x01,  # Packet Number (0x0001)
        0x00, 0x00,
        0x00  # Hardware Channel Number (0x0000)
    ])

    MESSAGE_CTRL.append(4)  # payload size (LSB)
    MESSAGE_CTRL.append(0)
    MESSAGE_CTRL.append(0)  # type: command
    MESSAGE_CTRL.append(0)
    MESSAGE_CTRL.append(1)  # frame number
    MESSAGE_CTRL.append(0)  # total frames
    MESSAGE_CTRL.append(1)
    MESSAGE_CTRL.append(1)  # 0x01 command:
    MESSAGE_CTRL.append(135)  # 0x87  --> total 0x0187 --> 391
    MESSAGE_CTRL.append(0)
    MESSAGE_CTRL.append(0)
    MESSAGE_CTRL.append(order)
    MESSAGE_CTRL.append(0)

    print(f"Order (16-bit): {order:016b}")
    print(f"Byte stored: {MESSAGE_CTRL[-2]:08b}")  # Print the byte representation

    hex_representation = MESSAGE_CTRL.hex(sep="|")

    # Send message over UDP
    try:
        udp_socket.sendto(MESSAGE_CTRL, (RX_IP, UDP_PORT))  # Send packed message
        if enable_MESSAGE_debug_var.get():
            response_text.insert(tk.END, f"Message 16-bit stream:\n {MESSAGE_CTRL}\n")
        if enable_HEX_debug_var.get():
            response_text.insert(tk.END, f"Hex: {hex_representation}\n")

        udp_socket.settimeout(1)
        while True:
            try:
                data, adr = udp_socket.recvfrom(1024)
                if adr[0] == RX_IP:
                    break  # Exit loop if response is from RX_IP
            except Exception as e:
                response_text.insert(tk.END, f"Timeout or error: {e}\n")
                return

        if data:
            payload = data[16:]
            payload_str = ""
            for i, h in enumerate(payload):
                payload_str += str(h) + " "
                if i % 4 == 3:
                    payload_str += "\n"
            if enable_RESPONSE_debug_var.get():
                response_text.insert(tk.END, f"\nOrder: {payload_str}")
    except Exception as e:
        response_text.insert(tk.END, f"Error sending message: {e}\n")

def reset_registers():

    if udp_socket:
        send_ctrl(0)
        time.sleep(0.1)
        send_reps(0)
        time.sleep(0.1)
        data = np.zeros(4095, dtype=np.uint8)
        send_sequence(data)
    else:
        response_text.insert(tk.END,"Error: Not connected to FPGA\n")

def shooting_table(runs, samples, stacks):

    global udp_socket

    if udp_socket:
        # Step 1: Send SHOOTING_TABLE to Blockmaster
        request_data_state = ('SHOOTING_TABLE', runs, samples, stacks)
        sequences.blockmaster_shooting_table(request_data_state, UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE,
                                             CONSOLE_QUEUE)
        response_text.insert(tk.END, CONSOLE_QUEUE.get())
        while not UDP_TRANSMIT_MESSAGE_QUEUE.empty():
            udp_message, target_ip = UDP_TRANSMIT_MESSAGE_QUEUE.get()
            print(f"Sending to {COLDFIRE_IP}: {udp_message.hex()}")
            udp_socket.sendto(udp_message, (COLDFIRE_IP, UDP_PORT))
            time.sleep(0.3)

        response_text.insert(tk.END,"\nShooting table successfully sent\n")
        print('ENABLE RX PART')

        # Step 2: Enable RX Ports
        sequences.set_RX_pwr_on(UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE, CONSOLE_QUEUE)

        response_text.insert(tk.END,CONSOLE_QUEUE.get())
        while not UDP_TRANSMIT_MESSAGE_QUEUE.empty():
            udp_message, target_ip = UDP_TRANSMIT_MESSAGE_QUEUE.get()
            print(f"Sending to {RX_IP}: {udp_message.hex()}")
            udp_socket.sendto(udp_message, (RX_IP, UDP_PORT))
            time.sleep(2)
        response_text.insert(tk.END,"\nRX power on\n")

    else:
        response_text.insert(tk.END, "Error: Not connected to FPGA")


stop_measurement = False  # Use a flag to stop the loop safely

def run_measurement(arg):
    global udp_socket, receiver_thread, stop_measurement

    if arg == "start":
        # Stop existing measurement if already running
        if udp_socket:
            udp_socket.close()
            print("Closed existing socket.")

        # Create a new UDP socket
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.settimeout(5)
        udp_socket.bind(("", 0x555))

        # Reset stop flag
        stop_measurement = False

        # Start receiver thread
        receiver_thread = threading.Thread(target=testengine.recieved_data_handler, args=[CONSOLE_QUEUE, udp_socket],
                                           daemon=True)
        receiver_thread.start()

        # Update GUI safely
        run_button.after(0, lambda: run_button.configure(text="Stop", background="#d4263a",
                                                         command=lambda: run_measurement("stop")))

        # Start measurement loop in a new thread
        threading.Thread(target=measurement_loop, daemon=True).start()

    elif arg == "stop":
        stop_measurement = True  # Set stop flag to exit loop
        if udp_socket:
            udp_socket.close()
            udp_socket = None
            print("Measurement stopped, socket closed.")

        # Update GUI safely
        run_button.after(0, lambda: run_button.configure(text="Run", background="#129628",
                                                         command=lambda: run_measurement("start")))

def measurement_loop():
    """
    Handles sending GET_TRACE commands and waiting for responses.
    Runs until stop_measurement is set to True.
    """
    global stop_measurement

    while not stop_measurement:
        # Step 1: Send GET_TRACE command
        testengine.get_trace("GET_TRACE", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                             testengine.BLOCKMASTER)

        # Step 2: Transmit UDP messages
        while not UDP_TRANSMIT_MESSAGE_QUEUE.empty():
            udp_message, _ = UDP_TRANSMIT_MESSAGE_QUEUE.get()
            print(f"Sending GET_TRACE command to {COLDFIRE_IP}: {udp_message.hex()}")
            if udp_socket:
                udp_socket.sendto(udp_message, (COLDFIRE_IP, UDP_PORT))
            time.sleep(2)

        # Step 3: Wait for trace to be written
        time.sleep(3)

        # Step 4: Read and process the trace file
        try:
            with open(TRACE_FILE, "r") as file:
                lines = file.readlines()

            if lines:
                response_text.after(0, lambda: response_text.insert(tk.END, "\nTrace obtained\n"))
                print(f"Trace file updated! Last trace: {lines[-1][:50]}...")  # Show first 50 chars
            else:
                print("Trace file is still empty!")
        except FileNotFoundError:
            print(f"Error: {TRACE_FILE} not found!")

    print("Measurement loop stopped.")


def trace():

    global udp_socket
    if udp_socket:
        udp_socket.close()
        print("Closed existing socket.")

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(5)
    udp_socket.bind(("", 0x555))

    receiver_thread = threading.Thread(target=testengine.recieved_data_handler, args=[CONSOLE_QUEUE, udp_socket],
                                       daemon=True)
    receiver_thread.start()

    with open(TRACE_FILE, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
        last_recorded_row = lines[-1] if lines else None

    if udp_socket:
        testengine.get_trace("GET_TRACE", parameterlist.parameterlist, UDP_TRANSMIT_MESSAGE_QUEUE,
                             testengine.BLOCKMASTER)
        while not UDP_TRANSMIT_MESSAGE_QUEUE.empty():
            udp_message, _ = UDP_TRANSMIT_MESSAGE_QUEUE.get()
            print(f"Sending GET_TRACE command to {COLDFIRE_IP}: {udp_message.hex()}")
            udp_socket.sendto(udp_message, (COLDFIRE_IP, UDP_PORT))
            time.sleep(0.2)

    time.sleep(0.2)  # Wait for trace to be written

    written = False
    while not written:
        try:
            with open(TRACE_FILE, 'r') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]  # Ignore empty lines
            if lines:
                last_line = lines[-1]
                second_last_line = lines[-2] # Get last non-empty line
                if last_line == last_recorded_row:
                    time.sleep(0.5)
                    continue

                fields = last_line.split(',')
                channel_number = int(fields[1].strip())  # Convert channel to int safely
                if channel_number == 2:

                    new_line = f"{command_input.get()},{repeat_input.get()},{runs_input.get()},{last_line}"
                    lines[-1] = new_line  # Update last line in list

                    new_line2 = f"{command_input.get()},{repeat_input.get()},{runs_input.get()},{second_last_line}"
                    lines[-2] = new_line2  # Update last line in list

                    # Write back to file
                    with open(TRACE_FILE, 'w') as f:
                        f.write("\n".join(lines) + "\n")

                    update_trace_plot(arg=1)
                    written = True
                    print("Trace plot updated for channel 2.")
            else:
                print("Trace container is empty, waiting...")
        except FileNotFoundError:
            print("trace_container2.txt not found, waiting...")
        except Exception as e:
            print(f"Error reading trace file: {e}")

        time.sleep(0.1)  # Avoid excessive CPU usage

def update_trace_plot(arg):
    global all_traces  # Ensure we modify the global list

    if arg == 1:
        all_traces.clear()  # Clear stored trace data
        ax3.cla()  # Clear the plot
        ax3.set_title("Trace Data")
        canvas.draw()  # Redraw canvas to reflect changes
        try:
            # Read trace data from file
            with open(TRACE_FILE, "r") as file:
                lines = file.readlines()

            # Convert lines to numerical data, skipping the first 6 columns
            new_trace_data = [
                list(map(float, line.strip().split(',')[9:]))  # Skip first 6 columns
                for i, line in enumerate(lines[1:]) if i % 2 == 0 and line.strip()
            ]

            if new_trace_data:
                all_traces.extend(new_trace_data)  # Append new traces instead of overwriting
                ax3.set_title("Trace Data")  # Ensure the title is set


                try:
                    #order = int(command_input.get().strip())
                    #runs = int(runs_input.get().strip())
                    #reps = int(repeat_input.get().strip())
                    #bscan.bscan_main(order,runs,bscan_canvas,enable_drawMeanLine_var, TRACE_FILE,reps)
                    info_string = bscan_main(bscan_canvas, enable_drawMeanLine_var, TRACE_FILE, plot_threshold_input)
                    response_text.insert(tk.END,info_string)
                except Exception as e:
                    response_text.insert(tk.END,f"Error parsing order or runs: {e}")



                for trace in new_trace_data:
                    ax3.plot(trace)  # Plot only new traces without clearing old ones
                ax3.set_navigate(True)
                canvas.draw()  # Update the plot
            else:
                print("No new trace data found!")
                response_text.insert(tk.END,"No trace data found\n")

        except FileNotFoundError:
            print("Trace file not found!")
        except ValueError:
            print("Error processing trace data. Ensure all values (except metadata) are numeric.")

    elif arg == 0:
        with open(TRACE_FILE, "w") as file:
            pass
        all_traces.clear()  # Clear stored trace data
        ax3.cla()  # Clear the plot
        ax3.set_title("Trace Data")
        canvas.draw()

def plot(number):
    global canvas, fig, ax1, ax2

    filename = f"../../Documents/my_mls{number}_1p_1f.txt"

    try:

        data = np.loadtxt(filename, skiprows=1)
        column_data = data[:, 1]
        data[:,1] *= -1
        if len(column_data) > 100:
            column_data = column_data[:100]

        # x indices
        x = np.arange(0, len(column_data))

        # Create step plot-like behavior
        x_boxy = np.repeat(x, 2)
        y_boxy = np.repeat(column_data, 2)

        # Insert the initial step to create the "stairs" effect
        x_boxy = np.insert(x_boxy, 0, x_boxy[0] - 1)
        y_boxy = np.insert(y_boxy, 0, y_boxy[0])

        ax1.clear()
        ax2.clear()

        ax1.step(x_boxy, y_boxy, where='mid', color='black', linewidth=2)
        ax1.grid(True)
        ax1.set_xlim([0, len(column_data) + 1])
        ax1.set_ylim([min(y_boxy) - 0.5, max(y_boxy) + 0.5])
        ax1.set_title("Preview")

        # Update canvas with the new plot
        canvas.draw()

        # Autocorrelation plot
        lags = np.arange(-len(data[:, 1]) + 1, len(data[:, 1]))
        corr = correlate(data[:, 1], data[:, 1], mode='full', method='auto')
        ax2.plot(lags, corr)
        ax2.grid(True)
        ax2.set_title("Autocorrelation")
        canvas.draw()

        return data[:, 1]

    except Exception as e:
        response_text.insert(tk.END, f"Error loading file: {e}\n")

def send_check_ctrl():
    MESSAGE_CTRL = bytearray([
        0x55, 0x56,  # Protocol ID (0x5556)
        0x00, 0x01,  # Packet Number (0x0001)
        0x00, 0x00,
        0x00         # Hardware Channel Number (0x0000)
    ])
    MESSAGE_CTRL.append(4)  # payload size (LSB)
    MESSAGE_CTRL.append(0)
    MESSAGE_CTRL.append(0)  # type: command
    MESSAGE_CTRL.append(0)
    MESSAGE_CTRL.append(1)  # frame number
    MESSAGE_CTRL.append(0)  # total frames
    MESSAGE_CTRL.append(1)
    MESSAGE_CTRL.append(1)  # 0x01 command:
    MESSAGE_CTRL.append(138)  # 0x87  --> total 0x0187 --> 391
    MESSAGE_CTRL.append(0)
    MESSAGE_CTRL.append(0)
    MESSAGE_CTRL.append(0)  # Shift order left by 4 bits
    MESSAGE_CTRL.append(0)

    hex_representation = MESSAGE_CTRL.hex(sep="|")

    try:
        # Send message over UDP
        udp_socket.sendto(MESSAGE_CTRL, (RX_IP, UDP_PORT))
        if enable_MESSAGE_debug_var.get():
            response_text.insert(tk.END, f"Message 16-bit stream:\n {MESSAGE_CTRL}\n")
        if enable_HEX_debug_var.get():
            response_text.insert(tk.END, f"Hex: {hex_representation}\n")

        # Set a timeout so we don't block indefinitely
        udp_socket.settimeout(5)
        while True:
            try:
                data, adr = udp_socket.recvfrom(1024)
                if adr[0] == RX_IP:
                    break  # Exit loop if response is from RX_IP
            except Exception as e:
                response_text.insert(tk.END, f"Timeout or error: {e}\n")
                return

        if data:
            payload = data[16:]
            payload_str = ""
            for i, h in enumerate(payload):
                payload_str += str(h) + " "
                if i % 4 == 3:
                    payload_str += "\n"
            if enable_RESPONSE_debug_var.get():
                response_text.insert(tk.END, f"\nCTRL: {payload_str}")
    except Exception as e:
        response_text.insert(tk.END, f"Error sending message: {e}\n")

def send_check_seq():
    MESSAGE_CTRL = bytearray([
        0x55, 0x56,  # Protocol ID (0x5556)
        0x00, 0x01,  # Packet Number (0x0001)
        0x00, 0x00,
        0x00  # Hardware Channel Number (0x0000)
    ])
    MESSAGE_CTRL.append(4)  # payload size (LSB)
    MESSAGE_CTRL.append(0)
    MESSAGE_CTRL.append(0)  # type: command
    MESSAGE_CTRL.append(0)
    MESSAGE_CTRL.append(1)  # frame number
    MESSAGE_CTRL.append(0)  # total frames
    MESSAGE_CTRL.append(1)
    MESSAGE_CTRL.append(1)  # 0x01 command:
    MESSAGE_CTRL.append(139)  # 0x87  --> total 0x0187 --> 391
    MESSAGE_CTRL.append(0)
    MESSAGE_CTRL.append(0)
    MESSAGE_CTRL.append(0)  # Shift order left by 4 bits
    MESSAGE_CTRL.append(0)

    hex_representation = MESSAGE_CTRL.hex(sep="|")

    # Send message over UDP
    try:
        udp_socket.sendto(MESSAGE_CTRL, (RX_IP, UDP_PORT))  # Send packed message
        if enable_MESSAGE_debug_var.get():
            response_text.insert(tk.END, f"Message 16-bit stream:\n {MESSAGE_CTRL}\n")
        if enable_HEX_debug_var.get():
            response_text.insert(tk.END, f"Hex: {hex_representation}\n")

        udp_socket.settimeout(5)
        while True:
            try:
                data, adr = udp_socket.recvfrom(1024)
                if adr[0] == RX_IP:
                    break  # Exit loop if response is from RX_IP
            except Exception as e:
                response_text.insert(tk.END, f"Timeout or error: {e}\n")
                return

        if data:
            payload = data[16:]
            payload_str = ""
            for i, h in enumerate(payload):
                payload_str += str(h) + " "
                if i % 4 == 3:
                    payload_str += "\n"
            if enable_RESPONSE_debug_var.get():
                response_text.insert(tk.END, f"\nSEQ: {payload_str}")
    except Exception as e:
        response_text.insert(tk.END, f"Error sending message: {e}\n")

def send_check_reps():
    MESSAGE_CTRL = bytearray([
        0x55, 0x56,  # Protocol ID (0x5556)
        0x00, 0x01,  # Packet Number (0x0001)
        0x00, 0x00,
        0x00  # Hardware Channel Number (0x0000)
    ])
    MESSAGE_CTRL.append(4)  # payload size (LSB)
    MESSAGE_CTRL.append(0)
    MESSAGE_CTRL.append(0)  # type: command
    MESSAGE_CTRL.append(0)
    MESSAGE_CTRL.append(1)  # frame number
    MESSAGE_CTRL.append(0)  # total frames
    MESSAGE_CTRL.append(1)
    MESSAGE_CTRL.append(1)  # 0x01 command:
    MESSAGE_CTRL.append(140)  # 0x87  --> total 0x0187 --> 391
    MESSAGE_CTRL.append(0)
    MESSAGE_CTRL.append(0)
    MESSAGE_CTRL.append(0)  # Shift order left by 4 bits
    MESSAGE_CTRL.append(0)

    hex_representation = MESSAGE_CTRL.hex(sep="|")

    # Send message over UDP
    try:
        udp_socket.sendto(MESSAGE_CTRL, (RX_IP, UDP_PORT))  # Send packed message
        if enable_MESSAGE_debug_var.get():
            response_text.insert(tk.END, f"Message 16-bit stream:\n {MESSAGE_CTRL}\n")
        if enable_HEX_debug_var.get():
            response_text.insert(tk.END, f"Hex: {hex_representation}\n")

        udp_socket.settimeout(5)
        while True:
            try:
                data, adr = udp_socket.recvfrom(1024)
                if adr[0] == RX_IP:
                    break  # Exit loop if response is from RX_IP
            except Exception as e:
                response_text.insert(tk.END, f"Timeout or error: {e}\n")
                return

        if data:
            payload = data[16:]
            payload_str = ""
            for i, h in enumerate(payload):
                payload_str += str(h) + " "
                if i % 4 == 3:
                    payload_str += "\n"
            if enable_RESPONSE_debug_var.get():
                response_text.insert(tk.END, f"\nREPS: {payload_str}")
    except Exception as e:
        response_text.insert(tk.END, f"Error sending message: {e}\n")

root = tk.Tk()
root.title("Coldfire Ethernet GUI")

# Use a main frame for better control
main_frame = tk.Frame(root)
main_frame.pack(fill="y", expand=True)

# Configure grid layout
main_frame.columnconfigure(0, weight=1)  # Left-side frame (fixed)
main_frame.columnconfigure(1, weight=3)  # Right-side frame (expands)
main_frame.columnconfigure(2, weight=1)  # B-scan frame (fixed)

main_frame.rowconfigure(0, weight=1)  # Ensure vertical expansion

# Create sub-frames
left_frame = tk.Frame(main_frame, padx=10, pady=10)
left_frame.grid(row=0, column=0, sticky="ns")

right_frame = tk.Frame(main_frame, padx=10, pady=10)
right_frame.grid(row=0, column=1, sticky="nsew")  # Expands properly

bscan_frame = tk.Frame(main_frame, padx=10, pady=10)
bscan_frame.grid(row=0, column=2, sticky="ns")  # Far right

# === Instructions Section ===
instructions_text = tk.Label(
    left_frame, text=(
        "Welcome to the ColdFire Communication GUI\n\n"
        "Instructions:\n"
        "1. Enter an M-sequence order (2^n - 1).\n"
        "2. Enter the number of periods per spatial measurement.\n"
        "3. Click 'Send Command to Coldfire'.\n"
        "4. Feedback appears in the response area.\n\n"
        "Use 'Connect to ColdFire' to establish a connection.\n"
    ),
    justify="left", wraplength=350
)
instructions_text.pack(pady=5)

# === Debug Options Section ===
debug_frame = tk.LabelFrame(left_frame, text="Options", padx=5, pady=5)
debug_frame.pack(fill="x", pady=5)

enable_MESSAGE_debug_var = tk.BooleanVar()
enable_HEX_debug_var = tk.BooleanVar()
enable_RESPONSE_debug_var = tk.BooleanVar(value=1)

tk.Checkbutton(debug_frame, text="Enable MESSAGE Debug", variable=enable_MESSAGE_debug_var).grid(row=0, column=0, sticky="w", padx=5, pady=2)
tk.Checkbutton(debug_frame, text="Enable HEX Debug", variable=enable_HEX_debug_var).grid(row=1, column=0, sticky="w", padx=5, pady=2)
tk.Checkbutton(debug_frame, text="Enable Coldfire Response", variable=enable_RESPONSE_debug_var).grid(row=2, column=0, sticky="w", padx=5, pady=2)


connect_button = tk.Button(debug_frame, text="Connect to FPGA", width=25, command=lambda: connect_udp())
connect_button.grid(row=0, column=1, rowspan=3, padx=10, pady=2, sticky="ns")

# === Input Parameters Section ===
input_frame = tk.LabelFrame(left_frame, text="Input Parameters", padx=5, pady=5)
input_frame.pack(fill="x", pady=5)

tk.Label(input_frame, text="M-sequence order:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
command_input = tk.Entry(input_frame, width=10)
command_input.grid(row=0, column=1, padx=5, pady=2)
command_input.insert(tk.END, 5)

tk.Label(input_frame, text="Repetitions:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
repeat_input = tk.Entry(input_frame, width=10)
repeat_input.grid(row=1, column=1, padx=5, pady=2)
repeat_input.insert(tk.END, 1)

tk.Label(input_frame, text="Number of Runs:").grid(row=2, column=0, sticky="e", padx=5, pady=2)
runs_input = tk.Entry(input_frame, width=10)
runs_input.grid(row=2, column=1, padx=5, pady=2)
runs_input.insert(tk.END, 32)

tk.Label(input_frame, text="Samples:").grid(row=3, column=0, sticky="e", padx=5, pady=2)
samples_input = tk.Entry(input_frame, width=10)
samples_input.grid(row=3, column=1, padx=5, pady=2)
samples_input.insert(tk.END, 512)

tk.Label(input_frame, text="Stacks:").grid(row=4, column=0, sticky="e", padx=5, pady=2)
stacks_input = tk.Entry(input_frame, width=10)
stacks_input.grid(row=4, column=1, padx=5, pady=2)
stacks_input.insert(tk.END, 1)

clear_inputs = tk.Button(input_frame, text="Clear Registers", width=18, command=lambda: reset_registers())
clear_inputs.grid(row=0, column=2, rowspan=5, padx=12, pady=2, sticky="ns")

button_frame = tk.LabelFrame(left_frame, text="Actions", padx=5, pady=5)
button_frame.pack(fill="x", pady=5)

btn_width = 18  # Standardized button width

send_button = ttk.Button(button_frame, text="Send Sequence", width=btn_width, command=lambda: plot_and_send_command())
send_button.grid(row=0, column=0, padx=5, pady=2)

send_reps_button = ttk.Button(button_frame, text="Send Reps", width=btn_width,command=lambda: send_reps(int(repeat_input.get().strip())))
send_reps_button.grid(row=0, column=1, padx=5, pady=2)

shooting_button = ttk.Button(button_frame, text="Send Shooting Table", width=btn_width, command=lambda: shooting_table(int(runs_input.get()), int(samples_input.get()),int(stacks_input.get())))
shooting_button.grid(row=0, column=2, padx=5, pady=2)

debug_button = ttk.Button(button_frame, text="Get Trace", width=btn_width,command=lambda: trace())
debug_button.grid(row=1, column=0, padx=5, pady=2)

trace_button = ttk.Button(button_frame, text="Plot Trace Data", width=btn_width, command=lambda: update_trace_plot(arg=1))
trace_button.grid(row=1, column=1, padx=5, pady=2)

run_button = tk.Button(button_frame, text="Run", width=btn_width, command=lambda: run_measurement(arg="start"))
run_button.grid(row=1, column=2,padx=5,pady=2)

check_ctrl_button = ttk.Button(button_frame, text="Check CTRL", width=btn_width, command=lambda: send_check_ctrl())
check_ctrl_button.grid(row=4, column=0, padx=5, pady=2)

check_seq_button = ttk.Button(button_frame, text="Check SEQ", width=btn_width, command=lambda: send_check_seq())
check_seq_button.grid(row=4, column=1, padx=5, pady=2)

check_reps_button = ttk.Button(button_frame, text="Check REPS", width=btn_width, command=lambda: send_check_reps())
check_reps_button.grid(row=4, column=2, padx=5, pady=2)

# === Response Area ===
response_text = tk.Text(left_frame, height=16, width=50)
response_text.pack(pady=(5, 2), fill="x")  # Reduced bottom padding

# Create a frame to group buttons and center them
button_frame2 = tk.Frame(left_frame)
button_frame2.pack(pady=5)  # Slight spacing from text box

cleanup_button = ttk.Button(button_frame2, text="Clear Response Text", width=int(1.5 * btn_width),
                            command=lambda: response_text.delete('1.0', tk.END))
cleanup_button.grid(row=0, column=0, padx=5)  # Grid for better control

update_trace_button = ttk.Button(button_frame2, text="Clear Trace Plot", width=int(1.5 * btn_width),
                                 command=lambda: update_trace_plot(arg=0))
update_trace_button.grid(row=0, column=1, padx=5)  # Place next to cleanup_button

enable_drawMeanLine_var = tk.BooleanVar(value=1)
tk.Checkbutton(master=button_frame2, text="Enable Mean Line", variable=enable_drawMeanLine_var).grid(row=1, column=0, sticky="w", padx=5, pady=2)

tk.Label(button_frame2, text="Plot threshold:").grid(row=2, column=0, sticky="e", padx=5, pady=2)
plot_threshold_input = tk.Entry(button_frame2, width=10)
plot_threshold_input.grid(row=2, column=1, padx=5, pady=2)
plot_threshold_input.insert(tk.END, 30)


# === Matplotlib Figure & Canvas ===
fig = plt.figure(figsize=(6, 12), dpi=100)  # Adjust figure size for better spacing
gs = gridspec.GridSpec(3, 1, height_ratios=[1, 1, 1])  # 3 rows, 1 column

# Plots layout (stacked vertically)
ax1 = fig.add_subplot(gs[0, 0])  # Preview (Top)
ax2 = fig.add_subplot(gs[1, 0])  # Autocorrelation (Middle)
ax3 = fig.add_subplot(gs[2, 0])  # Trace Data (Bottom)

# Titles
ax1.set_title("Preview")
ax2.set_title("Autocorrelation")
ax3.set_title("Trace Data")

# Embed the figure in Tkinter
canvas = FigureCanvasTkAgg(fig, master=right_frame)
canvas.get_tk_widget().pack(fill="both", expand=True)

# Add a toolbar for interactivity
toolbar = NavigationToolbar2Tk(canvas, right_frame)
toolbar.update()

# === B-Scan Figure (B-Scan Frame) ===
bscan_fig = plt.figure(figsize=(7, 4), dpi=100)  # Adjusted width to 7 (slightly narrower)
bscan_gs = gridspec.GridSpec(2, 1, height_ratios=[1, 1])  # Separate gridspec for this figure

# Create subplots within the gridspec
bscan_ax1 = bscan_fig.add_subplot(bscan_gs[0, 0])  # B-scan Top Plot
bscan_ax2 = bscan_fig.add_subplot(bscan_gs[1, 0])  # B-scan Bottom Plot

# Set titles for the subplots
bscan_ax1.set_title("Correlated Traces")
bscan_ax2.set_title("B-Scan Autocorrelation")
gs = bscan_fig.add_gridspec(2, 1, height_ratios=[1, 3])  # Define grid layout

# Adjust the subplot spacing to ensure the second y-axis fits
bscan_fig.subplots_adjust(right=0.85)  # Adjust the right side to make space for the second y-axis

# Embed the figure in Tkinter
bscan_canvas = FigureCanvasTkAgg(bscan_fig, master=bscan_frame)
bscan_canvas.get_tk_widget().pack(fill="both", expand=True)

# Add a toolbar for interactivity
toolbar = NavigationToolbar2Tk(bscan_canvas, bscan_frame)
toolbar.update()
# Handle window close
root.protocol("WM_DELETE_WINDOW", lambda: root.quit())

# Start the Tkinter main loop
root.mainloop()
# Close the socket when exiting
if udp_socket:
    udp_socket.close()
