# TODO — CI/CD Learning Lab

Progress tracker for learning CI/CD with GitHub Actions (SDET practice).
Full lesson details live in `CLAUDE.md`; the curriculum lives in `README.md`.

Legend: `[x]` done · `[ ]` not started · `[~]` in progress

---

## Lab 1 — Baseline pipeline
- [x] Scaffold app under test (`app/calculator.py`, `app/api.py`)
- [x] Write unit tests (`tests/test_calculator.py`) and API tests (`tests/test_api.py`)
- [x] Add `requirements.txt`, `pytest.ini`, `.gitignore`
- [x] Create local venv, install deps, run tests locally (9 passed, ~91% coverage)
- [x] Fix `ModuleNotFoundError: app` → add `pythonpath = .` to `pytest.ini`
- [x] Write the commented pipeline `.github/workflows/ci.yml`
- [x] `git init`, commit, push to GitHub remote (`github`)
- [x] Confirm pipeline runs GREEN in the Actions tab
- [x] Create a branch, intentionally break an assertion (practice branch `break-a-case`, `test_add` → `== 6`)
- [~] Open a PR and watch CI go RED — done as throwaway practice; branch intentionally NOT merged
- [ ] Download the `test-reports` artifact and inspect `report.xml`
- [ ] (Optional) Add branch protection: Settings → Branches → Require status checks
- [~] Revert the broken test / close the PR — left `break-a-case` unmerged instead of reverting

## Lab 2 — Matrix builds
- [x] Run the suite across Python 3.9–3.12 in parallel via `strategy.matrix`
- [x] Set `fail-fast: false` so every failing version is reported, not just the first
- [x] Make artifact names unique per version (`upload-artifact@v4` 409-collision fix)
- [x] Push branch `lab-2-matrix` and open PR
- [ ] Observe one job definition fan out into 4 parallel checks in the Actions tab
- [ ] Confirm 4 artifact bundles (`test-reports-3.9` … `-3.12`); note any 3.9 cross-version failures

## Lab 3 — Multiple jobs + `needs`
- [x] Split `lint` (single, 3.10) and `test` (matrix 3.9–3.12) into separate jobs
- [x] Chain with `needs: lint` so `test` waits for lint to pass
- [x] Give each job its own checkout + setup-python + install (fresh-VM isolation)
- [ ] Observe the job graph (`lint → test (3.9…3.12)`) in the Actions tab
- [ ] (Optional) Add a lint error on purpose; confirm the 4 `test` jobs show SKIPPED

## Lab 4 — Secrets
- [x] Add a step reading `MY_TOKEN` via `env:` and echo it to watch GitHub mask it to `***`
- [ ] Create the `MY_TOKEN` repo secret (Settings → Secrets → Actions) so the value isn't empty
- [ ] Confirm the value shows as `***` in the run log (masking)

## Lab 5 — Caching (deeper)
- [x] Replace `cache: pip` with explicit `actions/cache@v4` keyed on `requirements.txt` hash
- [x] Add `restore-keys` prefix fallback; put `matrix.python-version` in the test job's key
- [ ] Observe cache hits vs misses and the speed difference (miss → no-op push → hit)

## Lab 6 — Scheduled & path-filtered runs
- [x] Add a nightly `schedule: cron "0 3 * * *"` (03:00 UTC) to `ci.yml`
- [x] Add isolated workflow `app-only.yml` that runs only when `app/**` changes (`on: push: paths:`)
- [ ] Confirm the cron run appears in the Actions tab (next morning; UTC, best-effort timing)
- [ ] Edit only `README.md` → `app-only.yml` stays idle; edit `app/` → it fires

## Lab 7 — Services / Docker
- [x] Write a `Dockerfile` (python:3.10-slim, deps-before-code layer caching) and a `.dockerignore`
- [x] Build + run the image locally; smoke-test `/health` → `{"status":"ok"}`
- [x] Add a `docker-build` CI job (`needs: test`) that builds the image and curls `/health`
- [x] Add an `integration-db` CI job with a `services: postgres` container + `pg_isready` health check
- [x] Connect with `psql` and run `SELECT version();` to prove connectivity
- [x] Push branch `lab-7-services-docker`, open PR #3, CI green, merged to main
- [ ] (Note) the postgres part is a mechanism demo only — the calculator has no DB

## Lab 8 — Environments & deploy gates
- [x] Add a `deploy` job (`needs: test`, `if: github.ref == 'refs/heads/main'`, `environment: production`)
- [x] Push branch `lab-8-environments`, open PR
- [ ] Define the `production` environment + required reviewer (Settings → Environments) — UI step
- [ ] Merge to `main`, watch the run PAUSE at `deploy`, click Approve, confirm it proceeds

## Lab 9 — Reusable & composite workflows
- [ ] Extract shared setup into a reusable workflow (`workflow_call`)

## Lab 10 — Reporting & badges
- [ ] Publish JUnit results as a PR check
- [ ] Publish HTML coverage as an artifact
- [ ] Add a build-status badge to `README.md`

---

## Stretch goal — Azure DevOps
- [ ] Port Labs 1–3 to `azure-pipelines.yml` (same concepts, different YAML)
- [ ] Compare GitHub Actions vs Azure DevOps Pipelines free tiers and syntax
