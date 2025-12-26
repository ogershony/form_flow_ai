import React, { useState } from 'react';

function InsertQuestionButton({ onInsert }) {
  const [isOpen, setIsOpen] = useState(false);

  const handleInsert = (type) => {
    onInsert(type);
    setIsOpen(false);
  };

  return (
    <div className="relative flex justify-center my-4">
      {!isOpen ? (
        <button
          onClick={() => setIsOpen(true)}
          className="group flex items-center space-x-2 px-4 py-2 text-sm font-medium text-gray-500 bg-white border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-400 hover:text-primary-600 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          <span>Insert Question</span>
        </button>
      ) : (
        <div className="flex gap-3 p-3 bg-white border-2 border-primary-300 rounded-lg shadow-sm">
          <button
            onClick={() => handleInsert('short-answer')}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Short Answer
          </button>
          <button
            onClick={() => handleInsert('multiple-choice')}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Multiple Choice
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700"
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}

export default InsertQuestionButton;
