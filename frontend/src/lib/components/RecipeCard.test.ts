import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import RecipeCard from './RecipeCard.svelte';
import type { RecipeListItem } from '$lib/api';

const baseRecipe: RecipeListItem = {
	id: 'recipe-1',
	title: 'Test Recipe',
	description: 'A delicious test recipe',
	prep_time_minutes: 15,
	cook_time_minutes: 30,
	servings: 4,
	category: {
		id: 'cat-1',
		name: 'Main Course',
		description: 'Main dishes',
		created_at: '2024-01-01T00:00:00Z'
	},
	tags: [
		{ id: 'tag-1', name: 'quick', created_at: '2024-01-01T00:00:00Z' },
		{ id: 'tag-2', name: 'easy', created_at: '2024-01-01T00:00:00Z' }
	],
	user: {
		id: 'user-1',
		username: 'chef',
		email: 'chef@example.com',
		role: 'standard',
		created_at: '2024-01-01T00:00:00Z',
		updated_at: '2024-01-01T00:00:00Z'
	},
	created_at: '2024-01-01T00:00:00Z'
};

describe('RecipeCard', () => {
	describe('basic rendering', () => {
		it('should render recipe title', () => {
			render(RecipeCard, { props: { recipe: baseRecipe } });
			expect(screen.getByText('Test Recipe')).toBeInTheDocument();
		});

		it('should render recipe description', () => {
			render(RecipeCard, { props: { recipe: baseRecipe } });
			expect(screen.getByText('A delicious test recipe')).toBeInTheDocument();
		});

		it('should link to recipe detail page', () => {
			render(RecipeCard, { props: { recipe: baseRecipe } });
			const link = screen.getByRole('link');
			expect(link).toHaveAttribute('href', '/recipes/recipe-1');
		});
	});

	describe('gradient placeholder', () => {
		it('should render a gradient placeholder element', () => {
			const { container } = render(RecipeCard, { props: { recipe: baseRecipe } });
			const gradient = container.querySelector('.h-48');
			expect(gradient).toBeInTheDocument();
			expect(gradient?.className).toContain('bg-gradient-to-br');
		});

		it('should produce deterministic gradient for same id', () => {
			const { container: c1 } = render(RecipeCard, { props: { recipe: baseRecipe } });
			const { container: c2 } = render(RecipeCard, { props: { recipe: baseRecipe } });
			const g1 = c1.querySelector('.h-48')?.className;
			const g2 = c2.querySelector('.h-48')?.className;
			expect(g1).toBe(g2);
		});
	});

	describe('category display', () => {
		it('should display category when present', () => {
			render(RecipeCard, { props: { recipe: baseRecipe } });
			expect(screen.getByText('Main Course')).toBeInTheDocument();
		});

		it('should not display category when absent', () => {
			const recipeWithoutCategory = {
				...baseRecipe,
				category: undefined
			};
			render(RecipeCard, { props: { recipe: recipeWithoutCategory } });
			expect(screen.queryByText('Main Course')).not.toBeInTheDocument();
		});
	});

	describe('tags display', () => {
		it('should display up to 2 tags', () => {
			render(RecipeCard, { props: { recipe: baseRecipe } });
			expect(screen.getByText('quick')).toBeInTheDocument();
			expect(screen.getByText('easy')).toBeInTheDocument();
		});

		it('should truncate to max 2 tags', () => {
			const recipeWithManyTags = {
				...baseRecipe,
				tags: [
					{ id: 'tag-1', name: 'quick', created_at: '2024-01-01T00:00:00Z' },
					{ id: 'tag-2', name: 'easy', created_at: '2024-01-01T00:00:00Z' },
					{ id: 'tag-3', name: 'healthy', created_at: '2024-01-01T00:00:00Z' }
				]
			};
			render(RecipeCard, { props: { recipe: recipeWithManyTags } });
			expect(screen.getByText('quick')).toBeInTheDocument();
			expect(screen.getByText('easy')).toBeInTheDocument();
			expect(screen.queryByText('healthy')).not.toBeInTheDocument();
		});

		it('should handle empty tags array', () => {
			const recipeWithoutTags = {
				...baseRecipe,
				tags: []
			};
			render(RecipeCard, { props: { recipe: recipeWithoutTags } });
			expect(screen.getByText('Test Recipe')).toBeInTheDocument();
		});
	});

	describe('time display', () => {
		it('should display total time', () => {
			render(RecipeCard, { props: { recipe: baseRecipe } });
			expect(screen.getByText('45m')).toBeInTheDocument();
		});

		it('should display time in hours and minutes for longer recipes', () => {
			const longRecipe = {
				...baseRecipe,
				prep_time_minutes: 30,
				cook_time_minutes: 90
			};
			render(RecipeCard, { props: { recipe: longRecipe } });
			expect(screen.getByText('2h')).toBeInTheDocument();
		});

		it('should display hours and minutes for mixed times', () => {
			const mixedTimeRecipe = {
				...baseRecipe,
				prep_time_minutes: 30,
				cook_time_minutes: 45
			};
			render(RecipeCard, { props: { recipe: mixedTimeRecipe } });
			expect(screen.getByText('1h 15m')).toBeInTheDocument();
		});

		it('should not display time when both are undefined', () => {
			const recipeWithoutTime = {
				...baseRecipe,
				prep_time_minutes: undefined,
				cook_time_minutes: undefined
			};
			render(RecipeCard, { props: { recipe: recipeWithoutTime } });
			expect(screen.queryByText(/^\d+[hm]/)).not.toBeInTheDocument();
		});

		it('should display time when only prep time is set', () => {
			const prepOnlyRecipe = {
				...baseRecipe,
				prep_time_minutes: 20,
				cook_time_minutes: undefined
			};
			render(RecipeCard, { props: { recipe: prepOnlyRecipe } });
			expect(screen.getByText('20m')).toBeInTheDocument();
		});

		it('should display time when only cook time is set', () => {
			const cookOnlyRecipe = {
				...baseRecipe,
				prep_time_minutes: undefined,
				cook_time_minutes: 45
			};
			render(RecipeCard, { props: { recipe: cookOnlyRecipe } });
			expect(screen.getByText('45m')).toBeInTheDocument();
		});
	});

	describe('servings display', () => {
		it('should display servings count', () => {
			render(RecipeCard, { props: { recipe: baseRecipe } });
			expect(screen.getByText('4 servings')).toBeInTheDocument();
		});

		it('should not display servings when undefined', () => {
			const recipeWithoutServings = {
				...baseRecipe,
				servings: undefined
			};
			render(RecipeCard, { props: { recipe: recipeWithoutServings } });
			expect(screen.queryByText(/servings$/)).not.toBeInTheDocument();
		});
	});

	describe('description display', () => {
		it('should not render description paragraph when absent', () => {
			const recipeWithoutDescription = {
				...baseRecipe,
				description: undefined
			};
			render(RecipeCard, { props: { recipe: recipeWithoutDescription } });
			expect(screen.queryByText('A delicious test recipe')).not.toBeInTheDocument();
		});

		it('should render empty string description', () => {
			const recipeWithEmptyDescription = {
				...baseRecipe,
				description: ''
			};
			render(RecipeCard, { props: { recipe: recipeWithEmptyDescription } });
			expect(screen.queryByRole('paragraph')).not.toBeInTheDocument();
		});
	});

	describe('styling', () => {
		it('should have card styling classes', () => {
			render(RecipeCard, { props: { recipe: baseRecipe } });
			const link = screen.getByRole('link');
			expect(link).toHaveClass('bg-white', 'rounded-xl', 'shadow-sm');
		});

		it('should have category badge styling', () => {
			render(RecipeCard, { props: { recipe: baseRecipe } });
			const categoryBadge = screen.getByText('Main Course');
			expect(categoryBadge).toHaveClass('bg-primary-100', 'text-primary-700');
		});

		it('should have tag badge styling', () => {
			render(RecipeCard, { props: { recipe: baseRecipe } });
			const tagBadge = screen.getByText('quick');
			expect(tagBadge).toHaveClass('bg-amber-100', 'text-amber-700');
		});
	});
});
