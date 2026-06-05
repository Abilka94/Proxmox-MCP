# Tests

Phase 1A starts with a skeleton smoke test. Unit, contract, and integration
coverage are added as the corresponding T-100...T-117 tasks land.

```powershell
python -m pytest
```

When pytest is not available in the local bootstrap environment, the current
stdlib-only subset can be run with:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```
