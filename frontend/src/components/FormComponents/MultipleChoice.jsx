import React from 'react';

function MultipleChoice({
  question,
  options = [],
  required = false,
  allowMultiple = false,
  value,
  onChange,
  isEditing = false,
  disabled = false,
}) {
  const handleChange = (option) => {
    if (disabled) return;

    if (allowMultiple) {
      // Handle multiple selection
      const currentValue = Array.isArray(value) ? value : [];
      if (currentValue.includes(option)) {
        onChange(currentValue.filter((v) => v !== option));
      } else {
        onChange([...currentValue, option]);
      }
    } else {
      // Single selection
      onChange(option);
    }
  };

  const isSelected = (option) => {
    if (allowMultiple) {
      return Array.isArray(value) && value.includes(option);
    }
    return value === option;
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="mb-4">
        <label className="block text-lg font-medium text-gray-900">
          {question}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
        {allowMultiple && (
          <p className="text-sm text-gray-500 mt-1">Select all that apply</p>
        )}
      </div>

      <div className="space-y-3">
        {options.map((option, index) => (
          <label
            key={index}
            className={`flex items-center p-3 rounded-lg border cursor-pointer transition-colors ${
              isSelected(option)
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-200 hover:border-gray-300'
            } ${disabled ? 'cursor-not-allowed opacity-60' : ''}`}
          >
            <input
              type={allowMultiple ? 'checkbox' : 'radio'}
              name={question}
              checked={isSelected(option)}
              onChange={() => handleChange(option)}
              disabled={disabled}
              className={`${
                allowMultiple
                  ? 'h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500'
                  : 'h-4 w-4 border-gray-300 text-primary-600 focus:ring-primary-500'
              }`}
            />
            <span className="ml-3 text-gray-700">{option}</span>
          </label>
        ))}
      </div>

      {isEditing && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-400">
            Component type: Multiple Choice | Options: {options.length}
          </p>
        </div>
      )}
    </div>
  );
}

export default MultipleChoice;
