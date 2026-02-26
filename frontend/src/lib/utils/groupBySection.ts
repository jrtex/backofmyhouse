export type SectionGroup<T> = { section: string | null; items: T[] };

export function groupBySection<T extends { section?: string }>(items: T[]): SectionGroup<T>[] {
	const groups: SectionGroup<T>[] = [];
	for (const item of items) {
		const section = item.section ?? null;
		const last = groups[groups.length - 1];
		if (last && last.section === section) {
			last.items.push(item);
		} else {
			groups.push({ section, items: [item] });
		}
	}
	return groups;
}
