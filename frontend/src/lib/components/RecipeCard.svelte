<script lang="ts">
	import type { RecipeListItem } from '$lib/api';

	export let recipe: RecipeListItem;

	function formatTime(minutes: number | undefined): string {
		if (!minutes) return '';
		if (minutes < 60) return `${minutes}m`;
		const hours = Math.floor(minutes / 60);
		const mins = minutes % 60;
		return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
	}
</script>

<a
	href="/recipes/{recipe.id}"
	class="block bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow"
>
	<div class="p-5">
		<h3 class="text-lg font-semibold text-gray-900 mb-2">{recipe.title}</h3>
		{#if recipe.description}
			<p class="text-gray-600 text-sm mb-3 line-clamp-2">{recipe.description}</p>
		{/if}
		<div class="flex flex-wrap gap-2 mb-3">
			{#if recipe.category}
				<span class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
					{recipe.category.name}
				</span>
			{/if}
			{#each recipe.tags as tag}
				<span class="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded">
					{tag.name}
				</span>
			{/each}
		</div>
		<div class="flex items-center text-sm text-gray-500 gap-4">
			{#if recipe.prep_time_minutes || recipe.cook_time_minutes}
				<span>
					{formatTime((recipe.prep_time_minutes || 0) + (recipe.cook_time_minutes || 0))} total
				</span>
			{/if}
			{#if recipe.servings}
				<span>{recipe.servings} servings</span>
			{/if}
		</div>
		<div class="mt-3 text-xs text-gray-400">
			by {recipe.user.username}
		</div>
	</div>
</a>
