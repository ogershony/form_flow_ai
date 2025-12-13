import React from 'react';
import MultipleChoice from './MultipleChoice';
import ShortAnswer from './ShortAnswer';

function FormComponentFactory({
  component,
  value,
  onChange,
  isEditing = false,
  disabled = false,
}) {
  if (!component || !component.type || !component.data) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-600">
        Invalid component configuration
      </div>
    );
  }

  const { type, data } = component;

  switch (type) {
    case 'multiple-choice':
      return (
        <MultipleChoice
          question={data.question}
          options={data.options}
          required={data.required}
          allowMultiple={data.allowMultiple}
          value={value}
          onChange={onChange}
          isEditing={isEditing}
          disabled={disabled}
        />
      );

    case 'short-answer':
      return (
        <ShortAnswer
          question={data.question}
          required={data.required}
          maxLength={data.maxLength}
          value={value}
          onChange={onChange}
          isEditing={isEditing}
          disabled={disabled}
        />
      );

    default:
      return (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-yellow-700">
          Unknown component type: {type}
        </div>
      );
  }
}

export default FormComponentFactory;
