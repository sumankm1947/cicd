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
- [ ] Create a branch, intentionally break an assertion (e.g. `test_add` → `== 6`)
- [ ] Open a PR and watch CI go RED (the merge gate in action)
- [ ] Download the `test-reports` artifact and inspect `report.xml`
- [ ] (Optional) Add branch protection: Settings → Branches → Require status checks
- [ ] Revert the broken test / close the PR; confirm CI goes GREEN again

## Lab 2 — Matrix builds
- [ ] Run the suite across Python 3.9–3.12 in parallel via `strategy.matrix`
- [ ] Observe one job definition fan out into multiple parallel runs

## Lab 3 — Multiple jobs + `needs`
- [ ] Split `lint` and `test` into separate jobs
- [ ] Chain with `needs:`; understand the job graph and parallelism

## Lab 4 — Secrets
- [ ] Add a repo secret, read via `${{ secrets.NAME }}`, confirm masking

## Lab 5 — Caching (deeper)
- [ ] Replace `cache: pip` with explicit `actions/cache` keyed on `requirements.txt` hash
- [ ] Observe cache hits vs misses and speed difference

## Lab 6 — Scheduled & path-filtered runs
- [ ] Add a nightly `schedule: cron`
- [ ] Add a workflow that only runs when `app/**` changes (`on: push: paths:`)

## Lab 7 — Services / Docker
- [ ] Add a `services:` container (e.g. postgres) for integration tests
- [ ] Write a `Dockerfile` and build the app image in CI

## Lab 8 — Environments & deploy gates
- [ ] Define a `production` environment with a required reviewer
- [ ] Add a `deploy` job that `needs: test` and runs only on `main`

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
