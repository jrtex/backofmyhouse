import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import { writable } from 'svelte/store';
import Navbar from './Navbar.svelte';

// Mock the auth store
vi.mock('$lib/stores/auth', () => {
	const mockUser = writable<{ username: string; role: string } | null>(null);
	const mockIsAuthenticated = writable(false);
	const mockIsAdmin = writable(false);

	return {
		auth: {
			subscribe: mockUser.subscribe,
			logout: vi.fn()
		},
		user: mockUser,
		isAuthenticated: mockIsAuthenticated,
		isAdmin: mockIsAdmin,
		// Helper functions for tests
		__setUser: (user: { username: string; role: string } | null) => {
			mockUser.set(user);
			mockIsAuthenticated.set(user !== null);
			mockIsAdmin.set(user?.role === 'admin');
		}
	};
});

// Mock goto
vi.mock('$app/navigation', () => ({
	goto: vi.fn()
}));

describe('Navbar', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	describe('when not authenticated', () => {
		beforeEach(async () => {
			const { __setUser } = await import('$lib/stores/auth');
			(__setUser as (user: null) => void)(null);
		});

		it('should render the brand name', () => {
			render(Navbar);
			expect(screen.getByText('Recipe Manager')).toBeInTheDocument();
		});

		it('should show Login and Register links', () => {
			render(Navbar);
			expect(screen.getByRole('link', { name: 'Login' })).toBeInTheDocument();
			expect(screen.getByRole('link', { name: 'Register' })).toBeInTheDocument();
		});

		it('should not show Recipes link', () => {
			render(Navbar);
			expect(screen.queryByRole('link', { name: 'Recipes' })).not.toBeInTheDocument();
		});

		it('should not show logout button', () => {
			render(Navbar);
			expect(screen.queryByRole('button', { name: 'Logout' })).not.toBeInTheDocument();
		});
	});

	describe('when authenticated as standard user', () => {
		beforeEach(async () => {
			const { __setUser } = await import('$lib/stores/auth');
			(__setUser as (user: { username: string; role: string }) => void)({
				username: 'testuser',
				role: 'standard'
			});
		});

		it('should show username', () => {
			render(Navbar);
			expect(screen.getByText('testuser')).toBeInTheDocument();
		});

		it('should show Recipes link', () => {
			render(Navbar);
			expect(screen.getByRole('link', { name: 'Recipes' })).toBeInTheDocument();
		});

		it('should show logout button', () => {
			render(Navbar);
			expect(screen.getByRole('button', { name: 'Logout' })).toBeInTheDocument();
		});

		it('should not show Admin link', () => {
			render(Navbar);
			expect(screen.queryByRole('link', { name: 'Admin' })).not.toBeInTheDocument();
		});

		it('should not show Admin badge', () => {
			render(Navbar);
			expect(screen.queryByText('Admin', { selector: 'span.bg-blue-100' })).not.toBeInTheDocument();
		});

		it('should not show Login/Register links', () => {
			render(Navbar);
			expect(screen.queryByRole('link', { name: 'Login' })).not.toBeInTheDocument();
			expect(screen.queryByRole('link', { name: 'Register' })).not.toBeInTheDocument();
		});
	});

	describe('when authenticated as admin user', () => {
		beforeEach(async () => {
			const { __setUser } = await import('$lib/stores/auth');
			(__setUser as (user: { username: string; role: string }) => void)({
				username: 'adminuser',
				role: 'admin'
			});
		});

		it('should show Admin link', () => {
			render(Navbar);
			expect(screen.getByRole('link', { name: 'Admin' })).toBeInTheDocument();
		});

		it('should show Admin badge next to username', () => {
			render(Navbar);
			const adminBadges = screen.getAllByText('Admin');
			// One is the link, one is the badge
			expect(adminBadges.length).toBeGreaterThanOrEqual(1);
		});
	});

	describe('logout functionality', () => {
		beforeEach(async () => {
			const { __setUser } = await import('$lib/stores/auth');
			(__setUser as (user: { username: string; role: string }) => void)({
				username: 'testuser',
				role: 'standard'
			});
		});

		it('should call auth.logout and navigate to login on logout click', async () => {
			const { auth } = await import('$lib/stores/auth');
			const { goto } = await import('$app/navigation');

			render(Navbar);

			const logoutButton = screen.getByRole('button', { name: 'Logout' });
			await fireEvent.click(logoutButton);

			expect(auth.logout).toHaveBeenCalled();
			expect(goto).toHaveBeenCalledWith('/login');
		});
	});

	describe('navigation links', () => {
		it('should have correct href for brand link', () => {
			render(Navbar);
			const brandLink = screen.getByRole('link', { name: 'Recipe Manager' });
			expect(brandLink).toHaveAttribute('href', '/');
		});

		it('should have correct href for login link when not authenticated', async () => {
			const { __setUser } = await import('$lib/stores/auth');
			(__setUser as (user: null) => void)(null);

			render(Navbar);
			const loginLink = screen.getByRole('link', { name: 'Login' });
			expect(loginLink).toHaveAttribute('href', '/login');
		});

		it('should have correct href for register link when not authenticated', async () => {
			const { __setUser } = await import('$lib/stores/auth');
			(__setUser as (user: null) => void)(null);

			render(Navbar);
			const registerLink = screen.getByRole('link', { name: 'Register' });
			expect(registerLink).toHaveAttribute('href', '/register');
		});

		it('should have correct href for recipes link when authenticated', async () => {
			const { __setUser } = await import('$lib/stores/auth');
			(__setUser as (user: { username: string; role: string }) => void)({
				username: 'testuser',
				role: 'standard'
			});

			render(Navbar);
			const recipesLink = screen.getByRole('link', { name: 'Recipes' });
			expect(recipesLink).toHaveAttribute('href', '/recipes');
		});

		it('should have correct href for admin link when admin', async () => {
			const { __setUser } = await import('$lib/stores/auth');
			(__setUser as (user: { username: string; role: string }) => void)({
				username: 'admin',
				role: 'admin'
			});

			render(Navbar);
			const adminLink = screen.getByRole('link', { name: 'Admin' });
			expect(adminLink).toHaveAttribute('href', '/admin');
		});
	});
});
