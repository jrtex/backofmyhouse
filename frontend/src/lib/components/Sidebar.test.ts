import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import { writable } from 'svelte/store';
import Sidebar from './Sidebar.svelte';

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

// Mock api
vi.mock('$lib/api', () => ({
	api: {
		getCategories: vi.fn().mockResolvedValue({
			data: [
				{ id: 'cat-1', name: 'Appetizers', created_at: '2024-01-01T00:00:00Z' },
				{ id: 'cat-2', name: 'Main Course', created_at: '2024-01-01T00:00:00Z' }
			]
		})
	}
}));

describe('Sidebar', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	describe('when authenticated as standard user', () => {
		beforeEach(async () => {
			const { __setUser } = await import('$lib/stores/auth');
			(__setUser as (user: { username: string; role: string }) => void)({
				username: 'testuser',
				role: 'standard'
			});
		});

		it('should render the brand name', () => {
			render(Sidebar, { props: { currentPath: '/recipes', open: false } });
			expect(screen.getByText('Recipe Manager')).toBeInTheDocument();
		});

		it('should render My Library link', () => {
			render(Sidebar, { props: { currentPath: '/recipes', open: false } });
			expect(screen.getByText('My Library')).toBeInTheDocument();
		});

		it('should render Import Recipe link', () => {
			render(Sidebar, { props: { currentPath: '/recipes', open: false } });
			expect(screen.getByText('Import Recipe')).toBeInTheDocument();
		});

		it('should render logout button', () => {
			render(Sidebar, { props: { currentPath: '/recipes', open: false } });
			expect(screen.getByText('Logout')).toBeInTheDocument();
		});

		it('should render username', () => {
			render(Sidebar, { props: { currentPath: '/recipes', open: false } });
			expect(screen.getByText('testuser')).toBeInTheDocument();
		});

		it('should not show Admin Settings link for standard user', () => {
			render(Sidebar, { props: { currentPath: '/recipes', open: false } });
			expect(screen.queryByText('Admin Settings')).not.toBeInTheDocument();
		});

		it('should call auth.logout and navigate on logout click', async () => {
			const { auth } = await import('$lib/stores/auth');
			const { goto } = await import('$app/navigation');

			render(Sidebar, { props: { currentPath: '/recipes', open: false } });

			const logoutButton = screen.getByText('Logout');
			await fireEvent.click(logoutButton);

			expect(auth.logout).toHaveBeenCalled();
			expect(goto).toHaveBeenCalledWith('/login');
		});
	});

	describe('when authenticated as admin', () => {
		beforeEach(async () => {
			const { __setUser } = await import('$lib/stores/auth');
			(__setUser as (user: { username: string; role: string }) => void)({
				username: 'adminuser',
				role: 'admin'
			});
		});

		it('should show Admin Settings link for admin user', () => {
			render(Sidebar, { props: { currentPath: '/recipes', open: false } });
			expect(screen.getByText('Admin Settings')).toBeInTheDocument();
		});

		it('should show Admin role badge', () => {
			render(Sidebar, { props: { currentPath: '/recipes', open: false } });
			expect(screen.getByText('Admin')).toBeInTheDocument();
		});
	});

	describe('categories list', () => {
		beforeEach(async () => {
			const { __setUser } = await import('$lib/stores/auth');
			(__setUser as (user: { username: string; role: string }) => void)({
				username: 'testuser',
				role: 'standard'
			});
		});

		it('should render the Collections heading', async () => {
			render(Sidebar, { props: { currentPath: '/recipes', open: false } });
			// Wait for categories to load
			const heading = await screen.findByText('Collections');
			expect(heading).toBeInTheDocument();
		});

		it('should render category links', async () => {
			render(Sidebar, { props: { currentPath: '/recipes', open: false } });
			const appetizers = await screen.findByText('Appetizers');
			expect(appetizers).toBeInTheDocument();
			expect(screen.getByText('Main Course')).toBeInTheDocument();
		});
	});

	describe('navigation links', () => {
		beforeEach(async () => {
			const { __setUser } = await import('$lib/stores/auth');
			(__setUser as (user: { username: string; role: string }) => void)({
				username: 'testuser',
				role: 'standard'
			});
		});

		it('should have correct href for My Library', () => {
			render(Sidebar, { props: { currentPath: '/recipes', open: false } });
			const link = screen.getByText('My Library').closest('a');
			expect(link).toHaveAttribute('href', '/recipes');
		});

		it('should have correct href for Import Recipe', () => {
			render(Sidebar, { props: { currentPath: '/recipes', open: false } });
			const link = screen.getByText('Import Recipe').closest('a');
			expect(link).toHaveAttribute('href', '/recipes/import');
		});
	});
});
