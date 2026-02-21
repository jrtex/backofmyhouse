<script lang="ts">
	import { api } from '$lib/api';
	import { isAuthenticated } from '$lib/stores/auth';
	import { goto } from '$app/navigation';

	let username = '';
	let email = '';
	let password = '';
	let confirmPassword = '';
	let error = '';
	let success = '';
	let loading = false;

	$: if ($isAuthenticated) {
		goto('/recipes');
	}

	async function handleSubmit() {
		error = '';
		success = '';

		if (password !== confirmPassword) {
			error = 'Passwords do not match';
			return;
		}

		if (password.length < 8) {
			error = 'Password must be at least 8 characters';
			return;
		}

		loading = true;

		const { data, error: apiError } = await api.register({ username, email, password });

		if (apiError) {
			error = apiError;
		} else {
			success = `Registration successful! You are registered as ${data?.role}. Please login.`;
			username = '';
			email = '';
			password = '';
			confirmPassword = '';
		}

		loading = false;
	}
</script>

<div class="max-w-md mx-auto px-4 py-12">
	<h1 class="text-2xl font-bold text-gray-900 mb-6 text-center">Register</h1>

	<form on:submit|preventDefault={handleSubmit} class="bg-white p-6 rounded-lg shadow-sm border">
		{#if error}
			<div class="mb-4 p-3 bg-red-100 text-red-700 rounded-md text-sm">
				{error}
			</div>
		{/if}

		{#if success}
			<div class="mb-4 p-3 bg-green-100 text-green-700 rounded-md text-sm">
				{success}
				<a href="/login" class="underline ml-1">Go to login</a>
			</div>
		{/if}

		<div class="mb-4">
			<label for="username" class="block text-sm font-medium text-gray-700 mb-1">Username</label>
			<input
				type="text"
				id="username"
				bind:value={username}
				required
				minlength="3"
				class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
			/>
		</div>

		<div class="mb-4">
			<label for="email" class="block text-sm font-medium text-gray-700 mb-1">Email</label>
			<input
				type="email"
				id="email"
				bind:value={email}
				required
				class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
			/>
		</div>

		<div class="mb-4">
			<label for="password" class="block text-sm font-medium text-gray-700 mb-1">Password</label>
			<input
				type="password"
				id="password"
				bind:value={password}
				required
				minlength="8"
				class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
			/>
		</div>

		<div class="mb-6">
			<label for="confirmPassword" class="block text-sm font-medium text-gray-700 mb-1"
				>Confirm Password</label
			>
			<input
				type="password"
				id="confirmPassword"
				bind:value={confirmPassword}
				required
				class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
			/>
		</div>

		<button
			type="submit"
			disabled={loading}
			class="w-full bg-primary-600 hover:bg-primary-700 disabled:bg-primary-400 text-white py-2 rounded-md font-medium"
		>
			{loading ? 'Registering...' : 'Register'}
		</button>

		<p class="mt-4 text-center text-sm text-gray-600">
			Already have an account?
			<a href="/login" class="text-primary-600 hover:underline">Login</a>
		</p>
	</form>
</div>
