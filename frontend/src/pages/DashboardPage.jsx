import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { listForms } from '../services/api';

function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [forms, setForms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Load user's forms
  useEffect(() => {
    const loadForms = async () => {
      try {
        const data = await listForms();
        setForms(data.forms || []);
      } catch (err) {
        setError(err.message || 'Failed to load forms');
      } finally {
        setLoading(false);
      }
    };

    loadForms();
  }, []);

  // Handle logout
  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  // Format date
  const formatDate = (timestamp) => {
    if (!timestamp) return 'Unknown';
    const date = timestamp.toDate ? timestamp.toDate() : new Date(timestamp);
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <Link to="/" className="text-2xl font-bold text-primary-600">
            FormFlow
          </Link>
          <div className="flex items-center space-x-4">
            <span className="text-gray-500">{user?.email}</span>
            <button
              onClick={handleLogout}
              className="text-gray-600 hover:text-gray-900 font-medium"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">My Forms</h1>
            <p className="mt-1 text-gray-600">Manage and view your forms</p>
          </div>
          <Link
            to="/"
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
          >
            <svg
              className="-ml-1 mr-2 h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            Create New Form
          </Link>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">
            {error}
          </div>
        )}

        {/* Loading state */}
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="spinner w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
          </div>
        ) : forms.length > 0 ? (
          /* Forms grid */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {forms.map((form) => (
              <div
                key={form.formId}
                className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
              >
                <div className="p-6">
                  <h3 className="text-lg font-medium text-gray-900 truncate">
                    {form.title || 'Untitled Form'}
                  </h3>
                  {form.description && (
                    <p className="mt-1 text-sm text-gray-500 line-clamp-2">
                      {form.description}
                    </p>
                  )}
                  <div className="mt-4 flex items-center text-sm text-gray-500">
                    <svg
                      className="mr-1.5 h-4 w-4"
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
                    {form.responseCount || 0} responses
                  </div>
                  <div className="mt-1 text-xs text-gray-400">
                    Updated {formatDate(form.updatedAt)}
                  </div>
                </div>
                <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 flex justify-between">
                  <Link
                    to={`/${form.formId}/edit`}
                    className="text-sm font-medium text-primary-600 hover:text-primary-500"
                  >
                    Edit
                  </Link>
                  <Link
                    to={`/${form.formId}/responses`}
                    className="text-sm font-medium text-gray-600 hover:text-gray-500"
                  >
                    Responses
                  </Link>
                  <button
                    onClick={() => {
                      const link = `${window.location.origin}/${form.formId}`;
                      navigator.clipboard.writeText(link);
                    }}
                    className="text-sm font-medium text-gray-600 hover:text-gray-500"
                  >
                    Share
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          /* Empty state */
          <div className="text-center py-12">
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
            <h3 className="mt-2 text-sm font-medium text-gray-900">No forms yet</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by creating your first form.
            </p>
            <div className="mt-6">
              <Link
                to="/"
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
              >
                <svg
                  className="-ml-1 mr-2 h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                Create Form
              </Link>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default DashboardPage;
