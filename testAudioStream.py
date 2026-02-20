import pyaudio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Audio stream parameters
FORMAT = pyaudio.paInt16 # 16-bit resolution
CHANNELS = 1             # Mono audio
RATE = 44100             # Sample rate (Hz)
CHUNK = 44100             # Number of frames per buffer

fig, ax = plt.subplots()
x_data = np.linspace(0, 4200, 4200)
global y_data
y_data = np.zeros(4200)
line, = ax.plot(x_data, y_data, '-')
ax.set_ylim(0, 4200) # Set appropriate limits for frequency magnitude


p = pyaudio.PyAudio()

def update(frame):
    # 1. Acquire new data (replace with actual data source reading)
    # new_data = read_from_source() 
    # For this example, we simulate random data
    global y_data
    new_data = y_data

    # 2. Perform FFT
    # S = np.fft.fft(new_data)
    # S_magnitude = np.abs(S)
    # S_magnitude = S_magnitude[:CHUNK // 2] # Only show relevant half

    # 3. Update the plot line's y-data
    line.set_ydata(new_data) # Use S_magnitude for frequency plot
    return line,

def callback(in_data, frame_count, time_info, status):
    """
    This function is called by the PortAudio stream for each audio chunk.
    in_data: The input audio data as a bytes object.
    frame_count, time_info, status: Additional stream info.
    """
    audio_data = np.frombuffer(in_data, dtype=np.int16)
    # Perform real-time processing here

    # Apply FFT
    fft_data = np.fft.rfft(audio_data)
    fft_abs = np.abs(fft_data)
    # Get frequencies
    freqs = np.fft.rfftfreq(CHUNK, 1.0/RATE)
    
    # Print max frequency component (example)
    print(freqs[np.argmax(fft_abs)])

    print(f"Processed a chunk of {len(audio_data)} frames")
    global y_data
    y_data = fft_abs[:4200] # Only plot up to highest note on piano (4186 Hz)

    # ax.cla()  # Clear the current axes
    # x = np.linspace(0, 4200, 4200);  # Only plot up to Nyquist frequency
    # y = fft_abs[:4200]
    # ax.plot(x, y)


    # fig.canvas.draw()  # Draw the plot
    # fig.canvas.flush_events()  # Flush GUI events
    
    # You can pass the processed data to another output stream if needed
    # return processed_data, pyaudio.paContinue 
    return in_data, pyaudio.paContinue # Pass through the original data (for loopback/monitoring)


ani = FuncAnimation(fig, update, interval=50, blit=True) 
plt.xlabel('Frequency (Hz)')
plt.ylabel('Magnitude')
plt.title('Real-Time Frequency Data')
plt.show()


# Open a non-blocking stream
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                output=False, # Set to True if you want to play the audio back in real-time
                frames_per_buffer=CHUNK,
                stream_callback=callback)

# Start the stream
stream.start_stream()

print("Stream started. Press Ctrl+C to stop.")

# Keep the script running while the stream is active
try:
    while stream.is_active():
        pass
except KeyboardInterrupt:
    pass


# Stop and close the stream and PyAudio instance
stream.stop_stream()
stream.close()
p.terminate()