<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { get } from 'svelte/store';
	import { api, type Category, type Tag, type Ingredient, type Instruction, type Recipe, type RecipeComplexity } from '$lib/api';
	import { isAuthenticated } from '$lib/stores/auth';
	import { importedRecipe } from '$lib/stores/importedRecipe';

	let categories: Category[] = [];
	let tags: Tag[] = [];
	let loading = true;
	let saving = false;
	let error = '';

	let editId = '';
	let title = '';
	let description = '';
	let ingredients: Ingredient[] = [{ name: '', quantity: '', unit: '', notes: '' }];
	let instructions: Instruction[] = [{ step_number: 1, text: '' }];
	let prep_time_minutes: number | undefined;
	let cook_time_minutes: number | undefined;
	let servings: number | undefined;
	let notes = '';
	let category_id = '';
	let selectedTags: string[] = [];
	let complexity: RecipeComplexity | '' = '';
	let special_equipment: string[] = [''];
	let source_author = '';
	let source_url = '';

	const complexityOptions: { value: RecipeComplexity | ''; label: string }[] = [
		{ value: '', label: 'Select complexity' },
		{ value: 'very_easy', label: 'Very Easy' },
		{ value: 'easy', label: 'Easy' },
		{ value: 'medium', label: 'Medium' },
		{ value: 'hard', label: 'Hard' },
		{ value: 'very_hard', label: 'Very Hard' }
	];

	$: if (!$isAuthenticated) {
		goto('/login');
	}

	onMount(async () => {
		editId = $page.url.searchParams.get('edit') || '';

		const [categoriesRes, tagsRes] = await Promise.all([api.getCategories(), api.getTags()]);
		categories = categoriesRes.data || [];
		tags = tagsRes.data || [];

		if (editId) {
			const { data: recipe } = await api.getRecipe(editId);
			if (recipe) {
				title = recipe.title;
				description = recipe.description || '';
				ingredients = recipe.ingredients.length > 0 ? recipe.ingredients : [{ name: '', quantity: '', unit: '', notes: '' }];
				instructions = recipe.instructions.length > 0 ? recipe.instructions : [{ step_number: 1, text: '' }];
				prep_time_minutes = recipe.prep_time_minutes;
				cook_time_minutes = recipe.cook_time_minutes;
				servings = recipe.servings;
				notes = recipe.notes || '';
				category_id = recipe.category?.id || '';
				selectedTags = recipe.tags.map((t) => t.id);
				complexity = recipe.complexity || '';
				special_equipment = recipe.special_equipment?.length ? recipe.special_equipment : [''];
				source_author = recipe.source_author || '';
				source_url = recipe.source_url || '';
			}
		} else {
			// Check for imported recipe data
			const imported = get(importedRecipe);
			if (imported.extraction) {
				const ext = imported.extraction;
				title = ext.title;
				description = ext.description || '';
				ingredients = ext.ingredients.length > 0 ? ext.ingredients : [{ name: '', quantity: '', unit: '', notes: '' }];
				instructions = ext.instructions.length > 0 ? ext.instructions : [{ step_number: 1, text: '' }];
				prep_time_minutes = ext.prep_time_minutes;
				cook_time_minutes = ext.cook_time_minutes;
				servings = ext.servings;
				notes = ext.notes || '';
				special_equipment = ext.special_equipment?.length ? ext.special_equipment : [''];
				// Auto-populate source URL if this was a URL import
				if (imported.sourceUrl) {
					source_url = imported.sourceUrl;
				}
				// Clear the store to prevent stale data on revisit
				importedRecipe.clear();
			}
		}

		loading = false;
	});

	function addIngredient() {
		ingredients = [...ingredients, { name: '', quantity: '', unit: '', notes: '' }];
	}

	function removeIngredient(index: number) {
		ingredients = ingredients.filter((_, i) => i !== index);
	}

	function addInstruction() {
		instructions = [...instructions, { step_number: instructions.length + 1, text: '' }];
	}

	function removeInstruction(index: number) {
		instructions = instructions.filter((_, i) => i !== index);
		instructions = instructions.map((inst, i) => ({ ...inst, step_number: i + 1 }));
	}

	function toggleTag(tagId: string) {
		if (selectedTags.includes(tagId)) {
			selectedTags = selectedTags.filter((id) => id !== tagId);
		} else {
			selectedTags = [...selectedTags, tagId];
		}
	}

	function addEquipment() {
		special_equipment = [...special_equipment, ''];
	}

	function removeEquipment(index: number) {
		special_equipment = special_equipment.filter((_, i) => i !== index);
	}

	async function handleSubmit() {
		error = '';
		saving = true;

		const filteredIngredients = ingredients.filter((ing) => ing.name.trim());
		const filteredInstructions = instructions.filter((inst) => inst.text.trim());
		const filteredEquipment = special_equipment.filter((eq) => eq.trim());

		const recipeData = {
			title,
			description: description || undefined,
			ingredients: filteredIngredients,
			instructions: filteredInstructions,
			prep_time_minutes: prep_time_minutes || undefined,
			cook_time_minutes: cook_time_minutes || undefined,
			servings: servings || undefined,
			notes: notes || undefined,
			complexity: complexity || undefined,
			special_equipment: filteredEquipment.length > 0 ? filteredEquipment : undefined,
			source_author: source_author || undefined,
			source_url: source_url || undefined,
			category_id: category_id || undefined,
			tag_ids: selectedTags
		};

		const result = editId
			? await api.updateRecipe(editId, recipeData)
			: await api.createRecipe(recipeData);

		if (result.error) {
			error = result.error;
			saving = false;
		} else {
			goto(`/recipes/${result.data!.id}`);
		}
	}
</script>

<div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	<h1 class="text-2xl font-bold text-gray-900 mb-6">
		{editId ? 'Edit Recipe' : 'New Recipe'}
	</h1>

	{#if loading}
		<div class="text-center py-12 text-gray-500">Loading...</div>
	{:else}
		<form on:submit|preventDefault={handleSubmit} class="bg-white p-6 rounded-lg shadow-sm border">
			{#if error}
				<div class="mb-4 p-3 bg-red-100 text-red-700 rounded-md text-sm">{error}</div>
			{/if}

			<div class="mb-4">
				<label for="title" class="block text-sm font-medium text-gray-700 mb-1">Title *</label>
				<input
					type="text"
					id="title"
					bind:value={title}
					required
					class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
				/>
			</div>

			<div class="mb-4">
				<label for="description" class="block text-sm font-medium text-gray-700 mb-1"
					>Description</label
				>
				<textarea
					id="description"
					bind:value={description}
					rows="3"
					class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
				></textarea>
			</div>

			<div class="grid grid-cols-3 gap-4 mb-4">
				<div>
					<label for="prep_time" class="block text-sm font-medium text-gray-700 mb-1"
						>Prep Time (min)</label
					>
					<input
						type="number"
						id="prep_time"
						bind:value={prep_time_minutes}
						min="0"
						class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
				</div>
				<div>
					<label for="cook_time" class="block text-sm font-medium text-gray-700 mb-1"
						>Cook Time (min)</label
					>
					<input
						type="number"
						id="cook_time"
						bind:value={cook_time_minutes}
						min="0"
						class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
				</div>
				<div>
					<label for="servings" class="block text-sm font-medium text-gray-700 mb-1">Servings</label
					>
					<input
						type="number"
						id="servings"
						bind:value={servings}
						min="1"
						class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
				</div>
			</div>

			<div class="mb-4">
				<label for="category" class="block text-sm font-medium text-gray-700 mb-1">Category</label>
				<select
					id="category"
					bind:value={category_id}
					class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
				>
					<option value="">No category</option>
					{#each categories as category}
						<option value={category.id}>{category.name}</option>
					{/each}
				</select>
			</div>

			<div class="mb-4">
				<label class="block text-sm font-medium text-gray-700 mb-1">Tags</label>
				<div class="flex flex-wrap gap-2">
					{#each tags as tag}
						<button
							type="button"
							on:click={() => toggleTag(tag.id)}
							class="px-3 py-1 rounded-full text-sm {selectedTags.includes(tag.id)
								? 'bg-blue-500 text-white'
								: 'bg-gray-100 text-gray-700 hover:bg-gray-200'}"
						>
							{tag.name}
						</button>
					{/each}
				</div>
			</div>

			<div class="mb-4">
				<div class="flex justify-between items-center mb-2">
					<label class="block text-sm font-medium text-gray-700">Ingredients</label>
					<button
						type="button"
						on:click={addIngredient}
						class="text-sm text-blue-600 hover:underline"
					>
						+ Add Ingredient
					</button>
				</div>
				{#each ingredients as ing, i}
					<div class="flex gap-2 mb-2">
						<input
							type="text"
							bind:value={ing.quantity}
							placeholder="Qty"
							class="w-16 px-2 py-1 border rounded text-sm"
						/>
						<input
							type="text"
							bind:value={ing.unit}
							placeholder="Unit"
							class="w-20 px-2 py-1 border rounded text-sm"
						/>
						<input
							type="text"
							bind:value={ing.name}
							placeholder="Ingredient name"
							class="flex-1 px-2 py-1 border rounded text-sm"
						/>
						<input
							type="text"
							bind:value={ing.notes}
							placeholder="Notes"
							class="w-32 px-2 py-1 border rounded text-sm"
						/>
						{#if ingredients.length > 1}
							<button
								type="button"
								on:click={() => removeIngredient(i)}
								class="text-red-500 hover:text-red-700 px-2"
							>
								&times;
							</button>
						{/if}
					</div>
				{/each}
			</div>

			<div class="mb-4">
				<div class="flex justify-between items-center mb-2">
					<label class="block text-sm font-medium text-gray-700">Instructions</label>
					<button
						type="button"
						on:click={addInstruction}
						class="text-sm text-blue-600 hover:underline"
					>
						+ Add Step
					</button>
				</div>
				{#each instructions as inst, i}
					<div class="flex gap-2 mb-2">
						<span
							class="w-6 h-6 bg-gray-200 rounded-full flex items-center justify-center text-sm flex-shrink-0"
						>
							{i + 1}
						</span>
						<textarea
							bind:value={inst.text}
							placeholder="Step {i + 1} instructions..."
							rows="2"
							class="flex-1 px-2 py-1 border rounded text-sm"
						></textarea>
						{#if instructions.length > 1}
							<button
								type="button"
								on:click={() => removeInstruction(i)}
								class="text-red-500 hover:text-red-700 px-2"
							>
								&times;
							</button>
						{/if}
					</div>
				{/each}
			</div>

			<div class="mb-6">
				<label for="notes" class="block text-sm font-medium text-gray-700 mb-1">Notes</label>
				<textarea
					id="notes"
					bind:value={notes}
					rows="3"
					placeholder="Additional tips, variations, etc."
					class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
				></textarea>
			</div>

			<!-- Advanced Section -->
			<div class="border-t pt-4 mt-4 mb-6">
				<h2 class="text-lg font-medium text-gray-900 mb-4">Advanced (Optional)</h2>

				<div class="grid grid-cols-2 gap-4 mb-4">
					<div>
						<label for="complexity" class="block text-sm font-medium text-gray-700 mb-1">
							Complexity
						</label>
						<select
							id="complexity"
							bind:value={complexity}
							class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
						>
							{#each complexityOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
					</div>
				</div>

				<div class="grid grid-cols-2 gap-4 mb-4">
					<div>
						<label for="source_author" class="block text-sm font-medium text-gray-700 mb-1">
							Source Author
						</label>
						<input
							type="text"
							id="source_author"
							bind:value={source_author}
							placeholder="e.g., Julia Child"
							class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>
					<div>
						<label for="source_url" class="block text-sm font-medium text-gray-700 mb-1">
							Source URL / Book
						</label>
						<input
							type="text"
							id="source_url"
							bind:value={source_url}
							placeholder="e.g., https://example.com/recipe"
							class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>
				</div>

				<div class="mb-4">
					<div class="flex justify-between items-center mb-2">
						<label class="block text-sm font-medium text-gray-700">Special Equipment</label>
						<button
							type="button"
							on:click={addEquipment}
							class="text-sm text-blue-600 hover:underline"
						>
							+ Add Equipment
						</button>
					</div>
					{#each special_equipment as eq, i}
						<div class="flex gap-2 mb-2">
							<input
								type="text"
								bind:value={special_equipment[i]}
								placeholder="e.g., Stand mixer"
								class="flex-1 px-2 py-1 border rounded text-sm"
							/>
							{#if special_equipment.length > 1}
								<button
									type="button"
									on:click={() => removeEquipment(i)}
									class="text-red-500 hover:text-red-700 px-2"
								>
									&times;
								</button>
							{/if}
						</div>
					{/each}
				</div>
			</div>

			<div class="flex gap-4">
				<button
					type="submit"
					disabled={saving}
					class="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white py-2 rounded-md font-medium"
				>
					{saving ? 'Saving...' : editId ? 'Update Recipe' : 'Create Recipe'}
				</button>
				<a
					href={editId ? `/recipes/${editId}` : '/recipes'}
					class="px-6 py-2 border rounded-md text-gray-700 hover:bg-gray-50"
				>
					Cancel
				</a>
			</div>
		</form>
	{/if}
</div>
