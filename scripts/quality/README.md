# Portable campaign test command

From the repository root with a private interpreter providing the project test dependencies:

```sh
"$PYTHON" scripts/quality/run_campaign.py --output-dir "$RESULTS_DIR" --extra-path "$DE_DS_COMMON_CHECKOUT" --extra-path "$PRIVATE_DEPENDENCY_DIR"
```

The optional dependency paths may also be supplied using FILE50_TEST_DEP_PATHS.
No installation or fixed scratch location is embedded in the runner or tests.
Only campaign-selection.json files are collected. Preserved pre-campaign tests are not altered or implicitly collected.
Unknown --group values and an empty selection are errors. The interpreter and installed dependency versions remain the caller's explicit profile.
SDK calls/configuration and network I/O are isolated; transforms and original ETL algorithms execute unchanged.
Logs/JUnit/coverage/case IDs distinguish failures from collection errors; a failing suite returns nonzero.
