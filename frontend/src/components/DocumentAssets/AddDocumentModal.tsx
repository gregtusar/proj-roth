import React, { useState } from 'react';
import { XMarkIcon, LinkIcon, DocumentPlusIcon } from '../Common/Icons';

interface AddDocumentModalProps {
  onClose: () => void;
  onDocumentAdded: (doc: any) => void;
}

const AddDocumentModal: React.FC<AddDocumentModalProps> = ({ onClose, onDocumentAdded }) => {
  const [mode, setMode] = useState<'link' | 'create'>('link');
  const [title, setTitle] = useState('');
  const [url, setUrl] = useState('');
  const [description, setDescription] = useState('');
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateGoogleUrl = (url: string): boolean => {
    const patterns = [
      /docs\.google\.com/,
      /drive\.google\.com/,
      /spreadsheets\.google\.com/,
      /forms\.google\.com/,
      /slides\.google\.com/
    ];
    return patterns.some(pattern => pattern.test(url));
  };

  const handleSubmitLink = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!title.trim()) {
      setError('Please enter a document title');
      return;
    }

    if (!url.trim()) {
      setError('Please enter a document URL');
      return;
    }

    if (!validateGoogleUrl(url)) {
      setError('Please enter a valid Google Docs, Sheets, Slides, Forms, or Drive URL');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/document-links', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          title: title.trim(),
          url: url.trim(),
          description: description.trim() || null,
          source: 'manual'
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to add document link');
      }

      const newDocument = await response.json();
      onDocumentAdded(newDocument);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNew = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!title.trim()) {
      setError('Please enter a document title');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('auth_token');
      
      // First create the document
      const createResponse = await fetch('/api/documents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          title: title.trim(),
          content: content.trim()
        })
      });

      if (!createResponse.ok) {
        throw new Error('Failed to create document');
      }

      const createdDoc = await createResponse.json();
      
      // Then store the link
      const linkResponse = await fetch('/api/document-links', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          title: createdDoc.title,
          url: createdDoc.url,
          description: description.trim() || 'Created via Document Assets',
          source: 'ai_generated'
        })
      });

      if (!linkResponse.ok) {
        console.error('Failed to store document link, but document was created');
      }

      const newDocument = await linkResponse.json();
      onDocumentAdded(newDocument);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b sticky top-0 bg-white">
          <h2 className="text-xl font-semibold text-gray-900">Add Document</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6">
          {/* Mode Selector */}
          <div className="flex gap-4 mb-6">
            <button
              type="button"
              onClick={() => setMode('link')}
              className={`flex-1 p-4 rounded-lg border-2 transition-colors ${
                mode === 'link' 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <LinkIcon className="h-8 w-8 mx-auto mb-2 text-gray-600" />
              <div className="font-medium">Add Existing Document</div>
              <div className="text-sm text-gray-500 mt-1">
                Link to an existing Google Doc
              </div>
            </button>
            <button
              type="button"
              onClick={() => setMode('create')}
              className={`flex-1 p-4 rounded-lg border-2 transition-colors ${
                mode === 'create' 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <DocumentPlusIcon className="h-8 w-8 mx-auto mb-2 text-gray-600" />
              <div className="font-medium">Create New Document</div>
              <div className="text-sm text-gray-500 mt-1">
                Create a new Google Doc
              </div>
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {error}
            </div>
          )}

          {mode === 'link' ? (
            <form onSubmit={handleSubmitLink}>
              <div className="mb-4">
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                  Document Title
                </label>
                <input
                  type="text"
                  id="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Voter Outreach Email - District 7"
                  disabled={loading}
                />
              </div>

              <div className="mb-4">
                <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
                  Google Document URL
                </label>
                <input
                  type="url"
                  id="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="https://docs.google.com/document/d/..."
                  disabled={loading}
                />
                <p className="mt-1 text-sm text-gray-500">
                  Supports Google Docs, Sheets, Slides, Forms, and Drive links
                </p>
              </div>

              <div className="mb-6">
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                  Description (Optional)
                </label>
                <textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Brief description of this document..."
                  rows={3}
                  disabled={loading}
                />
              </div>

              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={loading}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Adding...
                    </>
                  ) : (
                    'Add Document Link'
                  )}
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleCreateNew}>
              <div className="mb-4">
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                  Document Title
                </label>
                <input
                  type="text"
                  id="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Voter Outreach Email - District 7"
                  disabled={loading}
                />
              </div>

              <div className="mb-4">
                <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-2">
                  Initial Content (Optional)
                </label>
                <textarea
                  id="content"
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter initial content for your document..."
                  rows={6}
                  disabled={loading}
                />
                <p className="mt-1 text-sm text-gray-500">
                  You can also ask the AI assistant to help create content after the document is created.
                </p>
              </div>

              <div className="mb-6">
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                  Description (Optional)
                </label>
                <textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Brief description of this document..."
                  rows={3}
                  disabled={loading}
                />
              </div>

              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={loading}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Creating...
                    </>
                  ) : (
                    'Create Document'
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default AddDocumentModal;