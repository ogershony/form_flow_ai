/**
 * Tests for FormDiffView
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import FormDiffView from '../../components/FormComponents/FormDiffView';

describe('FormDiffView', () => {
  const mockDiff = {
    summary: 'Added 1 component(s); Removed 1 component(s)',
    changes: [
      {
        type: 'removed',
        componentId: 'comp_1',
        component: {
          id: 'comp_1',
          type: 'short-answer',
          data: {
            question: 'Old question?',
            required: false
          }
        },
        details: 'Removed short answer question'
      },
      {
        type: 'added',
        componentId: 'comp_2',
        component: {
          id: 'comp_2',
          type: 'short-answer',
          data: {
            question: 'New question?',
            required: true
          }
        },
        details: 'Added short answer question'
      }
    ]
  };

  const mockOldComponents = [
    {
      id: 'comp_1',
      type: 'short-answer',
      data: {
        question: 'Old question?',
        required: false
      }
    }
  ];

  const mockNewComponents = [
    {
      id: 'comp_2',
      type: 'short-answer',
      data: {
        question: 'New question?',
        required: true
      }
    }
  ];

  const mockOnAccept = jest.fn();
  const mockOnUndo = jest.fn();

  beforeEach(() => {
    mockOnAccept.mockClear();
    mockOnUndo.mockClear();
  });

  test('renders diff view with summary', () => {
    render(
      <FormDiffView
        diff={mockDiff}
        oldComponents={mockOldComponents}
        newComponents={mockNewComponents}
        onAccept={mockOnAccept}
        onUndo={mockOnUndo}
        isProcessing={false}
      />
    );

    expect(screen.getByText(/AI Changes - Review & Accept/)).toBeInTheDocument();
    expect(screen.getByText('Added 1 component(s); Removed 1 component(s)')).toBeInTheDocument();
  });

  test('renders accept and undo buttons', () => {
    render(
      <FormDiffView
        diff={mockDiff}
        oldComponents={mockOldComponents}
        newComponents={mockNewComponents}
        onAccept={mockOnAccept}
        onUndo={mockOnUndo}
        isProcessing={false}
      />
    );

    expect(screen.getByText('Accept Changes')).toBeInTheDocument();
    expect(screen.getByText('Undo Changes')).toBeInTheDocument();
  });

  test('calls onAccept when Accept Changes button is clicked', () => {
    render(
      <FormDiffView
        diff={mockDiff}
        oldComponents={mockOldComponents}
        newComponents={mockNewComponents}
        onAccept={mockOnAccept}
        onUndo={mockOnUndo}
        isProcessing={false}
      />
    );

    const acceptButton = screen.getByText('Accept Changes');
    fireEvent.click(acceptButton);
    
    expect(mockOnAccept).toHaveBeenCalledTimes(1);
  });

  test('calls onUndo when Undo Changes button is clicked', () => {
    render(
      <FormDiffView
        diff={mockDiff}
        oldComponents={mockOldComponents}
        newComponents={mockNewComponents}
        onAccept={mockOnAccept}
        onUndo={mockOnUndo}
        isProcessing={false}
      />
    );

    const undoButton = screen.getByText('Undo Changes');
    fireEvent.click(undoButton);
    
    expect(mockOnUndo).toHaveBeenCalledTimes(1);
  });

  test('disables buttons when processing', () => {
    render(
      <FormDiffView
        diff={mockDiff}
        oldComponents={mockOldComponents}
        newComponents={mockNewComponents}
        onAccept={mockOnAccept}
        onUndo={mockOnUndo}
        isProcessing={true}
      />
    );

    const acceptButton = screen.getByText('Accept Changes');
    const undoButton = screen.getByText('Undo Changes');
    
    expect(acceptButton).toBeDisabled();
    expect(undoButton).toBeDisabled();
  });

  test('renders removed and added components', () => {
    render(
      <FormDiffView
        diff={mockDiff}
        oldComponents={mockOldComponents}
        newComponents={mockNewComponents}
        onAccept={mockOnAccept}
        onUndo={mockOnUndo}
        isProcessing={false}
      />
    );

    expect(screen.getByText('Old question?')).toBeInTheDocument();
    expect(screen.getByText('New question?')).toBeInTheDocument();
    expect(screen.getByText('- REMOVED')).toBeInTheDocument();
    expect(screen.getByText('+ ADDED')).toBeInTheDocument();
  });

  test('renders null when no diff provided', () => {
    const { container } = render(
      <FormDiffView
        diff={null}
        oldComponents={[]}
        newComponents={[]}
        onAccept={mockOnAccept}
        onUndo={mockOnUndo}
        isProcessing={false}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  test('renders metadata changes when present', () => {
    const diffWithMetadata = {
      ...mockDiff,
      changes: [
        ...mockDiff.changes,
        {
          type: 'metadata',
          field: 'title',
          before: 'Old Title',
          after: 'New Title',
          details: 'Changed form title'
        }
      ]
    };

    render(
      <FormDiffView
        diff={diffWithMetadata}
        oldComponents={mockOldComponents}
        newComponents={mockNewComponents}
        onAccept={mockOnAccept}
        onUndo={mockOnUndo}
        isProcessing={false}
      />
    );

    expect(screen.getByText('Form Metadata Changes:')).toBeInTheDocument();
    expect(screen.getByText(/Old Title/)).toBeInTheDocument();
    expect(screen.getByText(/New Title/)).toBeInTheDocument();
  });
});
