import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { FormComponentFactory, QuestionEditor, InsertQuestionButton } from '../components/FormComponents';
import FormDiffView from '../components/FormComponents/FormDiffView';
import { getForm, editForm, saveForm, undoForm, deleteForm } from '../services/api';
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

  // Edit state
  const [editedTitle, setEditedTitle] = useState('');
  const [editedDescription, setEditedDescription] = useState('');
  const [editedComponents, setEditedComponents] = useState([]);

  // AI assistant state
  const [query, setQuery] = useState('');
  const [documents, setDocuments] = useState([]);
  const [processing, setProcessing] = useState(false);

  // AI changes diff mode state
  const [diffMode, setDiffMode] = useState(false);
  const [diffData, setDiffData] = useState({
    diff: null,
    oldComponents: [],
    newComponents: [],
    oldTitle: '',
    oldDescription: ''
  });

  // Load form data
  useEffect(() => {
    const loadForm = async () => {
      try {
        const data = await getForm(formId);
        setForm(data);

        // Initialize edit state
        setEditedTitle(data.title || '');
        setEditedDescription(data.description || '');
        setEditedComponents(data.schema?.components || []);
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
      // Store old state before making changes
      const oldComponents = [...editedComponents];
      const oldTitle = editedTitle;
      const oldDescription = editedDescription;

      const result = await editForm(formId, query, documents);

      // Update form state
      setForm((prev) => ({
        ...prev,
        schema: result.schema,
        title: result.title || prev.title,
        description: result.description || prev.description,
      }));

      // Update edit state
      setEditedTitle(result.title || form.title);
      setEditedDescription(result.description || form.description);
      setEditedComponents(result.schema?.components || []);

      setQuery('');
      setDocuments([]);

      // Enter diff mode if changes exist
      if (result.diff && result.diff.changes && result.diff.changes.length > 0) {
        setDiffMode(true);
        setDiffData({
          diff: result.diff,
          oldComponents: oldComponents,
          newComponents: result.schema?.components || [],
          oldTitle: oldTitle,
          oldDescription: oldDescription
        });
      }

      setSuccess('AI changes ready for review');
    } catch (err) {
      setError(err.message || 'Failed to update form');
    } finally {
      setProcessing(false);
    }
  };

  // Handle accepting AI changes
  const handleAcceptChanges = () => {
    // Simply exit diff mode - changes are already applied
    setDiffMode(false);
    setDiffData({
      diff: null,
      oldComponents: [],
      newComponents: [],
      oldTitle: '',
      oldDescription: ''
    });
    setSuccess('Changes accepted successfully');
  };

  // Handle undoing AI changes
  const handleUndoChanges = async () => {
    setError('');
    setSuccess('');
    setSaving(true);

    try {
      const result = await undoForm(formId);
      if (result.success) {
        // Restore to previous state
        setForm((prev) => ({
          ...prev,
          schema: result.schema,
        }));
        setEditedTitle(form.title);
        setEditedDescription(form.description);
        setEditedComponents(result.schema?.components || []);

        // Exit diff mode
        setDiffMode(false);
        setDiffData({
          diff: null,
          oldComponents: [],
          newComponents: [],
          oldTitle: '',
          oldDescription: ''
        });

        setSuccess('Changes reverted successfully');
      } else {
        setError(result.message || 'Failed to undo changes');
      }
    } catch (err) {
      setError(err.message || 'Failed to undo changes');
    } finally {
      setSaving(false);
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
        setEditedComponents(result.schema?.components || []);
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
      await saveForm(
        formId,
        { components: editedComponents },
        'Manual save',
        editedTitle,
        editedDescription
      );

      // Update form state with saved data
      setForm(prev => ({
        ...prev,
        title: editedTitle,
        description: editedDescription,
        schema: { components: editedComponents }
      }));

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

  // Handle delete
  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this form? This action cannot be undone.')) {
      return;
    }

    setError('');
    setSaving(true);

    try {
      await deleteForm(formId);
      navigate('/');
    } catch (err) {
      setError(err.message || 'Failed to delete form');
      setSaving(false);
    }
  };

  // Edit functions
  const updateComponent = (index, updatedComponent) => {
    const newComponents = [...editedComponents];
    newComponents[index] = updatedComponent;
    setEditedComponents(newComponents);
  };

  const deleteComponent = (index) => {
    setEditedComponents(editedComponents.filter((_, i) => i !== index));
  };

  const moveComponent = (index, direction) => {
    const newComponents = [...editedComponents];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    [newComponents[index], newComponents[targetIndex]] = [newComponents[targetIndex], newComponents[index]];
    setEditedComponents(newComponents);
  };

  const addQuestion = (type, insertIndex = null) => {
    const newId = `question_${Date.now()}`;
    const newComponent = {
      id: newId,
      type,
      data: {
        question: 'New Question',
        required: false,
        ...(type === 'multiple-choice'
          ? { options: ['Option 1', 'Option 2'], allowMultiple: false }
          : { maxLength: null })
      }
    };

    if (insertIndex !== null) {
      // Insert at specific position
      const newComponents = [...editedComponents];
      newComponents.splice(insertIndex, 0, newComponent);
      setEditedComponents(newComponents);
    } else {
      // Add to end
      setEditedComponents([...editedComponents, newComponent]);
    }
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
                {editedTitle || 'Untitled Form'}
              </h1>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={handleDelete}
                disabled={saving}
                className="px-3 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                Delete
              </button>
              <button
                onClick={handleUndo}
                disabled={saving || diffMode}
                className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
              >
                Undo
              </button>
              <button
                onClick={handleSave}
                disabled={saving || diffMode}
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
          {/* Form Edit */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Form Title
                  </label>
                  <input
                    type="text"
                    value={editedTitle}
                    onChange={(e) => setEditedTitle(e.target.value)}
                    disabled={diffMode}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="Untitled Form"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description (optional)
                  </label>
                  <textarea
                    value={editedDescription}
                    onChange={(e) => setEditedDescription(e.target.value)}
                    disabled={diffMode}
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="Add a description for your form"
                  />
                </div>
              </div>
            </div>

            {/* Diff Mode View */}
            {diffMode ? (
              <FormDiffView
                diff={diffData.diff}
                oldComponents={diffData.oldComponents}
                newComponents={diffData.newComponents}
                onAccept={handleAcceptChanges}
                onUndo={handleUndoChanges}
                isProcessing={saving}
              />
            ) : (
              /* Normal Edit Mode */
              <div>
                {editedComponents.length > 0 ? (
                <>
                  {/* Insert at beginning */}
                  <InsertQuestionButton onInsert={(type) => addQuestion(type, 0)} />

                  {editedComponents.map((component, index) => (
                    <React.Fragment key={component.id}>
                      <QuestionEditor
                        component={component}
                        onUpdate={(updated) => updateComponent(index, updated)}
                        onDelete={() => deleteComponent(index)}
                        onMoveUp={() => moveComponent(index, 'up')}
                        onMoveDown={() => moveComponent(index, 'down')}
                        isFirst={index === 0}
                        isLast={index === editedComponents.length - 1}
                      />
                      {/* Insert after this question */}
                      <InsertQuestionButton onInsert={(type) => addQuestion(type, index + 1)} />
                    </React.Fragment>
                  ))}
                </>
              ) : (
                <>
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
                      Use the AI assistant or click below to add questions to your form.
                    </p>
                  </div>

                  {/* Add first question */}
                  <InsertQuestionButton onInsert={(type) => addQuestion(type, 0)} />
                </>
              )}
              </div>
            )}
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
                  disabled={processing || (!query && documents.length === 0) || diffMode}
                  className="w-full py-2 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {diffMode ? (
                    'Review changes first'
                  ) : processing ? (
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
