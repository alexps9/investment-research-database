# memory/

Project knowledge base for **humans and code agents**. Read these first to get
up to speed quickly. Start with the root [`AGENTS.md`](../AGENTS.md) for the
agent-friendly summary + development conventions, then dive into the topic docs:

| Doc | Read it for |
|-----|-------------|
| [project_overview.md](project_overview.md) | What the product is, components, repo map |
| [architecture.md](architecture.md) | How the pieces fit; "backend is the only DB owner" |
| [data_model.md](data_model.md) | Every table, its columns and enum values |
| [api_reference.md](api_reference.md) | All `/api/*` endpoints |
| [deployment.md](deployment.md) | Remotes, HF Spaces, GitHub Pages, Supabase SQL |

These docs are maintained by hand — when you change the schema, an endpoint, or
the deployment topology, update the relevant file here in the same change.
