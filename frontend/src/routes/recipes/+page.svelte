<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
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
	let searchTimeout: ReturnType<typeof setTimeout>;

	$: if (!$isAuthenticated) {
		goto('/login');
	}

	// Pick up category from URL query param (sidebar links)
	$: {
		const urlCategory = $page.url.searchParams.get('category') || '';
		if (urlCategory !== selectedCategory) {
			selectedCategory = urlCategory;
		}
	}

	// Auto-filter on search/category/tag changes (debounce search)
	$: {
		// Track dependencies
		selectedCategory;
		selectedTag;
		if (!loading) {
			applyFilters();
		}
	}

	$: {
		searchQuery;
		if (!loading) {
			clearTimeout(searchTimeout);
			searchTimeout = setTimeout(applyFilters, 300);
		}
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

		// Apply initial category filter from URL
		const urlCategory = $page.url.searchParams.get('category') || '';
		if (urlCategory) {
			selectedCategory = urlCategory;
			applyFilters();
		}
	}

	async function applyFilters() {
		const params: Record<string, string> = {};
		if (selectedCategory) params.category_id = selectedCategory;
		if (selectedTag) params.tag_id = selectedTag;
		if (searchQuery) params.search = searchQuery;

		const { data, error: err } = await api.getRecipes(params);
		if (!err) {
			recipes = data || [];
		}
	}

	function toggleTag(tagId: string) {
		selectedTag = selectedTag === tagId ? '' : tagId;
	}

	function clearFilters() {
		selectedCategory = '';
		selectedTag = '';
		searchQuery = '';
		loadData();
	}
</script>

<div class="px-4 sm:px-6 lg:px-8 py-8 max-w-7xl">
	<!-- Header -->
	<div class="flex justify-between items-center mb-6">
		<h1 class="text-2xl font-bold text-gray-900">Recipe Library</h1>
		<a
			href="/recipes/new"
			class="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg font-medium"
		>
			Create Recipe
		</a>
	</div>

	<!-- Search + Category filter -->
	<div class="flex flex-col sm:flex-row gap-3 mb-4">
		<div class="relative flex-1">
			<svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
			</svg>
			<input
				type="text"
				bind:value={searchQuery}
				placeholder="Search recipes..."
				class="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
			/>
		</div>
		<select
			bind:value={selectedCategory}
			class="px-3 py-2.5 border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
		>
			<option value="">All Categories</option>
			{#each categories as category}
				<option value={category.id}>{category.name}</option>
			{/each}
		</select>
	</div>

	<!-- Tag filter chips -->
	{#if tags.length > 0}
		<div class="flex flex-wrap gap-2 mb-6">
			{#each tags as tag}
				<button
					on:click={() => toggleTag(tag.id)}
					class="px-3 py-1 rounded-full text-sm transition-colors
						{selectedTag === tag.id
							? 'bg-primary-600 text-white'
							: 'bg-white border border-gray-200 text-gray-600 hover:border-gray-300'}"
				>
					{tag.name}
				</button>
			{/each}
		</div>
	{/if}

	{#if error}
		<div class="p-4 bg-red-100 text-red-700 rounded-md mb-6">{error}</div>
	{/if}

	{#if loading}
		<div class="text-center py-12 text-gray-500">Loading recipes...</div>
	{:else if recipes.length === 0}
		<div class="text-center py-12 text-gray-500">
			No recipes found.
			<a href="/recipes/new" class="text-primary-600 hover:underline">Create one!</a>
		</div>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
			{#each recipes as recipe}
				<RecipeCard {recipe} />
			{/each}
		</div>
	{/if}
</div>
