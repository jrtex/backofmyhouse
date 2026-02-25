<script lang="ts">
	import type { RecipeListItem } from '$lib/api';

	export let recipe: RecipeListItem;

	const gradients = [
		'from-emerald-400 to-teal-500',
		'from-sky-400 to-blue-500',
		'from-violet-400 to-purple-500',
		'from-rose-400 to-pink-500',
		'from-amber-400 to-orange-500',
		'from-lime-400 to-green-500',
		'from-cyan-400 to-sky-500',
		'from-fuchsia-400 to-pink-500'
	];

	function getGradient(id: string): string {
		let hash = 0;
		for (let i = 0; i < id.length; i++) {
			hash = (hash * 31 + id.charCodeAt(i)) | 0;
		}
		return gradients[Math.abs(hash) % gradients.length];
	}

	function formatTime(minutes: number | undefined): string {
		if (!minutes) return '';
		if (minutes < 60) return `${minutes}m`;
		const hours = Math.floor(minutes / 60);
		const mins = minutes % 60;
		return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
	}

	$: displayTags = recipe.tags.slice(0, 2);
	$: totalTime = (recipe.prep_time_minutes || 0) + (recipe.cook_time_minutes || 0);
</script>

<a
	href="/recipes/{recipe.id}"
	class="block bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow overflow-hidden"
>
	<!-- Gradient placeholder -->
	<div class="h-48 bg-gradient-to-br {getGradient(recipe.id)}"></div>

	<div class="p-4">
		<!-- Badges -->
		<div class="flex flex-wrap gap-1.5 mb-2">
			{#if recipe.category}
				<span class="bg-primary-100 text-primary-700 text-xs px-2 py-0.5 rounded-full font-medium">
					{recipe.category.name}
				</span>
			{/if}
			{#each displayTags as tag}
				<span class="bg-amber-100 text-amber-700 text-xs px-2 py-0.5 rounded-full">
					{tag.name}
				</span>
			{/each}
		</div>

		<!-- Title -->
		<h3 class="font-semibold text-gray-900 line-clamp-1">{recipe.title}</h3>

		<!-- Description -->
		{#if recipe.description}
			<p class="text-sm text-gray-500 line-clamp-2 mt-1">{recipe.description}</p>
		{/if}

		<!-- Footer -->
		{#if totalTime || recipe.servings}
			<div class="flex items-center text-sm text-gray-400 gap-3 mt-3 pt-3 border-t border-gray-100">
				{#if totalTime}
					<span class="flex items-center gap-1">
						<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
						{formatTime(totalTime)}
					</span>
				{/if}
				{#if totalTime && recipe.servings}
					<span>&middot;</span>
				{/if}
				{#if recipe.servings}
					<span>{recipe.servings} servings</span>
				{/if}
			</div>
		{/if}
	</div>
</a>
