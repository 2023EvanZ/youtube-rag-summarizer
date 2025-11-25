import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [chunks, setChunks] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleTranscript = async () => {
    setLoading(true);
    try {
      await axios.post('http://localhost:8000/transcript', { youtube_url: youtubeUrl });
      alert('Transcript generated!');
    } catch (error) {
      alert('Error generating transcript.');
    }
    setLoading(false);
  };

  const handleChunk = async () => {
    setLoading(true);
    try {
      const res = await axios.post('http://localhost:8000/chunk', {
        file_path: 'test_transcript.txt',
        lines_per_chunk: 10
      });
      setChunks(res.data.notes);
    } catch (error) {
      alert('Error fetching notes.');
    }
    setLoading(false);
  };

  const handleClear = () => {
    setChunks([]);
  };

  return (
    <div>
      <h1 className="title">Smart YouTube Summarizer</h1>
      <div className="input-group">
        <input
          className="input"
          value={youtubeUrl}
          onChange={e => setYoutubeUrl(e.target.value)}
          placeholder="YouTube Video URL"
        />
        <button className="button" onClick={handleTranscript}>Generate Transcript</button>
      </div>
      <div className="button-group">
        <button className="button" onClick={handleChunk}>Chunk & Summarize Transcript</button>
        <button className="button clear" onClick={handleClear}>Clear</button>
      </div>
      {loading && <div className="loading">Loading...</div>}
      <div className="container">
        <ul className="notes-list">
          {chunks.flat().map((bullet, idx) => (
            <li key={idx} className="note" dangerouslySetInnerHTML={{ __html: bullet }} />
          ))}
        </ul>
      </div>
    </div>
  );
}

export default App;