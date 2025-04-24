import socket
import tkinter as tk
import time
import queue
import sequences
import testengine
import numpy as np
import os
import gui_functions

UDP_TRANSMIT_MESSAGE_QUEUE = queue.Queue()
SEQUENCER_MESSAGE_QUEUE = queue.Queue()
CONSOLE_QUEUE = queue.Queue()
UDP_RECEIVE_MESSAGE_QUEUE = queue.Queue()

COLDFIRE_IP = "192.168.1.2"  # Coldfire device IP
RX_IP = "192.168.1.101"
UDP_PORT: int = 0x555  # Port
udp_socket = None  # Global socket variable

class Message:
    def __init__(self):
        # Initialize the fixed part of the message once, avoiding repeated allocations
        self.message = bytearray([
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
            0, 0,  # type, command
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

def send_reps(repetitions,response_text,check_buttons):
    global udp_socket
    if udp_socket:
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
                    return True

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
            return True
    else:
        response_text.insert(tk.END,"Error: Not connected to FPGA\n")
        return True

def send_sequence(data,response_text,check_buttons):
    global udp_socket
    if udp_socket:
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

            try:
                time.sleep(0.05)
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
                        return True

                if data:
                    payload = data[16:]
                    payload_str = " ".join(str(h) for h in payload)
                    if check_buttons["RESPONSE"].get():
                        response_text.insert(tk.END, f"\nSequence response: {payload_str}")
            except Exception as e:
                response_text.insert(tk.END, f"Error sending message: {e}\n")
                return True
        response_text.insert(tk.END, "\n")
    else:
        response_text.insert(tk.END, "Error: Not connected to FPGA\n")
        return True

def send_ctrl(order,response_text,check_buttons):
    global udp_socket
    if udp_socket:
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
                    return True

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
            return True
    else:
        response_text.insert(tk.END, "Error: Not connected to FPGA\n")
        return True

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

def send_check(arg,response_text):
    if udp_socket:
        if arg == "CTRL":
            CMD = 394
        elif arg == "SEQ":
            CMD = 395
        else:
            CMD = 396

        messageheader = Message()
        messageheader.append_payload(cmd=CMD, payload_size=4, payload=0)
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
                payload = data[16:]  # Extract the payload after the header (starting at index 16)
                # Loop over the payload and extract each byte
                payload_str = ""
                for i, byte in enumerate(payload):
                    payload_str += f"{byte} "  # Add each byte value to the string
                response_text.insert(tk.END, f"{arg}: {payload_str}\n")

        except Exception as e:
            response_text.insert(tk.END, f"Error sending message: {e}\n")
    else:
        response_text.insert(tk.END,"Error: Not connected to FPGA\n")

def send_shooting_table(run_params, latest_run_params, response_text):
    global udp_socket
    shooting_table = []
    clean_params = []
    if not ("Order" in latest_run_params and latest_run_params["Order"]):
        response_text.insert(tk.END, f"Error: Please send sequence first\n")
        for param in run_params:
            run_params[param].config(background="#fac157")

    else:
        shooting_table, clean_params = gui_functions.validate_shooting_table(run_params, response_text, latest_run_params)

        if shooting_table is None:
            return  # Stop further processing if validation failed

    if udp_socket:
        if shooting_table:
            request_data_state = ('SHOOTING_TABLE', *shooting_table)
            sequences.blockmaster_shooting_table(
                request_data_state,
                UDP_TRANSMIT_MESSAGE_QUEUE,
                SEQUENCER_MESSAGE_QUEUE,
                CONSOLE_QUEUE
            )

            response_text.insert(tk.END, CONSOLE_QUEUE.get())

            while not UDP_TRANSMIT_MESSAGE_QUEUE.empty():
                udp_message, target_ip = UDP_TRANSMIT_MESSAGE_QUEUE.get()
                udp_socket.sendto(udp_message, (COLDFIRE_IP, UDP_PORT))
                time.sleep(0.3)

            response_text.insert(tk.END, "\nShooting table successfully sent\n")

            for field in clean_params:
                latest_run_params[field] = clean_params[field].get()

            sequences.set_RX_pwr_on(
                UDP_TRANSMIT_MESSAGE_QUEUE,
                SEQUENCER_MESSAGE_QUEUE,
                CONSOLE_QUEUE
            )

            response_text.insert(tk.END, CONSOLE_QUEUE.get())

            while not UDP_TRANSMIT_MESSAGE_QUEUE.empty():
                udp_message, target_ip = UDP_TRANSMIT_MESSAGE_QUEUE.get()
                udp_socket.sendto(udp_message, (RX_IP, UDP_PORT))
                time.sleep(0.3)

            response_text.insert(tk.END, "\nRX power on\n")
            run_params["Runs"].config(background="#8cde83")
            run_params["Samples"].config(background="#8cde83")
            run_params["Stacks"].config(background="#8cde83")
            run_params["Delay"].config(background="#8cde83")
    else:
        response_text.insert(tk.END, "Error: Not connected to FPGA\n")

def trace(latest_run_params,data_file,response_text,plot_handle,check_buttons):
    global udp_socket
    if udp_socket:
        required_keys = ["Order", "Reps", "Runs", "Samples", "Stacks", "Delay"]
        if all(key in latest_run_params and latest_run_params[key] for key in required_keys):
            testengine.start_run(udp_socket,latest_run_params,data_file, response_text,mode="TRACE")
            response_text.insert(tk.END, "Taking trace...")
            time.sleep(1)
            testengine.stop_run(udp_socket,response_text, mode="TRACE")
            response_text.insert(tk.END, "Done\n")
        else:
            response_text.insert(tk.END, "Error: Could not take trace\nMake sure to send parameters first\n")
    else:
        response_text.insert(tk.END, "Error: Not connected to FPGA\n")

    if check_buttons["DrawTrace"].get():
        file_path = os.path.join("runs", data_file.get())
        if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
            response_text.insert(tk.END, "Error: The input file is empty/doesn't exist.\n")
            return
        else:
            gui_functions.update_trace_plot(file_path,plot_handle,response_text)

def start_run_button_handler(button,latest_run_params,data_file,response_text):
    global udp_socket
    if udp_socket:
        required_keys = ["Order", "Reps", "Runs", "Samples", "Stacks", "Delay"]
        if all(key in latest_run_params and latest_run_params[key] for key in required_keys):
            if button["text"] == "START":
                response_text.insert(tk.END, "Starting RUN...")
                testengine.start_run(udp_socket,latest_run_params,data_file,response_text,mode="RUN")
                button.config(text="STOP", background="#f55656")
            elif button["text"] == "STOP":
                testengine.stop_run(udp_socket,response_text,mode="RUN")
                response_text.insert(tk.END, "Done\n")
                button.config(text="START", background="#f0f0f0")
        else:
            response_text.insert(tk.END,"Error: Could not start run\nMake sure to send parameters first\n")
    else:
        response_text.insert(tk.END,"Error: Not connected to FPGA\n")
