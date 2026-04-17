const ACTIVE_SEASON_KEY = "activeSeasonId";
const ACTIVE_SEASON_EVENT = "active-season-updated";

export function getActiveSeasonId(): number | null {
  const raw = window.localStorage.getItem(ACTIVE_SEASON_KEY);
  if (!raw) return null;
  const n = Number(raw);
  return Number.isFinite(n) && n > 0 ? n : null;
}

export function setActiveSeasonId(seasonId: number): void {
  window.localStorage.setItem(ACTIVE_SEASON_KEY, String(seasonId));
  window.dispatchEvent(new CustomEvent<number>(ACTIVE_SEASON_EVENT, { detail: seasonId }));
}

export function onActiveSeasonChange(
  cb: (seasonId: number) => void,
): () => void {
  const handler = (e: Event) => {
    const ce = e as CustomEvent<number>;
    if (typeof ce.detail === "number" && ce.detail > 0) {
      cb(ce.detail);
    }
  };
  window.addEventListener(ACTIVE_SEASON_EVENT, handler);
  return () => window.removeEventListener(ACTIVE_SEASON_EVENT, handler);
}

