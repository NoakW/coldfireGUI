import socket
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import correlate
import subprocess

# Global variables
coldfire_ip = "192.168.1.2" # Coldfire device IP
UDP_PORT: int = 0x555  # Port
udp_socket = None  # Global socket variable
get_version = True


# Function to establish a udp connection
def connect_udp():
    MESSAGE = bytearray([0x55, 0x56, 0x00, 0x01, 0x00, 0x00, 0x00])
    global udp_socket, get_version
    data = []
    try:
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind((socket.gethostbyname(socket.gethostname()), UDP_PORT))
        udp_socket.settimeout(1)  # Set a timeout to prevent blocking

        if get_version:
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

            udp_socket.sendto(MESSAGE, (coldfire_ip, UDP_PORT))
            print(f"Sending message {MESSAGE}")

            print(f"HEX {MESSAGE.hex(sep='|')}")
            data, adr = udp_socket.recvfrom(1024)

        # Provide response on established connection
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
    except Exception as e:
        # udp_socket = None
        response_text.insert(tk.END, f"Connection failed: {e}\n")


# Function to close the UDP connection and stop the GUI
def close_udp():
    global udp_socket

    if udp_socket:
        try:
            udp_socket.close()
        except Exception:
            pass

    response_text.insert(tk.END, "UDP connection closed.\n")
    root.destroy()  # Ensure Tkinter exits


def plot_and_send_command():
    error_list = []  # Store errors

    # Check if the UDP socket is available before proceeding
    if not udp_socket:
        response_text.insert(tk.END, "Error: Not connected to Coldfire.\n")
        return

    try:
        # Validate repetitions input
        repetitions_input = repeat_input.get().strip()
        if not repetitions_input:
            error_list.append("Enter number of repetitions.")
        elif not repetitions_input.isdigit():
            error_list.append("Repetitions must be a number.")
        else:
            repetitions = int(repetitions_input)
            if not (1 <= repetitions <= 600):
                error_list.append("Repetitions must be between 1 and 600.")

        # Validate M-sequence order input
        order_input = command_input.get().strip()
        if not order_input:
            error_list.append("Enter M-sequence order.")
        elif not order_input.isdigit():
            error_list.append("M-sequence order must be an integer.")
        else:
            order = int(order_input)
            if not (5 <= order <= 12):
                error_list.append("M-sequence order must be between 5 and 12.")

        # Stop execution if there are validation errors
        if error_list:
            response_text.insert(tk.END, "Error: " + " | ".join(error_list) + "\n")
            return

        # Generate M-sequence data
        data = plot(order)
        data[data == -1] = 0  # Convert -1 to 0
        data = data.astype(np.uint8)

        response_text.insert(tk.END, f"\nSENT: M-sequence order = {order}, repetitions = {repetitions}.")

        send_ctrl(order)
        send_reps(repetitions)
        send_sequence(data)


    except Exception as e:
        response_text.insert(tk.END, f"Unexpected error: {e}\n")

def send_reps(repetitions):
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
        udp_socket.sendto(MESSAGE, (coldfire_ip, UDP_PORT))  # Send packed message
        if enable_MESSAGE_debug_var.get():
            response_text.insert(tk.END, f"Repetitions message 16-bit stream:\n {MESSAGE}\n")
        if enable_HEX_debug_var.get():
            response_text.insert(tk.END, f"Hex: {hex_representation}\n")

        data, adr = udp_socket.recvfrom(1024)

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
            udp_socket.sendto(MESSAGE, (coldfire_ip, UDP_PORT))  # Send packed message
            if enable_MESSAGE_debug_var.get():
                response_text.insert(tk.END, f"Sequence message 16-bit stream:\n {MESSAGE}\n")
            if enable_HEX_debug_var.get():
                response_text.insert(tk.END, f"Hex: {hex_representation}\n")

        # Receive response
            data, adr = udp_socket.recvfrom(1024)

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
    # Construct the message with correct header
    MESSAGE_CTRL = bytearray([
        0x55, 0x56,  # Protocol ID (0x5556)
        0x00, 0x01,  # Packet Number (0x0001)
        0x00, 0x00,
        0x00# Hardware Channel Number (0x0000)
    ])

    MESSAGE_CTRL.append(4)  # payload size (LSB)
    MESSAGE_CTRL.append(0)
    MESSAGE_CTRL.append(0)  # type: command
    MESSAGE_CTRL.append(0)
    MESSAGE_CTRL.append(1)  # frame number
    MESSAGE_CTRL.append(0)  # total frames
    MESSAGE_CTRL.append(1)
    MESSAGE_CTRL.append(1)  # 0x01 command:
    MESSAGE_CTRL.append(135) #0x87  --> total 0x0187 --> 391
    MESSAGE_CTRL.append(0)
    MESSAGE_CTRL.append(0)  # e.g order 5 -->
    MESSAGE_CTRL.append(order) # 0x05 --> total 0x0005 --> 5
    MESSAGE_CTRL.append(0)
    print(f"Order (16-bit): {order:016b}")

    hex_representation = MESSAGE_CTRL.hex(sep="|")

    # Send message over UDP
    try:
        udp_socket.sendto(MESSAGE_CTRL, (coldfire_ip, UDP_PORT))  # Send packed message
        if enable_MESSAGE_debug_var.get():
            response_text.insert(tk.END, f"Message 16-bit stream:\n {MESSAGE_CTRL}\n")
        if enable_HEX_debug_var.get():
            response_text.insert(tk.END, f"Hex: {hex_representation}\n")

        data, adr = udp_socket.recvfrom(1024)

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


def ping_coldfire():
    global udp_socket
    if udp_socket:
        """Pings the ColdFire device and inserts the result into the response_text widget."""
        try:
            result = subprocess.run(["ping", "192.168.1.2"], capture_output=True, text=True)
            return result.stdout  # Return the ping output as a string

        except Exception as e:
            return f"Error pinging ColdFire: {e}\n"
    else:
        return "Please connect Coldfire first"


def check_coldfire():
    """Function to be executed when the button is clicked."""
    output = ping_coldfire()  # Get the ping result
    response_text.insert(tk.END, output + "\n")  # Insert into the text widget


# Function to plot and update preview
def plot(number):
    global canvas, fig, ax1, ax2

    filename = f"../../Documents/my_mls{number}_1p_1f.txt"

    try:
        # Load data from the file
        data = np.loadtxt(filename, skiprows=1)

        # Extract the second column
        column_data = data[:, 1]
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


# Tkinter GUI setup
root = tk.Tk()
root.title("Coldfire Ethernet GUI")

# Create a frame for the left-side UI elements
left_frame = tk.Frame(root)
left_frame.pack(side="left", padx=10, pady=10)

# Instructions text
instructions_text = tk.Label(left_frame, height=10, width=50, text=(  # Instructions text
    "Welcome to the ColdFire Communication GUI\n\n"
    "Instructions:\n"
    "1. Enter a number corresponding to an M-sequence order (2^n - 1).\n"
    "2. Enter a number corresponding to the number \n of periods per spatial measurement\n"
    "3. Click the 'Send Command to Coldfire' button.\n"
    "4. Feedback is shown in the response area below.\n\n"
    "Use the 'Connect to ColdFire' button to \n a connection with the ColdFire device.\n\n"
))
instructions_text.grid(row=0, column=0, columnspan=3, padx=5, pady=10)

# UI Elements (left side) - Grid layout
# M-sequence order label and input field
# Checkboxes - placed in separate row
enable_MESSAGE_debug_var = tk.BooleanVar()
enable_HEX_debug_var = tk.BooleanVar()
enable_RESPONSE_debug_var = tk.BooleanVar(value=1)

enable_MESSAGE_debug = tk.Checkbutton(left_frame, text="Enable MESSAGE Debug", variable=enable_MESSAGE_debug_var)
enable_MESSAGE_debug.grid(row=1, column=0, padx=5, pady=5, sticky="w")

enable_HEX_debug = tk.Checkbutton(left_frame, text="Enable HEX Debug", variable=enable_HEX_debug_var)
enable_HEX_debug.grid(row=1, column=1, padx=5, pady=5, sticky="w")

enable_RESPONSE_debug = tk.Checkbutton(left_frame, text="Enable Coldfire Response", variable=enable_RESPONSE_debug_var)
enable_RESPONSE_debug.grid(row=1, column=2, padx=5, pady=5, sticky="w")


tk.Label(left_frame, text="Enter M-sequence order:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
command_input = tk.Entry(left_frame)
command_input.grid(row=2, column=1, padx=5, pady=5, sticky="ew")


# Repetitions label and input field
tk.Label(left_frame, text="Enter number of repetitions:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
repeat_input = tk.Entry(left_frame)
repeat_input.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

# Buttons - placed horizontally next to each other
connect_button = tk.Button(left_frame, text="Connect to Coldfire", command=connect_udp)
connect_button.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

send_button = tk.Button(left_frame, text="Send Command to Coldfire", command=plot_and_send_command)
send_button.grid(row=4, column=2, padx=5, pady=5, sticky="ew")

# Response text area - span across columns
response_text = tk.Text(left_frame, height=25, width=50)
response_text.grid(row=5, column=0, columnspan=3, padx=5, pady=10, sticky="nsew")

cleanup_button = tk.Button(left_frame,text="Clear Window", command=lambda: response_text.delete('1.0', tk.END))
cleanup_button.grid(row=3, column=2, padx=5, pady=5, sticky="ew")

debug_button = tk.Button(left_frame, text="Check Coldfire", command=check_coldfire)
debug_button.grid(row=4, column=0, padx=5, pady=5, sticky="ew")

# Configure column weights to ensure proper resizing
left_frame.grid_columnconfigure(0, weight=1)
left_frame.grid_columnconfigure(1, weight=2)  # Make the input fields take more space
left_frame.grid_columnconfigure(2, weight=1)  # Make sure the buttons don't overflow
left_frame.grid_columnconfigure(3, weight=1)  # Give checkboxes some space

# Create a frame for the right-side plot area
right_frame = tk.Frame(root)
right_frame.pack(side="right", padx=10, pady=10)

# Create a single Matplotlib figure
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(5, 7), dpi=100)
ax1.set_title("Preview")
ax2.set_title("Autocorrelation")

# Create a single canvas for the plots
canvas = FigureCanvasTkAgg(fig, master=right_frame)
canvas.get_tk_widget().pack()

# Create toolbar once
toolbar = NavigationToolbar2Tk(canvas, right_frame)
toolbar.update()

# Handle window close
root.protocol("WM_DELETE_WINDOW", close_udp)

# Start the Tkinter main loop
root.mainloop()

# Close the socket when exiting
if udp_socket:
    udp_socket.close()  # Ensure UDP socket is closed at the end