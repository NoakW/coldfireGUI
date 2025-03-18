import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import correlate, find_peaks, resample
from scipy.constants import c
# Load MLS signal
class Cable:
    def __init__(self, length, coeff):
        self.length = length  # Cable length in meters
        self.coeff = coeff  # Propagation velocity factor (fraction of c)

    def time_delay(self):
        effective_velocity = self.coeff * c
        return self.length / effective_velocity  # time = distance / speed

def delay_calculator():
    lengths = np.array([0.305,0.35,0.5,0.37])  # Cable lengths in meters
    coeffs = np.array([0.695,2/3,2/3,2/3])  # Corresponding velocity factors
    amp_delay = 1.4e-9
    #print(time_to_peak)
    # Iterate over both lengths and coeffs
    total_cable_delay = sum(Cable(len, coeff).time_delay() for len, coeff in zip(lengths, coeffs))
    total_cable_delay = total_cable_delay+amp_delay
    #print(total_cable_delay)
    # Subtract cable delay from total measured time
    #true_time = time_to_peak - total_cable_delay
    print(f"total_cable_delay: {total_cable_delay}")
    #if true_time < 0:
    #    raise ValueError("Error: Cable delay is longer than the measured time!")
    #print(true_time)
    #total_distance = true_time * c  # Convert time to distance
    return total_cable_delay


def load_mls_signal(filename):
    mls = np.loadtxt(filename, skiprows=1)  # Skip header
    return mls[:, 1]

# Load data
def load_data(filename):

    return np.genfromtxt(filename, delimiter=',')


def extract_traces(full_data):

    order_list = full_data[1::2,0]
    reps_list = full_data[1::2,1]
    runs_list = full_data[1::2,2]

    return order_list, reps_list, runs_list, full_data[1::2, 9:]

def calculate_signal_length(runs,order,reps):
    signal_length = (2 ** order - 1) * reps
    sampling_rate = 160e6 * runs
    signal_time = 1 / (320e6) * signal_length
    return round(signal_time * sampling_rate)


def extract_relevant_data(data, start_idx, signal_length_in_samples):
    new_data = np.zeros((data.shape[0], signal_length_in_samples))

    for i in range(data.shape[0]):
        new_data[i, :] = data[i, start_idx:start_idx + signal_length_in_samples]
    return new_data


# Resample data
def resample_data(data, target_length):
    #new_resampled_data = np.zeros(1, target_length)
    #print("Succes2.5")
    #print(data.shape[:])
    #print(target_length)
    new_resampled_data = resample(data, target_length)
    #print(new_resampled_data.shape[:])
    return new_resampled_data

# Compute crosscorrelations for each trace
def compute_crosscorrelations(data, resampled_mls_signal):
    num_traces = data.shape[0]

    auto_corr = np.zeros((num_traces, data.shape[1] + len(resampled_mls_signal) - 1))

    for i in range(num_traces):
        corr = correlate(data[i, :], resampled_mls_signal, mode='full', method='fft')

        # Normalization by the energy of both signals

        corr /= np.sqrt(np.sum(data[i, :]**2) * np.sum(resampled_mls_signal**2))

        auto_corr[i, :] = corr

    return auto_corr


def bscan_main(bscan_canvas,drawMeanLine,TRACE_FILE, plot_threshold_input):
    info_string: str = ""

    full_data = load_data(f'C:/Users/noakw/PycharmProjects/coldfireGUIreal/{TRACE_FILE}')


    order_list, reps_list, runs_list, data = extract_traces(full_data)
    # Load MLS signal
    mls_signal = load_mls_signal(f"../../Documents/my_mls{int(order_list[-1])}_1p_1f.txt")
    full_mls_signal = np.tile(mls_signal, int(reps_list[-1]))

    signal_length_in_samples = calculate_signal_length(runs_list[-1], order_list[-1],reps_list[-1])
    start_idx = 0

    data = extract_relevant_data(data, start_idx, signal_length_in_samples)

    resampled_mls = resample_data(full_mls_signal, data.shape[1])
    auto_corr = compute_crosscorrelations(data, resampled_mls)
    lags = np.arange(-((auto_corr.shape[1]-1) / 2), (auto_corr.shape[1] -1)/2 + 1)

    # === PLOT INSIDE TKINTER CANVAS ===
    bscan_fig = bscan_canvas.figure  # Get the existing figure from canvas
    bscan_fig.clear()  # Clear the figure before plotting new data
    gs = bscan_fig.add_gridspec(2, 1, height_ratios=[1, 3])  # Define grid layout

    # Create axes
    ax1 = bscan_fig.add_subplot(gs[0, 0])  # Autocorrelation plot
    ax2 = bscan_fig.add_subplot(gs[1, 0])  # B-scan image

    # === PLOT AUTOCORRELATIONS ===
    colors = plt.cm.viridis(np.linspace(0, 1, auto_corr.shape[0]))
    for i in range(auto_corr.shape[0]):
        ax1.plot(lags, auto_corr[i, :] + (i - 1) * 0.5 * np.max(auto_corr[i, :]), color=colors[i])

    ax1.set_title("Autocorrelation Traces")
    ax1.set_xlabel("Lag")
    ax1.set_ylabel("Correlation")
    ax1.grid(True)
    sampling_rate = 160e6
    cable_delay = delay_calculator()
    #total_cable_time_delay = 3.691305e-08 #= lags/(
    total_cable_time_delay = 8.96806537e-09
    plot_threshold = int(plot_threshold_input.get())/100

    time_axis = lags / (sampling_rate*runs_list[-1])
    positive_lags_idx = np.where((lags >= 0) & (lags <= plot_threshold*auto_corr.shape[1]/2))[0]
    auto_corr_pos = auto_corr[:, positive_lags_idx]
    time_axis_pos = time_axis[positive_lags_idx]
    reversed_time_axis_pos = time_axis_pos[::-1]  # Reverse for correct plotting
    lags_pos = lags[positive_lags_idx]
    reversed_lags_pos = lags_pos[::-1]
    # Update B-Scan plot to show only positive time lags
    cax = ax2.imshow(auto_corr_pos.T, aspect='auto', cmap='binary',
               extent=[0, auto_corr.shape[0], reversed_lags_pos[0], reversed_lags_pos[-1]]
    )

    ax2.set_title("B-Scan Autocorrelation")
    ax2.set_xlabel("Trace Number")
    ax2.set_ylabel("Delay (ns)")

    # Compute distance axis correctly for positive time lags
    c = 2.998e8  # Speed of light in m/s

    #distance_axis_pos = reversed_time_axis_pos * c  # Convert time to distance

    distance_axis_pos = (reversed_time_axis_pos - cable_delay)*c

    # Add the colorbar
    #cbar = bscan_fig.colorbar(cax, ax=ax2)
    #cbar.set_label("Amplitude")

    ax3 = ax2.twinx()
    ax3.set_ylabel("Distance (m)")
    ax3.set_ylim(distance_axis_pos[0], distance_axis_pos[-1])

    if drawMeanLine.get() == True:

        trace_info = {}

        for i in range(auto_corr_pos.shape[0]):
            # Find all peaks
            peaks, _ = find_peaks(auto_corr_pos[i, :])

            if len(peaks) > 0:
                # === Primary Peak ===
                max_peak_idx = peaks[np.argmax(auto_corr_pos[i, peaks])]
                max_peak_lag = lags_pos[max_peak_idx]
                max_peak_value = auto_corr_pos[i, max_peak_idx]

                # === Secondary Peaks ===
                sec_peaks = [p for p in peaks if auto_corr_pos[i, p] >= 0.80 * max_peak_value and p >= max_peak_idx]
                sec_lags = [lags_pos[p] for p in sec_peaks]

                # Store trace information
                trace_info[i] = {
                    "primary_peak_lag": max_peak_lag,
                    "secondary_peak_lags": sec_lags,
                }

        # === Filter Primary Peaks Based on Distance Consistency ===
        primary_lags = [trace["primary_peak_lag"] for trace in trace_info.values()]
        median_primary = np.median(primary_lags)
        std_primary = np.std(primary_lags)

        # Filter primary peaks
        filtered_lags_info = {
            i: trace for i, trace in trace_info.items()
            if abs(trace["primary_peak_lag"] - median_primary) <= 0.25 * std_primary
        }

        # Extract valid primary lags after filtering
        valid_primary_lags = [trace["primary_peak_lag"] for trace in filtered_lags_info.values()]

        # === Scatter plot of primary and secondary peaks ===
        times_to_peaks = []
        primary_distances = []

        for lag in valid_primary_lags:
            time_to_peak = lag / (sampling_rate * runs_list[-1])
            times_to_peaks.append(time_to_peak)
            primary_distances.append((time_to_peak - total_cable_time_delay) * c)



        # Plot primary peaks
        ax3.scatter(filtered_lags_info.keys(),
                    primary_distances,
                    color='red', marker='o', s=100,
                    label="Primary Peaks")

        all_sec_distances = []
        # Plot secondary peaks (only those that are NOT the same as filtered primary peaks)
        for i, trace in trace_info.items():
            sec_lags = trace["secondary_peak_lags"]

            # Filter out secondary lags that match filtered primary lags
            filtered_sec_lags = [
                lag for lag in sec_lags
                if all(abs(lag - primary) > 0.5*std_primary for primary in valid_primary_lags)
            ]

            sec_times = [lag / (sampling_rate * runs_list[-1]) for lag in filtered_sec_lags]
            sec_distances = [(time - total_cable_time_delay) * c for time in sec_times]
            #print(sec_distances)
            ax3.scatter([i] * len(filtered_sec_lags), sec_distances,
                        color='blue', marker='x', s=80,
                        label="Secondary Peaks" if i == list(trace_info.keys())[0] else None)
            all_sec_distances.extend(sec_distances)

        # Find the max primary distance
        max_primary_distance = np.max(primary_distances)
        print(f"Min primary distance: {np.min(primary_distances)}")
        info_string += "Primary peak found at: " + str(max_primary_distance) + "\n"

        # Sort all secondary distances
        sorted_sec_distances = sorted(all_sec_distances)

        # Skip the shortest secondary distances until one is greater than the max primary distance
        valid_sec_distance = next(
            (d for d in sorted_sec_distances if d > max_primary_distance),
            None  # Return None if no valid secondary distance is found
        )

        if valid_sec_distance is not None:
            print(f"Min secondary distance: {valid_sec_distance}")
            info_string += "Secondary peak found at: " + str(valid_sec_distance) + "\n"
        else:
            print("No valid secondary distance found.")
        if valid_sec_distance:
            antenna_spacing = 0.6
            actual_distance=np.sqrt ( (  (   valid_sec_distance-np.min(primary_distances)  )/2 )**2 - antenna_spacing**2 )

            print(actual_distance)
            info_string += f"Path difference {valid_sec_distance-max_primary_distance}\nActual distance to reflector: {actual_distance}"
        ax3.legend(loc='lower right')
        #print(trace_info)


    bscan_canvas.draw()
    return info_string
