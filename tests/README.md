# PCSE helper functionality tests

Run the focused local behavior tests with the lane-local PCSE/Gym environment:

```sh
/home/josh/scratch/code-asset-parallel-20261101/lane-06/venvs/spwk_agtech_task/bin/python -m unittest discover -s tests -p 'test_pcse_helpers_functionality.py' -v
```

The package's legacy `tests/test_pcse.py` calls the full upstream PCSE test suite;
that suite is not needed for these reward and action-dispatch checks.
