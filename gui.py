import tkinter as tk
from tkinter import ttk
import udp_functions
import gui_functions
from Radargram import Radargram, Subfigures
import numpy as np

def launch():
    root = tk.Tk()
    root.title("M-sequence Radar GUI")

    trace_file_var = tk.StringVar(value="rundata.txt")

    check_buttons = {}
    sliders = {}

    # Use a main frame for better control
    left_frame, figure_frame, bscan_frame, bscan_config_frame = unpack_frames(root)
    left_response_text = tk.Text(left_frame, height=16, width=50)
    right_response_text = tk.Text(bscan_config_frame,height=14, width=40)

    # Create figure objects
    plot_handle = Subfigures(figure_frame, left_response_text, tk=tk)
    radargram_handle = Radargram(bscan_frame, right_response_text, tk=tk)

    # Setup left and right data option frames
    setup_left_frame(left_frame, check_buttons, trace_file_var, left_response_text, plot_handle, radargram_handle)
    setup_bscan_config_frame(bscan_config_frame, sliders, radargram_handle, right_response_text, trace_file_var)

    # Handle window close
    root.protocol("WM_DELETE_WINDOW", lambda: root.quit())
    root.state("zoomed")
    root.mainloop()

def unpack_frames(root):
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

    figure_frame = tk.Frame(main_frame, padx=10, pady=10)
    figure_frame.grid(row=0, column=1, sticky="nsew")  # Expands properly

    bscan_frame = tk.Frame(main_frame, padx=10, pady=10)
    bscan_frame.grid(row=0, column=2, sticky="nsew")  # Far right

    bscan_config_frame = tk.Frame(main_frame, padx=10, pady=10)
    bscan_config_frame.grid(row=0, column=3, sticky="ns")

    return left_frame, figure_frame, bscan_frame, bscan_config_frame

def setup_left_frame(left_frame, check_buttons, trace_file_var, response_text, plot_handle, radargram_handle):
    latest_run_params = {}
    run_params = {}

    instructions_text = tk.Label(
        left_frame, text=(
            "Welcome to the M-sequence Radar GUI\n\n"
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
    debug_frame = tk.LabelFrame(left_frame, text="Communications", padx=5, pady=5)
    debug_frame.pack(fill="x", pady=5)

    check_buttons["MESSAGE"] = tk.BooleanVar(value=False)
    check_buttons["HEX"] = tk.BooleanVar(value=False)
    check_buttons["RESPONSE"] = tk.BooleanVar(value=False)
    check_buttons["DrawTrace"] = tk.BooleanVar(value=True)

    tk.Checkbutton(debug_frame, text="Enable MESSAGE Debug", variable=check_buttons["MESSAGE"]).grid(row=0, column=0,
                                                                                                     sticky="w", padx=5,
                                                                                                     pady=2)
    tk.Checkbutton(debug_frame, text="Enable HEX Debug", variable=check_buttons["HEX"]).grid(row=1, column=0,
                                                                                             sticky="w", padx=5, pady=2)
    tk.Checkbutton(debug_frame, text="Enable Coldfire Response", variable=check_buttons["RESPONSE"]).grid(row=2,
                                                                                                          column=0,
                                                                                                          sticky="w",
                                                                                                          padx=5,
                                                                                                          pady=2)

    connect_button = tk.Button(debug_frame, text="Connect to FPGA", width=22,
                               command=lambda: udp_functions.connect_udp(response_text, connect_button, check_buttons))
    connect_button.grid(row=0, column=1, rowspan=3, padx=10, pady=2, sticky="ns")

    # === Input Parameters Section ===
    input_frame = tk.LabelFrame(left_frame, text="Input Parameters", padx=5, pady=5)
    input_frame.pack(fill="x", pady=5)

    tk.Label(input_frame, text="M-sequence order:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
    run_params["Order"] = tk.Entry(input_frame, width=10)
    run_params["Order"].grid(row=0, column=1, padx=5, pady=2)
    run_params["Order"].insert(tk.END, "9")

    tk.Label(input_frame, text="Repetitions:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
    run_params["Reps"] = tk.Entry(input_frame, width=10)
    run_params["Reps"].grid(row=1, column=1, padx=5, pady=2)
    run_params["Reps"].insert(tk.END, "1")

    tk.Label(input_frame, text="Runs:").grid(row=0, column=2, sticky="e", padx=5, pady=2)
    run_params["Runs"] = tk.Entry(input_frame, width=10)
    run_params["Runs"].grid(row=0, column=3, padx=5, pady=2)
    run_params["Runs"].insert(tk.END, "6")

    tk.Label(input_frame, text="Samples:").grid(row=1, column=2, sticky="e", padx=5, pady=2)
    run_params["Samples"] = tk.Entry(input_frame, width=10)
    run_params["Samples"].grid(row=1, column=3, padx=5, pady=2)
    run_params["Samples"].insert(tk.END, "1850")

    tk.Label(input_frame, text="Stacks:").grid(row=2, column=2, sticky="e", padx=5, pady=2)
    run_params["Stacks"] = tk.Entry(input_frame, width=10)
    run_params["Stacks"].grid(row=2, column=3, padx=5, pady=2)
    run_params["Stacks"].insert(tk.END, "1")

    tk.Label(input_frame, text="Delay (ms)").grid(row=3, column=2, sticky="e", padx=5, pady=2)
    run_params["Delay"] = tk.Entry(input_frame, width=10)
    run_params["Delay"].grid(row=3, column=3, padx=5, pady=2)
    run_params["Delay"].insert(tk.END, "200")

    send_button = tk.Button(input_frame, text="Send Sequence", width=15,
                                              command=lambda: gui_functions.plot_and_send_command(plot_handle,
                                                                                 run_params, latest_run_params,
                                                                                 check_buttons, response_text))
    send_button.grid(row=2, column=0, columnspan=2, padx=12, pady=2, sticky="nsew")

    shooting_button = tk.Button(input_frame,
                                 text="Send Shooting Table", width=15, command=lambda:
        udp_functions.send_shooting_table(run_params, latest_run_params, response_text))

    shooting_button.grid(row=3, column=0, columnspan=2, padx=12, pady=2, sticky="nsew")

    button_frame = tk.LabelFrame(left_frame, text="Actions", padx=5, pady=5)
    button_frame.pack(fill="x", pady=5)

    # Configure grid columns for better resizing
    for col in range(3):
        button_frame.columnconfigure(col, weight=1)

    clear_inputs = tk.Button(
        button_frame, text="Clear Registers", width=15,
        command=lambda: udp_functions.reset_registers(response_text, check_buttons)
    )
    clear_inputs.grid(row=0, column=0, padx=5, pady=2, sticky="ew")

    start_run_button = tk.Button(
        button_frame, text="START", width=20,
        command=lambda: udp_functions.start_run_button_handler(
            start_run_button, latest_run_params, trace_file_var, response_text
        )
    )
    start_run_button.grid(row=0, column=1, columnspan=2, padx=5, pady=6, sticky="ew")  # Spans two columns

    # Row 1: Debug + Get Trace + Draw Trace
    debug_button = tk.Button(
        button_frame, text="Debug Params", width=15,
        command=lambda: response_text.insert(
            tk.END,
            f'Run params: {", ".join(f"{key}={run_params[key].get()}" for key in ["Order", "Reps", "Runs", "Samples", "Stacks", "Delay"])}, '
            f'latest: {latest_run_params}\n'
        )
    )
    debug_button.grid(row=1, column=0, padx=5, pady=2, sticky="ew")

    trace_button = tk.Button(
        button_frame, text="Get Trace", width=15,
        command=lambda: udp_functions.trace(latest_run_params, trace_file_var, response_text, plot_handle,
                                            check_buttons)
    )
    trace_button.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

    tk.Checkbutton(
        button_frame, text="Draw Trace", variable=check_buttons["DrawTrace"]
    ).grid(row=1, column=2, sticky="w", padx=5, pady=2)

    # Place response text
    response_text.pack(pady=(5, 2), fill="x")

    # Create a frame to group buttons and center them
    lower_button_frame = tk.LabelFrame(left_frame, text="Data and Register Options")
    lower_button_frame.pack(pady=10, fill="x")  # Ensures it stretches horizontally

    # Ensure the frame expands properly
    lower_button_frame.columnconfigure(0, weight=1)  # Column 1 for Check buttons
    lower_button_frame.columnconfigure(1, weight=1)  # Column 2 for Clear buttons

    check_ctrl_button = tk.Button(lower_button_frame, text="Check CTRL",
                                   command=lambda: udp_functions.send_check("CTRL", response_text))
    check_ctrl_button.grid(row=0, column=0, padx=5, pady=4, sticky="ew")

    check_seq_button = tk.Button(lower_button_frame, text="Check SEQ",
                                  command=lambda: udp_functions.send_check("SEQ", response_text))
    check_seq_button.grid(row=1, column=0, padx=5, pady=4, sticky="ew")

    check_reps_button = tk.Button(lower_button_frame, text="Check REPS",
                                   command=lambda: udp_functions.send_check("REPS", response_text))
    check_reps_button.grid(row=2, column=0, padx=5, pady=4, sticky="ew")

    clear_data_button = tk.Button(lower_button_frame, text="Clear All",
                                   command=lambda: gui_functions.clear_data_and_plots(trace_file_var,
                                                                                      plot_handle, radargram_handle,
                                                                                      response_text))
    clear_data_button.grid(row=0, column=1, rowspan=2, padx=5, pady=4, sticky="nsew")

    cleanup_button = tk.Button(lower_button_frame, text="Clear Response Text",
                                command=lambda: response_text.delete('1.0', tk.END))
    cleanup_button.grid(row=2, column=1, rowspan=2, padx=5, pady=4, sticky="nsew")

    for i in range(3):
        lower_button_frame.rowconfigure(i, weight=1)

def setup_bscan_config_frame(bscan_config_frame, sliders, radargram_handle, response_text, trace_file_var):
    """Config frame"""
    config_frame = tk.LabelFrame(bscan_config_frame, text="Plot Options", padx=5, pady=5)
    config_frame.pack(fill="x", pady=5)
    config_frame.pack_propagate(False)

    file_frame = tk.LabelFrame(bscan_config_frame, text="File Options", padx=5, pady=5)
    file_frame.pack(fill="x", pady=5)

    # Define the dynamic frames directly into specific grid rows
    window_size_frame = tk.LabelFrame(config_frame,text="Remove Mean Settings")
    window_size_frame.grid(row=10, column=0, columnspan=4, sticky="ew", padx=5, pady=2)
    window_size_frame.grid_remove()  # Start hidden

    FREQ_plot_option_container = tk.LabelFrame(config_frame,text="Spectral content plot settings")
    FREQ_plot_option_container.grid(row=7, column=0,columnspan=4, sticky="ew", padx=5, pady=2)
    FREQ_plot_option_container.grid_remove()

    advanced_options_frame = tk.LabelFrame(config_frame,text="Peak Detection Settings")
    advanced_options_frame.grid(row=9, column=0, columnspan=4, sticky="ew", padx=5, pady=2)
    advanced_options_frame.grid_remove()  # Start hidden

    filter_frame = tk.LabelFrame(config_frame, text="Filter Settings")
    filter_frame.grid(row=11, column=0, columnspan=4, sticky="ew", padx=5, pady=2)
    filter_frame.grid_remove()  # Start hidden

    for frame in [config_frame, window_size_frame, advanced_options_frame, filter_frame]:
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)

    window_size_frame.columnconfigure(0, minsize=140)
    advanced_options_frame.columnconfigure(0, minsize=140)
    filter_frame.columnconfigure(0, minsize=140)

    sliders["Enable"] = tk.BooleanVar(value=False)
    sliders["RampEnabled"] = tk.BooleanVar(value=False)
    sliders["RampType"] = tk.StringVar(value="Linear")
    sliders["MeanRemoval"] = tk.BooleanVar(value=False)
    sliders["WindowSize"] = tk.DoubleVar(value=1)  # default value
    sliders["EnableBandPass"] = tk.BooleanVar(value=False)
    sliders["Contrast"] = tk.DoubleVar(value=0.8)
    sliders["LowBand"] = tk.DoubleVar(value=0)
    sliders["HighBand"] = tk.DoubleVar(value=200)
    sliders["NumPeaks"] = tk.IntVar(value=1)
    sliders["Aggressiveness"] = tk.DoubleVar(value=0.8)
    sliders["PatternLength"] = tk.IntVar(value=15)
    sliders["Closeness"] = tk.IntVar(value=6)
    sliders["Normalize"] = tk.BooleanVar(value=False)
    sliders["FREQ"] = tk.BooleanVar(value=False)
    sliders["RESP"] = tk.BooleanVar(value=True)
    sliders["STIM"] = tk.BooleanVar(value=True)
    sliders["f_c"] = tk.BooleanVar(value=True)
    sliders["TRACE"] = tk.BooleanVar(value=True)
    temp_trace_file_var = tk.StringVar()

    # Plot threshold label + entry (trace index range)
    tk.Label(config_frame, text="Plot Threshold (traces):").grid(row=0, column=0, sticky="e", padx=5, pady=2)

    trace_range_frame = tk.Frame(config_frame)
    trace_range_frame.grid(row=0, column=1, sticky="w", padx=2, pady=2)

    sliders["NumTraces"] = tk.Entry(trace_range_frame, width=14)
    sliders["NumTraces"].grid(row=0, column=0, sticky="w", padx=3, pady=2)
    gui_functions.update_trace_range(trace_file_var, sliders)

    update_trace_range_button = tk.Button(
        trace_range_frame,
        text="Reset",
        state="normal",
        command=lambda: gui_functions.update_trace_range(trace_file_var,sliders)
    )
    update_trace_range_button.grid(row=0, column=1, padx=5, pady=2, sticky="nsew")

    # Plot threshold label + entry
    tk.Label(config_frame, text="Plot Threshold (ns):").grid(row=1, column=0, sticky="e", padx=5, pady=2)
    sliders["Threshold"] = tk.Entry(config_frame, width=14)
    sliders["Threshold"].grid(row=1, column=1, padx=5, pady=2,sticky="w")
    sliders["Threshold"].insert(tk.END, "150")

    # Plot threshold label + entry
    tk.Label(config_frame, text='Estimated εᵣ:').grid(row=2, column=0, sticky="e", padx=5, pady=2)
    sliders["e_r"] = tk.Entry(config_frame, width=14)
    sliders["e_r"].grid(row=2, column=1, padx=5, pady=2,sticky="w")
    sliders["e_r"].insert(tk.END, "8")

    plotinfo_container = tk.Frame(config_frame)
    plotinfo_container.grid(row=3, column=0, sticky="e", padx=5, pady=2)
    plotinfo_label = tk.Label(plotinfo_container, text="Peak Detection")
    plotinfo_label.pack(side="left", padx=(0, 5))

    # Checkbox on the right
    enable_plotinfo_button = tk.Checkbutton(
        plotinfo_container,
        variable=sliders["Enable"],
        command=lambda: gui_functions.toggle_slider_option(sliders, "Enable", advanced_options_frame)
    )
    enable_plotinfo_button.pack(side="left")

    normalize_container = tk.Frame(config_frame)
    normalize_container.grid(row=3, column=1, sticky="w", padx=5, pady=2)
    normalize_label = tk.Label(normalize_container, text="Normalize")
    normalize_label.pack(side="left", padx=(0, 5))

    # Checkbox on the right
    enable_normalize_button = tk.Checkbutton(
        normalize_container,
        variable=sliders["Normalize"],
    )
    enable_normalize_button.pack(side="left",padx=(0, 5))

    # Container for label + checkbox
    mean_removal_container = tk.Frame(config_frame)
    mean_removal_container.grid(row=4, column=0, sticky="e", padx=5, pady=5)

    # Label on the left
    mean_removal_label = tk.Label(mean_removal_container, text="Remove Mean")
    mean_removal_label.pack(side="left", padx=(0, 5))

    # Checkbox on the right
    mean_removal_cb = tk.Checkbutton(
        mean_removal_container,
        variable=sliders["MeanRemoval"],
        command=lambda: gui_functions.toggle_slider_option(sliders, "MeanRemoval", window_size_frame)
    )
    mean_removal_cb.pack(side="left")

    # Container for label + checkbox
    filter_container = tk.Frame(config_frame)
    filter_container.grid(row=4, column=1, sticky="w", padx=5, pady=2)

    # Label on the left
    filter_label = tk.Label(filter_container, text="Filtering")
    filter_label.pack(side="left", padx=(10, 5))

    # Checkbox on the right
    filter_cb = tk.Checkbutton(
        filter_container,
        variable=sliders["EnableBandPass"],
        command=lambda: gui_functions.toggle_filter_option(sliders, "EnableBandPass", filter_frame,
                                                           trace_file_var.get(), response_text)
    )
    filter_cb.pack(side="right",padx=(0, 5))

    # Container for label + checkbox
    ramp_container = tk.Frame(config_frame)
    ramp_container.grid(row=5, column=0, sticky="e", padx=5, pady=5)

    # Label on the left
    ramp_label = tk.Label(ramp_container, text="Enable Ramp")
    ramp_label.pack(side="left", padx=(0, 5))

    # Checkbox on the right
    enable_ramp_checkbox = tk.Checkbutton(
        ramp_container,
        variable=sliders["RampEnabled"],
        command=lambda: gui_functions.toggle_ramp_options(sliders["RampEnabled"], ramp_dropdown)
    )
    enable_ramp_checkbox.pack(side="left")

    ramp_dropdown = ttk.Combobox(
        config_frame,
        textvariable=sliders["RampType"],
        values=["Linear", "Exponential", "Rsquared"],
        state="disabled",
        width=15
    )
    ramp_dropdown.grid(row=5, column=1, padx=5, pady=5, sticky="w")

    FREQ_container = tk.Frame(config_frame)
    FREQ_container.grid(row=6, column=0, sticky="e", padx=5, pady=2)
    FREQ_label = tk.Label(FREQ_container, text="Spectral Density")
    FREQ_label.pack(side="left", padx=(0, 5))

    # Checkbox on the right
    enable_FREQ_button = tk.Checkbutton(
        FREQ_container,
        variable=sliders["FREQ"],
        command=lambda: gui_functions.toggle_FREQ(sliders, enable_plotinfo_button, enable_ramp_checkbox,
                                                  mean_removal_cb,
                                                  filter_cb, enable_normalize_button,
                                                  advanced_options_frame, window_size_frame, filter_frame,FREQ_plot_option_container)
    )
    enable_FREQ_button.pack(side="left")

    # Option 1: Stimulus (Red Solid Line)
    STIM_label = tk.Label(
        FREQ_plot_option_container,
        text="x(𝜏)",  # solid line
        fg="red"
    )
    STIM_label.pack(side="left", padx=(0, 2))

    STIM_button = tk.Checkbutton(
        FREQ_plot_option_container,
        variable=sliders["STIM"],
    )
    STIM_button.pack(side="left", padx=(0, 2))

    # Option 2: Ground Response (Blue Solid Line)
    RESP_label = tk.Label(
        FREQ_plot_option_container,
        text="y(𝜏)",
        fg="blue"
    )
    RESP_label.pack(side="left", padx=(0, 2))

    RESP_button = tk.Checkbutton(
        FREQ_plot_option_container,
        variable=sliders["RESP"],
    )
    RESP_button.pack(side="left", padx=(0, 2))

    # Option 3: 2f_c Lines (Black Dashed Line)
    trace_freq_label = tk.Label(
        FREQ_plot_option_container,
        text="y(t)",  # dashed line
        fg="green"
    )
    trace_freq_label.pack(side="left", padx=(0, 2))

    trace_freq_button = tk.Checkbutton(
        FREQ_plot_option_container,
        variable=sliders["TRACE"],
    )
    trace_freq_button.pack(side="left", padx=(0, 2))

    # Option 3: 2f_c Lines (Black Dashed Line)
    f_c_label = tk.Label(
        FREQ_plot_option_container,
        text="Clock",  # dashed line
        fg="black"
    )
    f_c_label.pack(side="left", padx=(0, 2))

    f_c_button = tk.Checkbutton(
        FREQ_plot_option_container,
        variable=sliders["f_c"],
    )
    f_c_button.pack(side="left", padx=(0, 2))

    # Contrast slider container
    contrast_container = tk.LabelFrame(config_frame)
    contrast_container.grid(row=8, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

    # Label on the left
    tk.Label(contrast_container, text="Contrast").pack(side="left", padx=(0, 5))

    # Slider
    sliders["Contrast_slider"] = ttk.Scale(
        contrast_container,
        from_=0,
        to=0.99,
        orient="horizontal",
        variable=sliders["Contrast"],
        command=lambda x: contrast_value_label.config(text=f'{float(x):.2f}')
    )
    sliders["Contrast_slider"].pack(side="left", fill="x", expand=True)

    # Value label on the right
    contrast_value_label = tk.Label(contrast_container, text=f'{sliders["Contrast"].get():.2f}')
    contrast_value_label.pack(side="left", padx=(5, 0))

    tk.Label(advanced_options_frame, text="Peaks per Trace:").grid(row=0, column=0, sticky="e", padx=5, pady=2)

    # Create the slider to choose the number of peaks
    sliders["NumPeaks_slider"] = ttk.Scale(
        advanced_options_frame,
        from_=1,
        to=7,
        orient="horizontal",
        variable=sliders["NumPeaks"],
        command=lambda x: numpeak_label.config(text=f'{int(float(x))}')
    )

    sliders["NumPeaks_slider"].grid(row=0, column=1, columnspan=1, padx=5, pady=2, sticky="ew")

    # Label to display the number of peaks, formatted as an integer
    numpeak_label = tk.Label(advanced_options_frame, text=f'{sliders["NumPeaks"].get()}')
    numpeak_label.grid(row=0, column=3, padx=5, pady=2)

    tk.Label(advanced_options_frame, text="Pattern Length:").grid(row=1, column=0, sticky="e", padx=5, pady=2)

    # Create the slider to choose the number of peaks
    sliders["PatternLength_slider"] = ttk.Scale(
        advanced_options_frame,
        from_=1,
        to=50,
        orient="horizontal",
        variable=sliders["PatternLength"],
        command=lambda x: patternlength_label.config(text=f'{int(float(x))}')
    )

    sliders["PatternLength_slider"].grid(row=1, column=1, columnspan=1, padx=5, pady=2, sticky="ew")

    # Label to display the number of peaks, formatted as an integer
    patternlength_label = tk.Label(advanced_options_frame, text=f'{sliders["PatternLength"].get()}')
    patternlength_label.grid(row=1, column=3, padx=5, pady=2)

    tk.Label(advanced_options_frame, text="Closeness:").grid(row=2, column=0, sticky="e", padx=5, pady=2)

    # Create the slider to choose the number of peaks
    sliders["Closeness_slider"] = ttk.Scale(
        advanced_options_frame,
        from_=1,
        to=10,
        orient="horizontal",
        variable=sliders["Closeness"],
        command=lambda x: closeness_label.config(text=f'{int(float(x))}')
    )

    sliders["Closeness_slider"].grid(row=2, column=1, columnspan=1, padx=5, pady=2, sticky="ew")

    # Label to display the number of peaks, formatted as an integer
    closeness_label = tk.Label(advanced_options_frame, text=f'{sliders["Closeness"].get()}')
    closeness_label.grid(row=2, column=3, padx=5, pady=2)

    tk.Label(advanced_options_frame, text="Aggressiveness:").grid(row=3, column=0, sticky="e", padx=5, pady=2)

    # Create the slider to choose the number of peaks
    sliders["Aggressiveness_slider"] = ttk.Scale(
        advanced_options_frame,
        from_=0,
        to=1,
        orient="horizontal",
        variable=sliders["Aggressiveness"],
        command=lambda x: aggressiveness_label.config(text=f'{float(x):.2f}')
    )

    sliders["Aggressiveness_slider"].grid(row=3, column=1, columnspan=1, padx=5, pady=2, sticky="ew")

    # Label to display the number of peaks, formatted as an integer
    aggressiveness_label = tk.Label(advanced_options_frame, text=f'{sliders["Aggressiveness"].get()}')
    aggressiveness_label.grid(row=3, column=3, padx=5, pady=2)

    tk.Label(window_size_frame, text="Fractional Window:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
    sliders["WindowSizeSlider"] = ttk.Scale(
        window_size_frame,
        from_=0.0,
        to=1.0,
        orient="horizontal",
        variable=sliders["WindowSize"],
        command=lambda x: windowsize_label.config(text=f'{float(x):.2f}')
    )
    sliders["WindowSizeSlider"].grid(row=0, column=1, columnspan=1, padx=5, pady=2, sticky="ew")
    windowsize_label = tk.Label(window_size_frame, text=f'{sliders["WindowSize"].get():.2f}')
    windowsize_label.grid(row=0, column=3, padx=5, pady=2)

    tk.Label(filter_frame, text="Low (MHz):").grid(row=0, column=0, sticky="e", padx=5, pady=2)
    sliders["LowBand"] = tk.Entry(filter_frame, width=10)
    sliders["LowBand"].insert(tk.END, "30")
    sliders["LowBand"].grid(row=0, column=1, padx=5, pady=2)
    tk.Label(filter_frame, text="High (MHz):").grid(row=1, column=0, sticky="e", padx=5, pady=2)
    sliders["HighBand"] = tk.Entry(filter_frame, width=10)
    sliders["HighBand"].insert(tk.END, "200")
    sliders["HighBand"].grid(row=1, column=1, padx=5, pady=2)

    trace_file_label = ttk.Label(file_frame, text="Trace File Name:")
    trace_file_label.grid(row=0, column=0, sticky="e", padx=5, pady=5)

    update_traceplot_button = tk.Button(
        config_frame,
        text="Update",
        state="normal",
        command=lambda: gui_functions.update_radargram_plot(
            radargram_handle, trace_file_var.get(), response_text, sliders
        )
    )
    update_traceplot_button.grid(row=12, column=0, padx=0, pady=2, columnspan=3, sticky="nsew")

    # Entry field for the trace file name, bound to the temp variable
    trace_file_entry = tk.Entry(file_frame, textvariable=temp_trace_file_var, width=22)
    trace_file_entry.grid(row=0, column=1, sticky="w", padx=3, pady=5)
    trace_file_entry.insert(0,f"{trace_file_var.get()}")

    # The actual/confirmed file variable
    current_file_container = tk.Frame(file_frame)
    current_file_container.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

    current_trace_file_var = tk.StringVar(value=f"Current file: {trace_file_var.get()}")
    current_trace_label = ttk.Label(current_file_container, textvariable=current_trace_file_var)
    current_trace_label.grid(row=1, column=0, sticky="w", padx=5, pady=(0, 5))

    write_dir_button = tk.Button(file_frame,width=15, text="Write Data to File",
                                 command=lambda:gui_functions.write_to_dir(trace_file_var,response_text,radargram_handle,sliders))
    write_dir_button.grid(row=3,column=0,sticky="ew",padx=3,pady=5)
    # Place response text
    response_text.pack(pady=(5, 2), fill="x")

    # Button to confirm selection
    set_trace_button = tk.Button(
        file_frame,
        text="Set",
        width=15,
        command=lambda: gui_functions.update_trace_file_from_gui(
            temp_trace_file_var, trace_file_var, current_trace_file_var
        )
    )
    set_trace_button.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
