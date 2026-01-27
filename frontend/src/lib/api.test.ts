import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import { api } from './api';

describe('API Client', () => {
	describe('Auth', () => {
		describe('register', () => {
			it('should register a new user successfully', async () => {
				const result = await api.register({
					username: 'newuser',
					email: 'new@example.com',
					password: 'password123'
				});

				expect(result.error).toBeUndefined();
				expect(result.data).toEqual({
					message: 'User registered successfully',
					role: 'standard'
				});
			});

			it('should return error on failed registration', async () => {
				server.use(
					http.post('/api/auth/register', () => {
						return HttpResponse.json(
							{ detail: 'Username already registered' },
							{ status: 400 }
						);
					})
				);

				const result = await api.register({
					username: 'existing',
					email: 'existing@example.com',
					password: 'password123'
				});

				expect(result.error).toBe('Username already registered');
				expect(result.data).toBeUndefined();
			});
		});

		describe('login', () => {
			it('should login successfully with valid credentials', async () => {
				const result = await api.login({
					username: 'testuser',
					password: 'password123'
				});

				expect(result.error).toBeUndefined();
				expect(result.data).toEqual({ message: 'Login successful' });
			});

			it('should return error with invalid credentials', async () => {
				const result = await api.login({
					username: 'testuser',
					password: 'wrongpassword'
				});

				expect(result.error).toBe('Invalid username or password');
				expect(result.data).toBeUndefined();
			});
		});

		describe('logout', () => {
			it('should logout successfully', async () => {
				const result = await api.logout();

				expect(result.error).toBeUndefined();
				expect(result.data).toEqual({ message: 'Logged out successfully' });
			});
		});

		describe('getMe', () => {
			it('should return current user', async () => {
				const result = await api.getMe();

				expect(result.error).toBeUndefined();
				expect(result.data).toBeDefined();
				expect(result.data?.username).toBe('testuser');
				expect(result.data?.email).toBe('test@example.com');
			});

			it('should return error when not authenticated', async () => {
				server.use(
					http.get('/api/auth/me', () => {
						return HttpResponse.json(
							{ detail: 'Not authenticated' },
							{ status: 401 }
						);
					})
				);

				const result = await api.getMe();

				expect(result.error).toBe('Not authenticated');
			});
		});

		describe('refreshToken', () => {
			it('should refresh token successfully', async () => {
				const result = await api.refreshToken();

				expect(result.error).toBeUndefined();
				expect(result.data).toEqual({ message: 'Token refreshed successfully' });
			});
		});
	});

	describe('Recipes', () => {
		describe('getRecipes', () => {
			it('should return list of recipes', async () => {
				const result = await api.getRecipes();

				expect(result.error).toBeUndefined();
				expect(result.data).toHaveLength(1);
				expect(result.data?.[0].title).toBe('Test Recipe');
			});

			it('should pass query parameters', async () => {
				server.use(
					http.get('/api/recipes', ({ request }) => {
						const url = new URL(request.url);
						const search = url.searchParams.get('search');
						if (search === 'test') {
							return HttpResponse.json([]);
						}
						return HttpResponse.json([{ id: '1', title: 'Test' }]);
					})
				);

				const result = await api.getRecipes({ search: 'test' });

				expect(result.error).toBeUndefined();
				expect(result.data).toEqual([]);
			});
		});

		describe('getRecipe', () => {
			it('should return a single recipe', async () => {
				const result = await api.getRecipe('recipe-1');

				expect(result.error).toBeUndefined();
				expect(result.data?.title).toBe('Test Recipe');
				expect(result.data?.ingredients).toHaveLength(1);
			});

			it('should return error for non-existent recipe', async () => {
				const result = await api.getRecipe('non-existent');

				expect(result.error).toBe('Recipe not found');
			});
		});

		describe('createRecipe', () => {
			it('should create a recipe', async () => {
				const newRecipe = {
					title: 'New Recipe',
					ingredients: [{ name: 'Sugar', quantity: '1', unit: 'cup' }],
					instructions: [{ step_number: 1, text: 'Mix' }],
					tag_ids: []
				};

				const result = await api.createRecipe(newRecipe);

				expect(result.error).toBeUndefined();
				expect(result.data?.title).toBe('New Recipe');
			});
		});

		describe('updateRecipe', () => {
			it('should update a recipe', async () => {
				const result = await api.updateRecipe('recipe-1', {
					title: 'Updated Recipe'
				});

				expect(result.error).toBeUndefined();
				expect(result.data?.title).toBe('Updated Recipe');
			});
		});

		describe('deleteRecipe', () => {
			it('should delete a recipe', async () => {
				const result = await api.deleteRecipe('recipe-1');

				expect(result.error).toBeUndefined();
			});
		});
	});

	describe('Categories', () => {
		describe('getCategories', () => {
			it('should return list of categories', async () => {
				const result = await api.getCategories();

				expect(result.error).toBeUndefined();
				expect(result.data).toHaveLength(1);
				expect(result.data?.[0].name).toBe('Main Course');
			});
		});

		describe('createCategory', () => {
			it('should create a category', async () => {
				const result = await api.createCategory({
					name: 'Desserts',
					description: 'Sweet treats'
				});

				expect(result.error).toBeUndefined();
				expect(result.data?.name).toBe('Desserts');
			});
		});

		describe('updateCategory', () => {
			it('should update a category', async () => {
				const result = await api.updateCategory('cat-1', {
					name: 'Updated Category'
				});

				expect(result.error).toBeUndefined();
			});
		});

		describe('deleteCategory', () => {
			it('should delete a category', async () => {
				const result = await api.deleteCategory('cat-1');

				expect(result.error).toBeUndefined();
			});
		});
	});

	describe('Tags', () => {
		describe('getTags', () => {
			it('should return list of tags', async () => {
				const result = await api.getTags();

				expect(result.error).toBeUndefined();
				expect(result.data).toHaveLength(1);
				expect(result.data?.[0].name).toBe('quick');
			});
		});

		describe('createTag', () => {
			it('should create a tag', async () => {
				const result = await api.createTag({ name: 'vegetarian' });

				expect(result.error).toBeUndefined();
				expect(result.data?.name).toBe('vegetarian');
			});
		});

		describe('deleteTag', () => {
			it('should delete a tag', async () => {
				const result = await api.deleteTag('tag-1');

				expect(result.error).toBeUndefined();
			});
		});
	});

	describe('Users', () => {
		describe('getUsers', () => {
			it('should return list of users', async () => {
				const result = await api.getUsers();

				expect(result.error).toBeUndefined();
				expect(result.data).toHaveLength(2);
			});
		});

		describe('createUser', () => {
			it('should create a user', async () => {
				const result = await api.createUser({
					username: 'newuser',
					email: 'new@example.com',
					password: 'password123'
				});

				expect(result.error).toBeUndefined();
				expect(result.data?.username).toBe('newuser');
			});
		});

		describe('updateUser', () => {
			it('should update a user', async () => {
				const result = await api.updateUser('user-1', {
					username: 'updateduser'
				});

				expect(result.error).toBeUndefined();
			});
		});

		describe('deleteUser', () => {
			it('should delete a user', async () => {
				const result = await api.deleteUser('user-1');

				expect(result.error).toBeUndefined();
			});
		});
	});

	describe('Settings', () => {
		describe('getSettings', () => {
			it('should return settings', async () => {
				const result = await api.getSettings();

				expect(result.error).toBeUndefined();
				expect(result.data).toBeDefined();
				expect(result.data?.ai_provider).toBeNull();
				expect(result.data?.openai_api_key_configured).toBe(false);
				expect(result.data?.anthropic_api_key_configured).toBe(false);
				expect(result.data?.gemini_api_key_configured).toBe(false);
			});

			it('should return error when not admin', async () => {
				server.use(
					http.get('/api/settings', () => {
						return HttpResponse.json(
							{ detail: 'Admin access required' },
							{ status: 403 }
						);
					})
				);

				const result = await api.getSettings();

				expect(result.error).toBe('Admin access required');
			});
		});

		describe('updateSettings', () => {
			it('should update AI provider', async () => {
				const result = await api.updateSettings({
					ai_provider: 'openai'
				});

				expect(result.error).toBeUndefined();
				expect(result.data?.ai_provider).toBe('openai');
			});

			it('should update API key', async () => {
				const result = await api.updateSettings({
					openai_api_key: 'sk-test-key'
				});

				expect(result.error).toBeUndefined();
				expect(result.data?.openai_api_key_configured).toBe(true);
			});

			it('should return error for invalid API key', async () => {
				server.use(
					http.put('/api/settings', () => {
						return HttpResponse.json(
							{ detail: 'Invalid OPENAI API key' },
							{ status: 400 }
						);
					})
				);

				const result = await api.updateSettings({
					openai_api_key: 'invalid-key'
				});

				expect(result.error).toBe('Invalid OPENAI API key');
			});
		});
	});

	describe('Error Handling', () => {
		it('should handle network errors', async () => {
			server.use(
				http.get('/api/auth/me', () => {
					return HttpResponse.error();
				})
			);

			const result = await api.getMe();

			expect(result.error).toBe('Network error. Please try again.');
		});

		it('should handle non-JSON error responses', async () => {
			server.use(
				http.get('/api/recipes', () => {
					return new HttpResponse('Server Error', { status: 500 });
				})
			);

			const result = await api.getRecipes();

			expect(result.error).toBe('Error: 500');
		});
	});
});
