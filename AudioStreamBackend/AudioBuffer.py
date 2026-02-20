import numpy as np

class AudioBuffer:
    def __init__(self, size):
        self.size = size
        self.buffer = np.zeros(size, dtype=np.float32)
    
    def add_data(self, new_data):
        """
        Add new audio data to the buffer, maintaining a fixed size.
        """
        if len(new_data) >= self.size:
            # If new data exceeds buffer size, keep only the most recent part
            self.buffer = new_data[-self.size:]
        else:
            # Shift existing data and append new data
            self.buffer = np.roll(self.buffer, -len(new_data))
            self.buffer[-len(new_data):] = new_data
    
    def get_buffer(self):
        """
        Return the current contents of the buffer.
        """
        return self.buffer
