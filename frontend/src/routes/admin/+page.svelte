<script lang="ts">
	import { isAuthenticated, isAdmin } from '$lib/stores/auth';
	import { goto } from '$app/navigation';

	$: if (!$isAuthenticated) {
		goto('/login');
	}

	$: if ($isAuthenticated && !$isAdmin) {
		goto('/recipes');
	}
</script>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	<h1 class="text-2xl font-bold text-gray-900 mb-6">Admin Dashboard</h1>

	<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
		<a
			href="/admin/users"
			class="bg-white p-6 rounded-lg shadow-sm border hover:shadow-md transition-shadow"
		>
			<h2 class="text-lg font-semibold text-gray-900 mb-2">Users</h2>
			<p class="text-gray-600 text-sm">Manage user accounts and roles</p>
		</a>

		<a
			href="/admin/categories"
			class="bg-white p-6 rounded-lg shadow-sm border hover:shadow-md transition-shadow"
		>
			<h2 class="text-lg font-semibold text-gray-900 mb-2">Categories</h2>
			<p class="text-gray-600 text-sm">Manage recipe categories</p>
		</a>

		<a
			href="/admin/tags"
			class="bg-white p-6 rounded-lg shadow-sm border hover:shadow-md transition-shadow"
		>
			<h2 class="text-lg font-semibold text-gray-900 mb-2">Tags</h2>
			<p class="text-gray-600 text-sm">Manage recipe tags</p>
		</a>

		<a
			href="/admin/settings"
			class="bg-white p-6 rounded-lg shadow-sm border hover:shadow-md transition-shadow"
		>
			<h2 class="text-lg font-semibold text-gray-900 mb-2">Settings</h2>
			<p class="text-gray-600 text-sm">Configure AI providers and API keys</p>
		</a>

		<a
			href="/admin/backup"
			class="bg-white p-6 rounded-lg shadow-sm border hover:shadow-md transition-shadow"
		>
			<h2 class="text-lg font-semibold text-gray-900 mb-2">Backup</h2>
			<p class="text-gray-600 text-sm">Export and import recipe backups</p>
		</a>
	</div>
</div>
