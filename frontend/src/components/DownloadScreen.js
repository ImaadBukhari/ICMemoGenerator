// src/components/DownloadScreen.js
import React, { useState } from "react";
import "./DownloadScreen.css";
import api from "../api"; // ✅ use authenticated Axios instance

function DownloadScreen({ memoData, onReset }) {
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState(null);

  const handleDownload = async () => {
    try {
      setDownloading(true);
      setError(null);

      // 1️⃣ Download file via authenticated request
      const response = await api.get(`/memo/${memoData.memoId}/download`, {
        responseType: "blob", // ✅ needed for file download
      });

      // 2️⃣ Create download link
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download =
        memoData.filename ||
        `IC_Memo_${memoData.companyName.replace(/\s+/g, "_")}.docx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error("Download error:", err);
      setError(
        err.response?.data?.detail || err.message || "Download failed. Please try again."
      );
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="download-screen">
      <div className="success-icon">
        <svg viewBox="0 0 52 52" className="checkmark">
          <circle className="checkmark-circle" cx="26" cy="26" r="25" fill="none" />
          <path
            className="checkmark-check"
            fill="none"
            d="M14.1 27.2l7.1 7.2 16.7-16.8"
          />
        </svg>
      </div>

      <h2 className="success-title">Memo Generated Successfully</h2>

      <div className="memo-info">
        <div className="info-item">
          <span className="info-label">Company</span>
          <span className="info-value">{memoData.companyName}</span>
        </div>
        <div className="info-item">
          <span className="info-label">Sections</span>
          <span className="info-value">{memoData.sections} completed</span>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          <span className="error-text">{error}</span>
        </div>
      )}

      <div className="action-buttons">
        <button
          onClick={handleDownload}
          className="download-button"
          disabled={downloading}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path
              d="M10 1v12m0 0l-4-4m4 4l4-4M2 13v4a2 2 0 002 2h12a2 2 0 002-2v-4"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          {downloading ? "Downloading..." : "Download Memo"}
        </button>

        <button onClick={onReset} className="new-memo-button">
          Generate Another Memo
        </button>
      </div>
    </div>
  );
}

export default DownloadScreen;
