import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useApi } from '../contexts/ApiContext';
import { FileText, Clock, CheckCircle, AlertCircle, Eye } from 'lucide-react';

const MemoHistory = () => {
  const { listMemos } = useApi();
  const [memos, setMemos] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMemos = async () => {
      try {
        const result = await listMemos();
        setMemos(result);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch memos:', err);
        setError('Failed to load memo history');
      } finally {
        setIsLoading(false);
      }
    };

    fetchMemos();
  }, [listMemos]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
      case 'success':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading memo history...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Memo History</h1>
        <p className="text-lg text-gray-600">
          View and manage your previously generated investment committee memos.
        </p>
      </div>

      {/* Memos List */}
      {memos.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No memos yet</h3>
          <p className="text-gray-600 mb-6">
            You haven't generated any IC memos yet. Start by creating your first memo.
          </p>
          <Link
            to="/generate"
            className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
          >
            <FileText className="w-4 h-4 mr-2" />
            Generate First Memo
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">
              Generated Memos ({memos.length})
            </h3>
          </div>
          
          <div className="divide-y divide-gray-200">
            {memos.map((memo) => (
              <div key={memo.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    {getStatusIcon(memo.status)}
                    <div>
                      <h4 className="text-lg font-medium text-gray-900">
                        {memo.company_name}
                      </h4>
                      <p className="text-sm text-gray-600">
                        Generated on {formatDate(memo.created_at)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(memo.status)}`}>
                      {memo.status}
                    </span>
                    
                    <Link
                      to={`/memo/${memo.id}/progress`}
                      className="flex items-center space-x-2 text-primary-600 hover:text-primary-800"
                    >
                      <Eye className="w-4 h-4" />
                      <span>View Details</span>
                    </Link>
                  </div>
                </div>
                
                {memo.drive_link && (
                  <div className="mt-2">
                    <a
                      href={memo.drive_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      View in Google Drive →
                    </a>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MemoHistory;