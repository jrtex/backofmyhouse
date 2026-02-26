<script lang="ts">
	import { fly } from 'svelte/transition';
	import type { Ingredient } from '$lib/api';
	import { groupBySection } from '$lib/utils/groupBySection';

	export let open = false;
	export let ingredients: Ingredient[] = [];
	export let onClose: () => void;
</script>

{#if open}
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<div class="fixed inset-0 z-50 flex justify-end" on:click={onClose}>
		<div class="absolute inset-0 bg-black/40" />
		<div
			class="relative w-80 max-w-[85vw] bg-white h-full shadow-xl flex flex-col"
			transition:fly={{ x: 320, duration: 250 }}
			on:click|stopPropagation
		>
			<div class="flex items-center justify-between p-4 border-b">
				<h2 class="text-lg font-semibold">Ingredients</h2>
				<button
					on:click={onClose}
					class="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100"
					aria-label="Close ingredients panel"
				>
					<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>
			<div class="flex-1 overflow-y-auto p-4">
				{#each groupBySection(ingredients) as group}
					{#if group.section}
						<h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mt-4 mb-2 first:mt-0">{group.section}</h3>
					{/if}
					<ul class="space-y-2">
						{#each group.items as ing}
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
				{/each}
			</div>
		</div>
	</div>
{/if}
