import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { http, HttpResponse } from 'msw';
import { server } from '../../../mocks/server';
import ImportPage from './+page.svelte';

// Mock the auth store to simulate authenticated user
vi.mock('$lib/stores/auth', () => ({
	isAuthenticated: { subscribe: (fn: (value: boolean) => void) => { fn(true); return () => {}; } }
}));

// Mock goto for navigation tests
const mockGoto = vi.fn();
vi.mock('$app/navigation', () => ({
	goto: (path: string) => mockGoto(path)
}));

// Mock importedRecipe store
const mockSetExtraction = vi.fn();
vi.mock('$lib/stores/importedRecipe', () => ({
	importedRecipe: {
		subscribe: (fn: (value: { extraction: null }) => void) => { fn({ extraction: null }); return () => {}; },
		setExtraction: (extraction: unknown, sourceUrl?: string) => mockSetExtraction(extraction, sourceUrl),
		clear: vi.fn()
	}
}));

function createMockFile(name: string, type: string, size: number = 1024): File {
	const content = new Array(size).fill('a').join('');
	return new File([content], name, { type });
}

describe('Import Page', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	describe('tab navigation', () => {
		it('should show image tab as active by default', () => {
			render(ImportPage);
			const imageTab = screen.getByRole('tab', { name: /from image/i });
			expect(imageTab).toHaveAttribute('aria-selected', 'true');
		});

		it('should switch to URL tab when clicked', async () => {
			render(ImportPage);
			const urlTab = screen.getByRole('tab', { name: /from url/i });

			await fireEvent.click(urlTab);

			expect(urlTab).toHaveAttribute('aria-selected', 'true');
			expect(screen.getByLabelText(/recipe url/i)).toBeInTheDocument();
		});

		it('should switch back to image tab', async () => {
			render(ImportPage);

			// Switch to URL tab
			await fireEvent.click(screen.getByRole('tab', { name: /from url/i }));

			// Switch back to image tab
			const imageTab = screen.getByRole('tab', { name: /from image/i });
			await fireEvent.click(imageTab);

			expect(imageTab).toHaveAttribute('aria-selected', 'true');
			expect(screen.getByText(/drag and drop/i)).toBeInTheDocument();
		});

		it('should reset state when switching tabs', async () => {
			render(ImportPage);

			// Enter a URL
			await fireEvent.click(screen.getByRole('tab', { name: /from url/i }));
			const urlInput = screen.getByLabelText(/recipe url/i);
			await fireEvent.input(urlInput, { target: { value: 'https://example.com' } });

			// Switch to image tab
			await fireEvent.click(screen.getByRole('tab', { name: /from image/i }));

			// Switch back - URL should be cleared
			await fireEvent.click(screen.getByRole('tab', { name: /from url/i }));
			expect(screen.getByLabelText(/recipe url/i)).toHaveValue('');
		});
	});

	describe('image upload validation', () => {
		it('should reject non-image file types', async () => {
			render(ImportPage);
			const dropZone = screen.getByRole('tabpanel');
			const file = createMockFile('test.txt', 'text/plain');

			// Simulate file input change
			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			expect(screen.getByRole('alert')).toHaveTextContent(/invalid file type/i);
		});

		it('should reject files larger than 10MB', async () => {
			render(ImportPage);
			const file = createMockFile('large.jpg', 'image/jpeg', 11 * 1024 * 1024);

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			expect(screen.getByRole('alert')).toHaveTextContent(/file too large/i);
		});

		it('should accept valid JPEG files', async () => {
			render(ImportPage);
			const file = createMockFile('recipe.jpg', 'image/jpeg');

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			expect(screen.queryByRole('alert')).not.toBeInTheDocument();
			expect(screen.getByText('Extract Recipe')).toBeInTheDocument();
		});

		it('should accept valid PNG files', async () => {
			render(ImportPage);
			const file = createMockFile('recipe.png', 'image/png');

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			expect(screen.queryByRole('alert')).not.toBeInTheDocument();
		});

		it('should accept valid WebP files', async () => {
			render(ImportPage);
			const file = createMockFile('recipe.webp', 'image/webp');

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			expect(screen.queryByRole('alert')).not.toBeInTheDocument();
		});
	});

	describe('URL validation', () => {
		it('should show error for empty URL', async () => {
			render(ImportPage);
			await fireEvent.click(screen.getByRole('tab', { name: /from url/i }));

			const submitButton = screen.getByRole('button', { name: /extract recipe/i });
			expect(submitButton).toBeDisabled();
		});

		it('should show error for invalid URL format', async () => {
			render(ImportPage);
			await fireEvent.click(screen.getByRole('tab', { name: /from url/i }));

			const urlInput = screen.getByLabelText(/recipe url/i);
			await fireEvent.input(urlInput, { target: { value: 'not-a-valid-url' } });
			await fireEvent.click(screen.getByRole('button', { name: /extract recipe/i }));

			expect(screen.getByRole('alert')).toHaveTextContent(/valid url/i);
		});
	});

	describe('loading state', () => {
		it('should show loading state during image extraction', async () => {
			// Delay the response to observe loading state
			server.use(
				http.post('/api/import/image', async () => {
					await new Promise(resolve => setTimeout(resolve, 100));
					return HttpResponse.json({
						title: 'Test',
						ingredients: [],
						instructions: [],
						confidence: 0.8,
						warnings: []
					});
				})
			);

			render(ImportPage);
			const file = createMockFile('recipe.jpg', 'image/jpeg');

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			await fireEvent.click(screen.getByRole('button', { name: /extract recipe/i }));

			expect(screen.getByText(/extracting recipe/i)).toBeInTheDocument();
		});

		it('should show loading state during URL extraction', async () => {
			server.use(
				http.post('/api/import/url', async () => {
					await new Promise(resolve => setTimeout(resolve, 100));
					return HttpResponse.json({
						title: 'Test',
						ingredients: [],
						instructions: [],
						confidence: 0.8,
						warnings: []
					});
				})
			);

			render(ImportPage);
			await fireEvent.click(screen.getByRole('tab', { name: /from url/i }));

			const urlInput = screen.getByLabelText(/recipe url/i);
			await fireEvent.input(urlInput, { target: { value: 'https://example.com/recipe' } });
			await fireEvent.click(screen.getByRole('button', { name: /extract recipe/i }));

			expect(screen.getByText(/extracting recipe/i)).toBeInTheDocument();
		});
	});

	describe('error display', () => {
		it('should display error message on extraction failure', async () => {
			server.use(
				http.post('/api/import/image', () => {
					return HttpResponse.json(
						{ detail: 'Could not extract recipe from image' },
						{ status: 422 }
					);
				})
			);

			render(ImportPage);
			const file = createMockFile('recipe.jpg', 'image/jpeg');

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			await fireEvent.click(screen.getByRole('button', { name: /extract recipe/i }));

			await waitFor(() => {
				expect(screen.getByRole('alert')).toHaveTextContent(/could not extract/i);
			});
		});

		it('should show suggestion for AI not configured error', async () => {
			server.use(
				http.post('/api/import/image', () => {
					return HttpResponse.json(
						{ detail: 'AI service not configured' },
						{ status: 503 }
					);
				})
			);

			render(ImportPage);
			const file = createMockFile('recipe.jpg', 'image/jpeg');

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			await fireEvent.click(screen.getByRole('button', { name: /extract recipe/i }));

			await waitFor(() => {
				expect(screen.getByRole('alert')).toHaveTextContent(/contact an admin/i);
			});
		});

		it('should show suggestion for URL fetch error', async () => {
			server.use(
				http.post('/api/import/url', () => {
					return HttpResponse.json(
						{ detail: 'Could not fetch URL: Page not found' },
						{ status: 422 }
					);
				})
			);

			render(ImportPage);
			await fireEvent.click(screen.getByRole('tab', { name: /from url/i }));

			const urlInput = screen.getByLabelText(/recipe url/i);
			await fireEvent.input(urlInput, { target: { value: 'https://example.com/recipe' } });
			await fireEvent.click(screen.getByRole('button', { name: /extract recipe/i }));

			await waitFor(() => {
				expect(screen.getByRole('alert')).toHaveTextContent(/check the url/i);
			});
		});
	});

	describe('successful extraction', () => {
		it('should display extraction result with title', async () => {
			render(ImportPage);
			const file = createMockFile('recipe.jpg', 'image/jpeg');

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			await fireEvent.click(screen.getByRole('button', { name: /extract recipe/i }));

			await waitFor(() => {
				expect(screen.getByText('Extracted Recipe')).toBeInTheDocument();
			});
		});

		it('should display high confidence badge', async () => {
			render(ImportPage);
			const file = createMockFile('recipe.jpg', 'image/jpeg');

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			await fireEvent.click(screen.getByRole('button', { name: /extract recipe/i }));

			await waitFor(() => {
				expect(screen.getByText(/high confidence/i)).toBeInTheDocument();
			});
		});

		it('should display medium confidence badge for lower confidence', async () => {
			server.use(
				http.post('/api/import/image', () => {
					return HttpResponse.json({
						title: 'Test Recipe',
						ingredients: [],
						instructions: [],
						confidence: 0.6,
						warnings: ['Some fields could not be extracted']
					});
				})
			);

			render(ImportPage);
			const file = createMockFile('recipe.jpg', 'image/jpeg');

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			await fireEvent.click(screen.getByRole('button', { name: /extract recipe/i }));

			await waitFor(() => {
				expect(screen.getByText(/medium confidence/i)).toBeInTheDocument();
			});
		});

		it('should display warnings when present', async () => {
			server.use(
				http.post('/api/import/image', () => {
					return HttpResponse.json({
						title: 'Test Recipe',
						ingredients: [],
						instructions: [],
						confidence: 0.7,
						warnings: ['Could not determine servings', 'Instructions may be incomplete']
					});
				})
			);

			render(ImportPage);
			const file = createMockFile('recipe.jpg', 'image/jpeg');

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			await fireEvent.click(screen.getByRole('button', { name: /extract recipe/i }));

			await waitFor(() => {
				expect(screen.getByText(/could not determine servings/i)).toBeInTheDocument();
				expect(screen.getByText(/instructions may be incomplete/i)).toBeInTheDocument();
			});
		});

		it('should display ingredient count', async () => {
			render(ImportPage);
			const file = createMockFile('recipe.jpg', 'image/jpeg');

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			await fireEvent.click(screen.getByRole('button', { name: /extract recipe/i }));

			await waitFor(() => {
				expect(screen.getByText(/ingredients \(2\)/i)).toBeInTheDocument();
			});
		});

		it('should display instruction count', async () => {
			render(ImportPage);
			const file = createMockFile('recipe.jpg', 'image/jpeg');

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			await fireEvent.click(screen.getByRole('button', { name: /extract recipe/i }));

			await waitFor(() => {
				expect(screen.getByText(/instructions \(2 steps\)/i)).toBeInTheDocument();
			});
		});
	});

	describe('Edit & Save button', () => {
		it('should navigate to /recipes/new on click', async () => {
			render(ImportPage);
			const file = createMockFile('recipe.jpg', 'image/jpeg');

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			await fireEvent.click(screen.getByRole('button', { name: /extract recipe/i }));

			await waitFor(() => {
				expect(screen.getByText('Edit & Save')).toBeInTheDocument();
			});

			await fireEvent.click(screen.getByText('Edit & Save'));

			expect(mockGoto).toHaveBeenCalledWith('/recipes/new');
		});

		it('should store extraction in importedRecipe store', async () => {
			render(ImportPage);
			const file = createMockFile('recipe.jpg', 'image/jpeg');

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			await fireEvent.click(screen.getByRole('button', { name: /extract recipe/i }));

			await waitFor(() => {
				expect(screen.getByText('Edit & Save')).toBeInTheDocument();
			});

			await fireEvent.click(screen.getByText('Edit & Save'));

			expect(mockSetExtraction).toHaveBeenCalled();
			expect(mockSetExtraction.mock.calls[0][0].title).toBe('Extracted Recipe');
		});

		it('should pass source URL for URL imports', async () => {
			render(ImportPage);
			await fireEvent.click(screen.getByRole('tab', { name: /from url/i }));

			const urlInput = screen.getByLabelText(/recipe url/i);
			await fireEvent.input(urlInput, { target: { value: 'https://example.com/recipe' } });
			await fireEvent.click(screen.getByRole('button', { name: /extract recipe/i }));

			await waitFor(() => {
				expect(screen.getByText('Edit & Save')).toBeInTheDocument();
			});

			await fireEvent.click(screen.getByText('Edit & Save'));

			expect(mockSetExtraction).toHaveBeenCalledWith(
				expect.anything(),
				'https://example.com/recipe'
			);
		});
	});

	describe('Try Again button', () => {
		it('should reset to input form when clicked', async () => {
			render(ImportPage);
			const file = createMockFile('recipe.jpg', 'image/jpeg');

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			await fireEvent.click(screen.getByRole('button', { name: /extract recipe/i }));

			await waitFor(() => {
				expect(screen.getByText('Try Again')).toBeInTheDocument();
			});

			await fireEvent.click(screen.getByText('Try Again'));

			expect(screen.getByText(/drag and drop/i)).toBeInTheDocument();
			expect(screen.queryByText('Extracted Recipe')).not.toBeInTheDocument();
		});
	});

	describe('PDF upload', () => {
		it('should accept valid PDF files', async () => {
			render(ImportPage);
			const file = createMockFile('recipe.pdf', 'application/pdf');

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			expect(screen.queryByRole('alert')).not.toBeInTheDocument();
			expect(screen.getByText('Extract Recipe')).toBeInTheDocument();
		});

		it('should show PDF preview with filename', async () => {
			render(ImportPage);
			const file = createMockFile('my-recipe.pdf', 'application/pdf', 2 * 1024 * 1024);

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			expect(screen.getByText('my-recipe.pdf')).toBeInTheDocument();
			expect(screen.getByText(/MB/)).toBeInTheDocument();
		});

		it('should reject PDF files larger than 10MB', async () => {
			render(ImportPage);
			const file = createMockFile('large.pdf', 'application/pdf', 11 * 1024 * 1024);

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			expect(screen.getByRole('alert')).toHaveTextContent(/file too large/i);
		});

		it('should successfully extract recipe from PDF', async () => {
			render(ImportPage);
			const file = createMockFile('recipe.pdf', 'application/pdf');

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			await fireEvent.click(screen.getByRole('button', { name: /extract recipe/i }));

			await waitFor(() => {
				expect(screen.getByText('Extracted Recipe')).toBeInTheDocument();
			});
		});

		it('should show error when PDF not supported by provider', async () => {
			server.use(
				http.post('/api/import/image', () => {
					return HttpResponse.json(
						{ detail: 'PDF import is not supported with OpenAI. Please use Anthropic or Gemini.' },
						{ status: 422 }
					);
				})
			);

			render(ImportPage);
			const file = createMockFile('recipe.pdf', 'application/pdf');

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			await fireEvent.click(screen.getByRole('button', { name: /extract recipe/i }));

			await waitFor(() => {
				expect(screen.getByRole('alert')).toHaveTextContent(/not supported/i);
			});
		});

		it('should clear PDF preview when switching tabs', async () => {
			render(ImportPage);
			const file = createMockFile('recipe.pdf', 'application/pdf');

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			expect(screen.getByText('recipe.pdf')).toBeInTheDocument();

			// Switch to URL tab
			await fireEvent.click(screen.getByRole('tab', { name: /from url/i }));

			// Switch back to image tab
			await fireEvent.click(screen.getByRole('tab', { name: /from image/i }));

			// PDF preview should be cleared
			expect(screen.queryByText('recipe.pdf')).not.toBeInTheDocument();
			expect(screen.getByText(/drag and drop/i)).toBeInTheDocument();
		});
	});

	describe('accessibility', () => {
		it('should have proper tab roles', () => {
			render(ImportPage);
			const tablist = screen.getByRole('tablist');
			expect(tablist).toBeInTheDocument();

			const tabs = screen.getAllByRole('tab');
			expect(tabs).toHaveLength(3); // Image, URL, Text tabs
		});

		it('should have aria-selected on active tab', () => {
			render(ImportPage);
			const imageTab = screen.getByRole('tab', { name: /from image/i });
			const urlTab = screen.getByRole('tab', { name: /from url/i });

			expect(imageTab).toHaveAttribute('aria-selected', 'true');
			expect(urlTab).toHaveAttribute('aria-selected', 'false');
		});

		it('should have aria-controls on tabs', () => {
			render(ImportPage);
			const imageTab = screen.getByRole('tab', { name: /from image/i });
			expect(imageTab).toHaveAttribute('aria-controls', 'image-panel');
		});

		it('should have role alert on error messages', async () => {
			render(ImportPage);
			const file = createMockFile('test.txt', 'text/plain');

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			const alert = screen.getByRole('alert');
			expect(alert).toBeInTheDocument();
		});

		it('should have aria-busy on form during loading', async () => {
			server.use(
				http.post('/api/import/image', async () => {
					await new Promise(resolve => setTimeout(resolve, 100));
					return HttpResponse.json({
						title: 'Test',
						ingredients: [],
						instructions: [],
						confidence: 0.8,
						warnings: []
					});
				})
			);

			render(ImportPage);
			const file = createMockFile('recipe.jpg', 'image/jpeg');

			const input = document.getElementById('file-input') as HTMLInputElement;
			Object.defineProperty(input, 'files', { value: [file] });
			await fireEvent.change(input);

			await fireEvent.click(screen.getByRole('button', { name: /extract recipe/i }));

			const form = screen.getByRole('tabpanel').closest('[aria-busy]');
			expect(form).toHaveAttribute('aria-busy', 'true');
		});
	});
});
