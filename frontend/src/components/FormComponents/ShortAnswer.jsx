import React from 'react';

function ShortAnswer({
  question,
  required = false,
  maxLength,
  value = '',
  onChange,
  isEditing = false,
  disabled = false,
  placeholder = 'Type your answer here...',
}) {
  const handleChange = (e) => {
    if (disabled) return;

    const newValue = e.target.value;
    if (maxLength && newValue.length > maxLength) {
      return;
    }
    onChange(newValue);
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="mb-4">
        <label className="block text-lg font-medium text-gray-900">
          {question}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      </div>

      <div className="relative">
        <textarea
          value={value}
          onChange={handleChange}
          disabled={disabled}
          placeholder={placeholder}
          rows={3}
          maxLength={maxLength}
          className={`w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none transition-colors ${
            disabled ? 'bg-gray-50 cursor-not-allowed' : 'bg-white'
          }`}
        />
        {maxLength && (
          <div className="absolute bottom-2 right-2 text-xs text-gray-400">
            {value.length}/{maxLength}
          </div>
        )}
      </div>

      {isEditing && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-400">
            Component type: Short Answer
            {maxLength && ` | Max length: ${maxLength}`}
          </p>
        </div>
      )}
    </div>
  );
}

export default ShortAnswer;
