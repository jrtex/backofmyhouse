<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type RecipeListItem, type Category, type Tag } from '$lib/api';
	import { isAuthenticated } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import RecipeCard from '$lib/components/RecipeCard.svelte';

	let recipes: RecipeListItem[] = [];
	let categories: Category[] = [];
	let tags: Tag[] = [];
	let loading = true;
	let error = '';

	let selectedCategory = '';
	let selectedTag = '';
	let searchQuery = '';

	$: if (!$isAuthenticated) {
		goto('/login');
	}

	onMount(loadData);

	async function loadData() {
		loading = true;
		error = '';

		const [recipesRes, categoriesRes, tagsRes] = await Promise.all([
			api.getRecipes(),
			api.getCategories(),
			api.getTags()
		]);

		if (recipesRes.error) {
			error = recipesRes.error;
		} else {
			recipes = recipesRes.data || [];
		}

		categories = categoriesRes.data || [];
		tags = tagsRes.data || [];
		loading = false;
	}

	async function applyFilters() {
		loading = true;
		const params: Record<string, string> = {};
		if (selectedCategory) params.category_id = selectedCategory;
		if (selectedTag) params.tag_id = selectedTag;
		if (searchQuery) params.search = searchQuery;

		const { data, error: err } = await api.getRecipes(params);
		if (!err) {
			recipes = data || [];
		}
		loading = false;
	}

	function clearFilters() {
		selectedCategory = '';
		selectedTag = '';
		searchQuery = '';
		loadData();
	}
</script>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	<div class="flex justify-between items-center mb-6">
		<h1 class="text-2xl font-bold text-gray-900">Recipes</h1>
		<div class="flex gap-2">
			<a
				href="/recipes/import"
				class="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-md font-medium"
			>
				Import
			</a>
			<a
				href="/recipes/new"
				class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium"
			>
				New Recipe
			</a>
		</div>
	</div>

	<div class="bg-white p-4 rounded-lg shadow-sm border mb-6">
		<div class="grid grid-cols-1 md:grid-cols-4 gap-4">
			<div>
				<label for="search" class="block text-sm font-medium text-gray-700 mb-1">Search</label>
				<input
					type="text"
					id="search"
					bind:value={searchQuery}
					placeholder="Search recipes..."
					class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
				/>
			</div>
			<div>
				<label for="category" class="block text-sm font-medium text-gray-700 mb-1">Category</label>
				<select
					id="category"
					bind:value={selectedCategory}
					class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
				>
					<option value="">All Categories</option>
					{#each categories as category}
						<option value={category.id}>{category.name}</option>
					{/each}
				</select>
			</div>
			<div>
				<label for="tag" class="block text-sm font-medium text-gray-700 mb-1">Tag</label>
				<select
					id="tag"
					bind:value={selectedTag}
					class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
				>
					<option value="">All Tags</option>
					{#each tags as tag}
						<option value={tag.id}>{tag.name}</option>
					{/each}
				</select>
			</div>
			<div class="flex items-end gap-2">
				<button
					on:click={applyFilters}
					class="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-md font-medium"
				>
					Filter
				</button>
				<button
					on:click={clearFilters}
					class="px-4 py-2 text-gray-500 hover:text-gray-700"
				>
					Clear
				</button>
			</div>
		</div>
	</div>

	{#if error}
		<div class="p-4 bg-red-100 text-red-700 rounded-md mb-6">{error}</div>
	{/if}

	{#if loading}
		<div class="text-center py-12 text-gray-500">Loading recipes...</div>
	{:else if recipes.length === 0}
		<div class="text-center py-12 text-gray-500">
			No recipes found.
			<a href="/recipes/new" class="text-blue-600 hover:underline">Create one!</a>
		</div>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
			{#each recipes as recipe}
				<RecipeCard {recipe} />
			{/each}
		</div>
	{/if}
</div>
