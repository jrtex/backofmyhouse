<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type Tag } from '$lib/api';
	import { isAuthenticated, isAdmin } from '$lib/stores/auth';
	import { goto } from '$app/navigation';

	let tags: Tag[] = [];
	let loading = true;
	let error = '';
	let showForm = false;

	let name = '';

	$: if (!$isAuthenticated || !$isAdmin) {
		goto('/');
	}

	onMount(loadTags);

	async function loadTags() {
		loading = true;
		const { data, error: err } = await api.getTags();
		if (err) {
			error = err;
		} else {
			tags = data || [];
		}
		loading = false;
	}

	function openCreateForm() {
		name = '';
		showForm = true;
	}

	function closeForm() {
		showForm = false;
	}

	async function handleSubmit() {
		error = '';

		const { error: err } = await api.createTag({ name });
		if (err) {
			error = err;
			return;
		}

		closeForm();
		loadTags();
	}

	async function handleDelete(tagId: string) {
		if (!confirm('Are you sure you want to delete this tag?')) return;

		const { error: err } = await api.deleteTag(tagId);
		if (err) {
			error = err;
		} else {
			loadTags();
		}
	}
</script>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	<div class="flex justify-between items-center mb-6">
		<h1 class="text-2xl font-bold text-gray-900">Tags</h1>
		<button
			on:click={openCreateForm}
			class="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md font-medium"
		>
			Add Tag
		</button>
	</div>

	{#if error}
		<div class="mb-4 p-3 bg-red-100 text-red-700 rounded-md text-sm">{error}</div>
	{/if}

	{#if showForm}
		<div class="bg-white p-6 rounded-lg shadow-sm border mb-6">
			<h2 class="text-lg font-semibold mb-4">Create Tag</h2>
			<form on:submit|preventDefault={handleSubmit} class="flex gap-4">
				<div class="flex-1">
					<input
						type="text"
						bind:value={name}
						required
						placeholder="Tag name"
						class="w-full px-3 py-2 border rounded-md"
					/>
				</div>
				<button type="submit" class="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md">
					Create
				</button>
				<button type="button" on:click={closeForm} class="text-gray-600 hover:text-gray-800">
					Cancel
				</button>
			</form>
		</div>
	{/if}

	{#if loading}
		<div class="text-center py-12 text-gray-500">Loading...</div>
	{:else if tags.length === 0}
		<div class="text-center py-12 text-gray-500">No tags yet. Create one!</div>
	{:else}
		<div class="bg-white rounded-lg shadow-sm border p-6">
			<div class="flex flex-wrap gap-3">
				{#each tags as tag}
					<div
						class="flex items-center gap-2 bg-gray-100 px-3 py-2 rounded-full"
					>
						<span class="text-gray-700">{tag.name}</span>
						<button
							on:click={() => handleDelete(tag.id)}
							class="text-gray-400 hover:text-red-500"
						>
							&times;
						</button>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<div class="mt-6">
		<a href="/admin" class="text-primary-600 hover:underline">&larr; Back to Admin</a>
	</div>
</div>
