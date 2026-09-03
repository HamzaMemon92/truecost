import type { Transition, Variants } from "framer-motion";

/** One spring for the whole system — fast, natural, never bouncy. */
export const spring: Transition = { type: "spring", stiffness: 320, damping: 32, mass: 0.9 };

export const ease: Transition = { duration: 0.42, ease: [0.22, 1, 0.36, 1] };

/** Container that staggers its children in. */
export const stagger = (delay = 0.04, initial = 0.02): Variants => ({
  hidden: {},
  show: { transition: { staggerChildren: delay, delayChildren: initial } },
});

/** Standard child entrance: fade + 8px rise. */
export const riseIn: Variants = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0, transition: ease },
};

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: ease },
};

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.97 },
  show: { opacity: 1, scale: 1, transition: spring },
};

/** Reveal-on-scroll props for a section. */
export const revealProps = {
  initial: "hidden",
  whileInView: "show",
  viewport: { once: true, margin: "-60px" },
} as const;

/** Mount-time reveal props. */
export const mountProps = {
  initial: "hidden",
  animate: "show",
} as const;
