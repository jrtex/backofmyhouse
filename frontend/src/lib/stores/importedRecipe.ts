import { writable } from 'svelte/store';
import type { RecipeExtraction } from '$lib/api';

export interface ImportedRecipeState {
	extraction: RecipeExtraction | null;
	sourceUrl?: string;
}

function createImportedRecipeStore() {
	const { subscribe, set, update } = writable<ImportedRecipeState>({ extraction: null });

	return {
		subscribe,
		setExtraction: (extraction: RecipeExtraction, sourceUrl?: string) => {
			set({ extraction, sourceUrl });
		},
		clear: () => {
			set({ extraction: null });
		}
	};
}

export const importedRecipe = createImportedRecipeStore();
