# TrueChoice — Full System Redesign

A complete visual and motion overhaul of all ten routes, built on one obsidian-to-emerald design system with champagne gold as the precision accent. Light is the default mode; dark is a cinematic sibling, not an afterthought.

## Design language

**Palette (semantic tokens, oklch)**
- Obsidian Black — text, dark surfaces, landing canvas
- Deep Forest — elevated dark surfaces, sidebar in dark mode
- Rich Emerald — primary brand, recommended states, CTAs
- Refined Teal — secondary accent, charts, data lines
- Soft Mint — soft fills, badges, highlight backgrounds
- Champagne Gold — "Smart Pick", verified savings, premium markers only (used sparingly so it stays meaningful)

**Typography**
- Space Grotesk: headings, nav emphasis, all numerics/metrics (tabular figures, tight tracking)
- DM Sans: body, forms, tables, supporting text
- Loaded via `<link>` in the root route; families registered as theme tokens.

**Surface system**
Four elevation tiers with matched shadow + border + translucency recipes: flat, card, raised, floating. Glass is reserved for overlays that sit on top of content — header, mobile drawer, modals, sticky summary bars — never for dense data panels where it hurts legibility.

## What changes, screen by screen

1. **Landing (`/`)** — Cinematic obsidian hero, layered depth: atmospheric emerald gradient field, subtle grain, parallax agent-recommendation card floating over the headline. Scroll-revealed proof sections, partner logo band, gold-accented CTA.
2. **App shell** — Refined sidebar with active-state indicator that slides between items, glass header with command-bar search (⌘K styling), savings pill in gold, animated mobile tab bar with morphing indicator.
3. **Dashboard** — Restructured as a bento composition: hero intent input as the anchor, then metric tiles, category shortcuts, savings chart, watchlist, recommended actions — each staggered in on mount.
4. **Compare (index + product)** — Premium comparison table: sticky column headers, recommended column lifted with emerald edge glow, TrueCost breakdown as a stepped ledger, price-history chart with gradient area fill and hover crosshair.
5. **Rides** — Map panel with depth-layered route overlay, provider cards as a horizontally snapping rail, price-vs-time scatter with animated point entry, floating booking summary.
6. **Grocery** — Split-order optimizer as the visual centrepiece: store columns with per-store totals, animated savings callout, basket sidebar with quantity steppers.
7. **Travel** — Flight/hotel option cards with gold Smart Pick badges, vertical itinerary timeline with progressive draw-in, budget donut with animated arc.
8. **Ownership / Savings / Watchlist** — Owned-item gallery with product cards and status badges, savings bar chart with staggered column growth, ledger rows with hover elevation.

## Systemic states

Every page gets purpose-built empty, loading (skeleton shimmer matched to real layout), and error states in the same design language. Hover, focus-visible, and pressed states are defined once at the component level.

## Motion

Motion (Framer Motion) with one shared spring config:
- Route transitions: fade + 8px rise
- Staggered card entrances on mount and on scroll into view
- Chart/number values count and draw in
- Hover: 1–2px lift with shadow deepening; no scale-bounce
- `prefers-reduced-motion` disables all transforms

## Technical notes

- Tokens rewritten in `src/styles.css` under `@theme inline` / `:root` / `.dark`; no hardcoded colors in components. New tokens for gold, forest, obsidian, plus elevation shadow and gradient variables.
- Fonts via `<link>` in `src/routes/__root.tsx` (never `@import` in CSS).
- `framer-motion` added; shared variants live in a single `src/lib/motion.ts` so timing is consistent everywhere.
- New primitives in `src/components/tc/`: elevation-aware `Panel`, `GlassSurface`, `Skeleton`, `EmptyState`, `MetricTile`, `SegmentedControl`, animated `AnimatedNumber`.
- Theme toggle in the header, persisted to localStorage, no hydration flash.
- Existing mock data in `src/lib/mock-data.ts` is reused; content and information density stay as-is — this is presentation-layer work only.
- Responsive recomposition at each breakpoint (not scaling down): grid → stacked rails on tablet, single-column priority order on mobile.
