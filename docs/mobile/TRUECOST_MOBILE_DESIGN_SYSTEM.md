# TrueCost mobile design system

## Brand language

- Porcelain: `#F8F9FE` application canvas.
- Deep Ink: `#111329` primary copy.
- Electric Iris: `#6742F5`, with `#8B3CF5` used only for the reference-matched action gradient.
- Evidence Mint: `#087A61` only for supplied savings, success, availability and verification.
- Amber: `#B85F08` for uncertainty, urgency and freshness warnings.
- Danger: `#B4233A` for unavailable and destructive states.

## Foundations

- Spacing follows a 4/8pt rhythm: 4, 8, 12, 16, 24, 32 and 48.
- Cards use 12-18pt radii, fine lavender-neutral borders and restrained elevation, matching the compact reference layouts.
- Display, heading, body, label, eyebrow and tabular-price roles are defined in `mobile/design/tokens.ts`.
- Interactive targets are at least 44pt, include pressed and disabled states, and expose accessibility roles and labels.
- Each screen has one visually dominant action. Mint never decorates unsupported savings claims.
- Fixed navigation reserves bottom safe-area space and scroll content clears the rail.

## Navigation

The production Orbit Rail is a white floating surface with five destinations: Home, Explore, Compare, Saved and Profile. Compare is the compact elevated violet-gradient center action. Cart, notifications, activity, settings and category flows are stack destinations rather than competing top-level tabs.

## Reference fidelity

- The 54 deduplicated relevant references establish the production hierarchy: compact TrueCost masthead, white canvas, thin lavender borders, dense information cards, small provenance labels and a violet-gradient primary action.
- Oversized editorial headings, dark navigation rails and decorative claims are excluded even when an earlier implementation used them.
- Reference cards containing invented prices, savings, ratings or provider availability are layout references only. Runtime values must come from authenticated APIs, trusted ingestion or explicit device state.

## Truth and provenance

Observed price, estimated fees, missing data, freshness and final provider checkout are visually distinct. The UI never promotes sample provider names, ratings, inventory, payment benefits or savings into live facts without a backend payload. Flight and hotel result routes reject development-preview provenance and show an unavailable state instead.
