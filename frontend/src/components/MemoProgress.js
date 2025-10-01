import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useApi } from '../contexts/ApiContext';
import { 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  FileText, 
  Download, 
  ArrowLeft,
  RefreshCw,
  Cpu,
  Activity
} from 'lucide-react';

const MemoProgress = () => {
  const { memoId } = useParams();
  const navigate = useNavigate();
  const { getMemoStatus, getMemoSections, generateDocument, downloadDocument } = useApi();
  
  const [memoStatus, setMemoStatus] = useState(null);
  const [sections, setSections] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isGeneratingDoc, setIsGeneratingDoc] = useState(false);
  const [documentReady, setDocumentReady] = useState(false);
  const [error, setError] = useState(null);
  const [currentSection, setCurrentSection] = useState(null);

  // Section name mapping - updated to match backend generation order
  const sectionDisplayNames = {
    'executive_summary': 'EXECUTIVE_SUMMARY',
    'company_snapshot': 'COMPANY_SNAPSHOT',
    'people': 'TEAM_&_LEADERSHIP',
    'market_opportunity': 'MARKET_OPPORTUNITY',
    'competitive_landscape': 'COMPETITIVE_LANDSCAPE',
    'product': 'PRODUCT_&_TECHNOLOGY',
    'financial': 'FINANCIAL_ANALYSIS',
    'traction_validation': 'TRACTION_&_VALIDATION',
    'deal_considerations': 'DEAL_CONSIDERATIONS',
    'assessment_people': 'TEAM_ASSESSMENT',
    'assessment_market': 'MARKET_ASSESSMENT',
    'assessment_product': 'PRODUCT_ASSESSMENT',
    'assessment_financials': 'FINANCIAL_ASSESSMENT',
    'assessment_traction_validation': 'TRACTION_ASSESSMENT'
  };

  // Expected sections in generation order (from backend)
  const expectedSections = [
    'executive_summary',
    'company_snapshot', 
    'people',
    'market_opportunity',
    'competitive_landscape',
    'product',
    'financial',
    'traction_validation',
    'deal_considerations',
    'assessment_people',
    'assessment_market',
    'assessment_product',
    'assessment_financials',
    'assessment_traction_validation'
  ];

  const getCurrentlyProcessingSection = () => {
    if (!sections.length && isGenerating) {
      // If no sections in DB yet but memo is generating, assume first section
      return { section_name: expectedSections[0], status: 'in_progress' };
    }

    const completedSections = sections.filter(s => s.status === 'completed');
    const failedSections = sections.filter(s => s.status === 'failed');
    const inProgressSections = sections.filter(s => s.status === 'in_progress' || s.status === 'pending');
    
    // If there's an in-progress section, return it
    if (inProgressSections.length > 0) {
      return inProgressSections[0];
    }
    
    // If we have completed/failed sections, determine what should be next
    const processedSections = [...completedSections, ...failedSections];
    const processedSectionNames = processedSections.map(s => s.section_name);
    
    // Find the next expected section that hasn't been processed
    const nextSection = expectedSections.find(sectionName => 
      !processedSectionNames.includes(sectionName)
    );
    
    if (nextSection && isGenerating) {
      return { section_name: nextSection, status: 'in_progress' };
    }
    
    // If all sections are processed but memo is still generating, show compilation
    if (processedSections.length >= expectedSections.length && isGenerating) {
      return { section_name: 'final_compilation', status: 'in_progress' };
    }
    
    return null;
  };

  // Poll for updates more frequently during generation
  useEffect(() => {
    const fetchData = async () => {
      try {
        if (!isLoading) setIsLoading(true);
        
        const [statusResult, sectionsResult] = await Promise.all([
          getMemoStatus(memoId),
          getMemoSections(memoId).catch(() => ({ sections: [] }))
        ]);
        
        setMemoStatus(statusResult);
        setSections(sectionsResult.sections || []);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch memo data:', err);
        setError(err.response?.data?.detail || 'FAILED_TO_LOAD_MEMO_PROGRESS');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();

    // More frequent polling during generation
    const pollInterval = setInterval(() => {
      if (memoStatus?.status === 'pending' || memoStatus?.status === 'in_progress') {
        fetchData();
      }
    }, 1000); // Poll every second during generation

    return () => clearInterval(pollInterval);
  }, [memoId, getMemoStatus, getMemoSections, memoStatus?.status]);

  // Update current section when sections change
  useEffect(() => {
    setCurrentSection(getCurrentlyProcessingSection());
  }, [sections, memoStatus]);

  const handleGenerateDocument = async () => {
    try {
      setIsGeneratingDoc(true);
      const result = await generateDocument(memoId);
      
      if (result.status === 'success') {
        setDocumentReady(true);
      } else {
        throw new Error(result.error || 'DOCUMENT_GENERATION_FAILED');
      }
    } catch (err) {
      console.error('Failed to generate document:', err);
      setError(err.response?.data?.detail || 'DOCUMENT_GENERATION_FAILED');
    } finally {
      setIsGeneratingDoc(false);
    }
  };

  const handleDownloadDocument = async () => {
    try {
      const blob = await downloadDocument(memoId);
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `IC_MEMO_${memoStatus?.company_name?.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.docx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Failed to download document:', err);
      setError('DOCUMENT_DOWNLOAD_FAILED');
    }
  };

  const getSectionIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-green-400" />;
      case 'failed':
        return <AlertTriangle className="w-4 h-4 text-red-400" />;
      case 'in_progress':
        return <Activity className="w-4 h-4 text-accent" />;
      default:
        return <Clock className="w-4 h-4 text-secondary" />;
    }
  };

  const getSectionStatusClass = (status) => {
    switch (status) {
      case 'completed':
        return 'completed';
      case 'failed':
        return 'failed';
      case 'in_progress':
        return 'active';
      default:
        return '';
    }
  };

  const getProcessingMessage = () => {
    if (!currentSection) return 'FINALIZING_ANALYSIS';
    
    const sectionName = currentSection.section_name;
    
    const messages = {
      'executive_summary': 'SYNTHESIZING_EXECUTIVE_OVERVIEW',
      'company_snapshot': 'ANALYZING_COMPANY_PROFILE',
      'people': 'EVALUATING_TEAM_&_LEADERSHIP',
      'market_opportunity': 'PROCESSING_MARKET_INTELLIGENCE',
      'competitive_landscape': 'MAPPING_COMPETITIVE_DYNAMICS',
      'product': 'ASSESSING_PRODUCT_&_TECHNOLOGY',
      'financial': 'PROCESSING_FINANCIAL_DATA',
      'traction_validation': 'ANALYZING_TRACTION_&_METRICS',
      'deal_considerations': 'EVALUATING_DEAL_STRUCTURE',
      'assessment_people': 'RATING_TEAM_STRENGTH',
      'assessment_market': 'SCORING_MARKET_OPPORTUNITY',
      'assessment_product': 'EVALUATING_PRODUCT_VIABILITY',
      'assessment_financials': 'ANALYZING_FINANCIAL_HEALTH',
      'assessment_traction_validation': 'ASSESSING_MARKET_VALIDATION',
      'final_compilation': 'COMPILING_FINAL_ANALYSIS'
    };

    return messages[sectionName] || `GENERATING_${sectionName.replace(/_/g, '_').toUpperCase()}`;
  };

  // Calculate progress based on expected sections vs completed
  const completedSections = sections.filter(s => s.status === 'completed').length;
  const failedSections = sections.filter(s => s.status === 'failed').length;
  const totalExpectedSections = expectedSections.length;
  
  // Progress calculation: completed sections + partial credit for current section
  let progressPercentage = 0;
  if (totalExpectedSections > 0) {
    const baseProgress = (completedSections / totalExpectedSections) * 100;
    
    // Add partial progress for current section being processed
    if (currentSection && currentSection.status === 'in_progress' && isGenerating) {
      const partialCredit = (1 / totalExpectedSections) * 30; // 30% credit for in-progress
      progressPercentage = Math.min(baseProgress + partialCredit, 95); // Cap at 95% until complete
    } else {
      progressPercentage = baseProgress;
    }
  }

  const isGenerating = memoStatus?.status === 'pending' || memoStatus?.status === 'in_progress';

  if (isLoading && !memoStatus) {
    return (
      <div className="max-w-4xl mx-auto fade-in">
        <div className="card-cyber p-8 text-center bg-grid">
          <div className="w-12 h-12 bg-card border border-accent flex items-center justify-center mx-auto mb-6">
            <Cpu className="w-6 h-6 text-accent" />
          </div>
          <h2 className="text-lg font-mono font-semibold text-primary mb-4 tracking-wider">
            ACCESSING_MEMO_PROTOCOLS
          </h2>
          <div className="ellipses-loader">
            <span className="ellipse">.</span>
            <span className="ellipse">.</span>
            <span className="ellipse">.</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8 pb-4 border-b border-muted">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/generate')}
            className="btn-secondary flex items-center space-x-2 px-4 py-2 text-xs font-mono"
          >
            <ArrowLeft className="w-3 h-3" />
            <span>RETURN</span>
          </button>
          <div>
            <h1 className="text-xl font-mono font-bold text-primary tracking-wider">
              {memoStatus?.company_name?.toUpperCase() || 'MEMO'}_GENERATION_PROTOCOL
            </h1>
            <p className="text-secondary font-mono text-xs">
              STATUS: <span className="text-accent">{memoStatus?.status?.toUpperCase()}</span>
            </p>
          </div>
        </div>
        
        <button
          onClick={() => window.location.reload()}
          className="btn-secondary flex items-center space-x-2 px-4 py-2 text-xs font-mono"
        >
          <RefreshCw className="w-3 h-3" />
          <span>REFRESH</span>
        </button>
      </div>

      {/* Generation Progress */}
      {isGenerating && (
        <div className="card-cyber p-8 mb-8 bg-grid">
          <div className="text-center mb-8">
            <div className="w-12 h-12 bg-card border border-accent flex items-center justify-center mx-auto mb-6">
              <Activity className="w-6 h-6 text-accent animate-pulse" />
            </div>
            <h2 className="text-lg font-mono font-semibold text-primary mb-2 tracking-wider">
              AI_ANALYSIS_IN_PROGRESS
            </h2>
            <p className="text-sm text-secondary font-mono mb-6">
              {getProcessingMessage()}
            </p>
            
            {/* Progress Bar */}
            <div className="progress-bar h-3 mb-4">
              <div 
                className="progress-fill h-full transition-all duration-500"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
            
            <div className="text-xs text-secondary font-mono mb-6">
              {completedSections}_OF_{totalExpectedSections}_SECTIONS_COMPLETE • {progressPercentage.toFixed(0)}%
            </div>

            <div className="ellipses-loader">
              <span className="ellipse">.</span>
              <span className="ellipse">.</span>
              <span className="ellipse">.</span>
            </div>
            
            {currentSection && (
              <div className="mt-4 text-xs text-accent font-mono">
                CURRENT: {sectionDisplayNames[currentSection.section_name] || currentSection.section_name.toUpperCase()}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Progress Overview */}
      <div className="card-cyber p-6 mb-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-sm font-mono font-semibold text-accent tracking-wider">
            SECTION_ANALYSIS_STATUS
          </h2>
          <span className="text-xs text-secondary font-mono">
            {completedSections}/{totalExpectedSections}_MODULES_PROCESSED
          </span>
        </div>
        
        <div className="progress-bar h-2 mb-4">
          <div 
            className="progress-fill h-full transition-all duration-300"
            style={{ width: `${(completedSections / totalExpectedSections) * 100}%` }}
          />
        </div>
        
        <div className="text-right text-xs text-secondary font-mono">
          COMPLETION: {((completedSections / totalExpectedSections) * 100).toFixed(1)}%
        </div>
      </div>

      {/* Expected Sections Grid - shows all expected sections with status */}
      <div className="card-cyber p-6 mb-8">
        <h3 className="text-sm font-mono font-semibold text-accent mb-6 tracking-wider">
          DETAILED_SECTION_STATUS
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {expectedSections.map((sectionName, index) => {
            const section = sections.find(s => s.section_name === sectionName);
            const isCurrentlyProcessing = currentSection?.section_name === sectionName;
            const status = section?.status || (isCurrentlyProcessing ? 'in_progress' : 'pending');
            
            return (
              <div 
                key={sectionName} 
                className={`section-card p-4 transition-colors duration-150 ${getSectionStatusClass(status)}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getSectionIcon(status)}
                    <div>
                      <h4 className="font-mono font-medium text-primary text-xs">
                        {sectionDisplayNames[sectionName] || sectionName.replace(/_/g, '_').toUpperCase()}
                      </h4>
                      <p className="text-xs text-secondary font-mono">
                        {section?.content_length > 0 ? `${section.content_length}_CHARS` : 
                         status === 'completed' ? 'COMPLETED' :
                         status === 'in_progress' ? 'PROCESSING' :
                         status === 'failed' ? 'FAILED' : 'QUEUED'}
                      </p>
                    </div>
                  </div>
                  
                  <div className={`status-indicator ${status}`}></div>
                </div>
                
                {section?.error && (
                  <div className="mt-3 text-xs text-red-400 font-mono">
                    ERROR: {section.error}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Document Generation */}
      <div className="card-cyber p-6">
        <h3 className="text-sm font-mono font-semibold text-accent mb-6 tracking-wider">
          DOCUMENT_COMPILATION
        </h3>
        
        {memoStatus?.status === 'success' || memoStatus?.status === 'completed' || memoStatus?.status === 'partial_success' ? (
          <div className="space-y-6">
            <div className="flex items-center space-x-3 text-green-400">
              <CheckCircle2 className="w-4 h-4" />
              <span className="font-mono font-medium text-xs">
                {memoStatus?.status === 'partial_success' ? 'PARTIAL_ANALYSIS_COMPLETE' : 'ANALYSIS_COMPLETE'} • READY_FOR_EXPORT
              </span>
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={handleGenerateDocument}
                disabled={isGeneratingDoc}
                className="btn-primary flex items-center space-x-2 px-4 py-3 text-xs font-mono font-semibold"
              >
                {isGeneratingDoc ? (
                  <>
                    <div className="dots-loader mr-2">
                      <div className="dot"></div>
                      <div className="dot"></div>
                      <div className="dot"></div>
                    </div>
                    COMPILING_DOCUMENT
                  </>
                ) : (
                  <>
                    <FileText className="w-4 h-4" />
                    <span>GENERATE_WORD_DOCUMENT</span>
                  </>
                )}
              </button>
              
              {(documentReady || memoStatus?.drive_link) && (
                <button
                  onClick={handleDownloadDocument}
                  className="bg-green-600 border border-green-600 hover:bg-green-700 text-surface flex items-center space-x-2 px-4 py-3 text-xs font-mono font-semibold transition-colors duration-150"
                >
                  <Download className="w-4 h-4" />
                  <span>DOWNLOAD_MEMO</span>
                </button>
              )}
            </div>
            
            {memoStatus?.drive_link && (
              <div className="mt-4 p-4 bg-surface border border-muted">
                <p className="text-xs text-secondary font-mono mb-2">GOOGLE_DRIVE_LINK:</p>
                <a
                  href={memoStatus.drive_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-accent hover:text-primary font-mono text-xs underline"
                >
                  {memoStatus.drive_link}
                </a>
              </div>
            )}
          </div>
        ) : (
          <div className="text-secondary font-mono">
            <div className="flex items-center space-x-3 mb-4">
              <Clock className="w-4 h-4" />
              <span className="text-xs">AWAITING_ANALYSIS_COMPLETION</span>
            </div>
            <p className="text-xs">
              Document generation available once analysis is complete. 
              {completedSections > 0 && ` ${completedSections}/${totalExpectedSections} sections ready.`}
            </p>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="mt-8 card-cyber bg-surface border-red-500 p-6">
          <div className="flex items-center space-x-3">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <div>
              <h3 className="text-sm font-mono font-semibold text-red-300">SYSTEM_ERROR</h3>
              <div className="mt-2 text-xs text-red-400 font-mono">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MemoProgress;