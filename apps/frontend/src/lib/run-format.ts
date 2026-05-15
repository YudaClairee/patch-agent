export function statusClass(status: string) {
  if (status === "succeeded") return "text-[var(--patch-accent)]";
  if (status === "failed" || status === "cancelled") return "text-[var(--patch-error)]";
  if (status === "running") return "text-[var(--patch-warn)]";
  return "text-[var(--patch-dim)]";
}

export function formatAge(iso: string) {
  const ms = Date.now() - new Date(iso).getTime();
  const sec = Math.floor(ms / 1000);
  if (sec < 60) return `${sec}s`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h`;
  return `${Math.floor(hr / 24)}d`;
}
