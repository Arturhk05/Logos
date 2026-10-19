/**
 * Marks a high criticality incident nobody has taken, the most urgent exception in the queue.
 * With reduced motion the halo runs once and fades out (index.css), leaving a still dot.
 */
export function WaitingDot() {
  return (
    <span className="relative flex size-2.5 shrink-0">
      <span aria-hidden className="absolute inset-0 animate-waiting rounded-full bg-critical-ink" />
      <span aria-hidden className="relative size-2.5 rounded-full bg-critical-ink" />
      <span className="sr-only">Aguardando responsável</span>
    </span>
  );
}
