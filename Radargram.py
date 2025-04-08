import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import correlate, find_peaks, resample
from scipy.constants import c
from matplotlib import gridspec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import os

class Subfigures:
    def __init__(self,frame,response_text,tk):
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
        self.amp_delay = 1.4e-9  # Experimentally Determined
        self.coeff = 2/3
        self.clock_freq = 160e6  # Default value for clock frequency
        self.traces = None  # Initialized as None; will be populated later
        self.runs = None
        self.order = None
        self.reps = None
        self.lags = None
        self.time_axis = None
        self.signal_length_in_samples = None
        self.relevant_data = None
        self.full_mls_signal = None
        self.resampled_mls_signal = None
        self.cable_delay = None

        self.cross_corr_pos = None
        self.time_axis_pos = None
        self.distance_axis_pos = None

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

    def get_data(self, data_file):
        """Extracts relevant data from the provided data file."""
        if not os.path.exists(data_file) or os.stat(data_file).st_size == 0:
            self.response_text.insert(self.tk.END, "Error: The input file is empty or doesn't exist.\n")
            return False  # Early return if file doesn't exist or is empty

        try:
            # Load data from the file
            full_data = np.genfromtxt(data_file, delimiter=',')

            # Extract metadata and traces (assuming file format has specific structure)
            self.order = full_data[-1, 0]  # Extract order (last row, first column)
            self.reps = full_data[-1, 1]  # Extract reps (last row, second column)
            self.runs = full_data[-1, 2]  # Extract runs (last row, third column)
            self.traces = full_data[:, 9:]  # Trace data (excluding metadata)

            # Load m-sequence signal and repeat according to 'reps'
            mls_filename = f"Mseqs/my_mls{int(self.order)}_1p_1f.txt"
            mls_signal = np.loadtxt(mls_filename, skiprows=1)[:, 1]
            self.full_mls_signal = np.tile(mls_signal, int(self.reps))  # Repeat m-sequence signal

            return True  # Data loaded successfully

        except ValueError as e:
            self.response_text.insert(self.tk.END, f"Error: No trace data found.\n({e})\n")
            return False
        except IndexError as e:
            self.response_text.insert(self.tk.END, f"Error: Data format issue.\n({e})\n")
            return False
        except Exception as e:
            self.response_text.insert(self.tk.END, f"Unexpected error: {e}\n")
            return False

    def calculate_signal_length(self):
        """Calculates the total signal length based on order, reps, and clock frequency."""
        signal_length = (2 ** self.order - 1) * self.reps
        virtual_sampling_rate = self.clock_freq * self.runs
        signal_time = 1 / 320e6 * signal_length
        self.signal_length_in_samples = round(signal_time * virtual_sampling_rate)

    def extract_relevant_data(self,start_idx=0):
        """Extracts relevant trace data for cross-correlation computation."""
        self.relevant_data = np.zeros((self.traces.shape[0], self.signal_length_in_samples))
        for i in range(self.traces.shape[0]):
            self.relevant_data[i, :] = self.traces[i, start_idx:start_idx + self.signal_length_in_samples]

    def resample_data(self):
        """Resamples the data to a target length."""
        self.resampled_mls_signal=resample(self.full_mls_signal,self.relevant_data.shape[1])

    def compute_crosscorrelations(self):
        """Computes cross-correlation for each trace."""
        num_traces = self.relevant_data.shape[0]
        self.cross_correlation = np.zeros((num_traces, self.relevant_data.shape[1] + len(self.resampled_mls_signal) - 1))
        for i in range(num_traces):
            corr = correlate(self.relevant_data[i, :], self.resampled_mls_signal, mode='full', method='fft')
            corr /= np.sqrt(np.sum(self.relevant_data[i, :] ** 2) * np.sum(self.resampled_mls_signal ** 2))  # Normalize
            self.cross_correlation[i, :] = corr

    def calculate_time_axis(self):
        self.lags = np.arange(-((self.cross_correlation.shape[1] - 1) / 2), (self.cross_correlation.shape[1] - 1) / 2 + 1)
        self.time_axis = self.lags / (self.clock_freq * self.runs)

    def draw_plots(self, sliders):
        """Draws the plots based on the cross-correlation data."""

        try:
            self.cable_delay = np.double(sliders["CableLen"].get()) / (self.coeff * c) - self.amp_delay
            self.response_text.insert(self.tk.END, f"Cable delay: {self.cable_delay}\n")
        except ValueError as e:
            self.response_text.insert(self.tk.END, f"Error: (positive) numeric cable length required:\n{e}\n")

        try:
            threshold_limit = int(sliders["Threshold"].get())/100 * (self.cross_correlation.shape[1] / 2)
            positive_lags_idx = np.where((self.lags >= 0) & (self.lags <= threshold_limit))[0]
        except ValueError as e:
            self.response_text.insert(self.tk.END, f"Error: (positive) numeric plot threshold required:\n{e}\n")
            return

        # Store cross-correlation and other data
        self.cross_corr_pos = self.cross_correlation[:, positive_lags_idx]
        self.time_axis_pos = self.time_axis[positive_lags_idx]
        self.reversed_time_axis_pos = self.time_axis_pos[::-1]
        self.lags_pos = self.lags[positive_lags_idx]

        # Clear the entire figure to ensure a fresh redraw
        self.fig.clear()

        # Recreate the axes after clearing
        self.bscan_gs = gridspec.GridSpec(2, 1, height_ratios=[1, 2])
        self.bscan_ax1 = self.fig.add_subplot(self.bscan_gs[0, 0])
        self.bscan_ax2 = self.fig.add_subplot(self.bscan_gs[1, 0])

        # Reconfigure the axes with the correct titles, labels, and grid
        self.bscan_ax1.set_title("Cross-correlation Traces")
        self.bscan_ax1.set_xlabel("Lag")
        self.bscan_ax1.set_ylabel("Correlation")
        self.bscan_ax1.grid(True)

        self.bscan_ax2.set_title("B-Scan Cross-correlation")
        self.bscan_ax2.set_xlabel("Trace Number")
        self.bscan_ax2.set_ylabel("Time (ns)")

        # Plot top panel
        num_lines = self.cross_corr_pos.shape[0]
        step = max(1, round(num_lines / 20))  # Always plot at least every line if < 20

        colors = plt.cm.viridis(np.linspace(0, 1, num_lines))
        for i in range(0, num_lines, step):
            self.bscan_ax1.plot(self.lags_pos, self.cross_corr_pos[i, :] + (i - 1) * 10/num_lines, color=colors[i])
        # Plot bottom panel
        self.distance_axis_pos = (self.reversed_time_axis_pos - self.cable_delay) * c
        self.bscan_ax2.imshow(
            self.cross_corr_pos.T, aspect='auto', cmap='binary',
            extent=[0, self.cross_correlation.shape[0], self.distance_axis_pos[0] / c * 1e9,
                    self.distance_axis_pos[-1] / c * 1e9]
        )

        # Additional axis configuration for the right y-axis (distance)
        ax3 = self.bscan_ax2.twinx()
        ax3.set_ylabel("Distance (m)")
        ax3.set_ylim(self.distance_axis_pos[0], self.distance_axis_pos[-1])

        # Redraw the canvas
        self.canvas.draw()

    def reset_radargram(self):
        """Reset the radargram plot and clear stored data."""

        self.cross_corr_pos = np.zeros_like(self.cross_corr_pos)  # or reset to any other initial state
        self.time_axis_pos = None
        self.reversed_time_axis_pos = None
        self.lags_pos = None
        self.distance_axis_pos = None
        self.fig.clear()  # Clear the entire figure

        self.bscan_gs = gridspec.GridSpec(2, 1, height_ratios=[1, 2])
        self.bscan_ax1 = self.fig.add_subplot(self.bscan_gs[0, 0])
        self.bscan_ax2 = self.fig.add_subplot(self.bscan_gs[1, 0])

        # Reconfigure your axes (titles, labels, etc.)
        self.bscan_ax1.set_title("Cross-correlation Traces")
        self.bscan_ax2.set_title("B-Scan Cross-correlation")

        self.canvas.draw()

    def layer_plotinfo(self,sliders):
        """Finds and plots relevant phenomena in the crosscorrelation data"""
        times_to_peaks = []
        primary_distances = []

        info_string = ""
        trace_info = {}

        for i in range(self.cross_corr_pos.shape[0]):
            # Find all peaks
            peaks, _ = find_peaks(self.cross_corr_pos[i, :])

            if len(peaks) > 0:
                # Primary peak
                max_peak_idx = peaks[np.argmax(self.cross_corr_pos[i, peaks])]
                max_peak_lag = self.lags_pos[max_peak_idx]
                max_peak_value = self.cross_corr_pos[i, max_peak_idx]

                # Secondary peak(s)
                sec_peaks = [p for p in peaks if self.cross_corr_pos[i, p] >= sliders["PeakAmp"].get() * max_peak_value and p >= max_peak_idx]
                sec_lags = [self.lags_pos[p] for p in sec_peaks]

                # Store peak information
                trace_info[i] = {
                    "primary_peak_lag": max_peak_lag,
                    "secondary_peak_lags": sec_lags,
                }

        primary_lags = [trace["primary_peak_lag"] for trace in trace_info.values()]
        median_primary = np.median(primary_lags)
        std_primary = np.std(primary_lags)
        # Filter primary peaks that lie "far" away from the rest
        filtered_lags_info = {
            i: trace for i, trace in trace_info.items()
            if abs(trace["primary_peak_lag"] - median_primary) <= 0.25 * std_primary
        }

        valid_primary_lags = [trace["primary_peak_lag"] for trace in filtered_lags_info.values()]
        for lag in valid_primary_lags:
            time_to_peak = lag / (self.clock_freq * self.runs)
            times_to_peaks.append(time_to_peak)
            primary_distances.append((time_to_peak - self.cable_delay) * c)

        self.bscan_ax2.scatter(filtered_lags_info.keys(),
                         primary_distances,
                         color='red', marker='o', s=100,
                         label="Primary Peaks")

        all_sec_distances = []
        for i, trace in trace_info.items():
            sec_lags = trace["secondary_peak_lags"]
            filtered_sec_lags = [
                lag for lag in sec_lags
                if all(abs(lag - primary) > sliders["StdDev"].get() * std_primary for primary in valid_primary_lags)
            ]

            sec_times = [lag / (self.clock_freq * self.runs) for lag in filtered_sec_lags]
            sec_distances = [(time - self.cable_delay) * c for time in sec_times]
            self.bscan_ax2.scatter([i] * len(filtered_sec_lags), sec_distances,
                             color='blue', marker='x', s=80,
                             label="Secondary Peaks" if i == list(trace_info.keys())[0] else None)
            all_sec_distances.extend(sec_distances)
        # Find the max primary distance

        max_primary_distance = np.min(primary_distances)
        info_string += f"Primary peak found at: {max_primary_distance:.2f}\n"


        # Sort all secondary distances
        sorted_sec_distances = sorted(all_sec_distances)

        # Skip the shortest secondary distances until one is greater than the max primary distance
        valid_sec_distance = next((d for d in sorted_sec_distances if d > max_primary_distance), None)

        if valid_sec_distance is not None:
            print(f"Min secondary distance: {valid_sec_distance}")
            info_string += f"Secondary peak found at: {valid_sec_distance:.2f}\n"
        else:
            info_string += "No secondary peaks found\n"
        if valid_sec_distance:
            actual_distance = np.sqrt(((valid_sec_distance - np.min(primary_distances)) / 2) ** 2 - np.float64(sliders["AntennaSpacing"].get()) ** 2)

            print(actual_distance)
            info_string += f"Path difference {(valid_sec_distance - max_primary_distance):.2f}\nActual distance to reflector: {actual_distance:.2f}"
        self.bscan_ax2.legend(loc='lower right')
        self.response_text.insert(self.tk.END,f"{info_string}\n")
        self.canvas.draw()
