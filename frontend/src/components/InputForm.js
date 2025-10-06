import React, { useState } from 'react';
import './InputForm.css';

function InputForm({ onGenerate }) {
  const [companyName, setCompanyName] = useState('');
  const [affinityId, setAffinityId] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!companyName.trim() || !affinityId.trim()) {
      return;
    }

    setIsGenerating(true);
    await onGenerate(companyName, affinityId);
    setIsGenerating(false);
  };

  return (
    <div className="input-form-container">
      <div className="form-header">
        <h2 className="form-title">Generate IC Memo</h2>
        <p className="form-subtitle">Enter company details to create a comprehensive investment memo</p>
      </div>

      <form onSubmit={handleSubmit} className="input-form">
        <div className="form-group">
          <label htmlFor="companyName" className="form-label">Company Name</label>
          <input
            id="companyName"
            type="text"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            placeholder="Enter company name"
            className="form-input"
            disabled={isGenerating}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="affinityId" className="form-label">Affinity Company ID</label>
          <input
            id="affinityId"
            type="text"
            value={affinityId}
            onChange={(e) => setAffinityId(e.target.value)}
            placeholder="Enter Affinity ID"
            className="form-input"
            disabled={isGenerating}
            required
          />
        </div>

        <button
          type="submit"
          className="generate-button"
          disabled={isGenerating || !companyName.trim() || !affinityId.trim()}
        >
          {isGenerating ? 'Generating...' : 'Generate Memo'}
        </button>
      </form>
    </div>
  );
}

export default InputForm;