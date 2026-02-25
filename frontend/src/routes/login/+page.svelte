<script lang="ts">
	import { auth, isAuthenticated } from '$lib/stores/auth';
	import { goto } from '$app/navigation';

	let username = '';
	let password = '';
	let error = '';
	let loading = false;

	$: if ($isAuthenticated) {
		goto('/recipes');
	}

	async function handleSubmit() {
		error = '';
		loading = true;

		const result = await auth.login(username, password);
		if (result) {
			error = result;
		} else {
			goto('/recipes');
		}

		loading = false;
	}
</script>

<div class="max-w-md mx-auto px-4 py-12">
	<h1 class="text-2xl font-bold text-gray-900 mb-6 text-center">Login</h1>

	<form on:submit|preventDefault={handleSubmit} class="bg-white p-6 rounded-lg shadow-sm border">
		{#if error}
			<div class="mb-4 p-3 bg-red-100 text-red-700 rounded-md text-sm">
				{error}
			</div>
		{/if}

		<div class="mb-4">
			<label for="username" class="block text-sm font-medium text-gray-700 mb-1">Username</label>
			<input
				type="text"
				id="username"
				bind:value={username}
				required
				class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
			/>
		</div>

		<div class="mb-6">
			<label for="password" class="block text-sm font-medium text-gray-700 mb-1">Password</label>
			<input
				type="password"
				id="password"
				bind:value={password}
				required
				class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
			/>
		</div>

		<button
			type="submit"
			disabled={loading}
			class="w-full bg-primary-600 hover:bg-primary-700 disabled:bg-primary-400 text-white py-2 rounded-md font-medium"
		>
			{loading ? 'Logging in...' : 'Login'}
		</button>

		<p class="mt-4 text-center text-sm text-gray-600">
			Don't have an account?
			<a href="/register" class="text-primary-600 hover:underline">Register</a>
		</p>
	</form>
</div>
