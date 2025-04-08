import socket
import tkinter as tk
from scipy.signal import correlate
import time
import queue
import sequences
import testengine
import numpy as np
import os

UDP_TRANSMIT_MESSAGE_QUEUE = queue.Queue()
SEQUENCER_MESSAGE_QUEUE = queue.Queue()
CONSOLE_QUEUE = queue.Queue()
UDP_RECEIVE_MESSAGE_QUEUE = queue.Queue()

COLDFIRE_IP = "192.168.1.2"  # Coldfire device IP
RX_IP = "192.168.1.101"
UDP_PORT: int = 0x555  # Port
udp_socket = None  # Global socket variable
all_traces = []
plot_args = {}
clock_freq = 160e6 # Hz
interval = 3.2e-6 # s

class Message:
    def __init__(self):
        # Initialize the fixed part of the message once, avoiding repeated allocations
        self.message=bytearray([
            0x55, 0x56,  # Protocol ID (0x5556)
            0x00, 0x01,  # Packet Number (0x0001)
            0x00, 0x00,  # Hardware Channel Number (0x0000)
            0x00
        ])

    def append_payload(self, cmd, payload_size, payload):
        # Append the command bytes and payload to the message
        upper_CMD_byte = (cmd >> 8) & 0xff
        lower_CMD_byte = cmd & 0xff

        payload_bytes = payload.to_bytes(2, byteorder='big') if isinstance(payload, int) else payload

        # Build the complete message by appending required fields
        self.message.extend([
            payload_size,
            0, 0,  # type: command
            0, 1,  # frame number
            0, 1,  # total frames
            upper_CMD_byte, lower_CMD_byte, 0
        ])
        self.message.extend(payload_bytes)
        self.message.append(0)

        if payload_size == 6:
            self.message.append(0)

    def get_message(self):
        return self.message

def connect_udp(response_text, self_button,check_buttons):
    global udp_socket
    try:
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind((socket.gethostbyname(socket.gethostname()), UDP_PORT))
        udp_socket.settimeout(1)  # Set a timeout to prevent blocking

        messageheader = Message()
        messageheader.append_payload(cmd=61, payload_size=6, payload=0)
        MESSAGE = messageheader.get_message()

        if check_buttons["MESSAGE"].get():
            response_text.insert(tk.END, f"16-bit stream:\n {MESSAGE}\n")
        if check_buttons["HEX"].get():
            response_text.insert(tk.END, f"Hex: {MESSAGE.hex(sep='|')}\n")
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
            if check_buttons["RESPONSE"].get():
                response_text.insert(tk.END, f"\nVersion: {payload_str}")

            response_text.insert(tk.END, f"Version: {payload_str}")
            self_button.configure(state=tk.DISABLED, background="#8cde83", foreground="white")
    except Exception as e:
        udp_socket = None
        response_text.insert(tk.END, f"Connection failed: {e}\n")

def update_label(var, label):
    label.config(text=f"{var.get():.2f}")  # Show value with 2 decimal places

def plot_and_send_command(plot_handle,order,reps,check_buttons,response_text):

    error_messages = []
    sequence = []

    fields = [
        ("Order", order),
        ("Repetitions", reps),
    ]

    for name, field in fields:
        try:
            value = int(field.get().strip())
            if value <= 0:
                error_messages.append(f"Invalid value of {name}")
            elif name == "Order" and (value < 5 or value > 12):
                error_messages.append(f"Order must be between 5 and 12")
            else:
                sequence.append(value)
        except ValueError:
            error_messages.append(f"Non-numeric {name} ")

    if error_messages:
        response_text.insert(tk.END, "Error(s):\n" + "\n".join(f"- {msg}" for msg in error_messages) + "\n")
        return

    data = plot(sequence[0],plot_handle,response_text)
    data[data == -1] = 0
    data = data.astype(np.uint8)

    response_text.insert(tk.END, f"\nM-sequence order = {sequence[0]}, repetitions = {sequence[1]}.\n")

    if not udp_socket:
        response_text.insert(tk.END, "Error: Not connected to Coldfire.\n")
        return

    time.sleep(0.2)
    send_ctrl(sequence[0],response_text,check_buttons)
    time.sleep(0.1)
    send_reps(sequence[1],response_text,check_buttons)
    time.sleep(0.1)
    send_sequence(data,response_text,check_buttons)

def send_reps(repetitions,response_text,check_buttons):
    messageheader = Message()
    messageheader.append_payload(cmd=393, payload_size=4, payload=repetitions)
    MESSAGE = messageheader.get_message()

    if check_buttons["MESSAGE"].get():
        response_text.insert(tk.END, f"16-bit stream:\n {MESSAGE}\n")
    if check_buttons["HEX"].get():
        response_text.insert(tk.END, f"Hex: {MESSAGE.hex(sep='|')}\n")

    try:
        udp_socket.sendto(MESSAGE, (RX_IP, UDP_PORT))  # Send packed message
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
            if check_buttons["RESPONSE"].get():
                response_text.insert(tk.END, f"\nRepetitions: {payload_str}")

    except Exception as e:
        response_text.insert(tk.END, f"Error sending message: {e}\n")

def send_sequence(data,response_text,check_buttons):
    bit_string = "".join(str(bit) for bit in data)

    # Ensure length is a multiple of 16 by padding at the end
    padding = (16 - (len(bit_string) % 16)) % 16  # Avoid adding extra 16 if already aligned
    bit_string += "0" * padding

    # Convert to 16-bit words
    packed_16bit_words = [int(bit_string[i:i + 16], 2) for i in range(0, len(bit_string), 16)]
    for word in packed_16bit_words:

        # Construct the header
        messageheader = Message()
        messageheader.append_payload(cmd=392,payload_size=4,payload=word)
        MESSAGE = messageheader.get_message()

        print(f"DATA message {MESSAGE}")

        # Convert to hex for debugging
        hex_representation = MESSAGE.hex(sep="|")

        try:
            time.sleep(0.2)
            udp_socket.sendto(MESSAGE, (RX_IP, UDP_PORT))  # Send packed message

            if check_buttons["MESSAGE"].get():
                response_text.insert(tk.END, f"16-bit stream:\n {MESSAGE}\n")
            if check_buttons["HEX"].get():
                response_text.insert(tk.END, f"Hex: {MESSAGE.hex(sep='|')}\n")
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
                if check_buttons["RESPONSE"].get():
                    response_text.insert(tk.END, f"\nSequence response: {payload_str}")
        except Exception as e:
            response_text.insert(tk.END, f"Error sending message: {e}\n")

    response_text.insert(tk.END, "\n")

def send_ctrl(order,response_text,check_buttons):
    messageheader = Message()
    messageheader.append_payload(cmd=391, payload_size=4, payload=order)
    MESSAGE = messageheader.get_message()

    if check_buttons["MESSAGE"].get():
        response_text.insert(tk.END, f"16-bit stream:\n {MESSAGE}\n")
    if check_buttons["HEX"].get():
        response_text.insert(tk.END, f"Hex: {MESSAGE.hex(sep='|')}\n")

    try:
        udp_socket.sendto(MESSAGE, (RX_IP, UDP_PORT))  # Send packed message
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
            if check_buttons["RESPONSE"].get():
                response_text.insert(tk.END, f"\nOrder: {payload_str}")

    except Exception as e:
        response_text.insert(tk.END, f"Error sending message: {e}\n")

def reset_registers(response_text,check_buttons):

    if udp_socket:
        send_ctrl(0,response_text,check_buttons)
        response_text.insert(tk.END,"CTRL register cleared...\n")
        time.sleep(0.1)
        send_reps(0,response_text,check_buttons)
        response_text.insert(tk.END, "REPS register cleared...\n")
        time.sleep(0.1)
        zero_data = np.zeros(4095, dtype=np.uint8)
        send_sequence(zero_data,response_text,check_buttons)
        response_text.insert(tk.END, "SEQ register cleared\n")
    else:
        response_text.insert(tk.END,"Error: Not connected to FPGA\n")

def send_check_ctrl(response_text):
    if udp_socket:
        messageheader = Message()
        messageheader.append_payload(cmd=394, payload_size=4, payload=0)
        MESSAGE = messageheader.get_message()

        try:
            udp_socket.sendto(MESSAGE, (RX_IP, UDP_PORT))  # Send packed message
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
                    response_text.insert(tk.END, f"\nOrder: {payload_str}")

        except Exception as e:
            response_text.insert(tk.END, f"Error sending message: {e}\n")
    else:
        response_text.insert(tk.END,"Error: Not connected to FPGA\n")

def send_check_seq(response_text):
    if udp_socket:
        messageheader = Message()
        messageheader.append_payload(cmd=394, payload_size=4, payload=0)
        MESSAGE = messageheader.get_message()

        try:
            udp_socket.sendto(MESSAGE, (RX_IP, UDP_PORT))  # Send packed message
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
                    response_text.insert(tk.END, f"\nSequence: {payload_str}")

        except Exception as e:
            response_text.insert(tk.END, f"Error sending message: {e}\n")
    else:
        response_text.insert(tk.END,"Error: Not connected to FPGA\n")

def send_check_reps(response_text):
    if udp_socket:
        messageheader = Message()
        messageheader.append_payload(cmd=396, payload_size=4, payload=0)
        MESSAGE = messageheader.get_message()

        try:
            udp_socket.sendto(MESSAGE, (RX_IP, UDP_PORT))  # Send packed message
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
                    response_text.insert(tk.END, f"\nRepetitions: {payload_str}")

        except Exception as e:
            response_text.insert(tk.END, f"Error sending message: {e}\n")
    else:
        response_text.insert(tk.END,"Error: Not connected to FPGA\n")

def send_shooting_table(runs, samples, stacks, delay, response_text):
    global udp_socket
    error_messages = []
    shooting_table = []

    fields = [
        ("Runs", runs),
        ("Samples", samples),
        ("Stacks", stacks),
        ("Delay", delay)
    ]

    for name, field in fields:
        try:
            value = int(field.get().strip())
            if value <= 0:
                error_messages.append(f"Invalid value of {name}")
            else:
                shooting_table.append(value)
        except ValueError:
            error_messages.append(f"Non-numeric {name} ")

    if error_messages:
        response_text.insert(tk.END, "Error(s):\n" + "\n".join(f"- {msg}" for msg in error_messages) + "\n")
        return

    response_text.insert(tk.END, f"Shooting table values: {shooting_table}\n")

    if udp_socket:
        request_data_state = ('SHOOTING_TABLE', *shooting_table)
        sequences.blockmaster_shooting_table(request_data_state, UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE,
                                             CONSOLE_QUEUE)
        response_text.insert(tk.END, CONSOLE_QUEUE.get())
        while not UDP_TRANSMIT_MESSAGE_QUEUE.empty():
            udp_message, target_ip = UDP_TRANSMIT_MESSAGE_QUEUE.get()
            udp_socket.sendto(udp_message, (COLDFIRE_IP, UDP_PORT))
            time.sleep(0.3)

        response_text.insert(tk.END,"\nShooting table successfully sent\n")

        sequences.set_RX_pwr_on(UDP_TRANSMIT_MESSAGE_QUEUE, SEQUENCER_MESSAGE_QUEUE, CONSOLE_QUEUE)

        response_text.insert(tk.END,CONSOLE_QUEUE.get())
        while not UDP_TRANSMIT_MESSAGE_QUEUE.empty():
            udp_message, target_ip = UDP_TRANSMIT_MESSAGE_QUEUE.get()
            print(f"Sending to {RX_IP}: {udp_message.hex()}")
            udp_socket.sendto(udp_message, (RX_IP, UDP_PORT))
            time.sleep(0.3)
        response_text.insert(tk.END,"\nRX power on\n")

    else:
        response_text.insert(tk.END, "Error: Not connected to FPGA\n")

def update_trace_plot(data_file,plot_handle):
    plot_handle.ax3.cla()  # Clear the plot
    plot_handle.ax3.set_title("Trace Data")
    plot_handle.canvas.draw()  # Redraw canvas to reflect changes
    try:
        # Read trace data from file
        with open(data_file, "r") as file:
            lines = file.readlines()

        # Convert lines to numerical data, skipping the first 6 columns
        new_trace_data = [
            list(map(float, line.strip().split(',')[9:]))  # Skip first 6 columns
            for i, line in enumerate(lines[1:]) if i % 2 == 0 and line.strip()
        ]
        for trace in new_trace_data:
            plot_handle.ax3.plot(trace)  # Plot only new traces without clearing old ones
        plot_handle.ax3.set_navigate(True)
        plot_handle.canvas.draw()  # Update the plot
    except FileNotFoundError as e:
        print(f"Trace file not found! {e}\n")
    except ValueError as e:
        print(f"Error plotting trace data: {e}")

def trace(order,repetitions,runs,data_file,response_text,plot_handle):
    global udp_socket
    if udp_socket:
        testengine.start_run(udp_socket,order,repetitions,runs,data_file, response_text,mode="TRACE")
        response_text.insert(tk.END,"Taking trace...")
        time.sleep(1)
        testengine.stop_run(udp_socket,response_text, mode="TRACE")
        response_text.insert(tk.END, "Done\n")
    else:
        response_text.insert(tk.END, "Error: Not connected to FPGA\n")

    if not os.path.exists(data_file) or os.stat(data_file).st_size == 0:
        response_text.insert(tk.END, "Error: The input file is empty or doesn't exist.\n")
        return
    update_trace_plot(data_file,plot_handle)


def clear_data_and_plots(data_file,plot_handle, radargram_handle, response_text):
    # Try to open the file for reading to check if it exists
    try:
        with open(data_file, "r"):  # Open the file in read mode
            pass  # If no error occurs, the file exists
    except FileNotFoundError:
        response_text.insert(tk.END, f"Error: File {data_file} not found\n")
        return  # Exit the function if the file doesn't exist

    # Clear the file content
    try:
        with open(data_file, "w") as f:
            pass  # Clear the file content (overwrite with an empty file)
    except FileNotFoundError as e:
        response_text.insert(tk.END, f"Error: {e}\n")

    # Always clear plots, regardless of file result
    try:
        # Clear the provided axes (ax1, ax2, ax3)
        for ax in [plot_handle.ax1, plot_handle.ax2, plot_handle.ax3]:
            ax.clear()
        # Restore titles (axes are still intact)
        plot_handle.ax1.set_title("Preview")
        plot_handle.ax2.set_title("Autocorrelation")
        plot_handle.ax3.set_title("Trace Data")

        # Clear the radargram plot
        if radargram_handle:
            radargram_handle.reset_radargram()

        # Redraw the axes on the canvas (both the main and radargram canvas)
        if plot_handle.canvas:
            plot_handle.canvas.draw()  # Redraw the canvas for the main plot
        if radargram_handle.canvas:  # Ensure canvas is drawn correctly for radargram
            radargram_handle.canvas.draw()  # Redraw the radargram canvas

    except Exception as e:
        response_text.insert(tk.END, f"Error: {e}\n")

    # Notify the user that clearing was successful
    response_text.insert(tk.END, f"{data_file} and plots successfully cleared\n")

def plot(order,plot_handle,response_text):
    filename = f"Mseqs/my_mls{order}_1p_1f.txt"

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

        plot_handle.ax1.clear()
        plot_handle.ax2.clear()

        plot_handle.ax1.step(x_boxy, y_boxy, where='mid', color='black', linewidth=2)
        plot_handle.ax1.grid(True)
        plot_handle.ax1.set_xlim([0, len(column_data) + 1])
        plot_handle.ax1.set_ylim([min(y_boxy) - 0.5, max(y_boxy) + 0.5])
        plot_handle.ax1.set_title("Preview")

        # Update canvas with the new plot
        # canvas.draw()

        # Autocorrelation plot
        lags = np.arange(-len(data[:, 1]) + 1, len(data[:, 1]))
        corr = correlate(data[:, 1], data[:, 1], mode='full', method='auto')
        plot_handle.ax2.plot(lags, corr)
        plot_handle.ax2.grid(True)
        plot_handle.ax2.set_title("Autocorrelation")
        plot_handle.canvas.draw()

        return data[:, 1]

    except Exception as e:
        response_text.insert(tk.END, f"Error loading file: {e}\n")

def toggle_set_button(sliders):
    state = "normal" if sliders["Enable"].get() else "disabled"

    for key in ["AntennaSpacing", "CableLen", "StdDev", "PeakAmp"]:
        sliders[key].config(state=state)

def update_radargram_plot(radargram_handle, data_file, response_text, sliders):
    # Clear the previous response text
    response_text.delete("1.0", tk.END)

    # Attempt to get the data
    if not radargram_handle.get_data(data_file):
        return

    # Proceed with normal execution if data is valid
    response_text.insert(tk.END,
                         f"Order: {radargram_handle.order}, Reps: {radargram_handle.reps}, Runs: {radargram_handle.runs}\n")
    radargram_handle.calculate_signal_length()
    radargram_handle.extract_relevant_data(start_idx=0)
    radargram_handle.resample_data()
    radargram_handle.compute_crosscorrelations()
    radargram_handle.calculate_time_axis()
    radargram_handle.draw_plots(sliders)
    response_text.insert(tk.END, "Plots updated\n")

    if sliders["Enable"].get():
        radargram_handle.layer_plotinfo(sliders)

def start_run_button_handler(button,order,repetitions,runs,data_file,response_text):
    global udp_socket
    if udp_socket:
        if button["text"] == "START":
            response_text.insert(tk.END, "Starting RUN...")
            testengine.start_run(udp_socket,order,repetitions,runs,data_file,response_text,mode="RUN")
            button.config(text="STOP")
        elif button["text"] == "STOP":
            testengine.stop_run(udp_socket,response_text,mode="RUN")
            response_text.insert(tk.END, "Done\n")
            button.config(text="START")
    else:
        response_text.insert(tk.END,"Error: Not connected to FPGA\n")


def update_trace_file_from_gui(trace_file_var, current_trace_file_var):
    """Update the trace file from the GUI entry."""
    filename = trace_file_var.get()

    if filename and not filename.endswith(".txt"):
        filename += ".txt"
    trace_file_var.set(filename)
    current_trace_file_var.set(f"Current file: {filename}")

def toggle_ramp_options(enable_ramp_var,ramp_dropdown):
    if enable_ramp_var.get():
        ramp_dropdown.config(state="readonly")  # Enable
    else:
        ramp_dropdown.config(state="disabled")  # Disable
