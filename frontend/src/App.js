import React, { useEffect, useState } from "react";

const STRING_FREQS = [82.41, 110.0, 146.83, 196.0, 246.94, 329.63];

export default function App() {
  const [freq, setFreq] = useState(0);
  const [status, setStatus] = useState("disconnected");

  useEffect(() => {
    let ws;
    try {
      ws = new WebSocket("ws://localhost:8000/ws");
    } catch (e) {
      setStatus("error");
      return;
    }

    ws.onopen = () => setStatus("connected");
    ws.onclose = () => setStatus("closed");
    ws.onerror = () => setStatus("error");
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data.max_freq !== undefined) setFreq(Number(data.max_freq));
      } catch (e) {
        // ignore
      }
    };

    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) ws.close();
    };
  }, []);

  // find nearest string
  const nearest = STRING_FREQS.reduce((acc, f) => {
    const d = Math.abs(f - freq);
    if (acc === null || d < acc.dist) return { freq: f, dist: d };
    return acc;
  }, null);

  return (
    <div style={{ fontFamily: "sans-serif", padding: 24 }}>
      <h1>Real-time Peak Frequency</h1>
      <div style={{ fontSize: 56, color: "#2a9d8f", marginBottom: 8 }}>
        {freq.toFixed(1)} Hz
      </div>
      <div style={{ marginBottom: 12 }}>WebSocket: {status}</div>
      <div>
        <strong>Nearest string:</strong>{" "}
        {nearest ? `${nearest.freq} Hz (Δ ${nearest.dist.toFixed(1)} Hz)` : "—"}
      </div>
      <div style={{ marginTop: 16 }}>
        <strong>Guitar strings:</strong>
        <ul>
          {STRING_FREQS.map((f) => (
            <li key={f} style={{ color: f === nearest?.freq ? "#e76f51" : "inherit" }}>
              {f} Hz
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
