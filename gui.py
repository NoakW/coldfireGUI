import tkinter as tk
from tkinter import ttk
import button_functions
from Radargram import Radargram, Subfigures

plot_args = {}

data_file = "rundata.txt"
def launch():
    root = tk.Tk()
    root.title("Coldfire Ethernet GUI")

    trace_file_var = tk.StringVar(value="rundata.txt")

    check_buttons = {
        "MESSAGE": tk.BooleanVar(value=0),
        "HEX": tk.BooleanVar(value=0),
        "RESPONSE": tk.BooleanVar(value=0)
    }

    sliders = {}

    # Use a main frame for better control
    main_frame = tk.Frame(root)
    main_frame.pack(fill="y", expand=True)

    # Configure grid layout
    main_frame.columnconfigure(0, weight=1)  # Left-side frame (fixed)
    main_frame.columnconfigure(1, weight=3)  # Right-side frame (expands)
    main_frame.columnconfigure(2, weight=1)  # B-scan frame (fixed)
    main_frame.columnconfigure(3, weight=1)

    main_frame.rowconfigure(0, weight=1)  # Ensure vertical expansion

    # Create sub-frames
    left_frame = tk.Frame(main_frame, padx=10, pady=10)
    left_frame.grid(row=0, column=0, sticky="ns")

    right_frame = tk.Frame(main_frame, padx=10, pady=10)
    right_frame.grid(row=0, column=1, sticky="nsew")  # Expands properly

    bscan_frame = tk.Frame(main_frame, padx=10, pady=10)
    bscan_frame.grid(row=0, column=2, sticky="nsew")  # Far right

    bscan_config_frame = tk.Frame(main_frame, padx=10,pady=10)
    bscan_config_frame.grid(row=0,column=3,sticky="ns")

    # === Instructions Section ===
    instructions_text = tk.Label(
        left_frame, text=(
            "Welcome to the ColdFire Communication GUI\n\n"
            "Instructions:\n"
            "1. Use 'Connect to ColdFire' to establish a connection.\n"
            "2. Enter an M-sequence order (2^n - 1) and number of repetitions.\n" 
            "Send by clicking 'Send Command to FPGA'.\n"
            "3. Enter 'Runs', 'Samples' and 'Stacks' and send Shooting Table"
            "Send by clicking 'Send Shooting Table'\n"
            "4. Click 'Get Trace' to carry out measurements\n"
            "5. Data options are found to the right of the B-scan plot"
        ),
        justify="left", wraplength=350
    )
    instructions_text.pack(pady=5)

    # === Debug Options Section ===
    debug_frame = tk.LabelFrame(left_frame, text="Options", padx=5, pady=5)
    debug_frame.pack(fill="x", pady=5)

    tk.Checkbutton(debug_frame, text="Enable MESSAGE Debug", variable=check_buttons["MESSAGE"]).grid(row=0, column=0, sticky="w", padx=5, pady=2)
    tk.Checkbutton(debug_frame, text="Enable HEX Debug", variable=check_buttons["HEX"]).grid(row=1, column=0, sticky="w", padx=5, pady=2)
    tk.Checkbutton(debug_frame, text="Enable Coldfire Response", variable=check_buttons["RESPONSE"]).grid(row=2, column=0, sticky="w", padx=5, pady=2)

    connect_button = tk.Button(debug_frame, text="Connect to FPGA", width=25,
                               command=lambda: button_functions.connect_udp(response_text,connect_button,check_buttons))
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

    tk.Label(input_frame, text="Runs:").grid(row=0, column=2, sticky="e", padx=5, pady=2)
    runs_input = tk.Entry(input_frame, width=10)
    runs_input.grid(row=0, column=3, padx=5, pady=2)
    runs_input.insert(tk.END, 6)

    tk.Label(input_frame, text="Samples:").grid(row=1, column=2, sticky="e", padx=5, pady=2)
    samples_input = tk.Entry(input_frame, width=10)
    samples_input.grid(row=1, column=3, padx=5, pady=2)
    samples_input.insert(tk.END, 1850)

    tk.Label(input_frame, text="Stacks:").grid(row=2, column=2, sticky="e", padx=5, pady=2)
    stacks_input = tk.Entry(input_frame, width=10)
    stacks_input.grid(row=2, column=3, padx=5, pady=2)
    stacks_input.insert(tk.END, 1)

    tk.Label(input_frame,text="Delay (ms)").grid(row=3,column=2,sticky="e",padx=5,pady=2)
    delay_input = tk.Entry(input_frame, width=10)
    delay_input.grid(row=3, column=3, padx=5, pady=2)
    delay_input.insert(tk.END, 200)

    clear_inputs = tk.Button(input_frame, text="Clear Registers", command=lambda: button_functions.reset_registers(response_text,check_buttons))
    clear_inputs.grid(row=2, column=0, rowspan=2,columnspan=2, padx=12, pady=2,sticky="nsew")

    button_frame = tk.LabelFrame(left_frame, text="Actions", padx=5, pady=5)
    button_frame.pack(fill="x", pady=5)

    btn_width = 15  # Standardized button width

    start_run_button = ttk.Button(button_frame, text="START", width=btn_width,
                                  command=lambda: button_functions.start_run_button_handler(start_run_button,command_input.get(),repeat_input.get(),runs_input.get(),data_file,response_text))
    start_run_button.grid(row=0, column=1, padx=5, pady=2)

    shooting_button = ttk.Button(button_frame,
        text="Send Shooting Table", width=btn_width*1.2, command=lambda:
            button_functions.send_shooting_table(runs_input, samples_input,stacks_input,delay_input,response_text))

    shooting_button.grid(row=0, column=2, padx=5, pady=2)

    trace_button = ttk.Button(button_frame, text="Get Trace", width=btn_width,command=lambda:
        button_functions.trace(command_input.get(),repeat_input.get(),runs_input.get(),data_file,response_text,plot_handle))
    trace_button.grid(row=1, column=0, padx=5, pady=2, columnspan=2, sticky="nsew")

    # === Response Area ===
    response_text = tk.Text(left_frame, height=16, width=50)
    response_text.pack(pady=(5, 2), fill="x")  # Reduced bottom padding

    # Create a frame to group buttons and center them
    button_frame2 = tk.LabelFrame(left_frame, text="Data and Register Options")
    button_frame2.pack(pady=10, fill="x")  # Ensures it stretches horizontally

    # Ensure the frame expands properly
    button_frame2.columnconfigure(0, weight=1)  # Column 1 for Check buttons
    button_frame2.columnconfigure(1, weight=1)  # Column 2 for Clear buttons

    check_ctrl_button = ttk.Button(button_frame2, text="Check CTRL", command=lambda:button_functions.send_check_ctrl(response_text))
    check_ctrl_button.grid(row=0, column=0, padx=5, pady=3, sticky="ew")

    check_seq_button = ttk.Button(button_frame2, text="Check SEQ", command=lambda:button_functions.send_check_seq(response_text))
    check_seq_button.grid(row=1, column=0, padx=5, pady=3, sticky="ew")

    check_reps_button = ttk.Button(button_frame2, text="Check REPS", command=lambda:button_functions.send_check_reps(response_text))
    check_reps_button.grid(row=2, column=0, padx=5, pady=3, sticky="ew")

    clear_data_button = ttk.Button(button_frame2, text="Clear All", command=lambda: button_functions.clear_data_and_plots(trace_file_var.get(),plot_handle,radargram_handle,response_text))
    clear_data_button.grid(row=0, column=1, rowspan=2, padx=5, pady=3, sticky="nsew")

    cleanup_button = ttk.Button(button_frame2, text="Clear Response Text", command=lambda: response_text.delete('1.0', tk.END))
    cleanup_button.grid(row=2, column=1, rowspan=2, padx=5, pady=3, sticky="nsew")

    for i in range(3):
        button_frame2.rowconfigure(i, weight=1)

    plot_handle = Subfigures(right_frame,response_text,tk=tk)

    send_button = ttk.Button(button_frame, text="Send Sequence", width=btn_width,
                             command=lambda: button_functions.plot_and_send_command(plot_handle,
                                                command_input,repeat_input,check_buttons,response_text))

    send_button.grid(row=0, column=0, padx=5, pady=2)

    radargram_handle = Radargram(bscan_frame,response_text,tk=tk)

    """Config frame"""
    config_frame = tk.LabelFrame(bscan_config_frame, text="Plot Options", padx=5, pady=5)
    config_frame.pack(fill="x", pady=5)

    misc_frame = tk.LabelFrame(bscan_config_frame, text="Misc Options", padx=5, pady=5)
    misc_frame.pack(fill="x", pady=5)

    sliders["Enable"] = tk.BooleanVar(value=False)

    # Create the checkbutton using the sliders["Enable"] variable
    enable_plotinfo_button = tk.Checkbutton(
        config_frame,
        text="Enable Advanced Info",
        variable=sliders["Enable"],
        command=lambda: button_functions.toggle_set_button(sliders)
    )
    enable_plotinfo_button.grid(row=1, column=0, sticky="w", padx=5, pady=2)

    # Plot threshold label + entry
    tk.Label(config_frame, text="Plot Threshold (%):").grid(row=0, column=0, sticky="e", padx=5, pady=2)
    sliders["Threshold"] = tk.Entry(config_frame, width=10)
    sliders["Threshold"].grid(row=0, column=1, padx=5, pady=2)
    sliders["Threshold"].insert(tk.END, "20")



    enable_ramp_var = tk.IntVar(value=0)

    # Variable to hold the selected ramp type
    ramp_type_var = tk.StringVar(value="Linear")

    enable_ramp_checkbox = tk.Checkbutton(
        config_frame,
        text="Enable Ramp",
        variable=enable_ramp_var,
        command=lambda: button_functions.toggle_ramp_options(enable_ramp_var,ramp_dropdown)
    )
    enable_ramp_checkbox.grid(row=2, column=0, padx=5, pady=5, sticky="w")

    # Dropdown (combobox) for selecting ramp type
    ramp_dropdown = ttk.Combobox(
        config_frame,
        textvariable=ramp_type_var,
        values=["Linear", "Exponential"],
        state="disabled",  # Initially disabled
        width=20
    )
    ramp_dropdown.grid(row=2, column=1, padx=5, pady=5, sticky="w")

    tk.Label(config_frame, text="Peak Amplitude:").grid(row=3, column=0, sticky="e", padx=5, pady=2)
    sliders["PeakAmp_var"] = tk.DoubleVar(value=0.8)


    # Peak Amplitude Slider
    tk.Label(config_frame, text="Peak Amplitude:").grid(row=3, column=0, sticky="e", padx=5, pady=2)
    sliders["PeakAmp_var"] = tk.DoubleVar(value=0.8)

    # Save the actual slider widget
    sliders["PeakAmp"] = ttk.Scale(
        config_frame,
        from_=0,
        to=1,
        orient="horizontal",
        variable=sliders["PeakAmp_var"],
        command=lambda x: peak_amplitude_label.config(text=f'{float(x):.2f}'),
        state="disabled"
    )
    sliders["PeakAmp"].grid(row=3, column=1, columnspan=2, padx=5, pady=2, sticky="ew")

    # Label for PeakAmp value
    peak_amplitude_label = tk.Label(config_frame, text=f'{sliders["PeakAmp_var"].get():.2f}')
    peak_amplitude_label.grid(row=3, column=3, padx=5, pady=2)

    # Std Deviation Slider
    tk.Label(config_frame, text="Primary Std Deviation:").grid(row=4, column=0, sticky="e", padx=5, pady=2)
    sliders["StdDev_var"] = tk.DoubleVar(value=0.5)

    sliders["StdDev"] = ttk.Scale(
        config_frame,
        from_=0,
        to=1,
        orient="horizontal",
        variable=sliders["StdDev_var"],
        command=lambda x: std_dev_label.config(text=f'{float(x):.2f}')
    )
    sliders["StdDev"].grid(row=4, column=1, columnspan=2, padx=5, pady=2, sticky="ew")

    # Label for StdDev value
    std_dev_label = tk.Label(config_frame, text=f'{sliders["StdDev_var"].get():.2f}')
    std_dev_label.grid(row=4, column=3, padx=5, pady=2)

    # Cable Length Entry
    tk.Label(config_frame, text="Cable Length (m):").grid(row=5, column=0, sticky="e", padx=5, pady=2)
    sliders["CableLen"] = tk.Entry(config_frame, width=10)
    sliders["CableLen"].grid(row=5, column=1, padx=5, pady=2)
    sliders["CableLen"].insert(tk.END, "3")

    # Antenna Spacing Entry
    tk.Label(config_frame, text="Antenna Spacing (m):").grid(row=5, column=0, sticky="e", padx=5, pady=2)
    sliders["AntennaSpacing"] = tk.Entry(config_frame, width=10)
    sliders["AntennaSpacing"].grid(row=5, column=1, padx=5, pady=2)
    sliders["AntennaSpacing"].insert(tk.END, "0.55")

    update_traceplot_button = tk.Button(config_frame, text="Update", state="normal",
                                        command=lambda: button_functions.update_radargram_plot(radargram_handle,trace_file_var.get(),response_text,sliders))
    update_traceplot_button.grid(row=7, column=0, padx=5, pady=2, columnspan=2,sticky="ew")

    # Adjust column widths for consistent spacing
    config_frame.columnconfigure(1, weight=1)

    # Label for input
    trace_file_label = ttk.Label(misc_frame, text="Trace File Name:")
    trace_file_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

    # Entry field for the trace file name, bound to trace_file_var
    trace_file_entry = ttk.Entry(misc_frame, textvariable=trace_file_var, width=15)
    trace_file_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)

    # Label to display the current trace file
    current_trace_file_var = tk.StringVar(value=f"Current file: {trace_file_var.get()}")
    current_trace_label = ttk.Label(misc_frame, textvariable=current_trace_file_var)
    current_trace_label.grid(row=1, column=0, columnspan=4, sticky="w", padx=5, pady=(0, 5))

    # Button to call the function in button_functions.py
    set_trace_button = ttk.Button(misc_frame, text="Set",
                                  command=lambda: button_functions.update_trace_file_from_gui(trace_file_var,
                                                                                              current_trace_file_var))
    set_trace_button.grid(row=1, column=2,sticky="w", padx=5, pady=5)

    # Handle window close
    root.protocol("WM_DELETE_WINDOW", lambda: root.quit())
    root.state("zoomed")
    # Start the Tkinter main loop
    root.mainloop()
