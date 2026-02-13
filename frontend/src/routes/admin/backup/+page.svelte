<script lang="ts">
	import {
		api,
		type BackupImportResult,
		type ConflictStrategy,
		type RecipeListItem
	} from '$lib/api';
	import { isAuthenticated, isAdmin } from '$lib/stores/auth';
	import { goto } from '$app/navigation';

	$: if (!$isAuthenticated) {
		goto('/login');
	}

	$: if ($isAuthenticated && !$isAdmin) {
		goto('/recipes');
	}

	// Export state
	type ExportStep = 'idle' | 'selecting' | 'exporting';
	let exportStep: ExportStep = 'idle';
	let exportRecipes: RecipeListItem[] = [];
	let selectedExportIds: Set<string> = new Set();
	let exportSelectAll = true;
	let exportError = '';
	let loadingExportRecipes = false;

	// Import state
	type ImportStep = 'idle' | 'selecting' | 'importing';
	let importStep: ImportStep = 'idle';
	let parsedBackup: { recipes: Array<{ title: string; category_name?: string }> } | null = null;
	let selectedImportTitles: Set<string> = new Set();
	let importSelectAll = true;
	let importError = '';
	let importResult: BackupImportResult | null = null;
	let selectedFile: File | null = null;
	let conflictStrategy: ConflictStrategy = 'skip';

	// Export functions
	async function startExportSelection() {
		loadingExportRecipes = true;
		exportError = '';
		const result = await api.getRecipes();
		loadingExportRecipes = false;

		if (result.error) {
			exportError = result.error;
			return;
		}

		exportRecipes = result.data || [];
		selectedExportIds = new Set(exportRecipes.map((r) => r.id));
		exportSelectAll = true;
		exportStep = 'selecting';
	}

	function toggleExportSelectAll() {
		if (exportSelectAll) {
			selectedExportIds = new Set();
		} else {
			selectedExportIds = new Set(exportRecipes.map((r) => r.id));
		}
		exportSelectAll = !exportSelectAll;
	}

	function toggleExportRecipe(id: string) {
		if (selectedExportIds.has(id)) {
			selectedExportIds.delete(id);
		} else {
			selectedExportIds.add(id);
		}
		selectedExportIds = selectedExportIds;
		exportSelectAll = selectedExportIds.size === exportRecipes.length;
	}

	async function handleExportSelected() {
		exportStep = 'exporting';
		exportError = '';
		try {
			const ids = Array.from(selectedExportIds);
			await api.exportBackup(ids.length > 0 ? ids : undefined);
			exportStep = 'idle';
		} catch (err) {
			exportError = err instanceof Error ? err.message : 'Export failed';
			exportStep = 'selecting';
		}
	}

	function cancelExport() {
		exportStep = 'idle';
		exportRecipes = [];
		selectedExportIds = new Set();
	}

	// Import functions
	function handleFileSelect(event: Event) {
		const input = event.target as HTMLInputElement;
		if (input.files && input.files.length > 0) {
			selectedFile = input.files[0];
			importResult = null;
			importError = '';
			parseBackupFile(input.files[0]);
		}
	}

	async function parseBackupFile(file: File) {
		try {
			const text = await file.text();
			const data = JSON.parse(text);

			if (!data.recipes || !Array.isArray(data.recipes)) {
				importError = 'Invalid backup file format';
				return;
			}

			parsedBackup = {
				recipes: data.recipes.map((r: { title: string; category_name?: string }) => ({
					title: r.title,
					category_name: r.category_name
				}))
			};
			selectedImportTitles = new Set(parsedBackup.recipes.map((r) => r.title));
			importSelectAll = true;
			importStep = 'selecting';
		} catch {
			importError = 'Failed to parse backup file';
			parsedBackup = null;
		}
	}

	function toggleImportSelectAll() {
		if (!parsedBackup) return;
		if (importSelectAll) {
			selectedImportTitles = new Set();
		} else {
			selectedImportTitles = new Set(parsedBackup.recipes.map((r) => r.title));
		}
		importSelectAll = !importSelectAll;
	}

	function toggleImportRecipe(title: string) {
		if (selectedImportTitles.has(title)) {
			selectedImportTitles.delete(title);
		} else {
			selectedImportTitles.add(title);
		}
		selectedImportTitles = selectedImportTitles;
		importSelectAll = parsedBackup
			? selectedImportTitles.size === parsedBackup.recipes.length
			: false;
	}

	async function handleImportSelected() {
		if (!selectedFile) return;

		importStep = 'importing';
		importError = '';
		importResult = null;

		const titles = Array.from(selectedImportTitles);
		const result = await api.importBackup(
			selectedFile,
			conflictStrategy,
			titles.length > 0 ? titles : undefined
		);

		if (result.error) {
			importError = result.error;
			importStep = 'selecting';
		} else if (result.data) {
			importResult = result.data;
			importStep = 'idle';
			parsedBackup = null;
			selectedFile = null;
		}
	}

	function cancelImport() {
		importStep = 'idle';
		parsedBackup = null;
		selectedImportTitles = new Set();
		selectedFile = null;
	}
</script>

<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	<div class="mb-6">
		<a href="/admin" class="text-blue-600 hover:text-blue-800 text-sm">&larr; Back to Admin</a>
	</div>

	<h1 class="text-2xl font-bold text-gray-900 mb-8">Backup & Restore</h1>

	<!-- Export Section -->
	<div class="bg-white rounded-lg shadow-sm border p-6 mb-6">
		<h2 class="text-lg font-semibold text-gray-900 mb-4">Export Recipes</h2>
		<p class="text-gray-600 text-sm mb-4">
			Select which recipes to export as a JSON backup file. This includes all recipe data,
			categories, tags, and metadata.
		</p>

		{#if exportError}
			<div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
				{exportError}
			</div>
		{/if}

		{#if exportStep === 'idle'}
			<button
				on:click={startExportSelection}
				disabled={loadingExportRecipes}
				class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
			>
				{loadingExportRecipes ? 'Loading...' : 'Export Recipes'}
			</button>
		{:else if exportStep === 'selecting'}
			<!-- Recipe Selection List -->
			<div class="border rounded-lg mb-4">
				<!-- Select All Header -->
				<div class="border-b px-4 py-3 bg-gray-50">
					<label class="flex items-center gap-3 cursor-pointer">
						<input
							type="checkbox"
							checked={exportSelectAll}
							on:change={toggleExportSelectAll}
							class="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
						/>
						<span class="font-medium text-gray-900">Select All</span>
						<span class="text-sm text-gray-500">
							({selectedExportIds.size} of {exportRecipes.length} selected)
						</span>
					</label>
				</div>

				<!-- Recipe List -->
				<div class="max-h-96 overflow-y-auto">
					{#each exportRecipes as recipe}
						<label
							class="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
						>
							<input
								type="checkbox"
								checked={selectedExportIds.has(recipe.id)}
								on:change={() => toggleExportRecipe(recipe.id)}
								class="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
							/>
							<span class="text-gray-900">{recipe.title}</span>
							{#if recipe.category}
								<span class="text-gray-500 text-xs">({recipe.category.name})</span>
							{/if}
						</label>
					{/each}
					{#if exportRecipes.length === 0}
						<div class="px-4 py-8 text-center text-gray-500">No recipes found</div>
					{/if}
				</div>
			</div>

			<div class="flex gap-3">
				<button
					on:click={handleExportSelected}
					disabled={selectedExportIds.size === 0}
					class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
				>
					Export Selected ({selectedExportIds.size})
				</button>
				<button
					on:click={cancelExport}
					class="bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200"
				>
					Cancel
				</button>
			</div>
		{:else if exportStep === 'exporting'}
			<div class="flex items-center gap-2 text-gray-600">
				<svg class="animate-spin h-5 w-5" viewBox="0 0 24 24">
					<circle
						class="opacity-25"
						cx="12"
						cy="12"
						r="10"
						stroke="currentColor"
						stroke-width="4"
						fill="none"
					></circle>
					<path
						class="opacity-75"
						fill="currentColor"
						d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
					></path>
				</svg>
				<span>Exporting recipes...</span>
			</div>
		{/if}
	</div>

	<!-- Import Section -->
	<div class="bg-white rounded-lg shadow-sm border p-6">
		<h2 class="text-lg font-semibold text-gray-900 mb-4">Import Recipes</h2>
		<p class="text-gray-600 text-sm mb-4">
			Restore recipes from a JSON backup file. Categories and tags will be created automatically if
			they don't exist.
		</p>

		{#if importError}
			<div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
				{importError}
			</div>
		{/if}

		{#if importStep === 'idle'}
			<!-- File Input -->
			<div class="mb-4">
				<label class="block text-sm font-medium text-gray-700 mb-2"> Backup File </label>
				<input
					type="file"
					accept=".json"
					on:change={handleFileSelect}
					class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
				/>
			</div>
		{:else if importStep === 'selecting' && parsedBackup}
			<!-- Recipe Selection List -->
			<div class="border rounded-lg mb-4">
				<!-- Select All Header -->
				<div class="border-b px-4 py-3 bg-gray-50">
					<label class="flex items-center gap-3 cursor-pointer">
						<input
							type="checkbox"
							checked={importSelectAll}
							on:change={toggleImportSelectAll}
							class="h-4 w-4 text-green-600 rounded border-gray-300 focus:ring-green-500"
						/>
						<span class="font-medium text-gray-900">Select All</span>
						<span class="text-sm text-gray-500">
							({selectedImportTitles.size} of {parsedBackup.recipes.length} selected)
						</span>
					</label>
				</div>

				<!-- Recipe List -->
				<div class="max-h-96 overflow-y-auto">
					{#each parsedBackup.recipes as recipe}
						<label
							class="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
						>
							<input
								type="checkbox"
								checked={selectedImportTitles.has(recipe.title)}
								on:change={() => toggleImportRecipe(recipe.title)}
								class="h-4 w-4 text-green-600 rounded border-gray-300 focus:ring-green-500"
							/>
							<span class="text-gray-900">{recipe.title}</span>
							{#if recipe.category_name}
								<span class="text-gray-500 text-xs">({recipe.category_name})</span>
							{/if}
						</label>
					{/each}
				</div>
			</div>

			<!-- Conflict Strategy -->
			<div class="mb-4">
				<label class="block text-sm font-medium text-gray-700 mb-2">
					If recipe title already exists
				</label>
				<select
					bind:value={conflictStrategy}
					class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"
				>
					<option value="skip">Skip (keep existing)</option>
					<option value="replace">Replace (overwrite existing)</option>
					<option value="rename">Rename (create with numbered suffix)</option>
				</select>
			</div>

			<div class="flex gap-3">
				<button
					on:click={handleImportSelected}
					disabled={selectedImportTitles.size === 0}
					class="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
				>
					Import Selected ({selectedImportTitles.size})
				</button>
				<button
					on:click={cancelImport}
					class="bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200"
				>
					Cancel
				</button>
			</div>
		{:else if importStep === 'importing'}
			<div class="flex items-center gap-2 text-gray-600">
				<svg class="animate-spin h-5 w-5" viewBox="0 0 24 24">
					<circle
						class="opacity-25"
						cx="12"
						cy="12"
						r="10"
						stroke="currentColor"
						stroke-width="4"
						fill="none"
					></circle>
					<path
						class="opacity-75"
						fill="currentColor"
						d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
					></path>
				</svg>
				<span>Importing recipes...</span>
			</div>
		{/if}

		<!-- Import Results -->
		{#if importResult}
			<div class="mt-6 bg-gray-50 rounded-lg p-4">
				<h3 class="font-medium text-gray-900 mb-3">Import Results</h3>
				<dl class="grid grid-cols-2 gap-4 sm:grid-cols-4">
					<div>
						<dt class="text-sm text-gray-500">Total in file</dt>
						<dd class="text-lg font-semibold text-gray-900">{importResult.total_in_file}</dd>
					</div>
					<div>
						<dt class="text-sm text-gray-500">Selected</dt>
						<dd class="text-lg font-semibold text-gray-900">{importResult.total_selected}</dd>
					</div>
					<div>
						<dt class="text-sm text-gray-500">Created</dt>
						<dd class="text-lg font-semibold text-green-600">{importResult.created}</dd>
					</div>
					<div>
						<dt class="text-sm text-gray-500">Skipped</dt>
						<dd class="text-lg font-semibold text-yellow-600">{importResult.skipped}</dd>
					</div>
					<div>
						<dt class="text-sm text-gray-500">Replaced</dt>
						<dd class="text-lg font-semibold text-blue-600">{importResult.replaced}</dd>
					</div>
					<div>
						<dt class="text-sm text-gray-500">Errors</dt>
						<dd class="text-lg font-semibold text-red-600">{importResult.errors}</dd>
					</div>
					<div>
						<dt class="text-sm text-gray-500">Categories created</dt>
						<dd class="text-lg font-semibold text-gray-900">{importResult.categories_created}</dd>
					</div>
					<div>
						<dt class="text-sm text-gray-500">Tags created</dt>
						<dd class="text-lg font-semibold text-gray-900">{importResult.tags_created}</dd>
					</div>
				</dl>

				{#if importResult.error_details.length > 0}
					<div class="mt-4">
						<h4 class="text-sm font-medium text-red-700 mb-2">Error Details</h4>
						<ul class="text-sm text-red-600 space-y-1">
							{#each importResult.error_details as detail}
								<li>
									<span class="font-medium">{detail.title}:</span>
									{detail.error}
								</li>
							{/each}
						</ul>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>
