import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getForm, getFormResponses } from '../services/api';

function ResponsesView() {
  const { formId } = useParams();
  const [form, setForm] = useState(null);
  const [responses, setResponses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Load form and responses
  useEffect(() => {
    const loadData = async () => {
      try {
        const [formData, responsesData] = await Promise.all([
          getForm(formId),
          getFormResponses(formId),
        ]);
        setForm(formData);
        setResponses(responsesData.responses || []);
      } catch (err) {
        setError(err.message || 'Failed to load responses');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [formId]);

  // Get question text by component ID
  const getQuestionText = (componentId) => {
    const component = form?.schema?.components?.find((c) => c.id === componentId);
    return component?.data?.question || componentId;
  };

  // Format answer for display
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
    const headers = ['Response ID', 'Submitted At', ...components.map((c) => c.data?.question || c.id)];

    const rows = responses.map((response) => {
      const row = [
        response.responseId,
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
              <p className="text-sm text-gray-500">Last Response</p>
              <p className="text-lg font-medium text-gray-900">
                {responses.length > 0
                  ? new Date(responses[responses.length - 1].submittedAt).toLocaleDateString()
                  : 'No responses yet'}
              </p>
            </div>
          </div>
        </div>

        {/* Responses table */}
        {responses.length > 0 ? (
          <div className="bg-white rounded-lg shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      #
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Submitted
                    </th>
                    {form?.schema?.components?.map((component) => (
                      <th
                        key={component.id}
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider max-w-xs truncate"
                      >
                        {component.data?.question || component.id}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {responses.map((response, index) => (
                    <tr key={response.responseId} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {index + 1}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(response.submittedAt).toLocaleString()}
                      </td>
                      {form?.schema?.components?.map((component) => (
                        <td
                          key={component.id}
                          className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate"
                        >
                          {formatAnswer(response.answers?.[component.id])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
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

        {/* Individual response cards for small screens */}
        {responses.length > 0 && (
          <div className="mt-6 lg:hidden space-y-4">
            {responses.map((response, index) => (
              <div key={response.responseId} className="bg-white rounded-lg shadow-sm p-4">
                <div className="flex justify-between items-center mb-4">
                  <span className="text-sm font-medium text-gray-900">
                    Response #{index + 1}
                  </span>
                  <span className="text-sm text-gray-500">
                    {new Date(response.submittedAt).toLocaleString()}
                  </span>
                </div>
                <div className="space-y-3">
                  {form?.schema?.components?.map((component) => (
                    <div key={component.id}>
                      <p className="text-xs text-gray-500">
                        {component.data?.question || component.id}
                      </p>
                      <p className="text-sm text-gray-900">
                        {formatAnswer(response.answers?.[component.id])}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default ResponsesView;
