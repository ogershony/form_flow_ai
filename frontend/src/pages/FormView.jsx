import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { FormComponentFactory } from '../components/FormComponents';
import { getForm, submitFormResponse } from '../services/api';

function FormView() {
  const { formId } = useParams();
  const [form, setForm] = useState(null);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  // Load form data
  useEffect(() => {
    const loadForm = async () => {
      try {
        const data = await getForm(formId);
        setForm(data);

        // Initialize answers
        const initialAnswers = {};
        data.schema?.components?.forEach((component) => {
          initialAnswers[component.id] = component.type === 'multiple-choice' ? '' : '';
        });
        setAnswers(initialAnswers);
      } catch (err) {
        setError(err.message || 'Failed to load form');
      } finally {
        setLoading(false);
      }
    };

    loadForm();
  }, [formId]);

  // Handle answer change
  const handleAnswerChange = (componentId, value) => {
    setAnswers((prev) => ({
      ...prev,
      [componentId]: value,
    }));
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validate required fields
    const missingRequired = form.schema?.components?.filter((component) => {
      if (component.data?.required) {
        const answer = answers[component.id];
        return !answer || (Array.isArray(answer) && answer.length === 0);
      }
      return false;
    });

    if (missingRequired?.length > 0) {
      setError('Please answer all required questions');
      return;
    }

    setSubmitting(true);

    try {
      await submitFormResponse(formId, answers);
      setSubmitted(true);
    } catch (err) {
      setError(err.message || 'Failed to submit response');
    } finally {
      setSubmitting(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="spinner w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading form...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error && !form) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="text-red-500 text-4xl mb-4">!</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Form not found</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <Link to="/" className="text-primary-600 hover:text-primary-500">
            Go to homepage
          </Link>
        </div>
      </div>
    );
  }

  // Success state
  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full mx-auto p-8 bg-white rounded-lg shadow-sm text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            Response Submitted
          </h2>
          <p className="text-gray-600 mb-6">
            Thank you for completing this form.
          </p>
          <button
            onClick={() => {
              setSubmitted(false);
              setAnswers({});
              form.schema?.components?.forEach((component) => {
                setAnswers((prev) => ({
                  ...prev,
                  [component.id]: '',
                }));
              });
            }}
            className="text-primary-600 hover:text-primary-500 font-medium"
          >
            Submit another response
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h1 className="text-2xl font-bold text-gray-900">{form?.title || 'Untitled Form'}</h1>
          {form?.description && (
            <p className="mt-2 text-gray-600">{form.description}</p>
          )}
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div className="space-y-6">
            {form?.schema?.components?.map((component) => (
              <FormComponentFactory
                key={component.id}
                component={component}
                value={answers[component.id]}
                onChange={(value) => handleAnswerChange(component.id, value)}
              />
            ))}
          </div>

          {/* Submit button */}
          {form?.schema?.components?.length > 0 && (
            <div className="mt-8">
              <button
                type="submit"
                disabled={submitting}
                className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? (
                  <span className="flex items-center">
                    <svg className="spinner -ml-1 mr-2 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Submitting...
                  </span>
                ) : (
                  'Submit'
                )}
              </button>
            </div>
          )}
        </form>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>
            Powered by{' '}
            <span className="text-primary-600 font-medium">FormFlow</span>
          </p>
        </div>
      </div>
    </div>
  );
}

export default FormView;
