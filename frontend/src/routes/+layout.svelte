<script lang="ts">
	import '../app.css';
	import Navbar from '$lib/components/Navbar.svelte';
	import { auth, authInitialized } from '$lib/stores/auth';
	import { onMount } from 'svelte';

	onMount(() => {
		auth.init();
	});
</script>

<div class="min-h-screen flex flex-col">
	<Navbar />
	<main class="flex-1">
		{#if $authInitialized}
			<slot />
		{:else}
			<div class="flex items-center justify-center h-64">
				<div class="text-gray-500">Loading...</div>
			</div>
		{/if}
	</main>
</div>
