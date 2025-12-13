import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { FormComponentFactory } from '../components/FormComponents';
import { getForm, editForm, saveForm, undoForm } from '../services/api';
import { useAuth } from '../context/AuthContext';

function FormEditor() {
  const { formId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [form, setForm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // AI assistant state
  const [query, setQuery] = useState('');
  const [documents, setDocuments] = useState([]);
  const [processing, setProcessing] = useState(false);

  // Preview state
  const [previewAnswers, setPreviewAnswers] = useState({});

  // Load form data
  useEffect(() => {
    const loadForm = async () => {
      try {
        const data = await getForm(formId);
        setForm(data);

        // Initialize preview answers
        const initial = {};
        data.schema?.components?.forEach((c) => {
          initial[c.id] = '';
        });
        setPreviewAnswers(initial);
      } catch (err) {
        setError(err.message || 'Failed to load form');
      } finally {
        setLoading(false);
      }
    };

    loadForm();
  }, [formId]);

  // File drop handler
  const onDrop = useCallback((acceptedFiles) => {
    const processFiles = async () => {
      const processed = await Promise.all(
        acceptedFiles.map(async (file) => {
          const content = await readFileAsBase64(file);
          const type = file.type === 'application/pdf' ? 'pdf' : 'text';
          return { name: file.name, type, content };
        })
      );
      setDocuments((prev) => [...prev, ...processed]);
    };
    processFiles();
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/plain': ['.txt'], 'application/pdf': ['.pdf'] },
    maxSize: 10 * 1024 * 1024,
    maxFiles: 5,
  });

  // Remove document
  const removeDocument = (index) => {
    setDocuments((prev) => prev.filter((_, i) => i !== index));
  };

  // Handle AI edit
  const handleAIEdit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!query && documents.length === 0) {
      setError('Please enter instructions or upload documents');
      return;
    }

    setProcessing(true);

    try {
      const result = await editForm(formId, query, documents);
      setForm((prev) => ({
        ...prev,
        schema: result.schema,
        title: result.title || prev.title,
        description: result.description || prev.description,
      }));
      setQuery('');
      setDocuments([]);
      setSuccess('Form updated successfully');

      // Reset preview answers
      const initial = {};
      result.schema?.components?.forEach((c) => {
        initial[c.id] = '';
      });
      setPreviewAnswers(initial);
    } catch (err) {
      setError(err.message || 'Failed to update form');
    } finally {
      setProcessing(false);
    }
  };

  // Handle undo
  const handleUndo = async () => {
    setError('');
    setSuccess('');
    setSaving(true);

    try {
      const result = await undoForm(formId);
      if (result.success) {
        setForm((prev) => ({
          ...prev,
          schema: result.schema,
        }));
        setSuccess('Reverted to previous version');
      } else {
        setError(result.message || 'Cannot undo further');
      }
    } catch (err) {
      setError(err.message || 'Failed to undo');
    } finally {
      setSaving(false);
    }
  };

  // Handle manual save
  const handleSave = async () => {
    setError('');
    setSuccess('');
    setSaving(true);

    try {
      await saveForm(formId, form.schema, 'Manual save');
      setSuccess('Form saved successfully');
    } catch (err) {
      setError(err.message || 'Failed to save form');
    } finally {
      setSaving(false);
    }
  };

  // Copy share link
  const copyShareLink = () => {
    const link = `${window.location.origin}/${formId}`;
    navigator.clipboard.writeText(link);
    setSuccess('Share link copied to clipboard');
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="spinner w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <Link to="/" className="text-2xl font-bold text-primary-600">
                FormFlow
              </Link>
              <span className="text-gray-300">|</span>
              <h1 className="text-lg font-medium text-gray-900 truncate max-w-xs">
                {form?.title || 'Untitled Form'}
              </h1>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={handleUndo}
                disabled={saving}
                className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
              >
                Undo
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
              <button
                onClick={copyShareLink}
                className="px-3 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700"
              >
                Share
              </button>
              <Link
                to={`/${formId}/responses`}
                className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Responses
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Messages */}
      {(error || success) && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4">
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">
              {error}
            </div>
          )}
          {success && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-green-600">
              {success}
            </div>
          )}
        </div>
      )}

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Form Preview */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
              <h2 className="text-xl font-semibold text-gray-900">
                {form?.title || 'Untitled Form'}
              </h2>
              {form?.description && (
                <p className="mt-2 text-gray-600">{form.description}</p>
              )}
            </div>

            <div className="space-y-6">
              {form?.schema?.components?.length > 0 ? (
                form.schema.components.map((component) => (
                  <FormComponentFactory
                    key={component.id}
                    component={component}
                    value={previewAnswers[component.id]}
                    onChange={(value) =>
                      setPreviewAnswers((prev) => ({ ...prev, [component.id]: value }))
                    }
                    isEditing={true}
                  />
                ))
              ) : (
                <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                  <svg
                    className="mx-auto h-12 w-12 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No questions yet</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Use the AI assistant to add questions to your form.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* AI Assistant Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6 sticky top-24">
              <h3 className="text-lg font-medium text-gray-900 mb-4">AI Assistant</h3>

              <form onSubmit={handleAIEdit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Edit instructions
                  </label>
                  <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="E.g., Add a question about email address, make question 2 required..."
                  />
                </div>

                {/* File upload */}
                <div
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer ${
                    isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300'
                  }`}
                >
                  <input {...getInputProps()} />
                  <p className="text-sm text-gray-600">
                    {isDragActive ? 'Drop files here' : 'Drop files or click to upload'}
                  </p>
                </div>

                {/* Uploaded files */}
                {documents.length > 0 && (
                  <div className="space-y-2">
                    {documents.map((doc, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-2 bg-gray-50 rounded"
                      >
                        <span className="text-sm text-gray-700 truncate">{doc.name}</span>
                        <button
                          type="button"
                          onClick={() => removeDocument(index)}
                          className="text-gray-400 hover:text-red-500"
                        >
                          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={processing || (!query && documents.length === 0)}
                  className="w-full py-2 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {processing ? (
                    <span className="flex items-center justify-center">
                      <svg className="spinner -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Processing...
                    </span>
                  ) : (
                    'Update Form'
                  )}
                </button>
              </form>

              {/* Quick actions */}
              <div className="mt-6 pt-6 border-t border-gray-200">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Quick actions</h4>
                <div className="space-y-2">
                  <button
                    onClick={() => setQuery('Add a question asking for email address')}
                    className="w-full text-left px-3 py-2 text-sm text-gray-600 bg-gray-50 rounded hover:bg-gray-100"
                  >
                    + Add email question
                  </button>
                  <button
                    onClick={() => setQuery('Add a multiple choice question about satisfaction (Very Satisfied, Satisfied, Neutral, Dissatisfied)')}
                    className="w-full text-left px-3 py-2 text-sm text-gray-600 bg-gray-50 rounded hover:bg-gray-100"
                  >
                    + Add satisfaction rating
                  </button>
                  <button
                    onClick={() => setQuery('Make all questions required')}
                    className="w-full text-left px-3 py-2 text-sm text-gray-600 bg-gray-50 rounded hover:bg-gray-100"
                  >
                    Make all required
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

// Helper function
function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const base64 = reader.result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export default FormEditor;
