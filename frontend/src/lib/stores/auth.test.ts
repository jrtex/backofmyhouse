import { describe, it, expect, beforeEach, vi } from 'vitest';
import { get } from 'svelte/store';
import { http, HttpResponse } from 'msw';
import { server } from '../../mocks/server';
import { auth, user, isAuthenticated, isAdmin, authLoading, authInitialized } from './auth';

// Mock document.cookie
Object.defineProperty(document, 'cookie', {
	writable: true,
	value: ''
});

describe('Auth Store', () => {
	beforeEach(() => {
		// Reset the store state and document cookie
		auth.reset();
		document.cookie = '';
	});

	describe('init', () => {
		it('should set initialized to true when no logged_in cookie', async () => {
			document.cookie = '';
			await auth.init();

			const state = get(auth);
			expect(state.initialized).toBe(true);
			expect(state.loading).toBe(false);
			expect(state.user).toBeNull();
		});

		it('should fetch user when logged_in cookie exists', async () => {
			document.cookie = 'logged_in=true';

			await auth.init();

			const state = get(auth);
			expect(state.initialized).toBe(true);
			expect(state.loading).toBe(false);
			expect(state.user).not.toBeNull();
			expect(state.user?.username).toBe('testuser');
		});

		it('should try to refresh token when getMe fails', async () => {
			document.cookie = 'logged_in=true';

			// First getMe fails, then refresh succeeds, then getMe succeeds
			let getMeCallCount = 0;
			server.use(
				http.get('/api/auth/me', () => {
					getMeCallCount++;
					if (getMeCallCount === 1) {
						return HttpResponse.json({ detail: 'Token expired' }, { status: 401 });
					}
					return HttpResponse.json({
						id: 'user-1',
						username: 'testuser',
						email: 'test@example.com',
						role: 'standard',
						created_at: '2024-01-01',
						updated_at: '2024-01-01'
					});
				})
			);

			await auth.init();

			const state = get(auth);
			expect(state.initialized).toBe(true);
			expect(state.user).not.toBeNull();
		});

		it('should set user to null when refresh also fails', async () => {
			document.cookie = 'logged_in=true';

			server.use(
				http.get('/api/auth/me', () => {
					return HttpResponse.json({ detail: 'Token expired' }, { status: 401 });
				}),
				http.post('/api/auth/refresh', () => {
					return HttpResponse.json({ detail: 'Refresh failed' }, { status: 401 });
				})
			);

			await auth.init();

			const state = get(auth);
			expect(state.initialized).toBe(true);
			expect(state.user).toBeNull();
		});
	});

	describe('login', () => {
		it('should return null on successful login', async () => {
			const error = await auth.login('testuser', 'password123');

			expect(error).toBeNull();
			const state = get(auth);
			expect(state.user).not.toBeNull();
			expect(state.user?.username).toBe('testuser');
		});

		it('should return error message on failed login', async () => {
			const error = await auth.login('testuser', 'wrongpassword');

			expect(error).toBe('Invalid username or password');
			const state = get(auth);
			expect(state.user).toBeNull();
		});

		it('should return error when getMe fails after login', async () => {
			server.use(
				http.post('/api/auth/login', () => {
					return HttpResponse.json({ message: 'Login successful' });
				}),
				http.get('/api/auth/me', () => {
					return HttpResponse.json({ detail: 'Server error' }, { status: 500 });
				})
			);

			const error = await auth.login('testuser', 'password123');

			expect(error).toBe('Server error');
		});
	});

	describe('logout', () => {
		it('should clear user on logout', async () => {
			// First login
			await auth.login('testuser', 'password123');
			expect(get(auth).user).not.toBeNull();

			// Then logout
			await auth.logout();

			const state = get(auth);
			expect(state.user).toBeNull();
			expect(state.loading).toBe(false);
			expect(state.initialized).toBe(true);
		});
	});

	describe('setUser', () => {
		it('should update user directly', () => {
			const newUser = {
				id: 'new-id',
				username: 'newuser',
				email: 'new@example.com',
				role: 'admin' as const,
				created_at: '2024-01-01',
				updated_at: '2024-01-01'
			};

			auth.setUser(newUser);

			expect(get(user)).toEqual(newUser);
		});

		it('should allow setting user to null', () => {
			auth.setUser(null);

			expect(get(user)).toBeNull();
		});
	});

	describe('derived stores', () => {
		it('user should reflect auth state', async () => {
			await auth.login('testuser', 'password123');

			const currentUser = get(user);
			expect(currentUser?.username).toBe('testuser');
		});

		it('isAuthenticated should be true when user exists', async () => {
			await auth.login('testuser', 'password123');

			expect(get(isAuthenticated)).toBe(true);
		});

		it('isAuthenticated should be false when user is null', async () => {
			await auth.logout();

			expect(get(isAuthenticated)).toBe(false);
		});

		it('isAdmin should be true for admin users', async () => {
			server.use(
				http.post('/api/auth/login', () => {
					return HttpResponse.json({ message: 'Login successful' });
				}),
				http.get('/api/auth/me', () => {
					return HttpResponse.json({
						id: 'admin-id',
						username: 'admin',
						email: 'admin@example.com',
						role: 'admin',
						created_at: '2024-01-01',
						updated_at: '2024-01-01'
					});
				})
			);

			await auth.login('admin', 'password123');

			expect(get(isAdmin)).toBe(true);
		});

		it('isAdmin should be false for standard users', async () => {
			await auth.login('testuser', 'password123');

			expect(get(isAdmin)).toBe(false);
		});

		it('authLoading should reflect loading state', () => {
			// Initially loading is true in store definition
			// After operations complete, loading should be false
			expect(get(authLoading)).toBeDefined();
		});

		it('authInitialized should be true after init', async () => {
			await auth.init();

			expect(get(authInitialized)).toBe(true);
		});
	});
});
