/**
 * Tests for DiffQuestionComponent
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import DiffQuestionComponent from '../../components/FormComponents/DiffQuestionComponent';

describe('DiffQuestionComponent', () => {
  const mockShortAnswerComponent = {
    id: 'comp_1',
    type: 'short-answer',
    data: {
      question: 'What is your name?',
      required: true
    }
  };

  const mockMultipleChoiceComponent = {
    id: 'comp_2',
    type: 'multiple-choice',
    data: {
      question: 'Select your preference',
      options: ['Option A', 'Option B', 'Option C'],
      required: false
    }
  };

  test('renders added short answer component', () => {
    render(<DiffQuestionComponent component={mockShortAnswerComponent} type="added" />);
    
    expect(screen.getByText('What is your name?')).toBeInTheDocument();
    expect(screen.getByText('+ ADDED')).toBeInTheDocument();
    expect(screen.getByText(/Short Answer/)).toBeInTheDocument();
    expect(screen.getByText(/Required/)).toBeInTheDocument();
  });

  test('renders removed short answer component with strikethrough', () => {
    render(<DiffQuestionComponent component={mockShortAnswerComponent} type="removed" />);
    
    const questionText = screen.getByText('What is your name?');
    expect(questionText).toHaveClass('line-through');
    expect(screen.getByText('- REMOVED')).toBeInTheDocument();
  });

  test('renders added multiple choice component with options', () => {
    render(<DiffQuestionComponent component={mockMultipleChoiceComponent} type="added" />);
    
    expect(screen.getByText('Select your preference')).toBeInTheDocument();
    expect(screen.getByText('Option A')).toBeInTheDocument();
    expect(screen.getByText('Option B')).toBeInTheDocument();
    expect(screen.getByText('Option C')).toBeInTheDocument();
  });

  test('renders removed multiple choice with strikethrough options', () => {
    render(<DiffQuestionComponent component={mockMultipleChoiceComponent} type="removed" />);
    
    const optionA = screen.getByText('Option A');
    expect(optionA).toHaveClass('line-through');
  });

  test('applies correct styling for added type', () => {
    const { container } = render(
      <DiffQuestionComponent component={mockShortAnswerComponent} type="added" />
    );
    
    const mainDiv = container.firstChild;
    expect(mainDiv).toHaveClass('bg-green-50');
    expect(mainDiv).toHaveClass('border-green-400');
  });

  test('applies correct styling for removed type', () => {
    const { container } = render(
      <DiffQuestionComponent component={mockShortAnswerComponent} type="removed" />
    );
    
    const mainDiv = container.firstChild;
    expect(mainDiv).toHaveClass('bg-red-50');
    expect(mainDiv).toHaveClass('border-red-400');
  });
});
