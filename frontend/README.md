# Burhan Frontend

Next.js (App Router, TypeScript, Tailwind CSS v4) interface for Burhan's Research Digital Twin.
It talks directly to the FastAPI backend; there is no mock data.

## Run

```bash
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL, defaults to http://localhost:8000
npm run dev                  # http://localhost:3000 (start the backend with `make dev` first)
```

## Scripts

| Script | Purpose |
|---|---|
| `npm run dev` | Development server |
| `npm run build` / `npm start` | Production build / serve |
| `npm run lint` | ESLint |
| `npm run typecheck` | TypeScript (`tsc --noEmit`) |
| `npm run gen:api` | Regenerate `src/lib/api/schema.d.ts` from the backend's OpenAPI schema |

## Structure

```
src/app/            routes: / (twin dashboard), /papers, /papers/[id], /graph, /evidence, /updates
src/lib/api/        client.ts (fetch + errors), endpoints.ts (typed API), hooks.ts (SWR), types.ts
src/lib/            entity styles, graph layout (d3-force), formatting, pipeline/update helpers
src/components/     layout, ui primitives, dashboard, papers, graph (React Flow), evidence, updates
public/burhan-logo.webp   official logo (unmodified)
```

API types are generated from the backend's Pydantic models, so a contract change shows up as a
TypeScript error after `npm run gen:api`.
