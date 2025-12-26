import React from 'react';

function QuestionEditor({ component, onUpdate, onDelete, onMoveUp, onMoveDown, isFirst, isLast }) {
  const { type, data } = component;

  const updateData = (field, value) => {
    onUpdate({
      ...component,
      data: {
        ...data,
        [field]: value,
      },
    });
  };

  const updateOption = (index, value) => {
    const newOptions = [...(data.options || [])];
    newOptions[index] = value;
    updateData('options', newOptions);
  };

  const addOption = () => {
    const newOptions = [...(data.options || []), ''];
    updateData('options', newOptions);
  };

  const removeOption = (index) => {
    const newOptions = (data.options || []).filter((_, i) => i !== index);
    updateData('options', newOptions);
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border-2 border-primary-300">
      {/* Question Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <input
            type="text"
            value={data.question || ''}
            onChange={(e) => updateData('question', e.target.value)}
            className="w-full text-lg font-medium border-0 border-b-2 border-gray-300 focus:border-primary-500 focus:ring-0 px-0"
            placeholder="Question text"
          />
        </div>
        <div className="flex items-center space-x-2 ml-4">
          <button
            onClick={onMoveUp}
            disabled={isFirst}
            className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
            title="Move up"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
            </svg>
          </button>
          <button
            onClick={onMoveDown}
            disabled={isLast}
            className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
            title="Move down"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <button
            onClick={onDelete}
            className="p-1 text-red-400 hover:text-red-600"
            title="Delete question"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>

      {/* Basic Settings */}
      <div className="flex items-center space-x-4 mb-4">
        <span className="text-sm text-gray-600">
          Type: <span className="font-medium">{type === 'multiple-choice' ? 'Multiple Choice' : 'Short Answer'}</span>
        </span>
        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            checked={data.required || false}
            onChange={(e) => updateData('required', e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
          />
          <span className="text-sm text-gray-700">Required</span>
        </label>
        {type === 'multiple-choice' && (
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={data.allowMultiple || false}
              onChange={(e) => updateData('allowMultiple', e.target.checked)}
              className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-gray-700">Allow multiple</span>
          </label>
        )}
      </div>

      {/* Multiple Choice Options - Always visible */}
      {type === 'multiple-choice' && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <label className="block text-sm font-medium text-gray-700 mb-2">Options:</label>
          <div className="space-y-2">
            {(data.options || []).map((option, index) => (
              <div key={index} className="flex items-center space-x-2">
                <input
                  type="text"
                  value={option}
                  onChange={(e) => updateOption(index, e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder={`Option ${index + 1}`}
                />
                <button
                  onClick={() => removeOption(index)}
                  className="p-2 text-red-400 hover:text-red-600"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
          <button
            onClick={addOption}
            className="mt-2 text-sm text-primary-600 hover:text-primary-700"
          >
            + Add option
          </button>
        </div>
      )}

      {/* Short Answer Settings */}
      {type === 'short-answer' && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Max Length (optional):
          </label>
          <input
            type="number"
            value={data.maxLength || ''}
            onChange={(e) => updateData('maxLength', e.target.value ? parseInt(e.target.value) : null)}
            className="w-32 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            placeholder="No limit"
            min="1"
          />
        </div>
      )}
    </div>
  );
}

export default QuestionEditor;
