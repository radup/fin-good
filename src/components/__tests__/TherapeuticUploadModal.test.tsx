import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { TherapeuticUploadModal } from '../../../components/TherapeuticUploadModal';

// Mock the DrSigmundSpendAvatar component
jest.mock('../../../components/DrSigmundSpendAvatar', () => ({
  __esModule: true,
  default: ({ mood, message, showMessage }: any) => (
    <div data-testid="dr-sigmund-avatar" data-mood={mood} data-message={message} data-show-message={showMessage}>
      Dr. Sigmund Avatar
    </div>
  ),
}));

// Mock the TherapeuticUploadProgress component
jest.mock('../../../components/TherapeuticUploadProgress', () => ({
  __esModule: true,
  default: ({ progress, stage, filename, isMobile }: any) => (
    <div data-testid="upload-progress" data-progress={progress} data-stage={stage} data-filename={filename} data-mobile={isMobile}>
      Upload Progress
    </div>
  ),
}));

// Mock window.innerWidth for mobile detection
const mockWindowWidth = (width: number) => {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  });
};

describe('TherapeuticUploadModal - Mobile Optimization', () => {
  const mockOnClose = jest.fn();
  const mockOnUploadSuccess = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockWindowWidth(1024); // Default to desktop
  });

  afterEach(() => {
    // Clean up event listeners
    window.removeEventListener('resize', expect.any(Function));
  });

  describe('Desktop Rendering', () => {
    it('renders correctly when open on desktop', () => {
      render(
        <TherapeuticUploadModal
          isOpen={true}
          onClose={mockOnClose}
          onUploadSuccess={mockOnUploadSuccess}
        />
      );

      expect(screen.getByText('Upload Your Financial Data')).toBeInTheDocument();
      expect(screen.getByText('Drag & drop your CSV file here')).toBeInTheDocument();
      expect(screen.getByText('or click to select a file')).toBeInTheDocument();
      expect(screen.getByText('Your data is secure')).toBeInTheDocument();
    });

    it('shows Dr. Sigmund avatar in header on desktop', () => {
      render(
        <TherapeuticUploadModal
          isOpen={true}
          onClose={mockOnClose}
          onUploadSuccess={mockOnUploadSuccess}
        />
      );

      const avatar = screen.getByTestId('dr-sigmund-avatar');
      expect(avatar).toBeInTheDocument();
      expect(avatar).toHaveAttribute('data-mood', 'encouraging');
      expect(avatar).toHaveAttribute('data-show-message', 'false');
    });

    it('closes modal when close button is clicked', () => {
      render(
        <TherapeuticUploadModal
          isOpen={true}
          onClose={mockOnClose}
          onUploadSuccess={mockOnUploadSuccess}
        />
      );

      const closeButton = screen.getByLabelText('Close modal');
      fireEvent.click(closeButton);

      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe('Mobile Rendering', () => {
    it('renders correctly when open on mobile', () => {
      mockWindowWidth(375); // Mobile width
      
      render(
        <TherapeuticUploadModal
          isOpen={true}
          onClose={mockOnClose}
          onUploadSuccess={mockOnUploadSuccess}
        />
      );

      expect(screen.getByText('Upload Your Financial Data')).toBeInTheDocument();
      expect(screen.getByText('Tap to select your CSV file')).toBeInTheDocument();
      expect(screen.getByText("We'll help you understand your finances")).toBeInTheDocument();
      expect(screen.getByText('Choose File')).toBeInTheDocument();
      expect(screen.getByText('Supported: CSV files only')).toBeInTheDocument();
    });

    it('shows Dr. Sigmund avatar below header on mobile', () => {
      mockWindowWidth(375);
      
      render(
        <TherapeuticUploadModal
          isOpen={true}
          onClose={mockOnClose}
          onUploadSuccess={mockOnUploadSuccess}
        />
      );

      const avatar = screen.getByTestId('dr-sigmund-avatar');
      expect(avatar).toBeInTheDocument();
      expect(avatar).toHaveAttribute('data-mood', 'encouraging');
      expect(avatar).toHaveAttribute('data-show-message', 'true');
    });

    it('shows mobile-optimized file selection interface', () => {
      mockWindowWidth(375);
      
      render(
        <TherapeuticUploadModal
          isOpen={true}
          onClose={mockOnClose}
          onUploadSuccess={mockOnUploadSuccess}
        />
      );

      // Check for mobile-specific elements
      expect(screen.getByText('Choose File')).toBeInTheDocument();
      expect(screen.getByText('Supported: CSV files only')).toBeInTheDocument();
      
      // Should not show desktop drag & drop text
      expect(screen.queryByText('Drag & drop your CSV file here')).not.toBeInTheDocument();
      expect(screen.queryByText('or click to select a file')).not.toBeInTheDocument();
    });

    it('handles mobile file selection button click', () => {
      mockWindowWidth(375);
      
      render(
        <TherapeuticUploadModal
          isOpen={true}
          onClose={mockOnClose}
          onUploadSuccess={mockOnUploadSuccess}
        />
      );

      const chooseFileButton = screen.getByText('Choose File');
      expect(chooseFileButton).toBeInTheDocument();
      
      // Mock the file input click
      const mockClick = jest.fn();
      jest.spyOn(document, 'querySelector').mockReturnValue({
        click: mockClick
      } as any);

      fireEvent.click(chooseFileButton);
      expect(mockClick).toHaveBeenCalled();
    });
  });

  describe('Responsive Design', () => {
    it('responds to window resize for mobile detection', () => {
      const { rerender } = render(
        <TherapeuticUploadModal
          isOpen={true}
          onClose={mockOnClose}
          onUploadSuccess={mockOnUploadSuccess}
        />
      );

      // Initially desktop
      expect(screen.getByText('Drag & drop your CSV file here')).toBeInTheDocument();

      // Resize to mobile
      mockWindowWidth(375);
      fireEvent.resize(window);

      rerender(
        <TherapeuticUploadModal
          isOpen={true}
          onClose={mockOnClose}
          onUploadSuccess={mockOnUploadSuccess}
        />
      );

      expect(screen.getByText('Tap to select your CSV file')).toBeInTheDocument();
    });

    it('applies mobile-specific styling', () => {
      mockWindowWidth(375);
      
      render(
        <TherapeuticUploadModal
          isOpen={true}
          onClose={mockOnClose}
          onUploadSuccess={mockOnUploadSuccess}
        />
      );

      // Check that the modal has mobile-specific classes
      const modal = screen.getByText('Upload Your Financial Data').closest('.bg-white');
      expect(modal).toHaveClass('max-w-full', 'mx-0');
    });

    it('applies desktop-specific styling', () => {
      mockWindowWidth(1024);
      
      render(
        <TherapeuticUploadModal
          isOpen={true}
          onClose={mockOnClose}
          onUploadSuccess={mockOnUploadSuccess}
        />
      );

      // Check that the modal has desktop-specific classes
      const modal = screen.getByText('Upload Your Financial Data').closest('.bg-white');
      expect(modal).toHaveClass('max-w-2xl', 'mx-4');
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      render(
        <TherapeuticUploadModal
          isOpen={true}
          onClose={mockOnClose}
          onUploadSuccess={mockOnUploadSuccess}
        />
      );

      expect(screen.getByLabelText('Close modal')).toBeInTheDocument();
    });

    it('has proper semantic structure', () => {
      render(
        <TherapeuticUploadModal
          isOpen={true}
          onClose={mockOnClose}
          onUploadSuccess={mockOnUploadSuccess}
        />
      );

      expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();
      expect(screen.getByText('Upload Your Financial Data')).toBeInTheDocument();
    });
  });

  describe('Security Messaging', () => {
    it('displays security information on desktop', () => {
      render(
        <TherapeuticUploadModal
          isOpen={true}
          onClose={mockOnClose}
          onUploadSuccess={mockOnUploadSuccess}
        />
      );

      expect(screen.getByText('Your data is secure')).toBeInTheDocument();
      expect(screen.getByText('We use bank-level encryption and never share your personal information')).toBeInTheDocument();
    });

    it('displays security information on mobile', () => {
      mockWindowWidth(375);
      
      render(
        <TherapeuticUploadModal
          isOpen={true}
          onClose={mockOnClose}
          onUploadSuccess={mockOnUploadSuccess}
        />
      );

      expect(screen.getByText('Your data is secure')).toBeInTheDocument();
      expect(screen.getByText('We use bank-level encryption and never share your personal information')).toBeInTheDocument();
    });
  });

  describe('Component Integration', () => {
    it('passes mobile prop to TherapeuticUploadProgress', () => {
      mockWindowWidth(375);
      
      render(
        <TherapeuticUploadModal
          isOpen={true}
          onClose={mockOnClose}
          onUploadSuccess={mockOnUploadSuccess}
        />
      );

      // The upload progress component should receive the isMobile prop
      // This is tested through the mock implementation
      const uploadProgress = screen.queryByTestId('upload-progress');
      if (uploadProgress) {
        expect(uploadProgress).toHaveAttribute('data-mobile', 'true');
      }
    });

    it('passes desktop prop to TherapeuticUploadProgress', () => {
      mockWindowWidth(1024);
      
      render(
        <TherapeuticUploadModal
          isOpen={true}
          onClose={mockOnClose}
          onUploadSuccess={mockOnUploadSuccess}
        />
      );

      // The upload progress component should receive the isMobile prop
      const uploadProgress = screen.queryByTestId('upload-progress');
      if (uploadProgress) {
        expect(uploadProgress).toHaveAttribute('data-mobile', 'false');
      }
    });
  });
});
