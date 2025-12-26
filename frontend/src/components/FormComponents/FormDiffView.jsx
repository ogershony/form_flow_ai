import React from 'react';
import DiffQuestionComponent from './DiffQuestionComponent';

function FormDiffView({ diff, oldComponents, newComponents, onAccept, onUndo, isProcessing }) {
  if (!diff || !diff.changes) return null;

  // Build a merged view of all components showing changes
  const buildDiffView = () => {
    const oldMap = {};
    const newMap = {};

    oldComponents.forEach((comp, idx) => {
      oldMap[comp.id] = { component: comp, index: idx };
    });

    newComponents.forEach((comp, idx) => {
      newMap[comp.id] = { component: comp, index: idx };
    });

    const diffItems = [];

    // Track which components we've already processed
    const processed = new Set();

    // Process changes in order
    diff.changes.forEach((change) => {
      if (change.type === 'metadata') {
        // Skip metadata changes for component view
        return;
      }

      if (change.type === 'removed') {
        diffItems.push({
          type: 'removed',
          component: change.component,
          key: `removed-${change.componentId}`
        });
        processed.add(change.componentId);
      } else if (change.type === 'added') {
        diffItems.push({
          type: 'added',
          component: change.component,
          key: `added-${change.componentId}`
        });
        processed.add(change.componentId);
      } else if (change.type === 'modified') {
        // Show old version (red) then new version (green)
        diffItems.push({
          type: 'removed',
          component: change.before,
          key: `modified-before-${change.componentId}`
        });
        diffItems.push({
          type: 'added',
          component: change.after,
          key: `modified-after-${change.componentId}`
        });
        processed.add(change.componentId);
      }
    });

    // Add any unchanged components (shouldn't happen if diff is correct, but just in case)
    newComponents.forEach((comp) => {
      if (!processed.has(comp.id)) {
        // This component is unchanged, show it normally
        diffItems.push({
          type: 'unchanged',
          component: comp,
          key: `unchanged-${comp.id}`
        });
      }
    });

    return diffItems;
  };

  const diffItems = buildDiffView();
  const hasMetadataChanges = diff.changes.some(c => c.type === 'metadata');

  return (
    <div className="mb-6">
      {/* Action bar */}
      <div className="bg-blue-600 text-white rounded-t-lg px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold flex items-center">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              AI Changes - Review & Accept
            </h2>
            <p className="text-sm text-blue-100 mt-1">{diff.summary}</p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={onUndo}
              disabled={isProcessing}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Undo Changes
            </button>
            <button
              onClick={onAccept}
              disabled={isProcessing}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Accept Changes
            </button>
          </div>
        </div>
      </div>

      {/* Metadata changes */}
      {hasMetadataChanges && (
        <div className="bg-blue-50 border-x-2 border-blue-200 px-6 py-4">
          <h3 className="text-sm font-semibold text-blue-900 mb-2">Form Metadata Changes:</h3>
          <div className="space-y-2">
            {diff.changes.filter(c => c.type === 'metadata').map((change, idx) => (
              <div key={idx} className="text-sm">
                <span className="font-medium text-blue-800">
                  {change.field === 'title' ? 'Title' : 'Description'}:
                </span>
                {change.before && (
                  <div className="ml-4 text-red-700">
                    <span className="font-mono">- </span>
                    <span className="line-through">{change.before}</span>
                  </div>
                )}
                {change.after && (
                  <div className="ml-4 text-green-700">
                    <span className="font-mono">+ </span>
                    <span>{change.after}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Diff view */}
      <div className="bg-gray-50 border-x-2 border-b-2 border-blue-200 rounded-b-lg px-6 py-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Question Changes:</h3>
        {diffItems.length > 0 ? (
          <div>
            {diffItems.map((item) => {
              if (item.type === 'unchanged') {
                // Show unchanged component in normal style
                return (
                  <div key={item.key} className="bg-white p-6 rounded-lg shadow-sm border-2 border-gray-200 mb-4">
                    <div className="mb-2">
                      <p className="text-lg font-medium text-gray-900">
                        {item.component.data?.question || 'Question text'}
                      </p>
                      <p className="text-sm text-gray-600 mt-1">
                        {item.component.type === 'multiple-choice' ? 'Multiple Choice' : 'Short Answer'}
                        {item.component.data?.required && ' • Required'}
                      </p>
                    </div>
                    {item.component.type === 'multiple-choice' && item.component.data?.options && (
                      <div className="space-y-2">
                        {item.component.data.options.map((option, index) => (
                          <div key={index} className="flex items-center space-x-3">
                            <div className="w-4 h-4 rounded-full border-2 border-gray-400 flex-shrink-0" />
                            <span className="text-sm text-gray-700">{option}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              } else {
                return (
                  <DiffQuestionComponent
                    key={item.key}
                    component={item.component}
                    type={item.type}
                  />
                );
              }
            })}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No component changes detected.</p>
        )}
      </div>

      {/* Helper text */}
      <div className="mt-3 px-2">
        <p className="text-xs text-gray-600">
          <span className="font-semibold">Review the changes above:</span> Green components are added,
          red components are removed. Click "Accept Changes" to keep them or "Undo Changes" to revert.
        </p>
      </div>
    </div>
  );
}

export default FormDiffView;
