import React from 'react';

function DiffQuestionComponent({ component, type }) {
  const { data } = component;
  const question = data?.question || '';
  const options = data?.options || [];
  const required = data?.required || false;
  const componentType = component?.type || '';

  const styles = {
    added: {
      bg: 'bg-green-50',
      border: 'border-green-400',
      textColor: 'text-green-900',
      label: 'bg-green-100 text-green-800',
      optionBg: 'bg-green-100',
      heading: 'text-green-700'
    },
    removed: {
      bg: 'bg-red-50',
      border: 'border-red-400',
      textColor: 'text-red-900',
      label: 'bg-red-100 text-red-800',
      optionBg: 'bg-red-100',
      heading: 'text-red-700'
    }
  };

  const style = styles[type] || styles.added;
  const isRemoved = type === 'removed';

  return (
    <div className={`${style.bg} p-6 rounded-lg shadow-sm border-2 ${style.border} mb-4 relative`}>
      {/* Diff indicator badge */}
      <div className="absolute -top-3 -left-3">
        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold ${style.label}`}>
          {isRemoved ? '- REMOVED' : '+ ADDED'}
        </span>
      </div>

      {/* Question text */}
      <div className="mb-4">
        <p className={`text-lg font-medium ${style.textColor} ${isRemoved ? 'line-through opacity-75' : ''}`}>
          {question || 'Question text'}
        </p>
        <p className={`text-sm ${style.heading} mt-1`}>
          {componentType === 'multiple-choice' ? 'Multiple Choice' : 'Short Answer'}
          {required && ' • Required'}
        </p>
      </div>

      {/* Multiple choice options */}
      {componentType === 'multiple-choice' && options.length > 0 && (
        <div className="space-y-2">
          {options.map((option, index) => (
            <div key={index} className="flex items-center space-x-3">
              <div className={`w-4 h-4 rounded-full border-2 ${style.border} flex-shrink-0`} />
              <span className={`text-sm ${style.textColor} ${isRemoved ? 'line-through opacity-75' : ''}`}>
                {option}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Short answer placeholder */}
      {componentType === 'short-answer' && (
        <div className={`border-2 ${style.border} rounded px-3 py-2 ${style.optionBg}`}>
          <span className={`text-sm ${style.textColor} italic ${isRemoved ? 'line-through opacity-75' : ''}`}>
            Short answer text
          </span>
        </div>
      )}
    </div>
  );
}

export default DiffQuestionComponent;
