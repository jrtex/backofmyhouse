import { http, HttpResponse } from 'msw';

// Mock user data
const mockUser = {
	id: 'test-user-id',
	username: 'testuser',
	email: 'test@example.com',
	role: 'standard' as const,
	created_at: '2024-01-01T00:00:00Z',
	updated_at: '2024-01-01T00:00:00Z'
};

const mockAdminUser = {
	...mockUser,
	id: 'admin-user-id',
	username: 'admin',
	email: 'admin@example.com',
	role: 'admin' as const
};

// Mock recipe data
const mockRecipe = {
	id: 'recipe-1',
	title: 'Test Recipe',
	description: 'A test recipe',
	ingredients: [{ name: 'Salt', quantity: '1', unit: 'tsp' }],
	instructions: [{ step_number: 1, text: 'Mix well' }],
	prep_time_minutes: 10,
	cook_time_minutes: 20,
	servings: 4,
	notes: null,
	category: { id: 'cat-1', name: 'Main Course', description: null, created_at: '2024-01-01T00:00:00Z' },
	tags: [{ id: 'tag-1', name: 'quick', created_at: '2024-01-01T00:00:00Z' }],
	user: mockUser,
	created_at: '2024-01-01T00:00:00Z',
	updated_at: '2024-01-01T00:00:00Z'
};

const mockCategory = {
	id: 'cat-1',
	name: 'Main Course',
	description: 'Main course dishes',
	created_at: '2024-01-01T00:00:00Z'
};

const mockTag = {
	id: 'tag-1',
	name: 'quick',
	created_at: '2024-01-01T00:00:00Z'
};

export const handlers = [
	// Auth endpoints
	http.post('/api/auth/register', async ({ request }) => {
		const body = await request.json() as { username: string; email: string; password: string };
		return HttpResponse.json({
			message: 'User registered successfully',
			role: 'standard'
		}, { status: 201 });
	}),

	http.post('/api/auth/login', async ({ request }) => {
		const body = await request.json() as { username: string; password: string };
		if (body.username === 'testuser' && body.password === 'password123') {
			return HttpResponse.json({ message: 'Login successful' });
		}
		return HttpResponse.json({ detail: 'Invalid username or password' }, { status: 401 });
	}),

	http.post('/api/auth/logout', () => {
		return HttpResponse.json({ message: 'Logged out successfully' });
	}),

	http.get('/api/auth/me', () => {
		return HttpResponse.json(mockUser);
	}),

	http.post('/api/auth/refresh', () => {
		return HttpResponse.json({ message: 'Token refreshed successfully' });
	}),

	// Recipe endpoints
	http.get('/api/recipes', () => {
		return HttpResponse.json([mockRecipe]);
	}),

	http.get('/api/recipes/:id', ({ params }) => {
		if (params.id === 'recipe-1') {
			return HttpResponse.json(mockRecipe);
		}
		return HttpResponse.json({ detail: 'Recipe not found' }, { status: 404 });
	}),

	http.post('/api/recipes', async ({ request }) => {
		const body = await request.json() as Record<string, unknown>;
		return HttpResponse.json({
			...mockRecipe,
			...body,
			id: 'new-recipe-id'
		}, { status: 201 });
	}),

	http.put('/api/recipes/:id', async ({ params, request }) => {
		const body = await request.json() as Record<string, unknown>;
		return HttpResponse.json({
			...mockRecipe,
			...body
		});
	}),

	http.delete('/api/recipes/:id', () => {
		return new HttpResponse(null, { status: 204 });
	}),

	// Category endpoints
	http.get('/api/categories', () => {
		return HttpResponse.json([mockCategory]);
	}),

	http.post('/api/categories', async ({ request }) => {
		const body = await request.json() as Record<string, unknown>;
		return HttpResponse.json({
			...mockCategory,
			...body,
			id: 'new-cat-id'
		}, { status: 201 });
	}),

	http.put('/api/categories/:id', async ({ request }) => {
		const body = await request.json() as Record<string, unknown>;
		return HttpResponse.json({
			...mockCategory,
			...body
		});
	}),

	http.delete('/api/categories/:id', () => {
		return new HttpResponse(null, { status: 204 });
	}),

	// Tag endpoints
	http.get('/api/tags', () => {
		return HttpResponse.json([mockTag]);
	}),

	http.post('/api/tags', async ({ request }) => {
		const body = await request.json() as Record<string, unknown>;
		return HttpResponse.json({
			...mockTag,
			...body,
			id: 'new-tag-id'
		}, { status: 201 });
	}),

	http.delete('/api/tags/:id', () => {
		return new HttpResponse(null, { status: 204 });
	}),

	// User endpoints (admin)
	http.get('/api/users', () => {
		return HttpResponse.json([mockUser, mockAdminUser]);
	}),

	http.post('/api/users', async ({ request }) => {
		const body = await request.json() as Record<string, unknown>;
		return HttpResponse.json({
			...mockUser,
			...body,
			id: 'new-user-id'
		}, { status: 201 });
	}),

	http.put('/api/users/:id', async ({ request }) => {
		const body = await request.json() as Record<string, unknown>;
		return HttpResponse.json({
			...mockUser,
			...body
		});
	}),

	http.delete('/api/users/:id', () => {
		return new HttpResponse(null, { status: 204 });
	})
];
