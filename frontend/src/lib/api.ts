const API_BASE = '/api';

interface ApiResponse<T> {
	data?: T;
	error?: string;
}

async function request<T>(
	endpoint: string,
	options: RequestInit = {}
): Promise<ApiResponse<T>> {
	try {
		const response = await fetch(`${API_BASE}${endpoint}`, {
			...options,
			headers: {
				'Content-Type': 'application/json',
				...options.headers
			},
			credentials: 'include'
		});

		if (!response.ok) {
			const errorData = await response.json().catch(() => ({}));
			return { error: errorData.detail || `Error: ${response.status}` };
		}

		if (response.status === 204) {
			return { data: undefined as T };
		}

		const data = await response.json();
		return { data };
	} catch (err) {
		return { error: 'Network error. Please try again.' };
	}
}

export const api = {
	// Auth
	register: (data: { username: string; email: string; password: string }) =>
		request<{ message: string; role: string }>('/auth/register', {
			method: 'POST',
			body: JSON.stringify(data)
		}),

	login: (data: { username: string; password: string }) =>
		request<{ message: string }>('/auth/login', {
			method: 'POST',
			body: JSON.stringify(data)
		}),

	logout: () =>
		request<{ message: string }>('/auth/logout', {
			method: 'POST'
		}),

	getMe: () => request<User>('/auth/me'),

	refreshToken: () =>
		request<{ message: string }>('/auth/refresh', {
			method: 'POST'
		}),

	// Recipes
	getRecipes: (params?: {
		category_id?: string;
		tag_id?: string;
		search?: string;
		user_id?: string;
		skip?: number;
		limit?: number;
	}) => {
		const searchParams = new URLSearchParams();
		if (params) {
			Object.entries(params).forEach(([key, value]) => {
				if (value !== undefined) searchParams.append(key, String(value));
			});
		}
		const query = searchParams.toString();
		return request<RecipeListItem[]>(`/recipes${query ? `?${query}` : ''}`);
	},

	getRecipe: (id: string) => request<Recipe>(`/recipes/${id}`),

	createRecipe: (data: RecipeCreate) =>
		request<Recipe>('/recipes', {
			method: 'POST',
			body: JSON.stringify(data)
		}),

	updateRecipe: (id: string, data: RecipeUpdate) =>
		request<Recipe>(`/recipes/${id}`, {
			method: 'PUT',
			body: JSON.stringify(data)
		}),

	deleteRecipe: (id: string) =>
		request<void>(`/recipes/${id}`, {
			method: 'DELETE'
		}),

	// Categories
	getCategories: () => request<Category[]>('/categories'),

	createCategory: (data: { name: string; description?: string }) =>
		request<Category>('/categories', {
			method: 'POST',
			body: JSON.stringify(data)
		}),

	updateCategory: (id: string, data: { name?: string; description?: string }) =>
		request<Category>(`/categories/${id}`, {
			method: 'PUT',
			body: JSON.stringify(data)
		}),

	deleteCategory: (id: string) =>
		request<void>(`/categories/${id}`, {
			method: 'DELETE'
		}),

	// Tags
	getTags: () => request<Tag[]>('/tags'),

	createTag: (data: { name: string }) =>
		request<Tag>('/tags', {
			method: 'POST',
			body: JSON.stringify(data)
		}),

	deleteTag: (id: string) =>
		request<void>(`/tags/${id}`, {
			method: 'DELETE'
		}),

	// Users (admin)
	getUsers: () => request<User[]>('/users'),

	createUser: (data: { username: string; email: string; password: string }) =>
		request<User>('/users', {
			method: 'POST',
			body: JSON.stringify(data)
		}),

	updateUser: (
		id: string,
		data: { username?: string; email?: string; password?: string; role?: string }
	) =>
		request<User>(`/users/${id}`, {
			method: 'PUT',
			body: JSON.stringify(data)
		}),

	deleteUser: (id: string) =>
		request<void>(`/users/${id}`, {
			method: 'DELETE'
		}),

	// Settings (admin)
	getSettings: () => request<Settings>('/settings'),

	updateSettings: (data: SettingsUpdate) =>
		request<Settings>('/settings', {
			method: 'PUT',
			body: JSON.stringify(data)
		}),

	// Test Connection
	testConnection: (provider: AIProvider, apiKey?: string) => {
		const body: Record<string, string> = { provider };
		if (apiKey) body.api_key = apiKey;
		return request<TestConnectionResponse>('/settings/test-connection', {
			method: 'POST',
			body: JSON.stringify(body)
		});
	},

	// Import
	importFromImage: async (file: File): Promise<ApiResponse<RecipeExtraction>> => {
		const formData = new FormData();
		formData.append('file', file);
		try {
			const response = await fetch(`${API_BASE}/import/image`, {
				method: 'POST',
				body: formData,
				credentials: 'include'
			});
			if (!response.ok) {
				const errorData = await response.json().catch(() => ({}));
				return { error: errorData.detail || `Error: ${response.status}` };
			}
			return { data: await response.json() };
		} catch {
			return { error: 'Network error. Please try again.' };
		}
	},

	importFromUrl: (url: string) =>
		request<RecipeExtraction>('/import/url', {
			method: 'POST',
			body: JSON.stringify({ url })
		}),

	importFromText: (text: string) =>
		request<RecipeExtraction>('/import/text', {
			method: 'POST',
			body: JSON.stringify({ text })
		}),

	// Backup
	exportBackup: async (recipeIds?: string[]): Promise<void> => {
		const params = recipeIds?.length
			? `?${recipeIds.map((id) => `recipe_ids=${id}`).join('&')}`
			: '';
		const response = await fetch(`${API_BASE}/backup/export${params}`, {
			credentials: 'include'
		});
		if (!response.ok) {
			const errorData = await response.json().catch(() => ({}));
			throw new Error(errorData.detail || 'Export failed');
		}
		const blob = await response.blob();
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `recipes-backup-${new Date().toISOString().split('T')[0]}.json`;
		a.click();
		URL.revokeObjectURL(url);
	},

	importBackup: async (
		file: File,
		conflictStrategy: ConflictStrategy,
		selectedTitles?: string[]
	): Promise<ApiResponse<BackupImportResult>> => {
		const formData = new FormData();
		formData.append('file', file);
		try {
			let params = `conflict_strategy=${conflictStrategy}`;
			if (selectedTitles?.length) {
				params += `&${selectedTitles.map((t) => `selected_titles=${encodeURIComponent(t)}`).join('&')}`;
			}
			const response = await fetch(`${API_BASE}/backup/import?${params}`, {
				method: 'POST',
				body: formData,
				credentials: 'include'
			});
			if (!response.ok) {
				const errorData = await response.json().catch(() => ({}));
				return { error: errorData.detail || `Error: ${response.status}` };
			}
			return { data: await response.json() };
		} catch {
			return { error: 'Network error. Please try again.' };
		}
	}
};

// Types
export interface User {
	id: string;
	username: string;
	email: string;
	role: 'admin' | 'standard';
	created_at: string;
	updated_at: string;
}

export interface Category {
	id: string;
	name: string;
	description?: string;
	created_at: string;
}

export interface Tag {
	id: string;
	name: string;
	created_at: string;
}

export interface Ingredient {
	name: string;
	quantity?: string;
	unit?: string;
	notes?: string;
}

export interface Instruction {
	step_number: number;
	text: string;
}

export type RecipeComplexity = 'very_easy' | 'easy' | 'medium' | 'hard' | 'very_hard';

export interface Recipe {
	id: string;
	title: string;
	description?: string;
	ingredients: Ingredient[];
	instructions: Instruction[];
	prep_time_minutes?: number;
	cook_time_minutes?: number;
	servings?: number;
	notes?: string;
	complexity?: RecipeComplexity;
	special_equipment?: string[];
	source_author?: string;
	source_url?: string;
	category?: Category;
	user: User;
	tags: Tag[];
	created_at: string;
	updated_at: string;
}

export interface RecipeListItem {
	id: string;
	title: string;
	description?: string;
	prep_time_minutes?: number;
	cook_time_minutes?: number;
	servings?: number;
	category?: Category;
	tags: Tag[];
	user: User;
	created_at: string;
}

export interface RecipeCreate {
	title: string;
	description?: string;
	ingredients: Ingredient[];
	instructions: Instruction[];
	prep_time_minutes?: number;
	cook_time_minutes?: number;
	servings?: number;
	notes?: string;
	complexity?: RecipeComplexity;
	special_equipment?: string[];
	source_author?: string;
	source_url?: string;
	category_id?: string;
	tag_ids: string[];
}

export interface RecipeUpdate {
	title?: string;
	description?: string;
	ingredients?: Ingredient[];
	instructions?: Instruction[];
	prep_time_minutes?: number;
	cook_time_minutes?: number;
	servings?: number;
	notes?: string;
	complexity?: RecipeComplexity;
	special_equipment?: string[];
	source_author?: string;
	source_url?: string;
	category_id?: string;
	tag_ids?: string[];
}

export type AIProvider = 'openai' | 'anthropic' | 'gemini';

export interface TestConnectionResponse {
	success: boolean;
	message: string;
}

export interface Settings {
	ai_provider: AIProvider | null;
	openai_api_key_configured: boolean;
	anthropic_api_key_configured: boolean;
	gemini_api_key_configured: boolean;
	openai_model: string;
	anthropic_model: string;
	gemini_model: string;
}

export interface SettingsUpdate {
	ai_provider?: AIProvider;
	openai_api_key?: string;
	anthropic_api_key?: string;
	gemini_api_key?: string;
	openai_model?: string;
	anthropic_model?: string;
	gemini_model?: string;
}

export interface RecipeExtraction {
	title: string;
	description?: string;
	ingredients: Ingredient[];
	instructions: Instruction[];
	prep_time_minutes?: number;
	cook_time_minutes?: number;
	servings?: number;
	notes?: string;
	special_equipment?: string[];
	confidence: number;
	warnings: string[];
}

export type ConflictStrategy = 'skip' | 'replace' | 'rename';

export interface BackupImportResult {
	total_in_file: number;
	total_selected: number;
	created: number;
	skipped: number;
	replaced: number;
	errors: number;
	categories_created: number;
	tags_created: number;
	error_details: Array<{ title: string; error: string }>;
}
