<script lang="ts">
	import { auth, user, isAuthenticated, isAdmin } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { api, type Category } from '$lib/api';

	export let currentPath = '';
	export let open = false;

	let categories: Category[] = [];

	$: if ($isAuthenticated) {
		loadCategories();
	}

	async function loadCategories() {
		const { data } = await api.getCategories();
		categories = data || [];
	}

	async function handleLogout() {
		await auth.logout();
		goto('/login');
	}

	function closeSidebar() {
		open = false;
	}

	function isActive(path: string): boolean {
		return currentPath === path;
	}
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<!-- svelte-ignore a11y-no-static-element-interactions -->
{#if open}
	<div
		class="fixed inset-0 bg-black/50 z-40 lg:hidden"
		on:click={closeSidebar}
	></div>
{/if}

<aside
	class="fixed top-0 left-0 z-50 h-full w-64 bg-white border-r border-gray-200 flex flex-col transform transition-transform duration-200 ease-in-out
		{open ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0"
>
	<!-- Logo -->
	<div class="flex items-center gap-3 px-6 py-5 border-b border-gray-100">
		<div class="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
			<svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
			</svg>
		</div>
		<span class="text-lg font-bold text-gray-900">Recipe Manager</span>
	</div>

	<!-- Navigation -->
	<nav class="flex-1 overflow-y-auto px-3 py-4">
		<div class="space-y-1">
			<a
				href="/recipes"
				on:click={closeSidebar}
				class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors
					{isActive('/recipes')
						? 'bg-primary-600 text-white'
						: 'text-gray-700 hover:bg-gray-100'}"
			>
				<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
				</svg>
				My Library
			</a>
			<a
				href="/recipes/import"
				on:click={closeSidebar}
				class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors
					{isActive('/recipes/import')
						? 'bg-primary-600 text-white'
						: 'text-gray-700 hover:bg-gray-100'}"
			>
				<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
				</svg>
				Import Recipe
			</a>
		</div>

		<!-- Collections (Categories) -->
		{#if categories.length > 0}
			<div class="mt-6">
				<h3 class="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">
					Collections
				</h3>
				<div class="mt-2 space-y-1">
					{#each categories as category}
						<a
							href="/recipes?category={category.id}"
							on:click={closeSidebar}
							class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100 transition-colors"
						>
							<span class="w-2 h-2 bg-primary-400 rounded-full"></span>
							{category.name}
						</a>
					{/each}
				</div>
			</div>
		{/if}

		<!-- Admin -->
		{#if $isAdmin}
			<div class="mt-6 pt-4 border-t border-gray-100">
				<a
					href="/admin"
					on:click={closeSidebar}
					class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors
						{currentPath.startsWith('/admin')
							? 'bg-primary-600 text-white'
							: 'text-gray-700 hover:bg-gray-100'}"
				>
					<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
						<path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
					</svg>
					Admin Settings
				</a>
			</div>
		{/if}
	</nav>

	<!-- User Section -->
	<div class="border-t border-gray-200 px-4 py-4">
		<div class="flex items-center gap-3">
			<div class="w-8 h-8 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center text-sm font-semibold uppercase">
				{$user?.username?.charAt(0) || '?'}
			</div>
			<div class="flex-1 min-w-0">
				<p class="text-sm font-medium text-gray-900 truncate">{$user?.username}</p>
				{#if $isAdmin}
					<span class="text-xs text-primary-600 font-medium">Admin</span>
				{:else}
					<span class="text-xs text-gray-500">Standard</span>
				{/if}
			</div>
		</div>
		<button
			on:click={handleLogout}
			class="mt-3 w-full text-left px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
		>
			Logout
		</button>
	</div>
</aside>
