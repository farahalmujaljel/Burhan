import type { TwinUpdate } from "@/lib/api/types";

export type ChangeKind = "added" | "strengthened" | "changed" | "removed";

export const CHANGE_STYLES: Record<ChangeKind, { label: string; color: string; hint: string }> = {
  added: { label: "Added", color: "#2f7d5b", hint: "New entities and relations" },
  strengthened: {
    label: "Strengthened",
    color: "#9c7a3c",
    hint: "Existing knowledge gained a supporting paper or more evidence",
  },
  changed: {
    label: "Changed",
    color: "#3d4fa8",
    hint: "New aliases, or evidence replaced by a re-extraction",
  },
  removed: { label: "Removed", color: "#b5542e", hint: "No longer supported by any paper" },
};

export const CHANGE_KINDS: ChangeKind[] = ["added", "strengthened", "changed", "removed"];

export function entityIds(u: TwinUpdate, kind: ChangeKind): string[] {
  return {
    added: u.added_entity_ids,
    strengthened: u.strengthened_entity_ids,
    changed: u.changed_entity_ids,
    removed: u.removed_entity_ids,
  }[kind] ?? [];
}

export function relationIds(u: TwinUpdate, kind: ChangeKind): string[] {
  return {
    added: u.added_relation_ids,
    strengthened: u.strengthened_relation_ids,
    changed: u.changed_relation_ids,
    removed: u.removed_relation_ids,
  }[kind] ?? [];
}

export function changeCount(u: TwinUpdate, kind: ChangeKind): number {
  return entityIds(u, kind).length + relationIds(u, kind).length;
}

export function isNoop(u: TwinUpdate): boolean {
  return CHANGE_KINDS.every((k) => changeCount(u, k) === 0);
}

export interface GrowthPoint {
  update: TwinUpdate;
  added: number;
  strengthened: number;
  removed: number;
  total: number; // entities in the twin after this update
}

/** Per-update entity changes plus the running entity total, oldest update first. */
export function growthSeries(updatesNewestFirst: TwinUpdate[]): GrowthPoint[] {
  return [...updatesNewestFirst].reverse().reduce<GrowthPoint[]>((series, update) => {
    const added = entityIds(update, "added").length;
    const removed = entityIds(update, "removed").length;
    const previous = series.at(-1)?.total ?? 0;
    series.push({
      update,
      added,
      removed,
      strengthened: entityIds(update, "strengthened").length,
      total: previous + added - removed,
    });
    return series;
  }, []);
}
