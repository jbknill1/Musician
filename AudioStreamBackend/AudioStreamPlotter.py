import pyaudio
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
import sys
from AudioBuffer import AudioBuffer

# --- Audio Constants ---
CHUNK = 4096   # number of samples per buffer
FORMAT = pyaudio.paInt16  # audio format
CHANNELS = 1  # mono sound
RATE = 44100   # sample rate (Hz)

class AudioStreamPlotter:
    def __init__(self):
        # Setup PyQtGraph
        self.AudioBuffer = AudioBuffer(RATE) # Buffer to hold the latest audio data for plotting
        self.app = QtWidgets.QApplication(sys.argv)
        self.win = pg.GraphicsLayoutWidget(show=True, title="Real-Time Audio Waveform Plot")
        self.win.resize(1000, 600)
        self.plot = self.win.addPlot(title="Microphone Input Waveform")
        self.plot.setYRange(0, 2**20) # 16-bit audio range
        self.curve = self.plot.plot(pen='c') # cyan color line

        # Guitar standard-tuning open-string frequencies (Hz)
        self.string_freqs = [82.41, 110.00, 146.83, 196.00, 246.94, 329.63]
        # Create a visible vertical line for each string
        self.string_lines = []
        for f in self.string_freqs:
            line = pg.InfiniteLine(pos=f, angle=90, pen=pg.mkPen('r', width=1, style=QtCore.Qt.DashLine))
            self.plot.addItem(line)
            self.string_lines.append(line)

        # Dynamic vertical line for the detected peak frequency
        self.max_freq = 0.0
        self.max_line = pg.InfiniteLine(pos=self.max_freq, angle=90, pen=pg.mkPen('y', width=2))
        self.plot.addItem(self.max_line)

        # Setup PyAudio
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=FORMAT,
                                  channels=CHANNELS,
                                  rate=RATE,
                                  input=True,
                                  output=False, 
                                  frames_per_buffer=CHUNK,
                                  stream_callback=self.audio_callback)
        
        # Data buffer
        self.data = np.zeros(CHUNK-50, dtype=np.float32)
        # Hold the most recent detected peak frequency (Hz)
        self.max_freq = 0.0

        # Setup update timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50) # Update rate in ms

    def audio_callback(self, in_data, frame_count, time_info, status):
        """
        Callback function for PyAudio stream. Runs in a separate thread.
        """
        # Convert bytes to numpy array
        audio_data = np.frombuffer(in_data, dtype=np.int16)
        # Perform real-time processing here

        self.AudioBuffer.add_data(audio_data);

        # Apply FFT
        buffer = self.AudioBuffer.get_buffer()
        fft_data = np.fft.rfft(buffer)
        fft_abs = np.abs(fft_data)
        # Frequency values for each FFT bin
        freqs = np.fft.rfftfreq(len(buffer), 1.0/RATE)

        # Plotting region in bin indices (same semantic slice as before)
        self.start_idx = 50
        self.end_idx = 500
        # Guard against buffers smaller than expected
        self.end_idx = min(self.end_idx, len(fft_abs))
        if self.end_idx > self.start_idx:
            region = fft_abs[self.start_idx:self.end_idx]
            self.data = region
            # store frequency axis for the plotted region
            self.freqs = freqs
            # Determine peak frequency in the plotted region
            rel_idx = int(np.argmax(region))
            peak_idx = self.start_idx + rel_idx
            self.max_freq = float(freqs[peak_idx])
        else:
            self.data = np.zeros(max(0, self.end_idx-self.start_idx), dtype=np.float32)
            self.freqs = freqs
            self.max_freq = 0.0

        # print(f"Processed a chunk of {len(audio_data)} frames")

        return (in_data, pyaudio.paContinue)

    def update(self):
        """
        Update the PyQtGraph plot with new data from the audio buffer.
        """
        # Plot with a proper frequency x-axis if available
        try:
            x = self.freqs[self.start_idx:self.end_idx]
            self.curve.setData(x=x, y=self.data)
            # Keep x range around the plotted region
            self.plot.setXRange(x[0], x[-1], padding=0.02)
        except Exception:
            # Fallback to plotting y-values only
            self.curve.setData(self.data)

        # Update the dynamic peak line position and title
        try:
            self.max_line.setPos(self.max_freq)
        except Exception:
            pass
        self.plot.setTitle(f"Microphone Input Waveform — Max freq: {self.max_freq:.1f} Hz")

    def start(self):
        """
        Start the application event loop.
        """
        self.stream.start_stream()
        sys.exit(self.app.exec()) # Use app.exec() for PyQt6

    def close(self):
        """
        Clean up resources when done.
        """
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

if __name__ == '__main__':
    plotter = AudioStreamPlotter()
    try:
        plotter.start()
    except KeyboardInterrupt:
        pass
    finally:
        plotter.close()
