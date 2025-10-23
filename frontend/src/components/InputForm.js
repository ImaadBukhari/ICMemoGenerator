import React, { useState } from 'react';
import './InputForm.css';

// Input form component for generating IC memo
function InputForm({ onGenerate }) {
  const [companyName, setCompanyName] = useState('');
  const [affinityId, setAffinityId] = useState('');
  const [description, setDescription] = useState('');
  const [memoType, setMemoType] = useState('full'); // 'full' or 'short'
  const [isGenerating, setIsGenerating] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!companyName.trim() || !affinityId.trim()) {
      return;
    }

    setIsGenerating(true);
    await onGenerate(companyName, affinityId, description.trim(), memoType);
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
            placeholder="e.g., Nash"
            className="form-input"
            disabled={isGenerating}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="description" className="form-label">
            Company Description <span className="optional-label">(Optional but recommended)</span>
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Brief description to help identify the company (e.g., 'AI-powered logistics startup based in San Francisco' or 'B2B SaaS platform for supply chain management')"
            className="form-textarea"
            disabled={isGenerating}
            rows="3"
          />
          <p className="field-hint">
            This helps us find the right company, especially if the name is common or ambiguous.
          </p>
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

        <div className="form-group">
          <label className="form-label">Memo Type</label>
          <div className="memo-type-selection">
            <label className="memo-type-option">
              <input
                type="radio"
                value="full"
                checked={memoType === 'full'}
                onChange={(e) => setMemoType(e.target.value)}
                disabled={isGenerating}
              />
              <span className="memo-type-label">
                <strong>Full Memo</strong>
                <small>Comprehensive 15-section analysis</small>
              </span>
            </label>
            <label className="memo-type-option">
              <input
                type="radio"
                value="short"
                checked={memoType === 'short'}
                onChange={(e) => setMemoType(e.target.value)}
                disabled={isGenerating}
              />
              <span className="memo-type-label">
                <strong>1-Page Summary</strong>
                <small>Concise initial IC memo</small>
              </span>
            </label>
          </div>
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