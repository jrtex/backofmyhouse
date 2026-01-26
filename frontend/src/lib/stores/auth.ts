import { writable, derived } from 'svelte/store';
import { api, type User } from '$lib/api';
import { browser } from '$app/environment';

interface AuthState {
	user: User | null;
	loading: boolean;
	initialized: boolean;
}

function createAuthStore() {
	const { subscribe, set, update } = writable<AuthState>({
		user: null,
		loading: true,
		initialized: false
	});

	return {
		subscribe,

		reset() {
			set({ user: null, loading: false, initialized: false });
		},

		async init() {
			if (!browser) return;

			const loggedIn = document.cookie.includes('logged_in=true');
			if (!loggedIn) {
				set({ user: null, loading: false, initialized: true });
				return;
			}

			update((state) => ({ ...state, loading: true }));
			const { data, error } = await api.getMe();

			if (error) {
				// Try to refresh token
				const refreshResult = await api.refreshToken();
				if (!refreshResult.error) {
					const retryResult = await api.getMe();
					if (retryResult.data) {
						set({ user: retryResult.data, loading: false, initialized: true });
						return;
					}
				}
				set({ user: null, loading: false, initialized: true });
			} else {
				set({ user: data!, loading: false, initialized: true });
			}
		},

		async login(username: string, password: string): Promise<string | null> {
			const { error } = await api.login({ username, password });
			if (error) return error;

			const { data, error: meError } = await api.getMe();
			if (meError) return meError;

			update((state) => ({ ...state, user: data! }));
			return null;
		},

		async logout() {
			await api.logout();
			set({ user: null, loading: false, initialized: true });
		},

		setUser(user: User | null) {
			update((state) => ({ ...state, user }));
		}
	};
}

export const auth = createAuthStore();
export const user = derived(auth, ($auth) => $auth.user);
export const isAuthenticated = derived(auth, ($auth) => !!$auth.user);
export const isAdmin = derived(auth, ($auth) => $auth.user?.role === 'admin');
export const authLoading = derived(auth, ($auth) => $auth.loading);
export const authInitialized = derived(auth, ($auth) => $auth.initialized);
