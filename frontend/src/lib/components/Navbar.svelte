<script lang="ts">
	import { auth, user, isAuthenticated, isAdmin } from '$lib/stores/auth';
	import { goto } from '$app/navigation';

	async function handleLogout() {
		await auth.logout();
		goto('/login');
	}
</script>

<nav class="bg-white shadow-sm border-b">
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
		<div class="flex justify-between h-16">
			<div class="flex items-center">
				<a href="/" class="text-xl font-bold text-gray-900">Recipe Manager</a>
				{#if $isAuthenticated}
					<div class="ml-10 flex items-center space-x-4">
						<a
							href="/recipes"
							class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
						>
							Recipes
						</a>
						{#if $isAdmin}
							<a
								href="/admin"
								class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
							>
								Admin
							</a>
						{/if}
					</div>
				{/if}
			</div>
			<div class="flex items-center">
				{#if $isAuthenticated}
					<span class="text-gray-600 text-sm mr-4">
						{$user?.username}
						{#if $isAdmin}
							<span class="ml-1 text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">Admin</span>
						{/if}
					</span>
					<button
						on:click={handleLogout}
						class="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-md text-sm font-medium"
					>
						Logout
					</button>
				{:else}
					<a
						href="/login"
						class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
					>
						Login
					</a>
					<a
						href="/register"
						class="ml-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
					>
						Register
					</a>
				{/if}
			</div>
		</div>
	</div>
</nav>
