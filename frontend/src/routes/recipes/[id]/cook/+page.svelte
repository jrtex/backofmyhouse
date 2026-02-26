<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { api, type Recipe, type Ingredient, type Instruction } from '$lib/api';
	import { isAuthenticated } from '$lib/stores/auth';
	import { groupBySection, type SectionGroup } from '$lib/utils/groupBySection';
	import IngredientsPanel from '$lib/components/IngredientsPanel.svelte';

	let recipe: Recipe | null = null;
	let loading = true;
	let error = '';

	type Slide =
		| { type: 'ingredients'; ingredients: SectionGroup<Ingredient>[] }
		| { type: 'instruction'; section: string | null; instruction: Instruction; stepLabel: string };

	let slides: Slide[] = [];
	let currentIndex = 0;
	let ingredientsPanelOpen = false;

	// Touch tracking
	let touchStartX = 0;
	let touchStartY = 0;
	let touchActive = false;

	// Wake lock
	let wakeLock: WakeSentinel | null = null;

	$: if (!$isAuthenticated) {
		goto('/login');
	}

	$: recipeId = $page.params.id;

	onMount(async () => {
		loading = true;
		const { data, error: err } = await api.getRecipe(recipeId);
		if (err) {
			error = err;
		} else {
			recipe = data!;
			buildSlides();
		}
		loading = false;

		window.addEventListener('keydown', handleKeydown);
		document.addEventListener('visibilitychange', handleVisibilityChange);
		acquireWakeLock();
	});

	onDestroy(() => {
		if (typeof window !== 'undefined') {
			window.removeEventListener('keydown', handleKeydown);
			document.removeEventListener('visibilitychange', handleVisibilityChange);
		}
		releaseWakeLock();
	});

	function buildSlides() {
		if (!recipe) return;

		const built: Slide[] = [];

		// Slide 0: ingredients overview
		built.push({
			type: 'ingredients',
			ingredients: groupBySection(recipe.ingredients)
		});

		// Slides 1..N: instructions in section order
		const instructionGroups = groupBySection(recipe.instructions);
		let stepNum = 0;
		let totalSteps = recipe.instructions.length;
		for (const group of instructionGroups) {
			for (const inst of group.items) {
				stepNum++;
				built.push({
					type: 'instruction',
					section: group.section,
					instruction: inst,
					stepLabel: `Step ${stepNum} of ${totalSteps}`
				});
			}
		}

		slides = built;
	}

	function goNext() {
		if (currentIndex >= slides.length - 1) {
			goto(`/recipes/${recipeId}`);
			return;
		}
		currentIndex++;
	}

	function goPrev() {
		if (currentIndex > 0) {
			currentIndex--;
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (ingredientsPanelOpen) return;
		if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
			e.preventDefault();
			goNext();
		} else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
			e.preventDefault();
			goPrev();
		} else if (e.key === 'Escape') {
			e.preventDefault();
			goto(`/recipes/${recipeId}`);
		}
	}

	function handleTouchStart(e: TouchEvent) {
		const touch = e.touches[0];
		touchStartX = touch.clientX;
		touchStartY = touch.clientY;
		touchActive = true;
	}

	function handleTouchMove(e: TouchEvent) {
		// Prevent default only if we detect a horizontal swipe, to avoid blocking scroll
	}

	function handleTouchEnd(e: TouchEvent) {
		if (!touchActive) return;
		touchActive = false;

		const touch = e.changedTouches[0];
		const dx = touch.clientX - touchStartX;
		const dy = touch.clientY - touchStartY;

		// Require horizontal dominance and minimum threshold
		if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) {
			if (dx < 0) {
				goNext(); // swipe left = next
			} else {
				goPrev(); // swipe right = prev
			}
		}
	}

	async function acquireWakeLock() {
		try {
			if ('wakeLock' in navigator) {
				wakeLock = await navigator.wakeLock.request('screen');
			}
		} catch {
			// Fail silently if unsupported or denied
		}
	}

	function releaseWakeLock() {
		if (wakeLock) {
			wakeLock.release();
			wakeLock = null;
		}
	}

	function handleVisibilityChange() {
		if (document.visibilityState === 'visible') {
			acquireWakeLock();
		}
	}

	function getSlidePreviewText(index: number): string {
		if (index < 0 || index >= slides.length) return '';
		const slide = slides[index];
		if (slide.type === 'ingredients') return 'Ingredients overview';
		return slide.instruction.text;
	}

	// Show section header on the first step of a new section
	function shouldShowSectionHeader(index: number): boolean {
		const slide = slides[index];
		if (slide.type !== 'instruction' || !slide.section) return false;

		// Show if previous slide is ingredients or a different section
		if (index <= 1) return true;
		const prev = slides[index - 1];
		if (prev.type !== 'instruction') return true;
		return prev.section !== slide.section;
	}

	$: currentSlide = slides[currentIndex];
	$: isFirst = currentIndex === 0;
	$: isLast = currentIndex === slides.length - 1;
	$: prevPreview = getSlidePreviewText(currentIndex - 1);
	$: nextPreview = getSlidePreviewText(currentIndex + 1);
	$: showSectionHeader = currentSlide?.type === 'instruction' && shouldShowSectionHeader(currentIndex);

	$: nextButtonText = isFirst ? 'Start Cooking' : isLast ? 'Done' : 'Next';
</script>

<svelte:head>
	<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
</svelte:head>

{#if loading}
	<div class="fixed inset-0 flex items-center justify-center bg-white">
		<p class="text-gray-500 text-lg">Loading recipe...</p>
	</div>
{:else if error}
	<div class="fixed inset-0 flex items-center justify-center bg-white p-4">
		<div class="text-center">
			<p class="text-red-600 mb-4">{error}</p>
			<a href="/recipes" class="text-primary-600 hover:underline">Back to recipes</a>
		</div>
	</div>
{:else if recipe && slides.length > 0}
	<div
		class="fixed inset-0 bg-white flex flex-col z-40"
		on:touchstart={handleTouchStart}
		on:touchmove={handleTouchMove}
		on:touchend={handleTouchEnd}
	>
		<!-- Header -->
		<div class="flex items-center justify-between px-4 py-3 border-b bg-white flex-shrink-0">
			<a
				href="/recipes/{recipeId}"
				class="flex items-center gap-1 text-gray-600 hover:text-gray-900 p-2 -m-2 rounded-lg"
				aria-label="Exit kitchen mode"
			>
				<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
				</svg>
				<span class="hidden sm:inline text-sm">Exit</span>
			</a>

			<h1 class="text-sm sm:text-base font-semibold text-gray-900 truncate mx-4 text-center flex-1">
				{recipe.title}
			</h1>

			<button
				on:click={() => (ingredientsPanelOpen = true)}
				class="flex items-center gap-1 text-gray-600 hover:text-gray-900 p-2 -m-2 rounded-lg"
				aria-label="Show ingredients"
			>
				<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
				</svg>
				<span class="hidden sm:inline text-sm">Ingredients</span>
			</button>
		</div>

		<!-- Main Content -->
		<div class="flex-1 flex flex-col justify-center overflow-y-auto px-6 py-4">
			<!-- Previous preview -->
			{#if prevPreview}
				<button
					on:click={goPrev}
					class="text-gray-400 text-sm text-center mb-4 truncate max-w-md mx-auto hover:text-gray-500 transition-colors"
				>
					&#8593; {prevPreview}
				</button>
			{/if}

			<!-- Current slide -->
			<div class="flex-1 flex flex-col items-center justify-center max-w-2xl mx-auto w-full">
				{#if currentSlide.type === 'ingredients'}
					<h2 class="text-lg font-semibold text-gray-500 mb-6">Ingredients</h2>
					<div class="w-full space-y-4 text-left">
						{#each currentSlide.ingredients as group}
							{#if group.section}
								<h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mt-2">{group.section}</h3>
							{/if}
							<ul class="space-y-2">
								{#each group.items as ing}
									<li class="flex items-start text-lg sm:text-xl">
										<span class="w-2 h-2 bg-blue-500 rounded-full mt-2.5 mr-3 flex-shrink-0"></span>
										<span>
											{#if ing.quantity}
												<span class="font-medium">{ing.quantity}</span>
											{/if}
											{#if ing.unit}
												<span>{ing.unit}</span>
											{/if}
											{ing.name}
											{#if ing.notes}
												<span class="text-gray-500 text-base">({ing.notes})</span>
											{/if}
										</span>
									</li>
								{/each}
							</ul>
						{/each}
					</div>
					<p class="text-gray-400 text-sm mt-8">Swipe or tap Next to start</p>
				{:else}
					{#if showSectionHeader}
						<div class="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
							{currentSlide.section}
						</div>
					{/if}
					<div class="text-sm font-medium text-gray-500 mb-4">
						{currentSlide.stepLabel}
					</div>
					<p class="text-2xl sm:text-3xl text-gray-900 text-center leading-relaxed">
						{currentSlide.instruction.text}
					</p>
				{/if}
			</div>

			<!-- Next preview -->
			{#if nextPreview}
				<button
					on:click={goNext}
					class="text-gray-400 text-sm text-center mt-4 truncate max-w-md mx-auto hover:text-gray-500 transition-colors"
				>
					&#8595; {nextPreview}
				</button>
			{/if}
		</div>

		<!-- Footer -->
		<div class="flex items-center justify-between px-4 py-3 border-t bg-white flex-shrink-0">
			{#if !isFirst}
				<button
					on:click={goPrev}
					class="flex items-center gap-1 px-5 py-3 min-h-[48px] rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium transition-colors"
				>
					<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
					</svg>
					Previous
				</button>
			{:else}
				<div></div>
			{/if}

			<button
				on:click={goNext}
				class="flex items-center gap-1 px-5 py-3 min-h-[48px] rounded-lg bg-primary-600 hover:bg-primary-700 text-white font-medium transition-colors"
			>
				{nextButtonText}
				{#if !isLast}
					<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
					</svg>
				{/if}
			</button>
		</div>
	</div>

	<IngredientsPanel
		open={ingredientsPanelOpen}
		ingredients={recipe.ingredients}
		onClose={() => (ingredientsPanelOpen = false)}
	/>
{/if}
