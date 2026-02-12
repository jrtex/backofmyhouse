<script lang="ts">
	import { api, type BackupImportResult, type ConflictStrategy } from '$lib/api';
	import { isAuthenticated, isAdmin } from '$lib/stores/auth';
	import { goto } from '$app/navigation';

	$: if (!$isAuthenticated) {
		goto('/login');
	}

	$: if ($isAuthenticated && !$isAdmin) {
		goto('/recipes');
	}

	let exporting = false;
	let exportError = '';

	let importing = false;
	let importError = '';
	let importResult: BackupImportResult | null = null;

	let selectedFile: File | null = null;
	let conflictStrategy: ConflictStrategy = 'skip';

	async function handleExport() {
		exporting = true;
		exportError = '';
		try {
			await api.exportBackup();
		} catch (err) {
			exportError = err instanceof Error ? err.message : 'Export failed';
		} finally {
			exporting = false;
		}
	}

	function handleFileSelect(event: Event) {
		const input = event.target as HTMLInputElement;
		if (input.files && input.files.length > 0) {
			selectedFile = input.files[0];
			importResult = null;
			importError = '';
		}
	}

	async function handleImport() {
		if (!selectedFile) return;

		importing = true;
		importError = '';
		importResult = null;

		const result = await api.importBackup(selectedFile, conflictStrategy);

		if (result.error) {
			importError = result.error;
		} else if (result.data) {
			importResult = result.data;
		}

		importing = false;
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
			Download all recipes as a JSON backup file. This includes all recipe data, categories, tags,
			and metadata.
		</p>

		{#if exportError}
			<div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
				{exportError}
			</div>
		{/if}

		<button
			on:click={handleExport}
			disabled={exporting}
			class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
		>
			{exporting ? 'Exporting...' : 'Export All Recipes'}
		</button>
	</div>

	<!-- Import Section -->
	<div class="bg-white rounded-lg shadow-sm border p-6">
		<h2 class="text-lg font-semibold text-gray-900 mb-4">Import Recipes</h2>
		<p class="text-gray-600 text-sm mb-4">
			Restore recipes from a JSON backup file. Categories and tags will be created automatically if
			they don't exist.
		</p>

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

		<!-- Conflict Strategy -->
		<div class="mb-4">
			<label class="block text-sm font-medium text-gray-700 mb-2">
				If recipe title already exists
			</label>
			<select
				bind:value={conflictStrategy}
				class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
			>
				<option value="skip">Skip (keep existing)</option>
				<option value="replace">Replace (overwrite existing)</option>
				<option value="rename">Rename (create with numbered suffix)</option>
			</select>
		</div>

		{#if importError}
			<div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
				{importError}
			</div>
		{/if}

		<button
			on:click={handleImport}
			disabled={importing || !selectedFile}
			class="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
		>
			{importing ? 'Importing...' : 'Import Recipes'}
		</button>

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
