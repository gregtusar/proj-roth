import React, { useState, useEffect } from 'react';
import { PlusIcon, DocumentTextIcon, ClockIcon, ArrowTopRightOnSquareIcon, TrashIcon } from '@heroicons/react/24/outline';
import { format } from 'date-fns';
import AddDocumentModal from './AddDocumentModal';
import DocumentViewer from './DocumentViewer';

interface Document {
  doc_id: string;
  title: string;
  url: string;
  created_at: string | null;
  updated_at: string | null;
}

const DocumentLibrary: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [showViewer, setShowViewer] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/document-links', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch documents');
      }

      const data = await response.json();
      setDocuments(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleDocumentAdded = (newDocument: Document) => {
    setDocuments([newDocument, ...documents]);
    setShowAddModal(false);
  };

  const handleViewDocument = (document: Document) => {
    setSelectedDocument(document);
    setShowViewer(true);
  };

  const handleDeleteDocument = async (doc: Document) => {
    if (!window.confirm(`Are you sure you want to delete "${doc.title}"?`)) {
      return;
    }

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/document-links/${doc.doc_id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete document');
      }

      setDocuments(documents.filter(d => d.doc_id !== doc.doc_id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete document');
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Unknown';
    try {
      return format(new Date(dateString), 'MMM d, yyyy h:mm a');
    } catch {
      return 'Unknown';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-800 flex items-center">
            <DocumentTextIcon className="h-8 w-8 mr-2 text-gray-600" />
            Document Assets
          </h2>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Add Document
          </button>
        </div>
        <p className="text-gray-600 mt-2">
          Create and manage documents for voter outreach emails, briefings, and notes.
        </p>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {documents.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <DocumentTextIcon className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No documents yet</h3>
          <p className="text-gray-600 mb-4">
            Create your first document to get started.
          </p>
          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Add Your First Document
          </button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {documents.map((doc) => (
            <div
              key={doc.doc_id}
              className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200"
            >
              <div className="p-5">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center">
                    <DocumentTextIcon className="h-6 w-6 text-blue-600 mr-2" />
                    <h3 className="text-lg font-semibold text-gray-900 truncate">
                      {doc.title}
                    </h3>
                  </div>
                </div>
                
                <div className="space-y-2 text-sm text-gray-600 mb-4">
                  <div className="flex items-center">
                    <ClockIcon className="h-4 w-4 mr-2" />
                    <span>Created: {formatDate(doc.created_at)}</span>
                  </div>
                  {doc.updated_at && (
                    <div className="flex items-center">
                      <ClockIcon className="h-4 w-4 mr-2" />
                      <span>Updated: {formatDate(doc.updated_at)}</span>
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => handleViewDocument(doc)}
                    className="flex-1 px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors text-sm font-medium"
                  >
                    View
                  </button>
                  <a
                    href={doc.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 px-3 py-2 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors text-sm font-medium flex items-center justify-center"
                  >
                    <ArrowTopRightOnSquareIcon className="h-4 w-4 mr-1" />
                    Open
                  </a>
                  <button
                    onClick={() => handleDeleteDocument(doc)}
                    className="px-3 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors text-sm font-medium"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showAddModal && (
        <AddDocumentModal
          onClose={() => setShowAddModal(false)}
          onDocumentAdded={handleDocumentAdded}
        />
      )}

      {showViewer && selectedDocument && (
        <DocumentViewer
          document={selectedDocument}
          onClose={() => {
            setShowViewer(false);
            setSelectedDocument(null);
          }}
          onUpdate={() => fetchDocuments()}
        />
      )}
    </div>
  );
};

export default DocumentLibrary;