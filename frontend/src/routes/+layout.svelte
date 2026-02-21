<script lang="ts">
	import '../app.css';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import { auth, authInitialized, isAuthenticated } from '$lib/stores/auth';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';

	let sidebarOpen = false;

	onMount(() => {
		auth.init();
	});

	$: currentPath = $page.url.pathname;
	$: showSidebar = $isAuthenticated && !['/login', '/register'].includes(currentPath);
</script>

<div class="min-h-screen bg-gray-50">
	{#if showSidebar}
		<Sidebar bind:open={sidebarOpen} {currentPath} />

		<!-- Mobile hamburger button -->
		<div class="fixed top-4 left-4 z-30 lg:hidden">
			<button
				on:click={() => (sidebarOpen = !sidebarOpen)}
				class="p-2 bg-white rounded-lg shadow-md border border-gray-200 text-gray-600 hover:text-gray-900"
				aria-label="Toggle sidebar"
			>
				<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
				</svg>
			</button>
		</div>
	{/if}

	<main class="{showSidebar ? 'lg:ml-64' : ''}">
		{#if $authInitialized}
			<slot />
		{:else}
			<div class="flex items-center justify-center h-64">
				<div class="text-gray-500">Loading...</div>
			</div>
		{/if}
	</main>
</div>
