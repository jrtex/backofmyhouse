<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type User } from '$lib/api';
	import { isAuthenticated, isAdmin, user as currentUser } from '$lib/stores/auth';
	import { goto } from '$app/navigation';

	let users: User[] = [];
	let loading = true;
	let error = '';
	let showForm = false;
	let editingUser: User | null = null;

	let username = '';
	let email = '';
	let password = '';
	let role = 'standard';

	$: if (!$isAuthenticated || !$isAdmin) {
		goto('/');
	}

	onMount(loadUsers);

	async function loadUsers() {
		loading = true;
		const { data, error: err } = await api.getUsers();
		if (err) {
			error = err;
		} else {
			users = data || [];
		}
		loading = false;
	}

	function openCreateForm() {
		editingUser = null;
		username = '';
		email = '';
		password = '';
		role = 'standard';
		showForm = true;
	}

	function openEditForm(user: User) {
		editingUser = user;
		username = user.username;
		email = user.email;
		password = '';
		role = user.role;
		showForm = true;
	}

	function closeForm() {
		showForm = false;
		editingUser = null;
	}

	async function handleSubmit() {
		error = '';

		if (editingUser) {
			const updateData: Record<string, string> = {};
			if (username !== editingUser.username) updateData.username = username;
			if (email !== editingUser.email) updateData.email = email;
			if (password) updateData.password = password;
			if (role !== editingUser.role) updateData.role = role;

			const { error: err } = await api.updateUser(editingUser.id, updateData);
			if (err) {
				error = err;
				return;
			}
		} else {
			const { error: err } = await api.createUser({ username, email, password });
			if (err) {
				error = err;
				return;
			}
		}

		closeForm();
		loadUsers();
	}

	async function handleDelete(userId: string) {
		if (!confirm('Are you sure you want to delete this user?')) return;

		const { error: err } = await api.deleteUser(userId);
		if (err) {
			error = err;
		} else {
			loadUsers();
		}
	}
</script>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	<div class="flex justify-between items-center mb-6">
		<h1 class="text-2xl font-bold text-gray-900">Users</h1>
		<button
			on:click={openCreateForm}
			class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium"
		>
			Add User
		</button>
	</div>

	{#if error}
		<div class="mb-4 p-3 bg-red-100 text-red-700 rounded-md text-sm">{error}</div>
	{/if}

	{#if showForm}
		<div class="bg-white p-6 rounded-lg shadow-sm border mb-6">
			<h2 class="text-lg font-semibold mb-4">{editingUser ? 'Edit User' : 'Create User'}</h2>
			<form on:submit|preventDefault={handleSubmit} class="grid grid-cols-2 gap-4">
				<div>
					<label class="block text-sm font-medium text-gray-700 mb-1">Username</label>
					<input
						type="text"
						bind:value={username}
						required
						class="w-full px-3 py-2 border rounded-md"
					/>
				</div>
				<div>
					<label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
					<input type="email" bind:value={email} required class="w-full px-3 py-2 border rounded-md" />
				</div>
				<div>
					<label class="block text-sm font-medium text-gray-700 mb-1">
						Password {editingUser ? '(leave blank to keep)' : ''}
					</label>
					<input
						type="password"
						bind:value={password}
						required={!editingUser}
						minlength="8"
						class="w-full px-3 py-2 border rounded-md"
					/>
				</div>
				{#if editingUser}
					<div>
						<label class="block text-sm font-medium text-gray-700 mb-1">Role</label>
						<select bind:value={role} class="w-full px-3 py-2 border rounded-md">
							<option value="standard">Standard</option>
							<option value="admin">Admin</option>
						</select>
					</div>
				{/if}
				<div class="col-span-2 flex gap-4">
					<button
						type="submit"
						class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md"
					>
						{editingUser ? 'Update' : 'Create'}
					</button>
					<button type="button" on:click={closeForm} class="text-gray-600 hover:text-gray-800">
						Cancel
					</button>
				</div>
			</form>
		</div>
	{/if}

	{#if loading}
		<div class="text-center py-12 text-gray-500">Loading...</div>
	{:else}
		<div class="bg-white rounded-lg shadow-sm border overflow-hidden">
			<table class="min-w-full divide-y divide-gray-200">
				<thead class="bg-gray-50">
					<tr>
						<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Username</th>
						<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
						<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
						<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
						<th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-200">
					{#each users as user}
						<tr>
							<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{user.username}</td>
							<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{user.email}</td>
							<td class="px-6 py-4 whitespace-nowrap">
								<span
									class="px-2 py-1 text-xs rounded-full {user.role === 'admin'
										? 'bg-blue-100 text-blue-800'
										: 'bg-gray-100 text-gray-800'}"
								>
									{user.role}
								</span>
							</td>
							<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
								{new Date(user.created_at).toLocaleDateString()}
							</td>
							<td class="px-6 py-4 whitespace-nowrap text-right text-sm">
								<button on:click={() => openEditForm(user)} class="text-blue-600 hover:underline mr-4">
									Edit
								</button>
								{#if user.id !== $currentUser?.id}
									<button on:click={() => handleDelete(user.id)} class="text-red-600 hover:underline">
										Delete
									</button>
								{/if}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}

	<div class="mt-6">
		<a href="/admin" class="text-blue-600 hover:underline">&larr; Back to Admin</a>
	</div>
</div>
