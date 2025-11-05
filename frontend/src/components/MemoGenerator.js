// src/components/MemoGenerator.js
import React, { useState, useRef } from 'react';
import InputForm from './InputForm';
import LoadingScreen from './LoadingScreen';
import DownloadScreen from './DownloadScreen';
import './MemoGenerator.css';
import api from '../api'; // ✅ Authenticated Axios client

function MemoGenerator() {
  const [stage, setStage] = useState('input');
  const [memoData, setMemoData] = useState(null);
  const [currentSection, setCurrentSection] = useState('');
  const [progress, setProgress] = useState(0);
  const [completedSections, setCompletedSections] = useState(0);
  const [totalSections, setTotalSections] = useState(15);

  const pollingIntervalRef = useRef(null);

  const handleGenerate = async (companyName, affinityId, description, memoType = 'full') => {
    setStage('loading');
    setCurrentSection('Gathering company data...');
    setProgress(0);
    setCompletedSections(0);
    
    // Always use full memo (15 sections)
    setTotalSections(15);

    try {
      // 1️⃣ Gather company data
      const { data: gatherData } = await api.post('/data/gather', {
        company_name: companyName,
        company_id: affinityId,
        description: description,
      });

      setCurrentSection('Starting memo generation...');

      // 2️⃣ Start memo generation (always use 'full' type)
      const { data: memoResult } = await api.post('/memo/generate', {
        source_id: gatherData.source_id,
        memo_type: 'full',
      });

      const memoId = memoResult.memo_request_id;

      // 3️⃣ Begin polling progress
      startPolling(memoId, companyName);

    } catch (error) {
      console.error('Error:', error);
      alert(`Error: ${error.message}`);
      setStage('input');
    }
  };

  // Poll memo progress (always full memo)
  const startPolling = (memoId, companyName) => {
    pollingIntervalRef.current = setInterval(async () => {
      try {
        const { data } = await api.get(`/memo/${memoId}/sections`);
        const sections = data.sections || [];

        const totalSectionsCount = 15; // Always 15 for full memo
        const completed = sections.filter(s => s.status === 'completed').length;
        const progressPercent = (completed / totalSectionsCount) * 100;

        setCompletedSections(completed);
        setProgress(progressPercent);

        // Always use full memo sections
        const expectedSections = [
          'executive_summary', 'company_snapshot', 'people', 'market_opportunity',
          'competitive_landscape', 'product', 'financial', 'traction_validation',
          'deal_considerations', 'assessment_people', 'assessment_market_opportunity',
          'assessment_product', 'assessment_financials', 'assessment_traction_validation',
          'assessment_deal_considerations'
        ];

        const completedNames = sections.filter(s => s.status === 'completed').map(s => s.section_name);
        const nextSection = expectedSections.find(s => !completedNames.includes(s));

        if (nextSection) {
          setCurrentSection(formatSectionName(nextSection));
        }

        // 4️⃣ When finished, generate final doc
        if (data.overall_status === 'completed' || data.overall_status === 'partial_success') {
          clearInterval(pollingIntervalRef.current);
          setProgress(100);
          setCurrentSection('Creating Google Doc...');

          try {
            const { data: docResult } = await api.post(`/memo/${memoId}/generate-document`);
            
            if (docResult.error) {
              // Check if it's a Google Drive access error
              if (docResult.error.includes('Secret Manager') || 
                  docResult.error.includes('No Google') ||
                  docResult.error.includes('Google Drive access')) {
                alert('Google Drive access error:\n\n' + docResult.error + '\n\nPlease contact the administrator to ensure the Secret Manager token is configured correctly.');
                setStage('input');
                return;
              }
              throw new Error(docResult.error);
            }

            setTimeout(() => {
              setMemoData({
                memoId,
                companyName,
                docUrl: docResult.doc_url || docResult.document_path,
                sections: completed,
              });
              setStage('download');
            }, 500);
          } catch (err) {
            console.error('Document generation error:', err);
            const errorMsg = err.response?.data?.error || err.message;
            if (errorMsg.includes('Secret Manager') || 
                errorMsg.includes('No Google') ||
                errorMsg.includes('Google Drive access')) {
              alert('Google Drive access error:\n\n' + errorMsg + '\n\nPlease contact the administrator to ensure the Secret Manager token is configured correctly.');
            } else {
              alert(`Error generating document: ${errorMsg}`);
            }
            setStage('input');
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 1000);
  };

  const formatSectionName = (sectionKey) => {
    const sectionNames = {
      // Full memo sections
      executive_summary: 'Executive Summary',
      company_snapshot: 'Company Snapshot',
      people: 'Team & Leadership',
      market_opportunity: 'Market Opportunity',
      competitive_landscape: 'Competitive Landscape',
      product: 'Product & Technology',
      financial: 'Financial Analysis',
      traction_validation: 'Traction & Validation',
      deal_considerations: 'Deal Considerations',
      assessment_people: 'Scorecard: Team',
      assessment_market_opportunity: 'Scorecard: Market',
      assessment_product: 'Scorecard: Product',
      assessment_financials: 'Scorecard: Financial',
      assessment_traction_validation: 'Scorecard: Traction',
      assessment_deal_considerations: 'Scorecard: Deal',
    };

    return sectionNames[sectionKey] || sectionKey
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const handleReset = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    setStage('input');
    setMemoData(null);
    setCurrentSection('');
    setProgress(0);
    setCompletedSections(0);
  };

  return (
    <div className="memo-generator">
      <div className="content-container">
        {stage === 'input' && <InputForm onGenerate={handleGenerate} />}
        {stage === 'loading' && (
          <LoadingScreen
            currentSection={currentSection}
            progress={progress}
            totalSections={totalSections}
            completedSections={completedSections}
          />
        )}
        {stage === 'download' && (
          <DownloadScreen memoData={memoData} onReset={handleReset} />
        )}
      </div>
    </div>
  );
}

export default MemoGenerator;
