<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type Settings, type AIProvider } from '$lib/api';
	import { isAuthenticated, isAdmin } from '$lib/stores/auth';
	import { goto } from '$app/navigation';

	let settings: Settings | null = null;
	let loading = true;
	let saving = false;
	let error = '';
	let success = '';

	let aiProvider: AIProvider | '' = '';
	let openaiApiKey = '';
	let anthropicApiKey = '';
	let geminiApiKey = '';
	let openaiModel = '';
	let anthropicModel = '';
	let geminiModel = '';

	$: if (!$isAuthenticated || !$isAdmin) {
		goto('/');
	}

	onMount(loadSettings);

	async function loadSettings() {
		loading = true;
		error = '';
		const { data, error: err } = await api.getSettings();
		if (err) {
			error = err;
		} else if (data) {
			settings = data;
			aiProvider = data.ai_provider || '';
			openaiModel = data.openai_model;
			anthropicModel = data.anthropic_model;
			geminiModel = data.gemini_model;
		}
		loading = false;
	}

	async function handleSubmit() {
		saving = true;
		error = '';
		success = '';

		const updateData: Record<string, string> = {};
		if (aiProvider) updateData.ai_provider = aiProvider;
		if (openaiApiKey) updateData.openai_api_key = openaiApiKey;
		if (anthropicApiKey) updateData.anthropic_api_key = anthropicApiKey;
		if (geminiApiKey) updateData.gemini_api_key = geminiApiKey;
		// Only send model if it differs from default (checking if user modified it)
		if (openaiModel && openaiModel !== settings?.openai_model) updateData.openai_model = openaiModel;
		if (anthropicModel && anthropicModel !== settings?.anthropic_model) updateData.anthropic_model = anthropicModel;
		if (geminiModel && geminiModel !== settings?.gemini_model) updateData.gemini_model = geminiModel;

		const { data, error: err } = await api.updateSettings(updateData);

		if (err) {
			error = err;
		} else if (data) {
			settings = data;
			aiProvider = data.ai_provider || '';
			openaiModel = data.openai_model;
			anthropicModel = data.anthropic_model;
			geminiModel = data.gemini_model;
			// Clear API key inputs after successful save
			openaiApiKey = '';
			anthropicApiKey = '';
			geminiApiKey = '';
			success = 'Settings saved successfully';
		}

		saving = false;
	}
</script>

<div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	<h1 class="text-2xl font-bold text-gray-900 mb-6">AI Settings</h1>

	{#if error}
		<div class="mb-4 p-3 bg-red-100 text-red-700 rounded-md text-sm">{error}</div>
	{/if}

	{#if success}
		<div class="mb-4 p-3 bg-green-100 text-green-700 rounded-md text-sm">{success}</div>
	{/if}

	{#if loading}
		<div class="text-center py-12 text-gray-500">Loading...</div>
	{:else}
		<form on:submit|preventDefault={handleSubmit} class="bg-white p-6 rounded-lg shadow-sm border space-y-6">
			<div>
				<label class="block text-sm font-medium text-gray-700 mb-1">AI Provider</label>
				<select bind:value={aiProvider} class="w-full px-3 py-2 border rounded-md">
					<option value="">Select a provider</option>
					<option value="openai">OpenAI</option>
					<option value="anthropic">Anthropic (Claude)</option>
					<option value="gemini">Google Gemini</option>
				</select>
				<p class="mt-1 text-xs text-gray-500">Select the AI provider to use for recipe import</p>
			</div>

			<div>
				<label class="block text-sm font-medium text-gray-700 mb-1">
					OpenAI API Key
					{#if settings?.openai_api_key_configured}
						<span class="ml-2 px-2 py-0.5 text-xs bg-green-100 text-green-800 rounded-full">Configured</span>
					{/if}
				</label>
				<input
					type="password"
					bind:value={openaiApiKey}
					placeholder={settings?.openai_api_key_configured ? '••••••••••••••••' : 'sk-...'}
					class="w-full px-3 py-2 border rounded-md"
				/>
				<p class="mt-1 text-xs text-gray-500">Leave blank to keep existing key</p>
			</div>

			<div>
				<label class="block text-sm font-medium text-gray-700 mb-1">OpenAI Model</label>
				<input
					type="text"
					bind:value={openaiModel}
					placeholder="gpt-4o-mini"
					class="w-full px-3 py-2 border rounded-md"
				/>
				<p class="mt-1 text-xs text-gray-500">Model name for OpenAI API (e.g., gpt-4o-mini, gpt-4o)</p>
			</div>

			<div>
				<label class="block text-sm font-medium text-gray-700 mb-1">
					Anthropic API Key
					{#if settings?.anthropic_api_key_configured}
						<span class="ml-2 px-2 py-0.5 text-xs bg-green-100 text-green-800 rounded-full">Configured</span>
					{/if}
				</label>
				<input
					type="password"
					bind:value={anthropicApiKey}
					placeholder={settings?.anthropic_api_key_configured ? '••••••••••••••••' : 'sk-ant-...'}
					class="w-full px-3 py-2 border rounded-md"
				/>
				<p class="mt-1 text-xs text-gray-500">Leave blank to keep existing key</p>
			</div>

			<div>
				<label class="block text-sm font-medium text-gray-700 mb-1">Anthropic Model</label>
				<input
					type="text"
					bind:value={anthropicModel}
					placeholder="claude-sonnet-4-20250514"
					class="w-full px-3 py-2 border rounded-md"
				/>
				<p class="mt-1 text-xs text-gray-500">Model name for Anthropic API (e.g., claude-sonnet-4-20250514)</p>
			</div>

			<div>
				<label class="block text-sm font-medium text-gray-700 mb-1">
					Google Gemini API Key
					{#if settings?.gemini_api_key_configured}
						<span class="ml-2 px-2 py-0.5 text-xs bg-green-100 text-green-800 rounded-full">Configured</span>
					{/if}
				</label>
				<input
					type="password"
					bind:value={geminiApiKey}
					placeholder={settings?.gemini_api_key_configured ? '••••••••••••••••' : 'AIza...'}
					class="w-full px-3 py-2 border rounded-md"
				/>
				<p class="mt-1 text-xs text-gray-500">Leave blank to keep existing key</p>
			</div>

			<div>
				<label class="block text-sm font-medium text-gray-700 mb-1">Gemini Model</label>
				<input
					type="text"
					bind:value={geminiModel}
					placeholder="gemini-2.0-flash"
					class="w-full px-3 py-2 border rounded-md"
				/>
				<p class="mt-1 text-xs text-gray-500">Model name for Gemini API (e.g., gemini-2.0-flash, gemini-1.5-pro)</p>
			</div>

			<div class="flex gap-4 pt-4">
				<button
					type="submit"
					disabled={saving}
					class="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-md font-medium"
				>
					{saving ? 'Saving...' : 'Save Settings'}
				</button>
			</div>
		</form>
	{/if}

	<div class="mt-6">
		<a href="/admin" class="text-blue-600 hover:underline">&larr; Back to Admin</a>
	</div>
</div>
