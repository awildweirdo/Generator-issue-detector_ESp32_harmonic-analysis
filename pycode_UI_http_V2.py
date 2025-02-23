import numpy as np
import tkinter as tk
from tkinter import ttk, scrolledtext, LabelFrame
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import json

# Global variables to store received data
received_voltage = None
received_current = None

# HTTP server handler
class DataHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global received_voltage, received_current
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            # Parse JSON data
            data = json.loads(post_data.decode('utf-8'))
            received_voltage = np.array(data.get("voltage", []))
            received_current = np.array(data.get("current", []))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Data received")
            connection_status_label.config(text="ESP32 Connection: Connected", foreground="green")
        except Exception as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid data format")
            connection_status_label.config(text="ESP32 Connection: Disconnected", foreground="red")
            print(f"Error parsing data: {e}")

def start_http_server():
    server = HTTPServer(('0.0.0.0', 8080), DataHandler)
    print("Starting HTTP server on port 8080...")
    server.serve_forever()


def fetch_data():
    if received_voltage is not None and received_current is not None:
        return received_voltage, received_current
    else:
        connection_status_label.config(text="ESP32 Connection: Disconnected", foreground="red")
        return None, None


def analyze_fft(signal):
    fft_values = np.fft.fft(signal)
    fft_magnitudes = np.abs(fft_values)
    return fft_magnitudes[:len(fft_magnitudes) // 2]


def detect_issues(harmonics, threshold=0.05):
    issues = []
    fundamental = harmonics[1]

    
    total_harmonic_content = np.sum(harmonics[2:]) / fundamental
    if total_harmonic_content > threshold * 5:
        issues.append(("High Harmonic Content", "core saturation or non-linear load characteristics", range(2, len(harmonics)), 'red'))
    
e
    odd_harmonics = [harmonics[i] for i in range(3, len(harmonics), 2)]
    odd_harmonic_content = sum(odd_harmonics) / fundamental
    if odd_harmonic_content > threshold:
        issues.append(("Odd Harmonic Dominance", "magnetic core properties and saturation effects", range(3, len(harmonics), 2), 'blue'))

    even_harmonics = [harmonics[i] for i in range(2, len(harmonics), 2)]
    even_harmonic_content = sum(even_harmonics) / fundamental
    if even_harmonic_content > threshold:
        issues.append(("Even Harmonics", "unbalanced or asymmetrical operation", range(2, len(harmonics), 2), 'green'))
    asymmetry_ratio = abs(odd_harmonic_content - even_harmonic_content)
    if asymmetry_ratio > threshold:
        issues.append(("Asymmetry in Waveforms", "core saturation or unbalanced loads", range(2, len(harmonics)), 'purple'))
    
    if not issues:
        issues.append(("No significant issues detected", "", None, None))

    return issues

def plot_harmonics(canvas, frequencies, voltage_fft, current_fft, voltage_issues, current_issues):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), dpi=100)
    
    # Plot Voltage Harmonics
    ax1.plot(frequencies, voltage_fft, label="Voltage Harmonics")
    ax1.set_title("Voltage Harmonics")
    ax1.set_xlabel("Frequency (Hz)")
    ax1.set_ylabel("Magnitude")
    ax1.grid(True)

    for issue in voltage_issues:
        if issue[2]:  # Check if there are specific indices to highlight
            ax1.scatter(frequencies[list(issue[2])], voltage_fft[list(issue[2])], color=issue[3], label=issue[0])
    
    # Plot Current Harmonics
    ax2.plot(frequencies, current_fft, label="Current Harmonics", color='orange')
    ax2.set_title("Current Harmonics")
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Magnitude")
    ax2.grid(True)
    
   
    for issue in current_issues:
        if issue[2]:  # Check if there are specific indices to highlight
            ax2.scatter(frequencies[list(issue[2])], current_fft[list(issue[2])], color=issue[3], label=issue[0])

    fig.tight_layout()
    canvas.figure = fig
    canvas.draw()


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
    plot_harmonics(canvas, frequencies, voltage_fft, current_fft, voltage_issues, current_issues)


root = tk.Tk()
root.title("Transformer Harmonic Analysis")
root.geometry("900x750")


connection_status_label = ttk.Label(root, text="ESP32 Connection: Unknown", foreground="gray")
connection_status_label.place(relx=1.0, rely=0.0, anchor="ne")

# Frame for analysis controls and issue display
frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky="EW")


analyze_button = ttk.Button(frame, text="Analyze Harmonics", command=analyze_data)
analyze_button.grid(row=0, column=0, pady=5)


issue_frame = ttk.Frame(root, padding="10")
issue_frame.grid(row=1, column=0, sticky="NSEW")

# Scrollable text box for issue display
issue_display = scrolledtext.ScrolledText(issue_frame, width=60, height=15, wrap=tk.WORD, state='disabled')
issue_display.grid(row=0, column=0, sticky="NSEW")

# Frame for harmonics plot
plot_frame = ttk.Frame(root, padding="10")
plot_frame.grid(row=2, column=0, sticky="NSEW")

# Matplotlib canvas for plotting
canvas = FigureCanvasTkAgg(plt.Figure(figsize=(8, 4)), master=plot_frame)
canvas.get_tk_widget().grid(row=0, column=0, sticky="NSEW")

legend_frame = LabelFrame(root, text="Issue Color Codes", padx=10, pady=5)
legend_frame.place(relx=1.0, rely=1.0, anchor="se")
tk.Label(legend_frame, text="High Harmonic Content", fg="red").pack(anchor="w")
tk.Label(legend_frame, text="Odd Harmonic Dominance", fg="blue").pack(anchor="w")
tk.Label(legend_frame, text="Even Harmonics", fg="green").pack(anchor="w")
tk.Label(legend_frame, text="Asymmetry in Waveforms",fg="purple").pack(anchor="w")

#column and row weights
root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)
root.rowconfigure(2, weight=1)
issue_frame.columnconfigure(0, weight=1)
issue_frame.rowconfigure(0, weight=1)
plot_frame.columnconfigure(0, weight=1)
plot_frame.rowconfigure(0, weight=1)

server_thread = threading.Thread(target=start_http_server, daemon=True)
server_thread.start()


root.mainloop()
