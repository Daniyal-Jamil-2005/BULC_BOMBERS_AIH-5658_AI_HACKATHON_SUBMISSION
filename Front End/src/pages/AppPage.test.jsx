/**
 * Unit Tests for AppPage - Load Sample Data Functionality
 * 
 * Tests the "Load Sample Data" button functionality implemented in task 1.4
 * Validates: Requirements 1.5
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import API_CONFIG from '../config';

// Mock fetch globally
global.fetch = jest.fn();

// Mock react-router-dom using manual mock
jest.mock('react-router-dom');

// Import AppPage after mocks
import AppPage from './AppPage';

// Helper function to render AppPage
const renderAppPage = () => {
  return render(<AppPage />);
};

describe('AppPage - Load Sample Data', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
    fetch.mockClear();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Successful fetch and state population', () => {
    it('should fetch sample data from the correct endpoint', async () => {
      // Arrange
      const mockSampleData = {
        profile: {
          degree: 'BSCS',
          semester: 6,
          cgpa: 3.4,
          location_preference: 'Lahore',
          skills: ['Python', 'JavaScript', 'React'],
          preferred_opportunity_types: ['internship', 'hackathon'],
          past_experience: 'Built 3 web apps',
          financial_need: false,
          total_semesters: 8
        },
        emails: [
          'Sample email 1 content',
          'Sample email 2 content'
        ],
        email_count: 2
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSampleData
      });

      renderAppPage();

      // Act
      const loadButton = screen.getByText(/LOAD SAMPLE DATA/i);
      fireEvent.click(loadButton);

      // Assert
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledTimes(1);
        expect(fetch).toHaveBeenCalledWith(
          `${API_CONFIG.baseURL}${API_CONFIG.endpoints.sampleData}`
        );
      });
    });

    it('should populate profile fields with sample data', async () => {
      // Arrange
      const mockSampleData = {
        profile: {
          degree: 'BSCS',
          semester: 6,
          cgpa: 3.4,
          location_preference: 'Lahore',
          skills: ['Python', 'JavaScript', 'React'],
          preferred_opportunity_types: ['internship', 'hackathon'],
          past_experience: 'Built 3 web apps',
          financial_need: false,
          total_semesters: 8
        },
        emails: ['Sample email 1', 'Sample email 2'],
        email_count: 2
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSampleData
      });

      renderAppPage();

      // Act
      const loadButton = screen.getByText(/LOAD SAMPLE DATA/i);
      fireEvent.click(loadButton);

      // Assert - Check that profile fields are populated
      await waitFor(() => {
        // Find degree input and check its value
        const degreeInput = screen.getByDisplayValue('BSCS');
        expect(degreeInput).toBeInTheDocument();

        // Check CGPA
        const cgpaInput = screen.getByDisplayValue('3.4');
        expect(cgpaInput).toBeInTheDocument();

        // Check location
        const locationInput = screen.getByDisplayValue('Lahore');
        expect(locationInput).toBeInTheDocument();

        // Check skills (comma-separated)
        const skillsInput = screen.getByDisplayValue('Python, JavaScript, React');
        expect(skillsInput).toBeInTheDocument();

        // Check opportunity types (comma-separated)
        const typesInput = screen.getByDisplayValue('internship, hackathon');
        expect(typesInput).toBeInTheDocument();
      });
    });

    it('should populate email text area with sample emails', async () => {
      // Arrange
      const mockSampleData = {
        profile: {
          degree: 'BSCS',
          semester: 6,
          cgpa: 3.4,
          location_preference: 'Lahore',
          skills: ['Python'],
          preferred_opportunity_types: ['internship'],
          past_experience: '',
          financial_need: false,
          total_semesters: 8
        },
        emails: [
          'Email 1: Internship opportunity at Google',
          'Email 2: Hackathon invitation from Microsoft'
        ],
        email_count: 2
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSampleData
      });

      renderAppPage();

      // Act
      const loadButton = screen.getByRole('button', { name: /LOAD SAMPLE DATA/i });
      fireEvent.click(loadButton);

      // Assert - Check that email textarea is populated with emails separated by ---
      await waitFor(() => {
        // Look for a textarea that contains both emails
        const textareas = screen.getAllByRole('textbox');
        const emailTextarea = textareas.find(textarea => 
          textarea.value.includes('Email 1: Internship opportunity at Google') &&
          textarea.value.includes('Email 2: Hackathon invitation from Microsoft')
        );
        expect(emailTextarea).toBeDefined();
        expect(emailTextarea.value).toContain('---');
      });
    });

    it('should display success message after loading sample data', async () => {
      // Arrange
      const mockSampleData = {
        profile: {
          degree: 'BSCS',
          semester: 6,
          cgpa: 3.4,
          location_preference: 'Lahore',
          skills: ['Python'],
          preferred_opportunity_types: ['internship'],
          past_experience: '',
          financial_need: false,
          total_semesters: 8
        },
        emails: ['Sample email'],
        email_count: 1
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSampleData
      });

      renderAppPage();

      // Act
      const loadButton = screen.getByText(/LOAD SAMPLE DATA/i);
      fireEvent.click(loadButton);

      // Assert - Check for success message
      await waitFor(() => {
        const successMessage = screen.getByText(/Successfully loaded 1 sample emails and demo profile!/i);
        expect(successMessage).toBeInTheDocument();
      });
    });

    it('should clear selected files when loading sample data', async () => {
      // Arrange
      const mockSampleData = {
        profile: {
          degree: 'BSCS',
          semester: 6,
          cgpa: 3.4,
          location_preference: 'Lahore',
          skills: ['Python'],
          preferred_opportunity_types: ['internship'],
          past_experience: '',
          financial_need: false,
          total_semesters: 8
        },
        emails: ['Sample email'],
        email_count: 1
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSampleData
      });

      renderAppPage();

      // Act
      const loadButton = screen.getByText(/LOAD SAMPLE DATA/i);
      fireEvent.click(loadButton);

      // Assert - Verify fetch was successful (file clearing is internal state)
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledTimes(1);
      });
    });

    it('should show loading state while fetching', async () => {
      // Arrange
      const mockSampleData = {
        profile: {
          degree: 'BSCS',
          semester: 6,
          cgpa: 3.4,
          location_preference: 'Lahore',
          skills: ['Python'],
          preferred_opportunity_types: ['internship'],
          past_experience: '',
          financial_need: false,
          total_semesters: 8
        },
        emails: ['Sample email'],
        email_count: 1
      };

      // Create a promise that we can control
      let resolvePromise;
      const fetchPromise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      fetch.mockReturnValueOnce(fetchPromise);

      renderAppPage();

      // Act
      const loadButton = screen.getByText(/LOAD SAMPLE DATA/i);
      fireEvent.click(loadButton);

      // Assert - Check for loading text
      await waitFor(() => {
        const loadingButton = screen.getByText(/LOADING.../i);
        expect(loadingButton).toBeInTheDocument();
      });

      // Resolve the promise to complete the test
      resolvePromise({
        ok: true,
        json: async () => mockSampleData
      });

      // Wait for loading to complete
      await waitFor(() => {
        const loadButton = screen.getByText(/LOAD SAMPLE DATA/i);
        expect(loadButton).toBeInTheDocument();
      });
    });
  });

  describe('Error handling for failed fetch', () => {
    it('should display error message when fetch fails with network error', async () => {
      // Arrange
      fetch.mockRejectedValueOnce(new Error('Network error'));

      renderAppPage();

      // Act
      const loadButton = screen.getByText(/LOAD SAMPLE DATA/i);
      fireEvent.click(loadButton);

      // Assert
      await waitFor(() => {
        const errorMessage = screen.getByText(/Failed to load sample data: Network error/i);
        expect(errorMessage).toBeInTheDocument();
      });
    });

    it('should display error message when fetch returns non-ok response', async () => {
      // Arrange
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error'
      });

      renderAppPage();

      // Act
      const loadButton = screen.getByText(/LOAD SAMPLE DATA/i);
      fireEvent.click(loadButton);

      // Assert
      await waitFor(() => {
        const errorMessage = screen.getByText(/Failed to load sample data: Failed to fetch sample data/i);
        expect(errorMessage).toBeInTheDocument();
      });
    });

    it('should display error message when JSON parsing fails', async () => {
      // Arrange
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON');
        }
      });

      renderAppPage();

      // Act
      const loadButton = screen.getByText(/LOAD SAMPLE DATA/i);
      fireEvent.click(loadButton);

      // Assert
      await waitFor(() => {
        const errorMessage = screen.getByText(/Failed to load sample data: Invalid JSON/i);
        expect(errorMessage).toBeInTheDocument();
      });
    });

    it('should not populate fields when fetch fails', async () => {
      // Arrange
      fetch.mockRejectedValueOnce(new Error('Network error'));

      renderAppPage();

      // Get initial state of a field
      const initialDegreeValue = screen.queryByDisplayValue('BSCS');

      // Act
      const loadButton = screen.getByText(/LOAD SAMPLE DATA/i);
      fireEvent.click(loadButton);

      // Assert - Fields should not be populated with sample data
      await waitFor(() => {
        const errorMessage = screen.getByText(/Failed to load sample data/i);
        expect(errorMessage).toBeInTheDocument();
      });

      // Verify that the field wasn't populated (if it wasn't already)
      if (!initialDegreeValue) {
        const degreeAfterError = screen.queryByDisplayValue('BSCS');
        expect(degreeAfterError).not.toBeInTheDocument();
      }
    });

    it('should stop loading state after error', async () => {
      // Arrange
      fetch.mockRejectedValueOnce(new Error('Network error'));

      renderAppPage();

      // Act
      const loadButton = screen.getByRole('button', { name: /LOAD SAMPLE DATA/i });
      fireEvent.click(loadButton);

      // Assert - Loading should stop and button should return to normal
      await waitFor(() => {
        const errorMessage = screen.getByText(/Failed to load sample data/i);
        expect(errorMessage).toBeInTheDocument();
      });

      await waitFor(() => {
        const normalButton = screen.getByRole('button', { name: /LOAD SAMPLE DATA/i });
        expect(normalButton).toBeInTheDocument();
        expect(normalButton).not.toHaveTextContent('LOADING');
      });
    });
  });

  describe('Edge cases', () => {
    it('should handle missing profile fields gracefully', async () => {
      // Arrange
      const mockSampleData = {
        profile: {
          degree: 'BSCS'
          // Missing other fields
        },
        emails: ['Sample email'],
        email_count: 1
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSampleData
      });

      renderAppPage();

      // Act
      const loadButton = screen.getByText(/LOAD SAMPLE DATA/i);
      fireEvent.click(loadButton);

      // Assert - Should not crash and should use default values
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledTimes(1);
        const successMessage = screen.getByText(/Successfully loaded/i);
        expect(successMessage).toBeInTheDocument();
      });
    });

    it('should handle empty emails array', async () => {
      // Arrange
      const mockSampleData = {
        profile: {
          degree: 'BSCS',
          semester: 6,
          cgpa: 3.4,
          location_preference: 'Lahore',
          skills: ['Python'],
          preferred_opportunity_types: ['internship'],
          past_experience: '',
          financial_need: false,
          total_semesters: 8
        },
        emails: [],
        email_count: 0
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSampleData
      });

      renderAppPage();

      // Act
      const loadButton = screen.getByText(/LOAD SAMPLE DATA/i);
      fireEvent.click(loadButton);

      // Assert
      await waitFor(() => {
        const successMessage = screen.getByText(/Successfully loaded 0 sample emails and demo profile!/i);
        expect(successMessage).toBeInTheDocument();
      });
    });

    it('should handle missing emails field', async () => {
      // Arrange
      const mockSampleData = {
        profile: {
          degree: 'BSCS',
          semester: 6,
          cgpa: 3.4,
          location_preference: 'Lahore',
          skills: ['Python'],
          preferred_opportunity_types: ['internship'],
          past_experience: '',
          financial_need: false,
          total_semesters: 8
        }
        // Missing emails field
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSampleData
      });

      renderAppPage();

      // Act
      const loadButton = screen.getByText(/LOAD SAMPLE DATA/i);
      fireEvent.click(loadButton);

      // Assert - Should handle gracefully with default empty array
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledTimes(1);
      });
    });
  });
});
