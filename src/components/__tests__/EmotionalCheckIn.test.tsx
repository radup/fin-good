import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import EmotionalCheckIn from '../../../components/EmotionalCheckIn';

// Mock DrSigmundSpendAvatar component
jest.mock('../../../components/DrSigmundSpendAvatar', () => ({
  __esModule: true,
  default: ({ mood, message, showMessage }: any) => (
    <div data-testid="dr-sigmund-avatar" data-mood={mood} data-message={message}>
      {showMessage && <span>{message}</span>}
    </div>
  ),
}));

const mockAchievements = [
  {
    id: '1',
    type: 'savings' as const,
    title: 'First Savings Goal',
    description: 'You saved $500 this month!',
    timestamp: new Date('2024-01-15'),
    value: 500
  },
  {
    id: '2',
    type: 'categorization' as const,
    title: 'Organized Finances',
    description: 'You categorized 50 transactions',
    timestamp: new Date('2024-01-14'),
    value: 50
  }
];

describe('EmotionalCheckIn Component', () => {
  const mockOnMoodSubmit = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initial Render', () => {
    it('renders quick mood check button when no mood is set', () => {
      render(<EmotionalCheckIn onMoodSubmit={mockOnMoodSubmit} />);
      
      expect(screen.getByText('How are you feeling today?')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /how are you feeling today/i })).toBeInTheDocument();
    });

    it('renders with achievements when provided', () => {
      render(<EmotionalCheckIn achievements={mockAchievements} onMoodSubmit={mockOnMoodSubmit} />);
      
      // Should show nudges based on achievements
      expect(screen.getByText(/You've achieved 2 financial milestones this week!/)).toBeInTheDocument();
    });
  });

  describe('Mood Check-in Flow', () => {
    it('opens mood check-in when button is clicked', () => {
      render(<EmotionalCheckIn onMoodSubmit={mockOnMoodSubmit} />);
      
      fireEvent.click(screen.getByRole('button', { name: /how are you feeling today/i }));
      
      expect(screen.getByText('How are you feeling?')).toBeInTheDocument();
      expect(screen.getByText('Stress Level (1-10)')).toBeInTheDocument();
      expect(screen.getByText('What\'s on your mind? (Optional)')).toBeInTheDocument();
    });

    it('displays all mood options', () => {
      render(<EmotionalCheckIn onMoodSubmit={mockOnMoodSubmit} />);
      
      fireEvent.click(screen.getByRole('button', { name: /how are you feeling today/i }));
      
      expect(screen.getByText('Great!')).toBeInTheDocument();
      expect(screen.getByText('Good')).toBeInTheDocument();
      expect(screen.getByText('Okay')).toBeInTheDocument();
      expect(screen.getByText('Stressed')).toBeInTheDocument();
      expect(screen.getByText('Overwhelmed')).toBeInTheDocument();
    });

    it('submits mood when option is selected', async () => {
      render(<EmotionalCheckIn onMoodSubmit={mockOnMoodSubmit} />);
      
      fireEvent.click(screen.getByRole('button', { name: /how are you feeling today/i }));
      fireEvent.click(screen.getByText('Great!'));
      
      await waitFor(() => {
        expect(mockOnMoodSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            mood: 'great',
            timestamp: expect.any(Date),
            stressLevel: 5
          })
        );
      });
    });

    it('allows stress level adjustment', () => {
      render(<EmotionalCheckIn onMoodSubmit={mockOnMoodSubmit} />);
      
      fireEvent.click(screen.getByRole('button', { name: /how are you feeling today/i }));
      
      const stressSlider = screen.getByRole('slider');
      expect(stressSlider).toHaveValue('5');
      
      fireEvent.change(stressSlider, { target: { value: '8' } });
      expect(stressSlider).toHaveValue('8');
    });

    it('shows stress intervention for high stress levels', () => {
      render(<EmotionalCheckIn onMoodSubmit={mockOnMoodSubmit} />);
      
      fireEvent.click(screen.getByRole('button', { name: /how are you feeling today/i }));
      
      const stressSlider = screen.getByRole('slider');
      fireEvent.change(stressSlider, { target: { value: '8' } });
      
      expect(screen.getByText(/Your feelings are valid. Consider reaching out to a friend/)).toBeInTheDocument();
    });

    it('allows financial context input', () => {
      render(<EmotionalCheckIn onMoodSubmit={mockOnMoodSubmit} />);
      
      fireEvent.click(screen.getByRole('button', { name: /how are you feeling today/i }));
      
      const contextTextarea = screen.getByPlaceholderText(/Share what's affecting your financial mood today/);
      fireEvent.change(contextTextarea, { target: { value: 'Feeling worried about bills' } });
      
      expect(contextTextarea).toHaveValue('Feeling worried about bills');
    });
  });

  describe('Current Mood Display', () => {
    it('shows current mood after submission', async () => {
      render(<EmotionalCheckIn onMoodSubmit={mockOnMoodSubmit} />);
      
      fireEvent.click(screen.getByRole('button', { name: /how are you feeling today/i }));
      fireEvent.click(screen.getByText('Good'));
      
      await waitFor(() => {
        expect(screen.getByText('Feeling Good')).toBeInTheDocument();
        expect(screen.getByText(/That's wonderful! You're in a good place with your finances/)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /update mood/i })).toBeInTheDocument();
      });
    });

    it('allows mood update from current mood display', async () => {
      render(<EmotionalCheckIn onMoodSubmit={mockOnMoodSubmit} />);
      
      // Submit initial mood
      fireEvent.click(screen.getByRole('button', { name: /how are you feeling today/i }));
      fireEvent.click(screen.getByText('Good'));
      
      await waitFor(() => {
        expect(screen.getByText('Feeling Good')).toBeInTheDocument();
      });
      
      // Update mood
      fireEvent.click(screen.getByRole('button', { name: /update mood/i }));
      
      expect(screen.getByText('How are you feeling?')).toBeInTheDocument();
    });
  });

  describe('Nudges System', () => {
    it('shows mood check nudge when no recent mood', () => {
      render(<EmotionalCheckIn onMoodSubmit={mockOnMoodSubmit} />);
      
      expect(screen.getByText(/How are you feeling about your finances today?/)).toBeInTheDocument();
      expect(screen.getByText('Check in now')).toBeInTheDocument();
    });

    it('shows stress support nudge for stressed mood', async () => {
      render(<EmotionalCheckIn onMoodSubmit={mockOnMoodSubmit} />);
      
      fireEvent.click(screen.getByRole('button', { name: /how are you feeling today/i }));
      fireEvent.click(screen.getByText('Stressed'));
      
      await waitFor(() => {
        expect(screen.getByText(/Financial stress is completely normal/)).toBeInTheDocument();
        expect(screen.getByText('Get support')).toBeInTheDocument();
      });
    });

    it('shows celebration nudge for recent achievements', () => {
      render(<EmotionalCheckIn achievements={mockAchievements} onMoodSubmit={mockOnMoodSubmit} />);
      
      expect(screen.getByText(/You've achieved 2 financial milestones this week!/)).toBeInTheDocument();
      expect(screen.getByText('Celebrate')).toBeInTheDocument();
    });

    it('handles nudge actions', async () => {
      render(<EmotionalCheckIn achievements={mockAchievements} onMoodSubmit={mockOnMoodSubmit} />);
      
      fireEvent.click(screen.getByText('Celebrate'));
      
      await waitFor(() => {
        expect(screen.getByText('Recent Achievements')).toBeInTheDocument();
        expect(screen.getByText('First Savings Goal')).toBeInTheDocument();
        expect(screen.getByText('Organized Finances')).toBeInTheDocument();
      });
    });
  });

  describe('Achievements Display', () => {
    it('shows achievements when celebration nudge is clicked', async () => {
      render(<EmotionalCheckIn achievements={mockAchievements} onMoodSubmit={mockOnMoodSubmit} />);
      
      fireEvent.click(screen.getByText('Celebrate'));
      
      await waitFor(() => {
        expect(screen.getByText('Recent Achievements')).toBeInTheDocument();
        expect(screen.getByText('First Savings Goal')).toBeInTheDocument();
        expect(screen.getByText('You saved $500 this month!')).toBeInTheDocument();
        expect(screen.getByText('Value: $500')).toBeInTheDocument();
      });
    });

    it('allows closing achievements display', async () => {
      render(<EmotionalCheckIn achievements={mockAchievements} onMoodSubmit={mockOnMoodSubmit} />);
      
      fireEvent.click(screen.getByText('Celebrate'));
      
      await waitFor(() => {
        expect(screen.getByText('Recent Achievements')).toBeInTheDocument();
      });
      
      fireEvent.click(screen.getByText('×'));
      
      await waitFor(() => {
        expect(screen.queryByText('Recent Achievements')).not.toBeInTheDocument();
      });
    });
  });

  describe('Mood History', () => {
    it('shows mood history after multiple submissions', async () => {
      render(<EmotionalCheckIn onMoodSubmit={mockOnMoodSubmit} />);
      
      // Submit first mood
      fireEvent.click(screen.getByRole('button', { name: /how are you feeling today/i }));
      fireEvent.click(screen.getByText('Good'));
      
      await waitFor(() => {
        expect(screen.getByText('Feeling Good')).toBeInTheDocument();
      });
      
      // Submit second mood
      fireEvent.click(screen.getByRole('button', { name: /update mood/i }));
      fireEvent.click(screen.getByText('Great!'));
      
      await waitFor(() => {
        expect(screen.getByText('Mood History')).toBeInTheDocument();
        expect(screen.getByText('Great!')).toBeInTheDocument();
        expect(screen.getByText('Good')).toBeInTheDocument();
      });
    });
  });

  describe('Stress Detection and Intervention', () => {
    it('shows appropriate intervention for different stress levels', () => {
      render(<EmotionalCheckIn onMoodSubmit={mockOnMoodSubmit} />);
      
      fireEvent.click(screen.getByRole('button', { name: /how are you feeling today/i }));
      
      const stressSlider = screen.getByRole('slider');
      
      // Low stress - no intervention
      fireEvent.change(stressSlider, { target: { value: '2' } });
      expect(screen.queryByText(/Consider taking a short break/)).not.toBeInTheDocument();
      
      // Medium stress - low intervention
      fireEvent.change(stressSlider, { target: { value: '4' } });
      expect(screen.getByText(/Consider taking a short break/)).toBeInTheDocument();
      
      // High stress - medium intervention
      fireEvent.change(stressSlider, { target: { value: '6' } });
      expect(screen.getByText(/Let's focus on one small financial task today/)).toBeInTheDocument();
      
      // Critical stress - high intervention
      fireEvent.change(stressSlider, { target: { value: '9' } });
      expect(screen.getByText(/Please consider talking to someone you trust/)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', () => {
      render(<EmotionalCheckIn onMoodSubmit={mockOnMoodSubmit} />);
      
      fireEvent.click(screen.getByRole('button', { name: /how are you feeling today/i }));
      
      expect(screen.getByRole('slider')).toHaveAttribute('min', '1');
      expect(screen.getByRole('slider')).toHaveAttribute('max', '10');
      expect(screen.getByRole('slider')).toHaveAttribute('value', '5');
    });

    it('supports keyboard navigation', () => {
      render(<EmotionalCheckIn onMoodSubmit={mockOnMoodSubmit} />);
      
      fireEvent.click(screen.getByRole('button', { name: /how are you feeling today/i }));
      
      const stressSlider = screen.getByRole('slider');
      stressSlider.focus();
      
      fireEvent.keyDown(stressSlider, { key: 'ArrowRight' });
      expect(stressSlider).toHaveValue('6');
    });
  });

  describe('Props and Configuration', () => {
    it('respects showNudges prop', () => {
      render(<EmotionalCheckIn showNudges={false} onMoodSubmit={mockOnMoodSubmit} />);
      
      expect(screen.queryByText(/How are you feeling about your finances today?/)).not.toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <EmotionalCheckIn className="custom-class" onMoodSubmit={mockOnMoodSubmit} />
      );
      
      expect(container.firstChild).toHaveClass('custom-class');
    });

    it('calls onMoodSubmit with correct data', async () => {
      render(<EmotionalCheckIn onMoodSubmit={mockOnMoodSubmit} />);
      
      fireEvent.click(screen.getByRole('button', { name: /how are you feeling today/i }));
      
      const contextTextarea = screen.getByPlaceholderText(/Share what's affecting your financial mood today/);
      fireEvent.change(contextTextarea, { target: { value: 'Test context' } });
      
      const stressSlider = screen.getByRole('slider');
      fireEvent.change(stressSlider, { target: { value: '7' } });
      
      fireEvent.click(screen.getByText('Stressed'));
      
      await waitFor(() => {
        expect(mockOnMoodSubmit).toHaveBeenCalledWith({
          mood: 'stressed',
          timestamp: expect.any(Date),
          financialContext: 'Test context',
          stressLevel: 7
        });
      });
    });
  });
});
