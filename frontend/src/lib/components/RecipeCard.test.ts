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

		it('should show author username', () => {
			render(RecipeCard, { props: { recipe: baseRecipe } });
			expect(screen.getByText('by chef')).toBeInTheDocument();
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
		it('should display all tags', () => {
			render(RecipeCard, { props: { recipe: baseRecipe } });
			expect(screen.getByText('quick')).toBeInTheDocument();
			expect(screen.getByText('easy')).toBeInTheDocument();
		});

		it('should handle empty tags array', () => {
			const recipeWithoutTags = {
				...baseRecipe,
				tags: []
			};
			render(RecipeCard, { props: { recipe: recipeWithoutTags } });
			// Should render without errors
			expect(screen.getByText('Test Recipe')).toBeInTheDocument();
		});
	});

	describe('time display', () => {
		it('should display total time', () => {
			render(RecipeCard, { props: { recipe: baseRecipe } });
			expect(screen.getByText('45m total')).toBeInTheDocument();
		});

		it('should display time in hours and minutes for longer recipes', () => {
			const longRecipe = {
				...baseRecipe,
				prep_time_minutes: 30,
				cook_time_minutes: 90 // Total: 2h
			};
			render(RecipeCard, { props: { recipe: longRecipe } });
			expect(screen.getByText('2h total')).toBeInTheDocument();
		});

		it('should display hours and minutes for mixed times', () => {
			const mixedTimeRecipe = {
				...baseRecipe,
				prep_time_minutes: 30,
				cook_time_minutes: 45 // Total: 1h 15m
			};
			render(RecipeCard, { props: { recipe: mixedTimeRecipe } });
			expect(screen.getByText('1h 15m total')).toBeInTheDocument();
		});

		it('should not display time when both are undefined', () => {
			const recipeWithoutTime = {
				...baseRecipe,
				prep_time_minutes: undefined,
				cook_time_minutes: undefined
			};
			render(RecipeCard, { props: { recipe: recipeWithoutTime } });
			expect(screen.queryByText(/total$/)).not.toBeInTheDocument();
		});

		it('should display time when only prep time is set', () => {
			const prepOnlyRecipe = {
				...baseRecipe,
				prep_time_minutes: 20,
				cook_time_minutes: undefined
			};
			render(RecipeCard, { props: { recipe: prepOnlyRecipe } });
			expect(screen.getByText('20m total')).toBeInTheDocument();
		});

		it('should display time when only cook time is set', () => {
			const cookOnlyRecipe = {
				...baseRecipe,
				prep_time_minutes: undefined,
				cook_time_minutes: 45
			};
			render(RecipeCard, { props: { recipe: cookOnlyRecipe } });
			expect(screen.getByText('45m total')).toBeInTheDocument();
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
			// Empty string is falsy, so should not render
			expect(screen.queryByRole('paragraph')).not.toBeInTheDocument();
		});
	});

	describe('styling', () => {
		it('should have card styling classes', () => {
			render(RecipeCard, { props: { recipe: baseRecipe } });
			const link = screen.getByRole('link');
			expect(link).toHaveClass('bg-white', 'rounded-lg', 'shadow-sm');
		});

		it('should have category badge styling', () => {
			render(RecipeCard, { props: { recipe: baseRecipe } });
			const categoryBadge = screen.getByText('Main Course');
			expect(categoryBadge).toHaveClass('bg-blue-100', 'text-blue-800');
		});

		it('should have tag badge styling', () => {
			render(RecipeCard, { props: { recipe: baseRecipe } });
			const tagBadge = screen.getByText('quick');
			expect(tagBadge).toHaveClass('bg-gray-100', 'text-gray-700');
		});
	});
});
