/**
 * Decorative motifs echoing the logo's diamond dots and four-point star.
 * These are original shapes for UI accents; the logo itself is never redrawn.
 */
export function Diamond({ size = 8, className }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 10 10" className={className} aria-hidden>
      <path d="M5 0 10 5 5 10 0 5Z" fill="currentColor" />
    </svg>
  );
}

export function StarMark({ size = 16, className }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} aria-hidden>
      <path
        d="M12 0c.6 5.8 2.6 10.4 12 12-9.4 1.6-11.4 6.2-12 12-.6-5.8-2.6-10.4-12-12C9.4 10.4 11.4 5.8 12 0Z"
        fill="currentColor"
      />
    </svg>
  );
}
