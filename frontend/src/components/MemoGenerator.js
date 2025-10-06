import React, { useState, useRef } from 'react';
import InputForm from './InputForm';
import LoadingScreen from './LoadingScreen';
import DownloadScreen from './DownloadScreen';
import './MemoGenerator.css';

function MemoGenerator() {
  const [stage, setStage] = useState('input');
  const [memoData, setMemoData] = useState(null);
  const [currentSection, setCurrentSection] = useState('');
  const [progress, setProgress] = useState(0);
  const [completedSections, setCompletedSections] = useState(0);
  const [totalSections] = useState(15);
  
  const pollingIntervalRef = useRef(null);

  const handleGenerate = async (companyName, affinityId) => {
    setStage('loading');
    setCurrentSection('Gathering company data...');
    setProgress(0);
    setCompletedSections(0);

    try {
      const gatherResponse = await fetch('http://localhost:8000/api/data/gather', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_name: companyName,
          company_id: affinityId
        })
      });

      if (!gatherResponse.ok) {
        throw new Error('Failed to gather company data');
      }

      const gatherData = await gatherResponse.json();
      setCurrentSection('Starting memo generation...');
      
      // Start memo generation (returns immediately now)
      const memoResponse = await fetch('http://localhost:8000/api/memo/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source_id: gatherData.source_id })
      });

      if (!memoResponse.ok) {
        throw new Error('Failed to start memo generation');
      }

      const memoResult = await memoResponse.json();
      const memoId = memoResult.memo_request_id;

      // NOW start polling - generation is happening in background
      startPolling(memoId, companyName);

    } catch (error) {
      console.error('Error:', error);
      alert(`Error: ${error.message}`);
      setStage('input');
    }
  };

  const startPolling = (memoId, companyName) => {
    pollingIntervalRef.current = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/memo/${memoId}/sections`);
        if (!response.ok) return;
        
        const data = await response.json();
        const sections = data.sections || [];
        
        const completed = sections.filter(s => s.status === 'completed').length;
        const progressPercent = (completed / totalSections) * 100;
        
        setCompletedSections(completed);
        setProgress(progressPercent);
        
        // Find current section
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

        // Check if all done
        if (data.overall_status === 'completed' || data.overall_status === 'partial_success') {
          clearInterval(pollingIntervalRef.current);
          
          setProgress(100);
          setCurrentSection('Creating Word document...');
          
          const docResponse = await fetch(`http://localhost:8000/api/memo/${memoId}/generate-document`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
          });

          if (docResponse.ok) {
            const docResult = await docResponse.json();
            
            setTimeout(() => {
              setMemoData({
                memoId: memoId,
                companyName: companyName,
                filename: docResult.filename,
                sections: completed
              });
              setStage('download');
            }, 500);
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 1000);
  };

  const formatSectionName = (sectionKey) => {
    const sectionNames = {
      'executive_summary': 'Executive Summary',
      'company_snapshot': 'Company Snapshot',
      'people': 'Team & Leadership',
      'market_opportunity': 'Market Opportunity',
      'competitive_landscape': 'Competitive Landscape',
      'product': 'Product & Technology',
      'financial': 'Financial Analysis',
      'traction_validation': 'Traction & Validation',
      'deal_considerations': 'Deal Considerations',
      'assessment_people': 'Scorecard: Team',
      'assessment_market_opportunity': 'Scorecard: Market',
      'assessment_product': 'Scorecard: Product',
      'assessment_financials': 'Scorecard: Financial',
      'assessment_traction_validation': 'Scorecard: Traction',
      'assessment_deal_considerations': 'Scorecard: Deal'
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
        {stage === 'download' && <DownloadScreen memoData={memoData} onReset={handleReset} />}
      </div>
    </div>
  );
}

export default MemoGenerator;