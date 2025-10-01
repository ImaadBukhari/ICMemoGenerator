import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApi } from '../contexts/ApiContext';
import { 
  Building2, 
  Hash, 
  Search, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowRight,
  Database,
  Globe,
  FileText,
  Activity
} from 'lucide-react';

const MemoGenerator = () => {
  const navigate = useNavigate();
  const { gatherCompanyData, generateMemo } = useApi();
  
  const [formData, setFormData] = useState({
    companyName: '',
    affinityCompanyId: ''
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState('form');
  const [gatheringResults, setGatheringResults] = useState(null);
  const [error, setError] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    setError(null);
  };

  const validateForm = () => {
    if (!formData.companyName.trim()) {
      setError('COMPANY_NAME_REQUIRED');
      return false;
    }
    if (!formData.affinityCompanyId.trim()) {
      setError('AFFINITY_ID_REQUIRED');
      return false;
    }
    return true;
  };

  const handleStartGeneration = async () => {
    if (!validateForm()) return;

    setIsLoading(true);
    setCurrentStep('gathering');
    setError(null);

    try {
      const gatheringResult = await gatherCompanyData(
        formData.companyName, 
        formData.affinityCompanyId
      );
      
      setGatheringResults(gatheringResult);
      
      if (!gatheringResult.source_id) {
        throw new Error('DATA_STORAGE_FAILED');
      }

      setCurrentStep('generating');
      
      const memoResult = await generateMemo(gatheringResult.source_id);
      
      if (memoResult.memo_request_id) {
        navigate(`/memo/${memoResult.memo_request_id}/progress`);
      } else {
        throw new Error('MEMO_GENERATION_FAILED');
      }

    } catch (err) {
      console.error('Generation error:', err);
      setError(err.response?.data?.detail || err.message || 'SYSTEM_ERROR');
      setCurrentStep('form');
    } finally {
      setIsLoading(false);
    }
  };

  const DataSourceCard = ({ icon: Icon, title, success, error, details, isActive = false }) => (
    <div className={`section-card p-4 transition-colors duration-150 ${
      success ? 'completed' : 
      error ? 'failed' : 
      isActive ? 'active' : ''
    }`}>
      <div className="flex items-center space-x-3">
        <div className={`p-2 border transition-colors duration-150 ${
          success ? 'bg-hover border-green-500 text-green-400' : 
          error ? 'bg-hover border-red-500 text-red-400' : 
          isActive ? 'bg-hover border-accent text-accent' :
          'bg-card border-muted text-secondary'
        }`}>
          <Icon className="w-4 h-4" />
        </div>
        <div className="flex-1">
          <h3 className="font-mono font-medium text-primary text-sm mb-1">
            {title}
          </h3>
          {details && (
            <p className="text-xs text-secondary font-mono">{details}</p>
          )}
        </div>
        <div className="flex-shrink-0">
          {success && <CheckCircle2 className="w-4 h-4 text-green-400" />}
          {error && <AlertTriangle className="w-4 h-4 text-red-400" />}
          {isActive && <Activity className="w-4 h-4 text-accent" />}
        </div>
      </div>
    </div>
  );

  if (currentStep === 'gathering') {
    return (
      <div className="max-w-4xl mx-auto slide-up">
        <div className="card-cyber p-8 bg-grid">
          <div className="text-center mb-8">
            <div className="w-12 h-12 bg-card border border-accent flex items-center justify-center mx-auto mb-6">
              <Database className="w-6 h-6 text-accent" />
            </div>
            <h2 className="text-xl font-mono font-semibold text-primary mb-2 tracking-wider">
              DATA_ACQUISITION_ACTIVE
            </h2>
            <p className="text-secondary font-mono text-sm mb-6">
              SCANNING_SOURCES_FOR: <span className="text-accent">{formData.companyName.toUpperCase()}</span>
            </p>
            
            <div className="mb-8">
              <div className="ellipses-loader mb-4">
                <span className="ellipse">.</span>
                <span className="ellipse">.</span>
                <span className="ellipse">.</span>
              </div>
              <p className="text-xs text-secondary font-mono">PROCESSING_DATA_STREAMS</p>
            </div>
          </div>

          {gatheringResults && (
            <div className="grid gap-3">
              <DataSourceCard
                icon={Database}
                title="AFFINITY_CRM"
                success={gatheringResults.affinity_success}
                error={!gatheringResults.affinity_success}
                details="COMPANY_PROFILE • DEAL_DATA • RELATIONSHIPS"
                isActive={!gatheringResults.affinity_success && !gatheringResults.drive_success && !gatheringResults.perplexity_success}
              />
              
              <DataSourceCard
                icon={FileText}
                title="GOOGLE_DRIVE"
                success={gatheringResults.drive_success}
                error={!gatheringResults.drive_success}
                details="DOCUMENTS • PRESENTATIONS • FILES"
                isActive={gatheringResults.affinity_success && !gatheringResults.drive_success && !gatheringResults.perplexity_success}
              />
              
              <DataSourceCard
                icon={Globe}
                title="MARKET_RESEARCH"
                success={gatheringResults.perplexity_success}
                error={!gatheringResults.perplexity_success}
                details="MARKET_ANALYSIS • COMPETITIVE_DATA"
                isActive={gatheringResults.affinity_success && gatheringResults.drive_success && !gatheringResults.perplexity_success}
              />
            </div>
          )}
        </div>
      </div>
    );
  }

  if (currentStep === 'generating') {
    return (
      <div className="max-w-4xl mx-auto slide-up">
        <div className="card-cyber p-8 bg-grid">
          <div className="text-center">
            <div className="w-12 h-12 bg-card border border-green-500 flex items-center justify-center mx-auto mb-6">
              <FileText className="w-6 h-6 text-green-400" />
            </div>
            <h2 className="text-xl font-mono font-semibold text-green-400 mb-2 tracking-wider">
              MEMO_GENERATION_ACTIVE
            </h2>
            <p className="text-secondary font-mono text-sm mb-8">
              COMPILING_ANALYSIS_FOR: <span className="text-green-400">{formData.companyName.toUpperCase()}</span>
            </p>
            
            <div className="mb-6">
              <div className="ellipses-loader mb-4">
                <span className="ellipse">.</span>
                <span className="ellipse">.</span>
                <span className="ellipse">.</span>
              </div>
              <p className="text-xs text-secondary font-mono">GENERATING_COMPREHENSIVE_ANALYSIS</p>
            </div>
            
            <div className="text-xs text-green-400 font-mono">
              REDIRECTING_TO_PROGRESS_MONITOR
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto fade-in">
      {/* Header */}
      <div className="text-center mb-12 py-8 bg-grid">
        <h1 className="text-2xl font-mono font-bold text-primary mb-4 tracking-wider">
          INVESTMENT_COMMITTEE_MEMO_GENERATOR
        </h1>
        <p className="text-sm text-secondary max-w-3xl mx-auto font-mono leading-relaxed">
          AUTOMATED_INTELLIGENCE_SYSTEM • MULTI_SOURCE_DATA_AGGREGATION<br />
          COMPREHENSIVE_INVESTMENT_ANALYSIS_PROTOCOL
        </p>
      </div>

      {/* Main Form */}
      <div className="card-cyber p-8 mb-8">
        <form onSubmit={(e) => { e.preventDefault(); handleStartGeneration(); }}>
          <div className="grid gap-6">
            {/* Company Name */}
            <div>
              <label htmlFor="companyName" className="block text-xs font-mono font-medium text-accent mb-2 tracking-wider">
                TARGET_COMPANY_DESIGNATION
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Building2 className="h-4 w-4 text-secondary" />
                </div>
                <input
                  type="text"
                  id="companyName"
                  name="companyName"
                  value={formData.companyName}
                  onChange={handleInputChange}
                  className="input-terminal block w-full pl-10 pr-3 py-3 text-sm"
                  placeholder="NUCLEARN_TECHNOLOGIES"
                  required
                />
              </div>
              <p className="mt-2 text-xs text-secondary font-mono">
                PRIMARY_IDENTIFIER_FOR_DATA_CORRELATION
              </p>
            </div>

            {/* Affinity Company ID */}
            <div>
              <label htmlFor="affinityCompanyId" className="block text-xs font-mono font-medium text-accent mb-2 tracking-wider">
                AFFINITY_CRM_REFERENCE_ID
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Hash className="h-4 w-4 text-secondary" />
                </div>
                <input
                  type="text"
                  id="affinityCompanyId"
                  name="affinityCompanyId"
                  value={formData.affinityCompanyId}
                  onChange={handleInputChange}
                  className="input-terminal block w-full pl-10 pr-3 py-3 text-sm font-mono"
                  placeholder="12345"
                  required
                />
              </div>
              <p className="mt-2 text-xs text-secondary font-mono">
                UNIQUE_DATABASE_IDENTIFIER_FOR_CRM_INTEGRATION
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-surface border border-red-500 p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <AlertTriangle className="h-4 w-4 text-red-400" />
                  </div>
                  <div className="ml-3">
                    <h3 className="text-xs font-mono font-medium text-red-300 tracking-wider">
                      SYSTEM_ERROR
                    </h3>
                    <div className="mt-1 text-xs text-red-400 font-mono">
                      <p>{error}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <div className="pt-4">
              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary w-full flex justify-center items-center px-6 py-3 text-xs font-mono font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <>
                    <div className="dots-loader mr-3">
                      <div className="dot"></div>
                      <div className="dot"></div>
                      <div className="dot"></div>
                    </div>
                    PROCESSING
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4 mr-2" />
                    INITIATE_MEMO_GENERATION
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Data Sources Info */}
      <div className="card-cyber p-6 bg-grid">
        <h3 className="text-sm font-mono font-semibold text-accent mb-4 tracking-wider">
          DATA_ACQUISITION_PROTOCOLS
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <DataSourceCard
            icon={Database}
            title="AFFINITY_CRM"
            details="COMPANY_PROFILES • DEAL_STAGES • FUNDING_HISTORY"
          />
          <DataSourceCard
            icon={FileText}
            title="GOOGLE_DRIVE"
            details="PITCH_DECKS • FINANCIAL_MODELS • DOCUMENTS"
          />
          <DataSourceCard
            icon={Globe}
            title="MARKET_INTELLIGENCE"
            details="INDUSTRY_ANALYSIS • COMPETITIVE_MAPPING"
          />
        </div>
      </div>
    </div>
  );
};

export default MemoGenerator;