import socket
import tkinter as tk
from scipy.signal import correlate, resample
import time
import queue
import sequences
import testengine
import numpy as np
import os
import udp_functions
from Radargram import Radargram
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def plot_and_send_command(plot_handle, run_params, latest_run_params, check_buttons, response_text):
    error_messages = []
    sequence = []

    run_params["Order"].config(background="white")
    run_params["Reps"].config(background="white")
    # Attempt to parse and validate fields
    fields = [
        ("Order", run_params["Order"]),
        ("Reps", run_params["Reps"]),
    ]

    cleaned_values = {}

    for name, field in fields:
        try:
            value = int(field.get().strip())
            if value <= 0:
                error_messages.append(f"Invalid value of {name}")
                run_params[name].config(background="#f55656")
            elif name == "Order" and (value < 5 or value > 12):
                error_messages.append(f"Order must be between 5 and 12")
                run_params[name].config(background="#f55656")
            else:
                cleaned_values[name] = value
                sequence.append(value)
        except ValueError:
            error_messages.append(f"Non-numeric {name}")
            run_params[name].config(background="#f55656")

    if error_messages:
        response_text.insert(tk.END, "Error(s):\n" + "\n".join(f"- {msg}" for msg in error_messages) + "\n")
        return

    # Use those parameters for plotting and UDP
    data = plot(sequence[0], plot_handle, response_text)
    data[data == -1] = 0
    data = data.astype(np.uint8)

    response_text.insert(tk.END, f"Sending M-sequence order = {sequence[0]}, Reps = {sequence[1]}...\n")
    # Send to FPGA
    interrupted = False
    if not interrupted:
        interrupted = udp_functions.send_ctrl(sequence[0], response_text, check_buttons)
        time.sleep(0.1)
    if not interrupted:
        interrupted = udp_functions.send_reps(sequence[1], response_text, check_buttons)
        time.sleep(0.1)
    if not interrupted:
        udp_functions.send_sequence(data, response_text, check_buttons)
    if not interrupted:
        run_params["Order"].config(background="#8cde83")
        run_params["Reps"].config(background="#8cde83")
        latest_run_params["Order"] = cleaned_values["Order"]
        latest_run_params["Reps"] = cleaned_values["Reps"]
        response_text.insert(tk.END, f"Success\n")
    else:
        run_params["Order"].config(background="#fac157")
        run_params["Reps"].config(background="#fac157")

def validate_shooting_table(run_params, response_text,latest_run_params):
    error_messages = []
    required_fields = ["Runs", "Samples", "Stacks", "Delay"]

    # Reset all backgrounds
    for field in required_fields:
        run_params[field].config(background="white")

    # Step 1: Basic validation
    valid_inputs = {}
    for name in required_fields:
        value_str = run_params[name].get().strip()
        try:
            value = int(value_str)
            if value <= 0:
                error_messages.append(f"- {name} must be > 0")
            valid_inputs[name] = value
        except ValueError:
            error_messages.append(f"- {name}: Expected integer, got {value_str}")
            run_params[name].config(background="#f55656")

    # Step 2: Field-specific rules (only if basic types were valid)
    if "Samples" in valid_inputs:
        if valid_inputs["Samples"] > 1900:
            error_messages.append("- Samples: too many samples (max 1900)")
            run_params["Samples"].config(background="#f55656")

    if "Stacks" in valid_inputs:
        if valid_inputs["Stacks"] > 300:
            error_messages.append("- Stacks: too many stacks (max 300)")
            run_params["Stacks"].config(background="#f55656")

    if "Delay" in valid_inputs:
        if not (10 <= valid_inputs["Delay"] <= 200):
            error_messages.append("- Delay: must be between 10 and 200")
            run_params["Delay"].config(background="#f55656")

    # Step 3: Signal length check
    if error_messages:
        response_text.insert(tk.END, "Error(s):\n" + "\n".join(error_messages) + "\n")
        return None, run_params

    order = int(latest_run_params["Order"])
    reps = int(latest_run_params["Reps"])
    runs = valid_inputs["Runs"]
    samples = valid_inputs["Samples"]

    signal_length = (2 ** order - 1) * reps
    virtual_sampling_rate = 160e6 * runs
    signal_time = signal_length / 320e6
    signal_length_samples = round(signal_time * virtual_sampling_rate)

    if samples < signal_length_samples:
        error_messages.append(f"- Samples: signal length {signal_length_samples} too long — increase Samples")
        run_params["Samples"].config(background="#f55656")

    # Step 4: Report or return
    if error_messages:
        response_text.insert(tk.END, "Error(s):\n" + "\n".join(error_messages) + "\n")
        return None, run_params

    shooting_table = [valid_inputs[name] for name in required_fields]
    response_text.insert(tk.END, f"Shooting table values: {shooting_table}\n")
    return shooting_table, run_params

def update_trace_plot(file_path, plot_handle, response_text):
    plot_handle.ax3.cla()
    plot_handle.ax3.set_title("Trace Data")
    try:
        with open(file_path, "r") as file:
            for line_num, line in enumerate(file):
                try:
                    data = list(map(float, line.strip().split(',')[11:]))
                    plot_handle.ax3.plot(data)
                except ValueError:
                    continue  # Skip malformed lines

        plot_handle.ax3.set_navigate(True)
        plot_handle.canvas.draw()

    except Exception as e:
        response_text.insert(tk.END, f"Error reading or plotting trace data: {e}\n")

def clear_data_and_plots(data_file,plot_handle, radargram_handle, response_text):

    file_path = os.path.join("runs", data_file.get())

    if os.path.exists(file_path):
        confirm_clear = tk.messagebox.askyesno("Confirm",
                                            f"Are you sure you want to remove the file: {data_file.get()} and clear the plots?")

        if not confirm_clear:
            return  # Abort if the user cancels
    else:
        response_text.insert(tk.END, f"Error: File {file_path} not found\n")
        return

    # Proceed with clearing if user confirms
    try:
        os.remove(file_path)  # Try to remove the file
    except Exception as e:
        response_text.insert(tk.END, f"Error deleting file: {e}\n")

    try:
        plot_handle.ax3.clear()
        plot_handle.ax3.set_title("Trace Data")

        # Clear the radargram plot
        if radargram_handle:
            radargram_handle.reset_radargram(eraseplots=True)

        # Redraw the axes on the canvas (both the main and radargram canvas)
        if plot_handle.canvas:
            plot_handle.canvas.draw()  # Redraw the canvas for the main plot
        if radargram_handle.canvas:  # Ensure canvas is drawn correctly for radargram
            radargram_handle.canvas.draw()  # Redraw the radargram canvas

    except Exception as e:
        response_text.insert(tk.END, f"Error clearing plots: {e}\n")

    # Notify the user that clearing was successful
    response_text.insert(tk.END, f"{file_path[5:]} and plots successfully cleared\n")

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
        plot_handle.ax1.set_ylim([np.min(y_boxy) - 0.5, np.max(y_boxy) + 0.5])
        plot_handle.ax1.set_title("Preview")

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

def update_trace_range(trace_file_var,sliders):
    with open(f"runs/{trace_file_var.get()}") as f:
        num_rows = sum(1 for _ in f) - 1
        sliders["NumTraces"].delete(0, tk.END)
        sliders["NumTraces"].insert(tk.END, f"0:{num_rows}")

def toggle_slider_option(sliders, slider_key, frame):
    if sliders[slider_key].get():
        frame.grid()
    else:
        frame.grid_remove()

def toggle_filter_option(sliders, slider_key, frame, trace_file, response_text):
    # Only execute if the slider is active (enabled)
    if sliders[slider_key].get():
        frame.grid()  # Ensure the frame is visible
        file_path = os.path.join("runs", trace_file)

        # Check if the file is valid before plotting
        if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
            # Display error if file is not valid
            response_text.insert(tk.END, "Error: Could not preview frequency content\n")

            # If a plot already exists, clear it and remove it
            if hasattr(frame, 'freq_canvas') and frame.freq_canvas is not None:
                frame.freq_canvas.get_tk_widget().destroy()  # Destroy the canvas widget
                frame.freq_canvas = None  # Clear the canvas reference

            return  # Exit early as there is no valid data

        # Create the figure and axis for plotting
        freq_fig = plt.figure(figsize=(1.9, 1.4), dpi=100)
        ax = freq_fig.add_subplot(111)
        ax.set_xlabel("Frequency (MHz)")
        ax.set_xlim([0, 250])
        ax.set_yticks([])# Set the x-axis limits
        ax.grid(True)

        # Create canvas and link it to the Tkinter frame
        freq_canvas = FigureCanvasTkAgg(freq_fig, master=frame)
        freq_canvas.draw()

        # Position the canvas widget in the frame
        freq_canvas.get_tk_widget().grid(row=2, column=0, columnspan=4, sticky="ew", padx=5, pady=5)
        freq_fig.tight_layout()
        # Store the canvas reference in the frame object for future cleanup
        frame.freq_canvas = freq_canvas

        # Read and process the data from the file
        try:
            full_data = np.genfromtxt(file_path, delimiter=',')
            raw_traces = full_data[:, 11:]
            runs = full_data[-1, 2]
            order = full_data[-1, 0]
            reps = full_data[-1, 1]
            mls_filename = f"Mseqs/my_mls{int(order)}_1p_1f.txt"
            mls_signal = np.loadtxt(mls_filename, skiprows=1)[:, 1]
            full_mls_signal = np.tile(mls_signal, int(reps))
            clock_freq = 160e6
            n_t = raw_traces.shape[1]
            fs = 160e6 * runs
            mls_freq = clock_freq * 2
            upsample_factor = (clock_freq * runs) / mls_freq
            resampled_mls_signal = resample(full_mls_signal, int(np.float64(len(full_mls_signal)) * upsample_factor))

            mls_len = len(resampled_mls_signal)

            if mls_len < n_t:
                pad_width = n_t - mls_len
                resampled_mls_signal = np.pad(resampled_mls_signal, (0, pad_width), mode='constant')

            cross_correlation = np.zeros((raw_traces.shape[0], n_t + len(resampled_mls_signal) - 1))

            for i in range(raw_traces.shape[0]):
                corr = correlate(raw_traces[i, :], resampled_mls_signal, mode='full', method='fft')
                corr /= np.sqrt(np.sum(raw_traces[i, :] ** 2) * np.sum(resampled_mls_signal ** 2))  # Normalize
                cross_correlation[i, :] = corr

            magnitudes = []
            for corr in cross_correlation:
                fft_vals = np.fft.rfft(corr)
                mag = np.abs(fft_vals)
                magnitudes.append(mag)

            freqs_t = np.fft.rfftfreq(cross_correlation.shape[1], d=1 / fs)
            mean_magnitude = np.mean(magnitudes, axis=0)

            # Plot the cross-correlation result
            ax.plot(freqs_t[1:] / 1e6, mean_magnitude[1:], label="Raw Response", color='g')

        except ValueError as e:
            response_text.insert("end", f"Error: {e}\n")
    else:
        # If the filter option is disabled, hide the frame
        frame.grid_remove()


def toggle_FREQ(sliders,enable_plotinfo_button,enable_ramp_checkbox,mean_removal_cb,filter_cb, enable_normalize_button,
               advanced_options_frame, window_size_frame, filter_frame,FREQ_plot_options_container):
    if sliders["FREQ"].get():
        sliders["Enable"].set(False)
        sliders["RampEnabled"].set(False)
        sliders["MeanRemoval"].set(False)
        sliders["EnableBandPass"].set(False)
        sliders["Normalize"].set(False)

        toggle_slider_option(sliders, "Enable", advanced_options_frame)
        toggle_slider_option(sliders, "MeanRemoval", window_size_frame)
        toggle_slider_option(sliders, "EnableBandPass", filter_frame)

        enable_normalize_button.config(state="disabled")
        enable_plotinfo_button.config(state="disabled")
        enable_ramp_checkbox.config(state="disabled")
        mean_removal_cb.config(state="disabled")
        filter_cb.config(state="disabled")
        sliders["Contrast_slider"].config(state="disabled")

        toggle_slider_option(sliders,"FREQ",FREQ_plot_options_container)

    else:
        # Re-enable them if needed
        enable_normalize_button.config(state="normal")
        enable_plotinfo_button.config(state="normal")
        enable_ramp_checkbox.config(state="normal")
        mean_removal_cb.config(state="normal")
        filter_cb.config(state="normal")
        sliders["Contrast_slider"].config(state="normal")

        toggle_slider_option(sliders, "FREQ", FREQ_plot_options_container)


def update_radargram_plot(radargram_handle, data_file, response_text, sliders):
    # Clear the previous response text
    if not sliders["FREQ"].get():
        response_text.delete("1.0", tk.END)
        file_path = os.path.join("runs", data_file)

        # Attempt to get the data
        if not radargram_handle.get_data(file_path, sliders):
            return
        # Proceed with normal execution if data is valid
        response_text.insert(tk.END,
                             f"Traces: {radargram_handle.traces.shape[0]}, Order: {radargram_handle.order}, Reps: {radargram_handle.reps}, Runs: {radargram_handle.runs}\n")
        radargram_handle.extract_relevant_data()
        radargram_handle.compute_crosscorrelations(sliders)
        if not radargram_handle.calculate_axes(sliders):
            return
        radargram_handle.draw_traces(sliders)
        if sliders["MeanRemoval"].get():
            radargram_handle.remove_mean(sliders)
        if sliders["EnableBandPass"].get():
            radargram_handle.apply_bandpass(sliders)
        if sliders["RampEnabled"].get():
            radargram_handle.apply_ramp(sliders)
        radargram_handle.draw_radargram(sliders)

        # radargram_handle.compute_snr_per_trace() #TODO Fix this? Currently experimental
        response_text.insert(tk.END, "Plots updated\n")

        if sliders["Enable"].get():
            radargram_handle.layer_plotinfo(sliders)
    else:
        response_text.delete("1.0", tk.END)
        file_path = os.path.join("runs", data_file)

        # Attempt to get the data
        if not radargram_handle.get_data(file_path, sliders):
            return
        # Proceed with normal execution if data is valid
        response_text.insert(tk.END,
                             f"Traces: {radargram_handle.traces.shape[0]}, Order: {radargram_handle.order}, Reps: {radargram_handle.reps}, Runs: {radargram_handle.runs}\n")
        radargram_handle.extract_relevant_data()
        radargram_handle.compute_crosscorrelations(sliders)
        if not radargram_handle.calculate_axes(sliders):
            return
        radargram_handle.fig.clear()
        radargram_handle.draw_traces(sliders)
        radargram_handle.draw_Freq(sliders)

def update_trace_file_from_gui(temp_trace_file_var, trace_file_var, current_trace_file_var):
    filename = temp_trace_file_var.get().strip()
    if filename and not filename.endswith(".txt"):
        filename += ".txt"

    trace_file_var.set(filename)
    current_trace_file_var.set(f"Current file: {filename}")

def toggle_ramp_options(ramp_enabled_var, ramp_dropdown_widget):
    if ramp_enabled_var.get():
        ramp_dropdown_widget.config(state="readonly")
    else:
        ramp_dropdown_widget.config(state="disabled")

def write_to_dir(trace_file_var, response_text,radargram_handle,sliders):
    exp_threshold = 500  # ns
    filename = trace_file_var.get().strip()
    file_path = os.path.join("runs", filename)

    if not radargram_handle.get_data(file_path,sliders):
        return
    radargram_handle.extract_relevant_data()
    radargram_handle.compute_crosscorrelations(sliders)
    if not radargram_handle.calculate_axes(sliders):
        response_text.insert(tk.END, "Could not calculate data and write to file, see above error:\n")
        return
    data = radargram_handle.raw_cross_corr_pos
    response_text.insert(tk.END,f"{data}\n")

    sampling_freq_in_MHz = int(radargram_handle.get_quantity("runs") * radargram_handle.get_quantity("clock_freq")/1e6)
    # samples = radargram_handle.get_quantity("raw_cross_corr_pos").shape[1]
    traces = radargram_handle.get_quantity("raw_cross_corr_pos").shape[0]

    exp_threshold_samples = int(exp_threshold*1e-9 * radargram_handle.runs*radargram_handle.clock_freq)
    print(exp_threshold_samples)

    data = data[:, :exp_threshold_samples]
    delay = radargram_handle.get_quantity("delay")
    stacks = radargram_handle.get_quantity("stacks")

    radargram_handle.reset_radargram(eraseplots=False)
    scaled = (data / 1e6).flatten().astype(np.int32)

    base_name = os.path.splitext(filename)[0]
    rd7_path = os.path.join("export", base_name + ".rd7")
    rad_path = os.path.join("export", base_name + ".RAD")

    # Save the binary .rd7
    scaled.tofile(rd7_path)
    response_text.insert(tk.END, f"Saved data to {rd7_path}\n")

    # Create the RAD file
    create_RAD_file(sampling_freq_in_MHz, exp_threshold_samples, traces, delay, stacks, rad_path, response_text)
    response_text.insert(tk.END, f"Saved header to {rad_path}\n")

def create_RAD_file(sampling_freq, samples, traces, delay, stacks, file_path, response_text):
    # Calculate derived parameters
    time_window = round(1000*(1/sampling_freq * samples))
    try:
        with open(file_path, 'w') as f:
            f.write(f"SAMPLES: {samples}\n")
            f.write(f"FREQUENCY: {sampling_freq}\n")
            f.write(f"FREQUENCY STEPS: 1\n")
            f.write(f"SIGNAL POSITION: 0\n")
            f.write(f"RAW SIGNAL POSITION: 0\n")
            f.write(f"DISTANCE FLAG: 0\n")
            f.write(f"TIME FLAG: 1\n")
            f.write(f"PROGRAM FLAG: 0\n")
            f.write(f"EXTERNAL FLAG: 0\n")
            f.write(f"TIME INTERVAL: {delay}\n")
            f.write(f"DISTANCE INTERVAL: 0.049857549369335175\n")
            f.write(f"OPERATOR:\n")
            f.write(f"CUSTOMER:\n")
            f.write(f"SITE:\n")
            f.write(f"ANTENNAS: 500 Mhz shielded\n")
            f.write(f"ANTENNA ORIENTATION: NOT VALID FIELD\n")
            f.write(f"ANTENNA SEPARATION: 0.45\n")
            f.write(f"COMMENT: ''\n")
            f.write(f"TIMEWINDOW: {time_window}\n")
            f.write(f"STACKS: {stacks}\n")
            f.write(f"STACK EXPONENT: 0\n")
            f.write(f"STACKING TIME: 1638.4000000000001\n")  # Placeholder
            f.write(f"LAST TRACE: {traces-1}\n")
            f.write(f"STOP POSITION: 0\n")
            f.write(f"SYSTEM CALIBRATION: 0.00019531250000000001\n")
            f.write(f"START POSITION: 0\n")
            f.write(f"SHORT FLAG: 1\n")
            f.write(f"INTERMEDIATE FLAG: 0\n")
            f.write(f"LONG FLAG: 0\n")
            f.write(f"PREPROCESSING: 0\n")
            f.write(f"HIGH: 0\n")
            f.write(f"LOW: 0\n")
            f.write(f"FIXED INCREMENT: 0\n")
            f.write(f"FIXED MOVES UP: 0\n")
            f.write(f"FIXED MOVES DOWN: 1\n")
            f.write(f"FIXED POSITION: 0\n")
            f.write(f"WHEEL CALIBRATION: 421.20001220703125\n")
            f.write(f"POSITIVE DIRECTION: 1\n")
            f.write(f"CHANNELS: 1\n")
            f.write(f"CHANNEL CONFIGURATION: T2:R2\n")
    except Exception as e:
        response_text.insert(tk.END,f"Error writing .RAD file: {e}")
