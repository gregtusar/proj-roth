import React, { useState, useEffect } from 'react';
import { XMarkIcon, PencilIcon, CheckIcon, XCircleIcon } from '@heroicons/react/24/outline';

interface DocumentViewerProps {
  document: {
    doc_id: string;
    title: string;
    url: string;
  };
  onClose: () => void;
  onUpdate: () => void;
}

const DocumentViewer: React.FC<DocumentViewerProps> = ({ document, onClose, onUpdate }) => {
  const [content, setContent] = useState('');
  const [editedContent, setEditedContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDocumentContent();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [document.doc_id]);

  const fetchDocumentContent = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/documents/${document.doc_id}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch document content');
      }

      const data = await response.json();
      setContent(data.content || '');
      setEditedContent(data.content || '');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/documents/${document.doc_id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          content: editedContent
        })
      });

      if (!response.ok) {
        throw new Error('Failed to update document');
      }

      setContent(editedContent);
      setEditing(false);
      onUpdate();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setEditedContent(content);
    setEditing(false);
    setError(null);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">{document.title}</h2>
            <a
              href={document.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:text-blue-700 mt-1 inline-block"
            >
              Open in Google Docs →
            </a>
          </div>
          <div className="flex items-center gap-2">
            {!editing ? (
              <button
                onClick={() => setEditing(true)}
                className="p-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded"
                title="Edit"
              >
                <PencilIcon className="h-5 w-5" />
              </button>
            ) : (
              <>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="p-2 text-green-600 hover:text-green-700 hover:bg-green-50 rounded disabled:opacity-50"
                  title="Save"
                >
                  <CheckIcon className="h-5 w-5" />
                </button>
                <button
                  onClick={handleCancel}
                  disabled={saving}
                  className="p-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded disabled:opacity-50"
                  title="Cancel"
                >
                  <XCircleIcon className="h-5 w-5" />
                </button>
              </>
            )}
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
            </div>
          ) : error ? (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {error}
            </div>
          ) : (
            <>
              {editing ? (
                <textarea
                  value={editedContent}
                  onChange={(e) => setEditedContent(e.target.value)}
                  className="w-full h-full min-h-[400px] p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  disabled={saving}
                />
              ) : (
                <div className="prose max-w-none">
                  {content ? (
                    <pre className="whitespace-pre-wrap font-sans">{content}</pre>
                  ) : (
                    <p className="text-gray-500 italic">This document is empty.</p>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {saving && (
          <div className="px-6 py-3 border-t bg-gray-50 text-sm text-gray-600">
            Saving changes...
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentViewer;