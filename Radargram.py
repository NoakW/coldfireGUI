import tkinter

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import correlate, find_peaks, resample, butter, filtfilt, welch
import scipy.ndimage
from scipy.constants import c
from matplotlib import gridspec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import os


class Subfigures:
    def __init__(self, frame, response_text, tk):
        self.frame = frame
        self.response_text = response_text
        self.tk = tk

        self.fig = plt.figure(figsize=(6, 12), dpi=100)  # Adjust figure size for better spacing
        self.gs = gridspec.GridSpec(3, 1, height_ratios=[1, 1, 1])  # 3 rows, 1 column

        # Plots layout (stacked vertically)
        self.ax1 = self.fig.add_subplot(self.gs[0, 0])  # Preview (Top)
        self.ax2 = self.fig.add_subplot(self.gs[1, 0])  # Autocorrelation (Middle)
        self.ax3 = self.fig.add_subplot(self.gs[2, 0])  # Trace Data (Bottom)

        # Titles
        self.ax1.set_title("Preview")
        self.ax2.set_title("Autocorrelation")
        self.ax3.set_title("Trace Data")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)


class Radargram:
    def __init__(self, frame, response_text, tk):

        # Initializing frame, response_text, and tk for GUI usage
        self.frame = frame
        self.response_text = response_text
        self.tk = tk

        # Initializing other instance variables
        self.clock_freq = 160e6  # Default value for clock frequency
        self.traces = None  # Initialized as None; will be populated later
        self.runs = None
        self.order = None
        self.reps = None
        self.lags = None
        self.time_axis = None
        self.full_mls_signal = None
        self.resampled_mls_signal = None
        self.offset = None
        self.name = None
        self.delay = None
        self.samples = None
        self.stacks = None

        self.trace_offset = None
        self.cross_corr_pos = None
        self.raw_cross_corr_pos = None
        self.positive_lags_idx = None
        self.time_axis_pos = None
        self.distance_axis_pos = None
        self.reversed_time_axis = None
        self.reversed_time_axis_pos = None
        # Initialize plot-related variables
        self.fig = plt.figure(figsize=(7, 4), dpi=100)
        self.bscan_gs = gridspec.GridSpec(2, 1, height_ratios=[1, 2])

        # Subplots for cross-correlation traces and B-scan
        self.bscan_ax1 = self.fig.add_subplot(self.bscan_gs[0, 0])
        self.bscan_ax2 = self.fig.add_subplot(self.bscan_gs[1, 0])

        self.bscan_ax1.set_title("Cross-correlation Traces")
        self.bscan_ax2.set_title("B-Scan Cross-correlation")

        # Adjust subplot layout
        self.fig.subplots_adjust(right=0.85)

        # Setup canvas for embedding matplotlib figure in Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Toolbar for navigation
        toolbar = NavigationToolbar2Tk(self.canvas, self.frame)
        toolbar.update()

        # Initialize placeholders for cross-correlation and time-axis data
        self.cross_correlation = None
        self.lags_pos = None
        self.time_axis_pos = None

    def get_data(self, data_file,sliders):
        """Extracts relevant data from the provided data file."""
        if not os.path.exists(data_file) or os.stat(data_file).st_size == 0:
            self.response_text.insert(self.tk.END, "Error: The input file is empty/ doesn't exist.\n")
            return False  # Early return if file doesn't exist or is empty
        try:
            # Load data from the file
            full_data = np.genfromtxt(data_file, delimiter=',')

            # Extract metadata and traces (assuming file format has specific structure)
            self.order = full_data[-1, 0]  # Extract order (last row, first column)
            self.reps = full_data[-1, 1]  # Extract reps (last row, second column)
            self.runs = full_data[-1, 2]  # Extract runs (last row, third column)
            self.stacks = full_data[-1, 3]
            self.delay = full_data[-1, 4]
            lo = None

            try:
                val = sliders["NumTraces"].get().strip().lower()
                max_rows = full_data.shape[0]

                if ":" in val:
                    lo_str, hi_str = val.split(":")
                    lo = int(lo_str.strip())
                    hi = int(hi_str.strip())

                    if lo < 0:
                        lo = 0
                    if hi > max_rows:
                        hi = max_rows
                    if lo >= hi:
                        raise ValueError(f"Invalid lo:hi range{lo}:{hi}")


                    self.traces = full_data[lo:hi, 11:]

                    #self.traces = full_data[lo:hi,11:]
                    # Update entry with the actual values used
                    sliders["NumTraces"].delete(0, self.tk.END)
                    sliders["NumTraces"].insert(0, f"{lo}:{hi}")

                else:
                    numTraces = int(val)
                    if numTraces <= 0 or numTraces > max_rows:
                        raise ValueError(f"Trace {numTraces} out of bounds")
                    self.traces = full_data[:numTraces, 11:]

                    # Reflect actual used range
                    sliders["NumTraces"].delete(0, self.tk.END)
                    sliders["NumTraces"].insert(0, f"0:{numTraces}")

            except Exception as e:
                self.response_text.insert(self.tk.END, f"Error: {e}, using all traces\n")
                sliders["NumTraces"].delete(0, self.tk.END)
                sliders["NumTraces"].insert(0, f"0:{max_rows}")
                self.traces = full_data[:, 11:]

            self.trace_offset = lo if lo else 0
            self.response_text.insert(self.tk.END,f"Trace offset {self.trace_offset}\n")
            # Load m-sequence signal and repeat according to 'reps'
            mls_filename = f"Mseqs/my_mls{int(self.order)}_1p_1f.txt"
            mls_signal = np.loadtxt(mls_filename, skiprows=1)[:, 1]
            self.full_mls_signal = np.tile(mls_signal, int(self.reps))
            #self.full_mls_signal[self.full_mls_signal == -1] = 0
            self.name = data_file
            self.samples = self.traces.shape[1]
            self.response_text.insert(self.tk.END,f"Samples {self.samples}\n")
            return True

        except ValueError as e:
            self.response_text.insert(self.tk.END, f"Error: No trace data found.\n({e})\n")
            return False
        except IndexError as e:
            self.response_text.insert(self.tk.END, f"Error: Data format issue.\n({e})\n")
            return False
        except Exception as e:
            self.response_text.insert(self.tk.END, f"Unexpected error: {e}\n")
            return False

    def extract_relevant_data(self):
        """Extracts relevant trace data for cross-correlation computation and estimates signal delay offset."""
        # Initialize relevant data array
        mls_freq = self.clock_freq * 2
        upsample_factor = (self.clock_freq * self.runs)/mls_freq
        self.resampled_mls_signal = resample(self.full_mls_signal, int(np.float64(len(self.full_mls_signal))*upsample_factor))

        mls_len = len(self.resampled_mls_signal)

        # Pad full_mls_signal if needed
        if mls_len < self.samples:
            pad_width = self.samples - mls_len
            self.resampled_mls_signal = np.pad(self.resampled_mls_signal, (0, pad_width), mode='constant')

        baseline = np.abs(np.mean(self.traces[:, 0]))  # First data point from each trace
        idxs = np.zeros(self.traces.shape[0])
        for trace in range(self.traces.shape[0]):
            for idx in range(self.traces.shape[1]):
                if np.abs(self.traces[trace, idx]) > 2 * baseline:
                    idxs[trace] = idx  # Store the index where threshold is exceeded
                    break
        self.offset = (np.mean(idxs) + 3) / (self.clock_freq * self.runs)

    def compute_crosscorrelations(self,sliders):
        """Computes cross-correlation for each trace."""
        num_traces = self.traces.shape[0]
        self.cross_correlation = np.zeros(
            (num_traces, self.traces.shape[1] + len(self.resampled_mls_signal) - 1))
        for i in range(num_traces):
            corr = correlate(self.traces[i, :], self.resampled_mls_signal, mode='full', method='fft')
            if sliders["Normalize"].get():
                corr /= np.sqrt(np.sum(self.traces[i, :] ** 2) * np.sum(self.resampled_mls_signal ** 2))  # Normalize
            self.cross_correlation[i, :] = corr

    def calculate_axes(self, sliders):
        self.lags = np.arange(-((self.cross_correlation.shape[1] - 1) / 2),
                              (self.cross_correlation.shape[1] - 1) / 2 + 1)
        self.time_axis = self.lags / (self.clock_freq * self.runs) - self.offset
        try:
            threshold = int(sliders["Threshold"].get())
        except ValueError as e:
            self.response_text.insert(self.tk.END, f"Error: (positive) numeric plot threshold required:\n{e}\n")
            return False
        threshold_limit_ns = threshold * 1e-9 + self.offset
        threshold_limit_lags = threshold_limit_ns * self.clock_freq * self.runs
        all_positive_lags_idx = np.where(self.lags >= 0)[0]

        if threshold_limit_lags > self.lags[all_positive_lags_idx[-1]]:
            positive_lags_idx = all_positive_lags_idx
            max_time_ns = int((self.lags[positive_lags_idx[-1]] / (self.clock_freq * self.runs) - self.offset) * 1e9)
            sliders["Threshold"].delete(0, self.tk.END)  # Clear the entry
            sliders["Threshold"].insert(0, f"{max_time_ns}")
        else:
            positive_lags_idx = np.where((self.lags >= 0) & (self.lags <= threshold_limit_lags))[0]
        # Store results
        self.positive_lags_idx = positive_lags_idx
        self.cross_corr_pos = self.cross_correlation[:, positive_lags_idx]
        self.raw_cross_corr_pos = self.cross_correlation[:, positive_lags_idx[0]:]
        self.time_axis_pos = self.time_axis[positive_lags_idx]
        self.reversed_time_axis_pos = self.time_axis_pos[::-1]
        self.lags_pos = self.lags[positive_lags_idx]
        try:
            e_r = float(sliders["e_r"].get())
            if e_r < 1:
                raise ValueError
            self.distance_axis_pos = self.reversed_time_axis_pos * c / np.sqrt(e_r)
        except ValueError:
            self.response_text.insert(self.tk.END, f"Error: Invalid value of εᵣ\n")
            return False
        return True

    def remove_mean(self, sliders):
        window_fraction = sliders["WindowSize"].get()
        num_traces = self.cross_corr_pos.shape[0]  # Number of data points per trace
        window_size = int(window_fraction * num_traces)

        # Ensure window size is at least 1
        if window_size <= 0:
            window_size = 1

        self.response_text.insert(self.tk.END, f'Removing mean with window size {window_size}...\n')

        # If window size is 1, calculate the overall mean trace
        if window_fraction == 1:
            mean_trace = np.mean(self.cross_corr_pos, axis=0, keepdims=True)  # Mean across all traces
            self.cross_corr_pos -= mean_trace  # Subtract the mean trace from each trace
        else:
            for i in range(self.cross_corr_pos.shape[0]):
                # Calculate the start and end indices for the moving average window
                start_idx = i
                end_idx = min(i + window_size, self.cross_corr_pos.shape[0])  # Don't go out of bounds
                # If we're near the end of the array, use the last indices repeatedly

                neighbors = self.cross_corr_pos[start_idx:end_idx]

                # Calculate the mean trace of the neighbors
                moving_avg = np.mean(neighbors, axis=0)

                # Subtract the moving average from the current trace
                self.cross_corr_pos[i] -= moving_avg

    def apply_bandpass(self, sliders):
        low = float(sliders["LowBand"].get()) * 1e6
        high = float(sliders["HighBand"].get()) * 1e6

        # Check if frequencies are within valid range
        if low <= 0 or high <= 0 or low >= high:
            self.response_text.insert(
                self.tk.END,
                f"Band pass not applied\nEnsure: 0 < Low < High < Nyquist ({nyquist:.2f} Hz)\n"
            )
        else:

            b, a = butter(N=4, Wn=[low, high], btype='bandpass', output='ba',fs=self.clock_freq*self.runs)
            filtered = filtfilt(b, a, self.cross_corr_pos, axis=1)
            self.cross_corr_pos = filtered

            self.response_text.insert(
                self.tk.END,
                f"Band-pass filter applied: Low = {low / 1e6:.0f} MHz, High = {high / 1e6:.0f} MHz\n"
            )

    def apply_ramp(self, sliders):
        if sliders["RampType"].get() == "Linear":
            self.response_text.insert(self.tk.END, f'{sliders["RampType"].get()} ramp enabled\n')
            ramp = self.time_axis_pos  # / np.max(self.time_axis_pos)  # shape: (n_time,)
            self.cross_corr_pos *= ramp[np.newaxis, :]
        elif sliders["RampType"].get() == "Exponential":
            self.response_text.insert(self.tk.END, f'{sliders["RampType"].get()} ramp enabled\n')
            ramp = np.exp(2.5 * self.time_axis_pos / np.max(self.time_axis_pos))
            self.cross_corr_pos *= ramp[np.newaxis, :]
        elif sliders["RampType"].get() == "Rsquared":
            self.response_text.insert(self.tk.END, f'{sliders["RampType"].get()} gain compensation enabled (1/r²)\n')
            ramp = self.time_axis_pos ** 2
            self.cross_corr_pos *= ramp[np.newaxis, :]

    def draw_traces(self,sliders):
        self.fig.clear()

        # Recreate the axes after clearing
        self.bscan_gs = gridspec.GridSpec(2, 1, height_ratios=[1, 2])
        self.bscan_ax1 = self.fig.add_subplot(self.bscan_gs[0, 0])
        # Reconfigure the axes with the correct titles, labels, and grid
        self.bscan_ax1.set_title("Cross-correlation Traces (Raw, Offset)")
        self.bscan_ax1.set_xlabel("Time (ns)")
        self.bscan_ax1.set_ylabel("Correlation")
        self.bscan_ax1.grid(True)

        # Plot top panel
        num_lines = self.cross_corr_pos.shape[0]
        step = max(1, round(num_lines / 20))  # Always plot at least every line if < 20

        colors = plt.cm.viridis(np.linspace(0, 1, num_lines))
        if sliders["Normalize"].get():
            for i in range(0, num_lines, step):
                self.bscan_ax1.plot(self.time_axis_pos * 1e9, self.cross_corr_pos[i, :] +
                                    (i - 1) * 10 / num_lines, color=colors[i])
        else:
            for i in range(0, num_lines, step):
                self.bscan_ax1.plot(self.time_axis_pos * 1e9, self.cross_corr_pos[i, :] +
                                    np.max(self.cross_corr_pos)*(i - 1) * 10 / num_lines, color=colors[i])

    def compute_snr_per_trace(self, exclusion_width=10):
        snrs = []

        for trace in self.cross_corr_pos:
            trace = np.abs(trace)
            peak_idx = np.argmax(trace)
            peak_value = trace[peak_idx]

            # Exclude a window around the peak to estimate noise
            noise_region = np.concatenate((
                trace[:max(0, peak_idx - exclusion_width)],
                trace[min(len(trace), peak_idx + exclusion_width + 1):]
            ))

            noise_level = np.std(noise_region)
            snr = peak_value / noise_level if noise_level > 0 else np.inf
            snrs.append(snr)

        self.response_text.insert(self.tk.END,f"Mean SNRs: {np.mean(snrs)}\n")
        self.response_text.insert(self.tk.END,f"Max SNR: {np.max(snrs)}\n")

    def draw_radargram(self, sliders):
        self.bscan_ax2 = self.fig.add_subplot(self.bscan_gs[1, 0])
        self.bscan_ax2.set_title("B-Scan Cross-correlation")
        self.bscan_ax2.set_xlabel("Trace Number")
        self.bscan_ax2.set_ylabel("Time (ns)")

        contrast = sliders["Contrast"].get()
        data = self.cross_corr_pos.T

        abs_max = np.max(np.abs(data))
        vmax = abs_max * (1 - contrast)
        vmin = -vmax
        self.bscan_ax2.imshow(
            data, aspect='auto', cmap='binary', extent=[self.trace_offset, self.cross_correlation.shape[0]+self.trace_offset,
                                                        self.distance_axis_pos[0] / (c / np.sqrt(np.float64(sliders["e_r"].get()))) * 1e9,
                                                        self.distance_axis_pos[-1] / (c / np.sqrt(np.float64(sliders["e_r"].get()))) * 1e9],
            vmin=vmin, vmax=vmax)

        ax3 = self.bscan_ax2.twinx()
        ax3.set_ylabel("Distance (m)")
        ax3.set_ylim(self.distance_axis_pos[0], self.distance_axis_pos[-1])
        self.canvas.draw()

    def layer_plotinfo(self, sliders):
        """Finds and plots up to N peaks in the cross-correlation data."""
        num_peaks = round(float(sliders["NumPeaks"].get()))
        num_traces = self.cross_corr_pos.shape[0]
        peaks = {rank: {"x": [], "y": []} for rank in range(num_peaks)}

        # Array to store peak times: shape (num_peaks, num_traces)
        peak_times_ns = np.full((num_peaks, num_traces), np.nan)

        # Iterate through each trace
        for trace_idx in range(num_traces):
            peak_indices, _ = find_peaks(self.cross_corr_pos[trace_idx, :])
            if len(peak_indices) == 0:
                continue

            # Sort by peak magnitude (descending)
            peak_values = self.cross_corr_pos[trace_idx, peak_indices]
            sorted_indices = np.argsort(peak_values)[::-1]

            for rank, idx in enumerate(sorted_indices[:num_peaks]):
                peak_idx = peak_indices[idx]
                peak_lag = self.lags_pos[peak_idx]
                time_to_peak = peak_lag / (self.clock_freq * self.runs)
                time_ns = (time_to_peak - self.offset) * 1e9

                peaks[rank]["x"].append(trace_idx + self.trace_offset)
                peaks[rank]["y"].append(time_ns)
                peak_times_ns[rank, trace_idx] = time_ns

        # Plot each rank
        # colors = ['red', 'blue', 'green', 'purple', 'orange','brown','indigo']
        # for rank, data in peaks.items():
        #    if data["x"]:  # Only plot if there are values
        #        label = f"{rank + 1}th Largest Peak" if rank > 0 else "Largest Peak"
        #        self.bscan_ax2.scatter(data["x"], data["y"],
        #                               color=colors[rank % len(colors)],
        #                               marker='o', s=3,
        #                               label=label)

        # Initialize the peak_flags matrix as before
        peak_flags = np.zeros_like(peak_times_ns, dtype=bool)
        for trace in range(num_traces):
            for peak in range(num_peaks):
                if not np.isnan(peak_times_ns[peak, trace]):
                    close_count = 0
                    for future_trace in range(trace + 1, min(trace + 1 + sliders["PatternLength"].get(), num_traces)):
                        found_close_peak = False
                        for future_peak in range(num_peaks):
                            if not np.isnan(peak_times_ns[future_peak, future_trace]):
                                time_diff = abs(peak_times_ns[peak, trace] - peak_times_ns[future_peak, future_trace])
                                if time_diff < sliders["Closeness"].get():
                                    found_close_peak = True
                                    break  # Exit loop once we find a close peak

                        if found_close_peak:
                            close_count += 1

                    if close_count >= int(sliders["PatternLength"].get() * sliders["Aggressiveness"].get()):
                        for future_trace in range(trace + 1,
                                                  min(trace + 1 + sliders["PatternLength"].get(), num_traces)):
                            for future_peak in range(num_peaks):
                                if not np.isnan(peak_times_ns[future_peak, future_trace]):
                                    time_diff = abs(
                                        peak_times_ns[peak, trace] - peak_times_ns[future_peak, future_trace])
                                    if time_diff < sliders["Closeness"].get():
                                        peak_flags[future_peak, future_trace] = True

        highlighted_peak_times = peak_flags * peak_times_ns
        non_zero_indices = np.where(highlighted_peak_times > 0)

        x_vals = non_zero_indices[1]  # Trace indices
        y_vals = highlighted_peak_times[non_zero_indices]  # Corresponding peak times
        self.bscan_ax2.scatter(x_vals+self.trace_offset, y_vals, color='magenta', marker='o', s=10)
        self.canvas.draw()

    def reset_radargram(self, eraseplots):
        """Reset the radargram plot and clear stored data."""

        self.cross_corr_pos = np.zeros_like(self.cross_corr_pos)  # or reset to any other initial state
        self.time_axis_pos = None
        self.reversed_time_axis_pos = None
        self.lags_pos = None
        self.raw_cross_corr_pos = None
        self.distance_axis_pos = None
        self.name = None

        if eraseplots:
            self.fig.clear()  # Clear the entire figure
            self.bscan_gs = gridspec.GridSpec(2, 1, height_ratios=[1, 2])
            self.bscan_ax1 = self.fig.add_subplot(self.bscan_gs[0, 0])
            self.bscan_ax2 = self.fig.add_subplot(self.bscan_gs[1, 0])

            # Reconfigure your axes (titles, labels, etc.)
            self.bscan_ax1.set_title("Cross-correlation Traces")
            self.bscan_ax2.set_title("B-Scan Cross-correlation")

            self.canvas.draw()

    def draw_Freq(self, sliders):
        self.bscan_ax2 = self.fig.add_subplot(self.bscan_gs[1, 0])
        self.bscan_ax2.clear()
        self.bscan_ax2.set_title("Cross-correlation Frequency Content (Mean)")
        self.bscan_ax2.set_xlabel("Frequency (MHz)")
        self.bscan_ax2.set_ylabel("Magnitude (dB)")

        self.response_text.insert(self.tk.END, "Drawing frequency content...\n")

        fs = self.clock_freq * self.runs
        n = self.cross_correlation.shape[1]

        # Always define freqs for plotting lines later
        freqs = np.fft.rfftfreq(n, d=1 / fs)

        if sliders["RESP"].get():
            cross_correlations = []

            for i, corr in enumerate(self.cross_correlation):
                corr /= np.sqrt(np.sum(self.traces[i, :] ** 2) * np.sum(self.full_mls_signal ** 2))
                cross_correlations.append(corr)

            magnitudes = []
            for corr in cross_correlations:
                fft_vals = np.fft.rfft(corr)
                mag = np.abs(fft_vals)
                magnitudes.append(mag)

            mean_magnitude = np.mean(magnitudes, axis=0)
            magnitude_db = 20 * np.log10(mean_magnitude + 1e-12)

            self.bscan_ax2.plot(freqs[1:] / 1e6, magnitude_db[1:], label="Ground response", color='b')

        if sliders["TRACE"].get():
            traces = []

            n_t = self.traces.shape[1]

            # Always define freqs for plotting lines later
            freqs_t = np.fft.rfftfreq(n_t, d=1 / fs)

            for i, trace in enumerate(self.traces):
                trace /= np.sqrt(np.sum(self.traces[i, :] ** 2))
                traces.append(trace)

            magnitudes = []
            for trace in traces:
                fft_vals = np.fft.rfft(trace)
                mag = np.abs(fft_vals)
                magnitudes.append(mag)

            mean_magnitude = np.mean(magnitudes, axis=0)
            magnitude_db = 20 * np.log10(mean_magnitude + 1e-12)

            self.bscan_ax2.plot(freqs_t[1:] / 1e6, magnitude_db[1:], label="Raw Response", color='g')

        if sliders["STIM"].get():
            mls_freq = self.clock_freq * 2
            upsample_factor = (self.clock_freq * self.runs) / mls_freq
            full_mls_signal = np.interp(
                np.linspace(0, len(self.full_mls_signal), len(self.full_mls_signal) * int(upsample_factor)),
                np.arange(len(self.full_mls_signal)),
                self.full_mls_signal
            )

            autocorr_stimulus = correlate(full_mls_signal, full_mls_signal, mode='full', method='fft')
            autocorr_stimulus /= np.max(np.abs(autocorr_stimulus))

            n_a = autocorr_stimulus.shape[0]
            freqs_a = np.fft.rfftfreq(n_a, d=1 / fs)

            psd_vals = np.fft.rfft(autocorr_stimulus)
            psd_mag = np.abs(psd_vals)
            psd_db = 20 * np.log10(psd_mag + 1e-12)

            self.bscan_ax2.plot(freqs_a[1:] / 1e6, psd_db[1:], label="Stimulus", color='r')

        if sliders["f_c"].get():
            # freqs is now always defined, so this block is safe
            line_freq = 2 * self.clock_freq
            line_pos = line_freq * np.arange(1, int(max(freqs) // line_freq) + 1)
            for line in line_pos:
                self.bscan_ax2.axvline(x=line / 1e6, color='k', linestyle='--')

        self.bscan_ax2.legend(loc="upper right")
        self.bscan_ax2.set_ylim(bottom=-100)
        self.bscan_ax2.grid(True)
        self.canvas.draw()

    def get_quantity(self, field):
        return getattr(self, field)
