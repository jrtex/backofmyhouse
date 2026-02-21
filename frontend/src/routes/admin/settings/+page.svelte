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
	let testing = false;
	let testResult: { success: boolean; message: string } | null = null;

	let aiProvider: AIProvider | '' = '';
	let apiKey = '';
	let selectedModel = '';
	let showApiKey = false;

	const providerLabels: Record<AIProvider, string> = {
		openai: 'OpenAI',
		anthropic: 'Anthropic (Claude)',
		gemini: 'Google Gemini'
	};

	const modelOptions: Record<AIProvider, { value: string; label: string }[]> = {
		openai: [
			{ value: 'gpt-4o', label: 'GPT-4o (Recommended)' },
			{ value: 'gpt-4o-mini', label: 'GPT-4o Mini' }
		],
		anthropic: [
			{ value: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6 (Recommended)' },
			{ value: 'claude-haiku-4-5', label: 'Claude Haiku 4.5' }
		],
		gemini: [
			{ value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash (Recommended)' },
			{ value: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro' }
		]
	};

	$: if (!$isAuthenticated || !$isAdmin) {
		goto('/');
	}

	$: isKeyConfigured = settings
		? aiProvider === 'openai'
			? settings.openai_api_key_configured
			: aiProvider === 'anthropic'
				? settings.anthropic_api_key_configured
				: aiProvider === 'gemini'
					? settings.gemini_api_key_configured
					: false
		: false;

	$: apiKeyPlaceholder = isKeyConfigured ? '••••••••••••••••••••••••••••••••••••••' : 'Enter your API key';

	function getStoredModel(provider: AIProvider): string {
		if (!settings) return '';
		if (provider === 'openai') return settings.openai_model;
		if (provider === 'anthropic') return settings.anthropic_model;
		if (provider === 'gemini') return settings.gemini_model;
		return '';
	}

	function onProviderChange() {
		if (aiProvider) {
			selectedModel = getStoredModel(aiProvider);
			// If stored model isn't in dropdown options, default to first option
			const options = modelOptions[aiProvider];
			if (!options.find((o) => o.value === selectedModel)) {
				selectedModel = options[0].value;
			}
		}
		apiKey = '';
		showApiKey = false;
		testResult = null;
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
			if (aiProvider) {
				selectedModel = getStoredModel(aiProvider);
				const options = modelOptions[aiProvider];
				if (!options.find((o) => o.value === selectedModel)) {
					selectedModel = options[0].value;
				}
			}
		}
		loading = false;
	}

	async function handleSubmit() {
		if (!aiProvider) {
			error = 'Please select a model provider';
			return;
		}

		saving = true;
		error = '';
		success = '';
		testResult = null;

		const updateData: Record<string, string> = {
			ai_provider: aiProvider
		};

		// Set model for the selected provider
		if (aiProvider === 'openai') updateData.openai_model = selectedModel;
		else if (aiProvider === 'anthropic') updateData.anthropic_model = selectedModel;
		else if (aiProvider === 'gemini') updateData.gemini_model = selectedModel;

		// Set API key if a new one was entered
		if (apiKey) {
			if (aiProvider === 'openai') updateData.openai_api_key = apiKey;
			else if (aiProvider === 'anthropic') updateData.anthropic_api_key = apiKey;
			else if (aiProvider === 'gemini') updateData.gemini_api_key = apiKey;
		}

		const { data, error: err } = await api.updateSettings(updateData);

		if (err) {
			error = err;
		} else if (data) {
			settings = data;
			aiProvider = data.ai_provider || '';
			if (aiProvider) {
				selectedModel = getStoredModel(aiProvider);
				const options = modelOptions[aiProvider];
				if (!options.find((o) => o.value === selectedModel)) {
					selectedModel = options[0].value;
				}
			}
			apiKey = '';
			showApiKey = false;
			success = 'Settings saved successfully';
		}

		saving = false;
	}

	async function handleTestConnection() {
		if (!aiProvider) return;

		testing = true;
		testResult = null;
		error = '';

		const { data, error: err } = await api.testConnection(
			aiProvider,
			apiKey || undefined
		);

		if (err) {
			testResult = { success: false, message: err };
		} else if (data) {
			testResult = data;
		}

		testing = false;
	}
</script>

<div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	{#if error}
		<div class="mb-4 p-3 bg-red-100 text-red-700 rounded-md text-sm">{error}</div>
	{/if}

	{#if success}
		<div class="mb-4 p-3 bg-green-100 text-green-700 rounded-md text-sm">{success}</div>
	{/if}

	{#if loading}
		<div class="text-center py-12 text-gray-500">Loading...</div>
	{:else}
		<form on:submit|preventDefault={handleSubmit}>
			<div class="bg-white p-6 sm:p-8 rounded-lg shadow-sm border">
				<!-- Header -->
				<h1 class="text-xl font-bold text-gray-900">Model Provider Configuration</h1>
				<p class="mt-1 text-sm text-gray-500">
					Configure the AI engine used for parsing recipe cards, URLs, and images.
				</p>

				<!-- Provider & Model Row -->
				<div class="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-6">
					<div>
						<label for="provider" class="block text-sm font-semibold text-gray-900 mb-2">
							Model Provider
						</label>
						<select
							id="provider"
							bind:value={aiProvider}
							on:change={onProviderChange}
							class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-primary-600 appearance-none cursor-pointer"
							style="background-image: url(&quot;data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E&quot;); background-repeat: no-repeat; background-position: right 12px center; background-size: 16px;"
						>
							<option value="">Select a provider</option>
							{#each Object.entries(providerLabels) as [value, label]}
								<option {value}>{label}</option>
							{/each}
						</select>
					</div>

					<div>
						<label for="model" class="block text-sm font-semibold text-gray-900 mb-2">
							Model Version
						</label>
						<select
							id="model"
							bind:value={selectedModel}
							disabled={!aiProvider}
							class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-primary-600 appearance-none disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
							style="background-image: url(&quot;data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E&quot;); background-repeat: no-repeat; background-position: right 12px center; background-size: 16px;"
						>
							{#if aiProvider}
								{#each modelOptions[aiProvider] as option}
									<option value={option.value}>{option.label}</option>
								{/each}
							{:else}
								<option value="">Select a provider first</option>
							{/if}
						</select>
					</div>
				</div>

				<!-- API Key Row -->
				<div class="mt-6">
					<label for="apiKey" class="block text-sm font-semibold text-gray-900 mb-2">
						API Key
					</label>
					<div class="flex gap-3">
						<div class="relative flex-1">
							{#if showApiKey}
								<input
									id="apiKey"
									type="text"
									bind:value={apiKey}
									placeholder={aiProvider ? apiKeyPlaceholder : 'Select a provider first'}
									disabled={!aiProvider}
									class="w-full px-4 py-2.5 pr-10 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-primary-600 disabled:opacity-50 disabled:cursor-not-allowed"
								/>
							{:else}
								<input
									id="apiKey"
									type="password"
									bind:value={apiKey}
									placeholder={aiProvider ? apiKeyPlaceholder : 'Select a provider first'}
									disabled={!aiProvider}
									class="w-full px-4 py-2.5 pr-10 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-primary-600 disabled:opacity-50 disabled:cursor-not-allowed"
								/>
							{/if}
							{#if aiProvider}
								<button
									type="button"
									on:click={() => (showApiKey = !showApiKey)}
									class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
									aria-label={showApiKey ? 'Hide API key' : 'Show API key'}
								>
									{#if showApiKey}
										<!-- Eye icon -->
										<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
											<path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
											<path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
										</svg>
									{:else}
										<!-- Eye-slash icon -->
										<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
											<path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
										</svg>
									{/if}
								</button>
							{/if}
						</div>
						<button
							type="button"
							on:click={handleTestConnection}
							disabled={!aiProvider || testing}
							class="flex items-center gap-2 px-4 py-2.5 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-600 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
						>
							<svg
								class="w-4 h-4 {testing ? 'animate-spin' : ''}"
								fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
							>
								<path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
							</svg>
							{testing ? 'Testing...' : 'Test Connection'}
						</button>
					</div>
					<p class="mt-2 text-xs text-primary-600 italic">
						Your API key is encrypted and stored securely.
					</p>

					{#if testResult}
						<div class="mt-2 text-sm {testResult.success ? 'text-green-600' : 'text-red-600'}">
							{testResult.message}
						</div>
					{/if}
				</div>

				<!-- Save Button -->
				<div class="mt-8 flex items-center gap-4">
					<button
						type="submit"
						disabled={saving || !aiProvider}
						class="bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-2.5 rounded-lg text-sm font-medium transition-colors"
					>
						{saving ? 'Saving...' : 'Save Settings'}
					</button>
					{#if isKeyConfigured && aiProvider}
						<span class="flex items-center gap-1.5 text-xs text-green-600">
							<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
								<path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
							</svg>
							API key configured
						</span>
					{/if}
				</div>
			</div>
		</form>
	{/if}

	<div class="mt-6">
		<a href="/admin" class="text-primary-600 hover:underline text-sm">&larr; Back to Admin</a>
	</div>
</div>
