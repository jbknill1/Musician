# backend.py
import threading
import time
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
import numpy as np
import pyaudio

RATE = 44100
CHUNK = 4096

app = FastAPI()
clients = set()
clients_lock = threading.Lock()

# thread-safe holder for the latest peak frequency
class PeakHolder:
    def __init__(self):
        self.lock = threading.Lock()
        self.max_freq = 0.0
holder = PeakHolder()

def audio_thread():
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    buf = np.zeros(CHUNK, dtype=np.float32)
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
        # Simple rolling buffer (here we just use the latest chunk)
        fft = np.fft.rfft(samples)
        fft_abs = np.abs(fft)
        freqs = np.fft.rfftfreq(len(samples), 1.0 / RATE)
        peak_idx = int(np.argmax(fft_abs))
        peak = float(freqs[peak_idx])
        with holder.lock:
            holder.max_freq = peak
        # small sleep to yield CPU
        time.sleep(0.01)

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    with clients_lock:
        clients.add(ws)
    try:
        while True:
            # send latest peak at ~20 Hz
            await asyncio.sleep(0.05)
            with holder.lock:
                msg = {"max_freq": round(holder.max_freq, 1)}
            try:
                await ws.send_text(json.dumps(msg))
            except Exception:
                break
    except WebSocketDisconnect:
        pass
    finally:
        with clients_lock:
            clients.discard(ws)

if __name__ == "__main__":
    t = threading.Thread(target=audio_thread, daemon=True)
    t.start()
    uvicorn.run(app, host="0.0.0.0", port=8000)