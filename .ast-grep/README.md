# ast-grep rules

Static-analysis rules for `ast-grep` (https://ast-grep.github.io/), config'd via
`sgconfig.yml` at the repo root (`ruleDirs: [.ast-grep/rules]`).

Run manually:

```bash
pnpm exec ast-grep scan          # scan the whole repo
pnpm exec ast-grep scan <path>   # scan a subset
```

(Also wired into CI — see `.github/workflows/ci.yml`.)

## Rules

- **`no-sync-http-in-async.yml`** — flags blocking `httpx.get/post/...` or
  `requests.get/post/...` calls (the synchronous APIs) inside an `async def`
  function body. This is exactly the bug that used to exist in
  `apps/backend/app/core/auth.py` (a blocking `httpx.get` in the async JWT
  verification path, later fixed to use `httpx.AsyncClient`).
- **`no-bare-except.yml`** — flags bare `except:` clauses, which swallow
  `SystemExit`/`KeyboardInterrupt` and hide bugs. Use `except Exception:` (or
  a narrower type) instead.

Requires the `ast-grep`/`sg` CLI (installed as the `@ast-grep/cli` root
devDependency; run via `pnpm exec ast-grep` or `pnpm exec sg`).
