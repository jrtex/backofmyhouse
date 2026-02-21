<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type Category } from '$lib/api';
	import { isAuthenticated, isAdmin } from '$lib/stores/auth';
	import { goto } from '$app/navigation';

	let categories: Category[] = [];
	let loading = true;
	let error = '';
	let showForm = false;
	let editingCategory: Category | null = null;

	let name = '';
	let description = '';

	$: if (!$isAuthenticated || !$isAdmin) {
		goto('/');
	}

	onMount(loadCategories);

	async function loadCategories() {
		loading = true;
		const { data, error: err } = await api.getCategories();
		if (err) {
			error = err;
		} else {
			categories = data || [];
		}
		loading = false;
	}

	function openCreateForm() {
		editingCategory = null;
		name = '';
		description = '';
		showForm = true;
	}

	function openEditForm(category: Category) {
		editingCategory = category;
		name = category.name;
		description = category.description || '';
		showForm = true;
	}

	function closeForm() {
		showForm = false;
		editingCategory = null;
	}

	async function handleSubmit() {
		error = '';

		if (editingCategory) {
			const { error: err } = await api.updateCategory(editingCategory.id, { name, description });
			if (err) {
				error = err;
				return;
			}
		} else {
			const { error: err } = await api.createCategory({ name, description });
			if (err) {
				error = err;
				return;
			}
		}

		closeForm();
		loadCategories();
	}

	async function handleDelete(categoryId: string) {
		if (!confirm('Are you sure you want to delete this category?')) return;

		const { error: err } = await api.deleteCategory(categoryId);
		if (err) {
			error = err;
		} else {
			loadCategories();
		}
	}
</script>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	<div class="flex justify-between items-center mb-6">
		<h1 class="text-2xl font-bold text-gray-900">Categories</h1>
		<button
			on:click={openCreateForm}
			class="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md font-medium"
		>
			Add Category
		</button>
	</div>

	{#if error}
		<div class="mb-4 p-3 bg-red-100 text-red-700 rounded-md text-sm">{error}</div>
	{/if}

	{#if showForm}
		<div class="bg-white p-6 rounded-lg shadow-sm border mb-6">
			<h2 class="text-lg font-semibold mb-4">
				{editingCategory ? 'Edit Category' : 'Create Category'}
			</h2>
			<form on:submit|preventDefault={handleSubmit} class="space-y-4">
				<div>
					<label class="block text-sm font-medium text-gray-700 mb-1">Name</label>
					<input type="text" bind:value={name} required class="w-full px-3 py-2 border rounded-md" />
				</div>
				<div>
					<label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
					<textarea bind:value={description} rows="3" class="w-full px-3 py-2 border rounded-md"
					></textarea>
				</div>
				<div class="flex gap-4">
					<button
						type="submit"
						class="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md"
					>
						{editingCategory ? 'Update' : 'Create'}
					</button>
					<button type="button" on:click={closeForm} class="text-gray-600 hover:text-gray-800">
						Cancel
					</button>
				</div>
			</form>
		</div>
	{/if}

	{#if loading}
		<div class="text-center py-12 text-gray-500">Loading...</div>
	{:else if categories.length === 0}
		<div class="text-center py-12 text-gray-500">No categories yet. Create one!</div>
	{:else}
		<div class="bg-white rounded-lg shadow-sm border overflow-hidden">
			<table class="min-w-full divide-y divide-gray-200">
				<thead class="bg-gray-50">
					<tr>
						<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
						<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase"
							>Description</th
						>
						<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
						<th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-200">
					{#each categories as category}
						<tr>
							<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{category.name}</td>
							<td class="px-6 py-4 text-sm text-gray-500">{category.description || '-'}</td>
							<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
								{new Date(category.created_at).toLocaleDateString()}
							</td>
							<td class="px-6 py-4 whitespace-nowrap text-right text-sm">
								<button
									on:click={() => openEditForm(category)}
									class="text-primary-600 hover:underline mr-4"
								>
									Edit
								</button>
								<button
									on:click={() => handleDelete(category.id)}
									class="text-red-600 hover:underline"
								>
									Delete
								</button>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}

	<div class="mt-6">
		<a href="/admin" class="text-primary-600 hover:underline">&larr; Back to Admin</a>
	</div>
</div>
