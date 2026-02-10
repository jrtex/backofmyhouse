<script lang="ts">
	import { tick } from 'svelte';
	import { goto } from '$app/navigation';
	import { api, type RecipeExtraction } from '$lib/api';
	import { isAuthenticated } from '$lib/stores/auth';
	import { importedRecipe } from '$lib/stores/importedRecipe';

	type ImportTab = 'image' | 'url' | 'text';

	let activeTab: ImportTab = 'image';
	let loading = false;
	let error = '';

	// Image import state
	let selectedFile: File | null = null;
	let imagePreview: string | null = null;
	let dragOver = false;

	// URL import state
	let urlInput = '';

	// Text import state
	let textInput = '';

	// Extraction result
	let extraction: RecipeExtraction | null = null;

	// Element ref for focus management
	let resultHeading: HTMLHeadingElement;

	$: if (!$isAuthenticated) {
		goto('/login');
	}

	/**
	 * Get actionable suggestion based on error message content.
	 */
	function getErrorSuggestion(errorMessage: string): string | null {
		const lowerError = errorMessage.toLowerCase();

		if (lowerError.includes('not configured') || lowerError.includes('ai service')) {
			return 'Contact an admin to configure AI settings.';
		}
		if (lowerError.includes('could not extract') || lowerError.includes('extraction')) {
			if (activeTab === 'image') {
				return 'Try a clearer image or a different photo.';
			} else if (activeTab === 'url') {
				return 'The page may not contain a recognizable recipe.';
			} else {
				return 'Make sure the text contains recipe details like ingredients and instructions.';
			}
		}
		if (lowerError.includes('could not fetch') || lowerError.includes('url')) {
			return 'Check the URL is correct and the site is accessible.';
		}
		if (lowerError.includes('rate limit') || lowerError.includes('429') || lowerError.includes('too many')) {
			return 'Please wait a moment and try again.';
		}
		if (lowerError.includes('blocked') || lowerError.includes('403')) {
			return 'This site may block automated access. Try a different recipe source.';
		}

		return null;
	}

	function handleTabChange(tab: ImportTab) {
		activeTab = tab;
		resetState();
	}

	function resetState() {
		error = '';
		extraction = null;
		selectedFile = null;
		imagePreview = null;
		urlInput = '';
		textInput = '';
	}

	function handleDragOver(e: DragEvent) {
		e.preventDefault();
		dragOver = true;
	}

	function handleDragLeave() {
		dragOver = false;
	}

	function handleDrop(e: DragEvent) {
		e.preventDefault();
		dragOver = false;
		const files = e.dataTransfer?.files;
		if (files && files.length > 0) {
			handleFileSelect(files[0]);
		}
	}

	function handleFileInput(e: Event) {
		const input = e.target as HTMLInputElement;
		if (input.files && input.files.length > 0) {
			handleFileSelect(input.files[0]);
		}
	}

	function handleFileSelect(file: File) {
		const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/heic'];
		if (!allowedTypes.includes(file.type)) {
			error = 'Invalid file type. Please use JPEG, PNG, WebP, or HEIC images.';
			return;
		}

		const maxSize = 10 * 1024 * 1024; // 10MB
		if (file.size > maxSize) {
			error = 'File too large. Maximum size is 10MB.';
			return;
		}

		error = '';
		selectedFile = file;
		extraction = null;

		// Create preview
		const reader = new FileReader();
		reader.onload = (e) => {
			imagePreview = e.target?.result as string;
		};
		reader.readAsDataURL(file);
	}

	async function handleImageImport() {
		if (!selectedFile) return;

		loading = true;
		error = '';

		const result = await api.importFromImage(selectedFile);

		if (result.error) {
			error = result.error;
		} else if (result.data) {
			extraction = result.data;
			// Focus result heading for accessibility after DOM updates
			await tick();
			resultHeading?.focus();
		}

		loading = false;
	}

	async function handleUrlImport() {
		if (!urlInput.trim()) {
			error = 'Please enter a URL.';
			return;
		}

		// Basic URL validation
		try {
			new URL(urlInput);
		} catch {
			error = 'Please enter a valid URL.';
			return;
		}

		loading = true;
		error = '';

		const result = await api.importFromUrl(urlInput);

		if (result.error) {
			error = result.error;
		} else if (result.data) {
			extraction = result.data;
			// Focus result heading for accessibility after DOM updates
			await tick();
			resultHeading?.focus();
		}

		loading = false;
	}

	async function handleTextImport() {
		if (!textInput.trim()) {
			error = 'Please enter some recipe text.';
			return;
		}

		if (textInput.trim().length < 10) {
			error = 'Please enter more text. The recipe should include ingredients and instructions.';
			return;
		}

		loading = true;
		error = '';

		const result = await api.importFromText(textInput);

		if (result.error) {
			error = result.error;
		} else if (result.data) {
			extraction = result.data;
			// Focus result heading for accessibility after DOM updates
			await tick();
			resultHeading?.focus();
		}

		loading = false;
	}

	function getConfidenceLabel(confidence: number): { text: string; class: string } {
		if (confidence >= 0.8) {
			return { text: 'High confidence', class: 'bg-green-100 text-green-800' };
		} else if (confidence >= 0.5) {
			return { text: 'Medium confidence - review suggested', class: 'bg-yellow-100 text-yellow-800' };
		} else {
			return { text: 'Low confidence - careful review needed', class: 'bg-red-100 text-red-800' };
		}
	}

	function handleEditAndSave() {
		if (!extraction) return;

		// Store the extraction for the recipe form to pick up
		importedRecipe.setExtraction(extraction, activeTab === 'url' ? urlInput : undefined);

		// Navigate to the recipe form
		goto('/recipes/new');
	}

	function handleTryAgain() {
		extraction = null;
		error = '';
	}
</script>

<div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	<div class="flex items-center justify-between mb-6">
		<h1 class="text-2xl font-bold text-gray-900">Import Recipe</h1>
		<a href="/recipes" class="text-gray-500 hover:text-gray-700">Cancel</a>
	</div>

	<!-- Tabs -->
	<div class="border-b border-gray-200 mb-6" role="tablist">
		<nav class="-mb-px flex space-x-8">
			<button
				type="button"
				role="tab"
				aria-selected={activeTab === 'image'}
				aria-controls="image-panel"
				on:click={() => handleTabChange('image')}
				class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === 'image'
					? 'border-blue-500 text-blue-600'
					: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
			>
				From Image
			</button>
			<button
				type="button"
				role="tab"
				aria-selected={activeTab === 'url'}
				aria-controls="url-panel"
				on:click={() => handleTabChange('url')}
				class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === 'url'
					? 'border-blue-500 text-blue-600'
					: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
			>
				From URL
			</button>
			<button
				type="button"
				role="tab"
				aria-selected={activeTab === 'text'}
				aria-controls="text-panel"
				on:click={() => handleTabChange('text')}
				class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === 'text'
					? 'border-blue-500 text-blue-600'
					: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
			>
				From Text
			</button>
		</nav>
	</div>

	{#if error}
		<div role="alert" class="mb-6 p-4 bg-red-100 text-red-700 rounded-md">
			<p>{error}</p>
			{#if getErrorSuggestion(error)}
				<p class="mt-2 text-sm text-red-600">{getErrorSuggestion(error)}</p>
			{/if}
		</div>
	{/if}

	{#if !extraction}
		<!-- Import Forms -->
		<div class="bg-white p-6 rounded-lg shadow-sm border" aria-busy={loading}>
			{#if activeTab === 'image'}
				<!-- Image Import -->
				<div
					id="image-panel"
					role="tabpanel"
					aria-label="Image upload area. Drag and drop or click to select an image."
					tabindex="0"
					on:dragover={handleDragOver}
					on:dragleave={handleDragLeave}
					on:drop={handleDrop}
					on:click={() => document.getElementById('file-input')?.click()}
					on:keydown={(e) => e.key === 'Enter' && document.getElementById('file-input')?.click()}
					class="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
						{dragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}"
				>
					{#if imagePreview}
						<img src={imagePreview} alt="Selected" class="max-h-64 mx-auto mb-4 rounded" />
						<p class="text-sm text-gray-600">{selectedFile?.name}</p>
						<p class="text-xs text-gray-400 mt-1">Click or drop to change</p>
					{:else}
						<svg
							class="mx-auto h-12 w-12 text-gray-400"
							stroke="currentColor"
							fill="none"
							viewBox="0 0 48 48"
						>
							<path
								d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
							/>
						</svg>
						<p class="mt-4 text-sm text-gray-600">
							Drag and drop an image, or click to select
						</p>
						<p class="mt-1 text-xs text-gray-400">
							JPEG, PNG, WebP, or HEIC up to 10MB
						</p>
					{/if}
				</div>
				<input
					type="file"
					id="file-input"
					accept="image/jpeg,image/png,image/webp,image/heic"
					on:change={handleFileInput}
					class="hidden"
				/>

				{#if selectedFile}
					<button
						type="button"
						on:click={handleImageImport}
						disabled={loading}
						class="mt-4 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white py-2 rounded-md font-medium"
					>
						{loading ? 'Extracting recipe...' : 'Extract Recipe'}
					</button>
				{/if}
			{:else if activeTab === 'url'}
				<!-- URL Import -->
				<div id="url-panel" role="tabpanel">
					<label for="url-input" class="block text-sm font-medium text-gray-700 mb-2">
						Recipe URL
					</label>
					<input
						type="url"
						id="url-input"
						bind:value={urlInput}
						placeholder="https://example.com/recipe"
						class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
					<p class="mt-2 text-xs text-gray-500">
						Works best with recipe websites that use structured data (e.g., AllRecipes, Food Network)
					</p>
				</div>

				<button
					type="button"
					on:click={handleUrlImport}
					disabled={loading || !urlInput.trim()}
					class="mt-4 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white py-2 rounded-md font-medium"
				>
					{loading ? 'Extracting recipe...' : 'Extract Recipe'}
				</button>
			{:else}
				<!-- Text Import -->
				<div id="text-panel" role="tabpanel">
					<label for="text-input" class="block text-sm font-medium text-gray-700 mb-2">
						Recipe Text
					</label>
					<textarea
						id="text-input"
						bind:value={textInput}
						placeholder="Paste your recipe text here...

Example:
Chocolate Chip Cookies

Ingredients:
- 2 cups flour
- 1 cup butter
- 1 cup sugar
...

Instructions:
1. Preheat oven to 350°F
2. Mix dry ingredients
..."
						rows="12"
						class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
					></textarea>
					<p class="mt-2 text-xs text-gray-500">
						Paste any recipe text - from emails, documents, messages, or anywhere else
					</p>
				</div>

				<button
					type="button"
					on:click={handleTextImport}
					disabled={loading || !textInput.trim()}
					class="mt-4 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white py-2 rounded-md font-medium"
				>
					{loading ? 'Extracting recipe...' : 'Extract Recipe'}
				</button>
			{/if}
		</div>
	{:else}
		<!-- Extraction Result -->
		<div class="bg-white p-6 rounded-lg shadow-sm border">
			<div class="flex items-start justify-between mb-4">
				<h2
					bind:this={resultHeading}
					tabindex="-1"
					class="text-xl font-semibold text-gray-900 outline-none"
				>
					{extraction.title}
				</h2>
				<span
					class="px-2 py-1 rounded-full text-xs font-medium {getConfidenceLabel(extraction.confidence).class}"
				>
					{getConfidenceLabel(extraction.confidence).text}
				</span>
			</div>

			{#if extraction.warnings.length > 0}
				<div class="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
					<p class="text-sm font-medium text-yellow-800 mb-1">Extraction notes:</p>
					<ul class="text-sm text-yellow-700 list-disc list-inside">
						{#each extraction.warnings as warning}
							<li>{warning}</li>
						{/each}
					</ul>
				</div>
			{/if}

			{#if extraction.description}
				<p class="text-gray-600 mb-4">{extraction.description}</p>
			{/if}

			<div class="grid grid-cols-3 gap-4 mb-4 text-sm">
				{#if extraction.prep_time_minutes}
					<div>
						<span class="text-gray-500">Prep:</span>
						<span class="font-medium">{extraction.prep_time_minutes} min</span>
					</div>
				{/if}
				{#if extraction.cook_time_minutes}
					<div>
						<span class="text-gray-500">Cook:</span>
						<span class="font-medium">{extraction.cook_time_minutes} min</span>
					</div>
				{/if}
				{#if extraction.servings}
					<div>
						<span class="text-gray-500">Servings:</span>
						<span class="font-medium">{extraction.servings}</span>
					</div>
				{/if}
			</div>

			<div class="mb-4">
				<h3 class="font-medium text-gray-900 mb-2">
					Ingredients ({extraction.ingredients.length})
				</h3>
				<ul class="text-sm text-gray-600 space-y-1">
					{#each extraction.ingredients.slice(0, 5) as ing}
						<li>
							{#if ing.quantity}{ing.quantity}{/if}
							{#if ing.unit}{ing.unit}{/if}
							{ing.name}
							{#if ing.notes}<span class="text-gray-400">({ing.notes})</span>{/if}
						</li>
					{/each}
					{#if extraction.ingredients.length > 5}
						<li class="text-gray-400">...and {extraction.ingredients.length - 5} more</li>
					{/if}
				</ul>
			</div>

			<div class="mb-6">
				<h3 class="font-medium text-gray-900 mb-2">
					Instructions ({extraction.instructions.length} steps)
				</h3>
				<ol class="text-sm text-gray-600 space-y-1 list-decimal list-inside">
					{#each extraction.instructions.slice(0, 3) as inst}
						<li class="truncate">{inst.text}</li>
					{/each}
					{#if extraction.instructions.length > 3}
						<li class="text-gray-400">...and {extraction.instructions.length - 3} more steps</li>
					{/if}
				</ol>
			</div>

			<div class="flex gap-4">
				<button
					type="button"
					on:click={handleEditAndSave}
					class="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-md font-medium"
				>
					Edit & Save
				</button>
				<button
					type="button"
					on:click={handleTryAgain}
					class="px-6 py-2 border rounded-md text-gray-700 hover:bg-gray-50"
				>
					Try Again
				</button>
			</div>
		</div>
	{/if}
</div>
