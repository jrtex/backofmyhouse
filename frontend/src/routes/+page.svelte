<script lang="ts">
	import { isAuthenticated } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	onMount(() => {
		if ($isAuthenticated) {
			goto('/recipes');
		}
	});

	$: if ($isAuthenticated) {
		goto('/recipes');
	}
</script>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
	<div class="text-center">
		<h1 class="text-4xl font-bold text-gray-900 mb-4">Recipe Manager</h1>
		<p class="text-xl text-gray-600 mb-8">
			Organize and share your favorite recipes
		</p>
		<div class="flex justify-center gap-4">
			<a
				href="/login"
				class="bg-primary-600 hover:bg-primary-700 text-white px-6 py-3 rounded-lg font-medium"
			>
				Login
			</a>
			<a
				href="/register"
				class="bg-gray-100 hover:bg-gray-200 text-gray-700 px-6 py-3 rounded-lg font-medium"
			>
				Register
			</a>
		</div>
	</div>
</div>
