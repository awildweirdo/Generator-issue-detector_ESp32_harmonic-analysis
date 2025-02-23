import numpy as np
import tkinter as tk
from tkinter import ttk, scrolledtext, LabelFrame
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# Function to simulate data fetching from ESP32 with more realistic data
def fetch_data():
    try:
        # Simulated time data for 512 samples (1 second at 512 Hz sampling rate)
        time = np.linspace(0, 1, 512, endpoint=False)

        # Simulated Voltage and Current signals with noise and harmonics
        # Fundamental frequency at 50 Hz
        fundamental_frequency = 50
        harmonics = [100, 150, 200, 250, 300]  # Harmonics at higher frequencies
        voltage_data = (
            np.sin(2 * np.pi * fundamental_frequency * time)  # Fundamental frequency component
            + 0.5 * np.sin(2 * np.pi * harmonics[0] * time)  # 2nd harmonic (stronger amplitude)
            + 0.3 * np.sin(2 * np.pi * harmonics[1] * time)  # 3rd harmonic
            + 0.1 * np.sin(2 * np.pi * harmonics[2] * time)  # 4th harmonic
            + 0.05 * np.sin(2 * np.pi * harmonics[3] * time)  # 5th harmonic
            + 0.02 * np.sin(2 * np.pi * harmonics[4] * time)  # 6th harmonic
            + 0.05 * np.random.normal(size=time.shape)  # Adding some noise to simulate real signal
        )

        current_data = (
            np.sin(2 * np.pi * fundamental_frequency * time)  # Fundamental frequency component
            + 0.6 * np.sin(2 * np.pi * harmonics[0] * time)  # 2nd harmonic (stronger amplitude)
            + 0.4 * np.sin(2 * np.pi * harmonics[1] * time)  # 3rd harmonic
            + 0.2 * np.sin(2 * np.pi * harmonics[2] * time)  # 4th harmonic
            + 0.1 * np.sin(2 * np.pi * harmonics[3] * time)  # 5th harmonic
            + 0.05 * np.sin(2 * np.pi * harmonics[4] * time)  # 6th harmonic
            + 0.1 * np.random.normal(size=time.shape)  # Adding noise to current signal
        )

        # Update connection status to "Connected"
        connection_status_label.config(text="ESP32 Connection: Connected", foreground="green")
        return voltage_data, current_data
    except:
        # If there's an error, update connection status to "Disconnected"
        connection_status_label.config(text="ESP32 Connection: Disconnected", foreground="red")
        return None, None

# Perform FFT and calculate harmonic magnitudes
def analyze_fft(signal):
    fft_values = np.fft.fft(signal)
    fft_magnitudes = np.abs(fft_values)
    return fft_magnitudes[:len(fft_magnitudes) // 2]

# Detect issues based on harmonic patterns
def detect_issues(harmonics, threshold=0.05):
    issues = []
    fundamental = harmonics[1]

    # High Harmonic Content in Current
    total_harmonic_content = np.sum(harmonics[2:]) / fundamental
    if total_harmonic_content > threshold * 3:  # Adjust threshold to be more sensitive
        issues.append(("High Harmonic Content", "core saturation or non-linear load characteristics", range(2, len(harmonics)), 'red'))
    
    # Odd Harmonic Dominance
    odd_harmonics = [harmonics[i] for i in range(3, len(harmonics), 2)]
    odd_harmonic_content = sum(odd_harmonics) / fundamental
    if odd_harmonic_content > threshold:
        issues.append(("Odd Harmonic Dominance", "magnetic core properties and saturation effects", range(3, len(harmonics), 2), 'blue'))

    # Even Harmonic Dominance
    even_harmonics = [harmonics[i] for i in range(2, len(harmonics), 2)]
    even_harmonic_content = sum(even_harmonics) / fundamental
    if even_harmonic_content > threshold:
        issues.append(("Even Harmonics", "unbalanced or asymmetrical operation", range(2, len(harmonics), 2), 'green'))

    # Asymmetry in Harmonics (highlight only when difference is significant)
    asymmetry_ratio = abs(odd_harmonic_content - even_harmonic_content)
    if asymmetry_ratio > threshold * 1.5:  # Make this more sensitive, but only trigger if it's more noticeable
        issues.append(("Asymmetry in Waveforms", "core saturation or unbalanced loads", range(2, len(harmonics)), 'purple'))
    
    if not issues:
        issues.append(("No significant issues detected", "", None, None))

    return issues

# Plot harmonics for voltage and current with highlighted issues
def plot_harmonics_and_input(canvas, frequencies, voltage_data, current_data, voltage_fft, current_fft, voltage_issues, current_issues):
    fig, axs = plt.subplots(2, 2, figsize=(12, 8), dpi=100)

    # Plot Time Domain (Input) Voltage Signal
    axs[0, 0].plot(voltage_data, label="Voltage Signal")
    axs[0, 0].set_title("Voltage (Time Domain)")
    axs[0, 0].set_xlabel("Samples")
    axs[0, 0].set_ylabel("Amplitude")
    axs[0, 0].grid(True)
    
    # Plot Time Domain (Input) Current Signal
    axs[0, 1].plot(current_data, label="Current Signal", color='orange')
    axs[0, 1].set_title("Current (Time Domain)")
    axs[0, 1].set_xlabel("Samples")
    axs[0, 1].set_ylabel("Amplitude")
    axs[0, 1].grid(True)

    # Plot Voltage Harmonics (FFT)
    axs[1, 0].plot(frequencies, voltage_fft, label="Voltage Harmonics")
    axs[1, 0].set_title("Voltage Harmonics (Frequency Domain)")
    axs[1, 0].set_xlabel("Frequency (Hz)")
    axs[1, 0].set_ylabel("Magnitude")
    axs[1, 0].grid(True)
    
    # Highlight voltage issues with color coding
    for issue in voltage_issues:
        if issue[2]:  # Check if there are specific indices to highlight
            axs[1, 0].scatter(frequencies[list(issue[2])], voltage_fft[list(issue[2])], color=issue[3], label=issue[0])

    # Plot Current Harmonics (FFT)
    axs[1, 1].plot(frequencies, current_fft, label="Current Harmonics", color='orange')
    axs[1, 1].set_title("Current Harmonics (Frequency Domain)")
    axs[1, 1].set_xlabel("Frequency (Hz)")
    axs[1, 1].set_ylabel("Magnitude")
    axs[1, 1].grid(True)
    
    # Highlight current issues with color coding
    for issue in current_issues:
        if issue[2]:  # Check if there are specific indices to highlight
            axs[1, 1].scatter(frequencies[list(issue[2])], current_fft[list(issue[2])], color=issue[3], label=issue[0])

    fig.tight_layout()
    canvas.figure = fig
    canvas.draw()

# Main function to analyze data and display results
def analyze_data():
    voltage_data, current_data = fetch_data()
    if voltage_data is None or current_data is None:
        issue_display.config(state='normal')
        issue_display.delete(1.0, tk.END)
        issue_display.insert(tk.END, "ESP32 Connection Failed. Please check your connection.\n")
        issue_display.config(state='disabled')
        return

    voltage_fft = analyze_fft(voltage_data)
    current_fft = analyze_fft(current_data)

    # Detect issues
    voltage_issues = detect_issues(voltage_fft)
    current_issues = detect_issues(current_fft)

    # Update UI with detected issues
    issue_display.config(state='normal')
    issue_display.delete(1.0, tk.END)
    issue_display.insert(tk.END, "Voltage Harmonics Analysis:\n")
    for issue in voltage_issues:
        issue_display.insert(tk.END, f"- {issue[0]}: {issue[1]}\n")
    issue_display.insert(tk.END, "\nCurrent Harmonics Analysis:\n")
    for issue in current_issues:
        issue_display.insert(tk.END, f"- {issue[0]}: {issue[1]}\n")
    issue_display.config(state='disabled')

    # Define frequency range and plot harmonics with highlighted issues
    frequencies = np.fft.fftfreq(len(voltage_data), 1 / 512)[:len(voltage_fft)]
    plot_harmonics_and_input(canvas, frequencies, voltage_data, current_data, voltage_fft, current_fft, voltage_issues, current_issues)

# Set up the main UI window
root = tk.Tk()
root.title("Transformer Harmonic Analysis")
root.geometry("1000x800")  # Adjusted window size for 2x2 plot grid

# Connection status display (top right corner)
connection_status_label = ttk.Label(root, text="ESP32 Connection: Unknown", foreground="gray")
connection_status_label.place(relx=1.0, rely=0.05, anchor="ne")

# Issue color code legend at the top
legend_frame = LabelFrame(root, text="Issue Color Codes", padx=10, pady=5)
legend_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)

tk.Label(legend_frame, text="High Harmonic Content", fg="red").pack(anchor="w")
tk.Label(legend_frame, text="Odd Harmonic Dominance", fg="blue").pack(anchor="w")
tk.Label(legend_frame, text="Even Harmonics", fg="green").pack(anchor="w")
tk.Label(legend_frame, text="Asymmetry in Waveforms", fg="purple").pack(anchor="w")

# Frame for the analysis controls and issue display
frame = ttk.Frame(root, padding="10")
frame.grid(row=1, column=0, sticky="ew")

# Button to start analysis
analyze_button = ttk.Button(frame, text="Analyze Harmonics", command=analyze_data)
analyze_button.grid(row=0, column=0, pady=5)

# Frame for issue display
issue_frame = ttk.Frame(root, padding="10")
issue_frame.grid(row=2, column=0, sticky="nsew")

# Scrollable text box to display issues
issue_display = scrolledtext.ScrolledText(issue_frame, width=40, height=15, wrap=tk.WORD, state='disabled')
issue_display.grid(row=0, column=0, sticky="nsew")

# Frame for the harmonics plot
plot_frame = ttk.Frame(root, padding="10")
plot_frame.grid(row=1, column=1, rowspan=2, sticky="nsew")

# Set up the Matplotlib canvas in the plot frame
canvas = FigureCanvasTkAgg(plt.Figure(figsize=(12, 8)), master=plot_frame)
canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

# Configure column and row weights
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=3)  # Give more weight to the plot area
root.rowconfigure(0, weight=0)
root.rowconfigure(1, weight=2)
root.rowconfigure(2, weight=2)

# Start the main loop
root.mainloop()
