# spwk-agtech-task: local campaign contracts

The selected50 baseline and immutable ready quality additive packet now provide real first-party assertions and necessary support. Product source is unchanged; all 7 selected production SHA values were checked during integration. Historical deliveries remain immutable.

## Actual execution

```sh
"$PYTHON" scripts/quality/run_campaign.py --output-dir "$RESULTS_DIR" --extra-path "$PRIVATE_DEPS"
```

The interpreter and read-only explicit dependency paths reproduce the delivered runtime profile. Original own-repo paths were redirected to this independent clone, so source is not imported from an adjacent worker checkout. The runner installs no packages.

Publication result: **exit 1**, **{"total": 12, "passed": 11, "failed": 1, "errors": 0, "skipped": 0}**. Full per-case results, command, JUnit, coverage and raw group logs are preserved in the publication receipt. Failed/error cases stay ordinary failures, with original assertions and expectations. No skip, xfail, source fix or threshold weakening was used.

Selected natural contract files:
- `tests/test_pcse_helpers_functionality.py`
- `tests/functional_wave3/test_pcse_numerics.py`
- `tests/functional_wave3/test_weather_cache_names.py`
- `tests/functional_wave3/test_nasapower_records.py`

## Runner correction and negative controls

Previous evidence is now archived in unique `previous-*` folders. A real missing-coverage negative control returned nonzero before and after: the old runner included one seeded prior passing case, while the corrected runner reported zero current cases. An unknown `--select unknown_test.py` returned 2. Old runner bytes and both raw invocations are preserved. Where the old offline runner exists, its identical stale-evidence defect was corrected and independently reproduced. No `ROOT.parent` sibling-source fallback was introduced.

## Limits and publication boundary

These tests execute local original definitions and isolate SDK/database/configuration/network boundaries. Mock/static/AST partial execution does not prove full service startup or actual SQL/API/S3 integration. No production credentials, weights, GPU, training or backpropagation execute. The actual default workflow paths inspected were: none in the checked .github/workflows tree.

No production DB/API/S3/ECR/deployment path was found in the checked push/PR/tag workflow scope. Existing documentation/style workflows, where present, remain unchanged. Current-head review and completed non-failing CI are still required before merge.

Original criteria: publish the exact approved packets, first-party assertions and necessary fixtures/support, preserve source SHA and raw failures, and squash only after actual current-head Codex review SUCCESS with completed non-failing CI. Publication exclusions: none. Criteria loosened: no. Undo: revert the eventual test-only squash commit.
