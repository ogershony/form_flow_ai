import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getForm, getFormResponses } from '../services/api';
import { FormComponentFactory } from '../components/FormComponents';

function ResponsesView() {
  const { formId } = useParams();
  const [form, setForm] = useState(null);
  const [responses, setResponses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [jumpToInput, setJumpToInput] = useState('');

  // Load form and responses
  useEffect(() => {
    const loadData = async () => {
      try {
        const [formData, responsesData] = await Promise.all([
          getForm(formId),
          getFormResponses(formId),
        ]);
        setForm(formData);
        const sortedResponses = (responsesData.responses || []).reverse(); // Most recent first
        setResponses(sortedResponses);
        setCurrentIndex(0); // Start with most recent
      } catch (err) {
        setError(err.message || 'Failed to load responses');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [formId]);

  // Navigation functions
  const goToPrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const goToNext = () => {
    if (currentIndex < responses.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handleJumpTo = (e) => {
    e.preventDefault();
    const index = parseInt(jumpToInput) - 1; // Convert 1-based to 0-based
    if (index >= 0 && index < responses.length) {
      setCurrentIndex(index);
      setJumpToInput('');
    }
  };

  // Format answer for display (for CSV export)
  const formatAnswer = (answer) => {
    if (Array.isArray(answer)) {
      return answer.join(', ');
    }
    return answer || '-';
  };

  // Export to CSV
  const exportToCSV = () => {
    if (!responses.length || !form?.schema?.components) return;

    const components = form.schema.components;
    const headers = ['Response #', 'Submitted At', ...components.map((c) => c.data?.question || c.id)];

    const rows = responses.map((response, index) => {
      const row = [
        responses.length - index, // Show as 1-based index
        new Date(response.submittedAt).toLocaleString(),
        ...components.map((c) => formatAnswer(response.answers?.[c.id])),
      ];
      return row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(',');
    });

    const csv = [headers.map((h) => `"${h}"`).join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${form.title || 'form'}-responses.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const currentResponse = responses[currentIndex];

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="spinner w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <Link to="/" className="text-2xl font-bold text-primary-600">
                FormFlow
              </Link>
              <span className="text-gray-300">|</span>
              <h1 className="text-lg font-medium text-gray-900">
                {form?.title || 'Untitled Form'} - Responses
              </h1>
            </div>
            <div className="flex items-center space-x-3">
              <Link
                to={`/${formId}/edit`}
                className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Edit Form
              </Link>
              <button
                onClick={exportToCSV}
                disabled={responses.length === 0}
                className="px-3 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                Export CSV
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">
            {error}
          </div>
        )}

        {/* Summary */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-sm text-gray-500">Total Responses</p>
              <p className="text-3xl font-bold text-gray-900">{responses.length}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Questions</p>
              <p className="text-3xl font-bold text-gray-900">
                {form?.schema?.components?.length || 0}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Most Recent Response</p>
              <p className="text-lg font-medium text-gray-900">
                {responses.length > 0
                  ? new Date(responses[0].submittedAt).toLocaleDateString()
                  : 'No responses yet'}
              </p>
            </div>
          </div>
        </div>

        {/* Response Navigation and Viewer */}
        {responses.length > 0 ? (
          <>
            {/* Navigation Controls */}
            <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
              <div className="flex items-center justify-between">
                <button
                  onClick={goToPrevious}
                  disabled={currentIndex === 0}
                  className="p-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label="Previous response"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                </button>

                <div className="flex items-center space-x-4">
                  <span className="text-sm font-medium text-gray-900">
                    Response {currentIndex + 1} of {responses.length}
                  </span>

                  <form onSubmit={handleJumpTo} className="flex items-center space-x-2">
                    <label htmlFor="jump-to" className="text-sm text-gray-600">
                      Jump to:
                    </label>
                    <input
                      id="jump-to"
                      type="number"
                      min="1"
                      max={responses.length}
                      value={jumpToInput}
                      onChange={(e) => setJumpToInput(e.target.value)}
                      placeholder="#"
                      className="w-16 px-2 py-1 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                    <button
                      type="submit"
                      className="px-3 py-1 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700"
                    >
                      Go
                    </button>
                  </form>

                  <span className="text-xs text-gray-500">
                    Submitted: {new Date(currentResponse.submittedAt).toLocaleString()}
                  </span>
                </div>

                <button
                  onClick={goToNext}
                  disabled={currentIndex === responses.length - 1}
                  className="p-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label="Next response"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Response Viewer - Form-like Display */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-gray-900">
                  {form?.title || 'Untitled Form'}
                </h2>
                {form?.description && (
                  <p className="mt-2 text-gray-600">{form.description}</p>
                )}
              </div>

              <div className="space-y-6">
                {form?.schema?.components?.map((component) => (
                  <FormComponentFactory
                    key={component.id}
                    component={component}
                    value={currentResponse.answers?.[component.id] || ''}
                    onChange={() => {}} // No-op since it's disabled
                    disabled={true}
                  />
                ))}
              </div>
            </div>
          </>
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
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No responses yet</h3>
            <p className="mt-1 text-sm text-gray-500">
              Share your form to start collecting responses.
            </p>
            <div className="mt-6">
              <button
                onClick={() => {
                  const link = `${window.location.origin}/${formId}`;
                  navigator.clipboard.writeText(link);
                }}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
              >
                Copy Share Link
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default ResponsesView;
