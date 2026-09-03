# Cleanup and correctness pass

The UI is in place across all routes. A review of the current code turned up a small set of real defects — no redesign work is required unless you ask for it.

## What's actually broken

1. **Type errors in the shopping backend layer** (6 errors, confirmed by a typecheck run). All in `src/lib/common-master/`:
   - `shopping-api.ts` passes possibly-undefined `session_id`/`user_id` into a request type that requires strings.
   - `shopping-provider-adapters.ts` reads `process.env.FLIPKART_*` with dot access, which the project's TS config rejects.
   - `shopping-workflow.ts` returns a possibly-undefined recommendation and indexes an array without a guard.
   - `shopping-mcp.ts` triggers "type instantiation is excessively deep" from the MCP tool-schema generics.

2. **Dead server code in the client tree.** Nothing in the app imports `shopping-api.ts`, `shopping-backend-client.ts`, or `shopping-mcp.ts`. The `/shopping` page runs purely on the local mock workflow. These modules pull in LangGraph, OpenAI, and the MCP SDK for no runtime benefit and are the source of most of the type errors.

3. **`/shopping` has no page metadata.** Every other route defines `head()` with a title and description; this one doesn't, so it inherits the generic root title.

## Plan

- Remove the unused server-side shopping modules (`shopping-api.ts`, `shopping-backend-client.ts`, `shopping-mcp.ts`) and the npm packages they alone pull in, keeping `shopping-workflow.ts` and `shopping-provider-adapters.ts` since the page and Python backend contract still reference their types.
- Fix the remaining type errors in `shopping-workflow.ts` and `shopping-provider-adapters.ts` with proper undefined guards and bracketed env access — no casts.
- Add a `head()` block to `/shopping` with a unique title, description, and OG/Twitter tags matching the pattern used by the other routes.
- Re-run the typecheck and confirm zero errors, then load the affected pages in the preview to confirm nothing regressed.

The Python service under `backend/` is untouched — it stays as the reference implementation.

## Note

If instead you want more visual/design work (specific pages redesigned, new sections, different branding), say which pages and I'll plan that separately.
