<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { api, type Recipe } from '$lib/api';
	import { isAuthenticated, user, isAdmin } from '$lib/stores/auth';

	let recipe: Recipe | null = null;
	let loading = true;
	let error = '';
	let deleting = false;
	let activeTab: 'main' | 'advanced' = 'main';

	$: if (!$isAuthenticated) {
		goto('/login');
	}

	$: recipeId = $page.params.id;

	onMount(async () => {
		loading = true;
		const { data, error: err } = await api.getRecipe(recipeId);
		if (err) {
			error = err;
		} else {
			recipe = data!;
		}
		loading = false;
	});

	$: canEdit = recipe && ($user?.id === recipe.user.id || $isAdmin);

	async function handleDelete() {
		if (!confirm('Are you sure you want to delete this recipe?')) return;

		deleting = true;
		const { error: err } = await api.deleteRecipe(recipeId);
		if (err) {
			error = err;
			deleting = false;
		} else {
			goto('/recipes');
		}
	}

	function formatTime(minutes: number | undefined): string {
		if (!minutes) return '-';
		if (minutes < 60) return `${minutes} min`;
		const hours = Math.floor(minutes / 60);
		const mins = minutes % 60;
		return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
	}

	function formatComplexity(complexity: string | undefined): string {
		if (!complexity) return '-';
		const labels: Record<string, string> = {
			very_easy: 'Very Easy',
			easy: 'Easy',
			medium: 'Medium',
			hard: 'Hard',
			very_hard: 'Very Hard'
		};
		return labels[complexity] || complexity;
	}

	function hasAdvancedData(recipe: Recipe): boolean {
		return !!(
			recipe.complexity ||
			(recipe.special_equipment && recipe.special_equipment.length > 0) ||
			recipe.source_author ||
			recipe.source_url
		);
	}
</script>

<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	{#if loading}
		<div class="text-center py-12 text-gray-500">Loading recipe...</div>
	{:else if error}
		<div class="p-4 bg-red-100 text-red-700 rounded-md">{error}</div>
	{:else if recipe}
		<div class="bg-white rounded-lg shadow-sm border p-6">
			<div class="flex justify-between items-start mb-6">
				<div>
					<h1 class="text-3xl font-bold text-gray-900">{recipe.title}</h1>
					<p class="text-gray-500 mt-1">by {recipe.user.username}</p>
				</div>
				{#if canEdit}
					<div class="flex gap-2">
						<a
							href="/recipes/new?edit={recipe.id}"
							class="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-md text-sm"
						>
							Edit
						</a>
						<button
							on:click={handleDelete}
							disabled={deleting}
							class="bg-red-100 hover:bg-red-200 text-red-700 px-4 py-2 rounded-md text-sm"
						>
							{deleting ? 'Deleting...' : 'Delete'}
						</button>
					</div>
				{/if}
			</div>

			{#if recipe.description}
				<p class="text-gray-700 mb-6">{recipe.description}</p>
			{/if}

			<div class="flex flex-wrap gap-2 mb-6">
				{#if recipe.category}
					<span class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
						{recipe.category.name}
					</span>
				{/if}
				{#each recipe.tags as tag}
					<span class="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm">
						{tag.name}
					</span>
				{/each}
			</div>

			<div class="grid grid-cols-3 gap-4 mb-8 p-4 bg-gray-50 rounded-lg">
				<div class="text-center">
					<div class="text-sm text-gray-500">Prep Time</div>
					<div class="font-semibold">{formatTime(recipe.prep_time_minutes)}</div>
				</div>
				<div class="text-center">
					<div class="text-sm text-gray-500">Cook Time</div>
					<div class="font-semibold">{formatTime(recipe.cook_time_minutes)}</div>
				</div>
				<div class="text-center">
					<div class="text-sm text-gray-500">Servings</div>
					<div class="font-semibold">{recipe.servings || '-'}</div>
				</div>
			</div>

			<!-- Tab Navigation -->
			<div class="border-b border-gray-200 mb-6">
				<nav class="-mb-px flex space-x-8">
					<button
						on:click={() => (activeTab = 'main')}
						class="py-2 px-1 border-b-2 font-medium text-sm {activeTab === 'main'
							? 'border-blue-500 text-blue-600'
							: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
					>
						Recipe
					</button>
					<button
						on:click={() => (activeTab = 'advanced')}
						class="py-2 px-1 border-b-2 font-medium text-sm {activeTab === 'advanced'
							? 'border-blue-500 text-blue-600'
							: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
					>
						Advanced
					</button>
				</nav>
			</div>

			{#if activeTab === 'main'}
			<div class="grid md:grid-cols-2 gap-8">
				<div>
					<h2 class="text-xl font-semibold mb-4">Ingredients</h2>
					{#if recipe.ingredients.length > 0}
						<ul class="space-y-2">
							{#each recipe.ingredients as ing}
								<li class="flex items-start">
									<span class="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
									<span>
										{#if ing.quantity}
											<span class="font-medium">{ing.quantity}</span>
										{/if}
										{#if ing.unit}
											<span>{ing.unit}</span>
										{/if}
										{ing.name}
										{#if ing.notes}
											<span class="text-gray-500 text-sm">({ing.notes})</span>
										{/if}
									</span>
								</li>
							{/each}
						</ul>
					{:else}
						<p class="text-gray-500">No ingredients listed</p>
					{/if}
				</div>

				<div>
					<h2 class="text-xl font-semibold mb-4">Instructions</h2>
					{#if recipe.instructions.length > 0}
						<ol class="space-y-4">
							{#each recipe.instructions as inst}
								<li class="flex">
									<span
										class="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm mr-3 flex-shrink-0"
									>
										{inst.step_number}
									</span>
									<span>{inst.text}</span>
								</li>
							{/each}
						</ol>
					{:else}
						<p class="text-gray-500">No instructions listed</p>
					{/if}
				</div>
			</div>

			{#if recipe.notes}
				<div class="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
					<h3 class="font-semibold text-yellow-800 mb-2">Notes</h3>
					<p class="text-yellow-700">{recipe.notes}</p>
				</div>
			{/if}
			{/if}

			{#if activeTab === 'advanced'}
			<div class="space-y-6">
				<div class="grid md:grid-cols-2 gap-6">
					<div class="bg-gray-50 p-4 rounded-lg">
						<h3 class="text-sm font-medium text-gray-500 mb-1">Complexity</h3>
						<p class="text-gray-900">{formatComplexity(recipe.complexity)}</p>
					</div>
					<div class="bg-gray-50 p-4 rounded-lg">
						<h3 class="text-sm font-medium text-gray-500 mb-1">Source</h3>
						{#if recipe.source_url}
							<p class="text-gray-900">
								{#if recipe.source_author}
									<span class="font-medium">{recipe.source_author}</span> -
								{/if}
								<a
									href={recipe.source_url}
									target="_blank"
									rel="noopener noreferrer"
									class="text-blue-600 hover:underline break-all"
								>
									{recipe.source_url}
								</a>
							</p>
						{:else if recipe.source_author}
							<p class="text-gray-900">{recipe.source_author}</p>
						{:else}
							<p class="text-gray-400">-</p>
						{/if}
					</div>
				</div>

				<div class="bg-gray-50 p-4 rounded-lg">
					<h3 class="text-sm font-medium text-gray-500 mb-2">Special Equipment</h3>
					{#if recipe.special_equipment && recipe.special_equipment.length > 0}
						<ul class="space-y-1">
							{#each recipe.special_equipment as equipment}
								<li class="flex items-center">
									<span class="w-2 h-2 bg-gray-400 rounded-full mr-2"></span>
									{equipment}
								</li>
							{/each}
						</ul>
					{:else}
						<p class="text-gray-400">No special equipment required</p>
					{/if}
				</div>
			</div>
			{/if}
		</div>
	{/if}

	<div class="mt-6">
		<a href="/recipes" class="text-blue-600 hover:underline">&larr; Back to recipes</a>
	</div>
</div>
