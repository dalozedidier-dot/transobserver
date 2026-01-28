# SystemD Multisector Tests v0.1

## What this is
A minimal multisector test pack based on **profiles-as-contract**:
- Same kernel everywhere (STRUCT_N: proxies 1..n)
- Different ingestion/adapters (docs/tickets/generic)
- Golden snapshots + SHA256 hashes for non-regression

## Run
From this folder:

### Update expected (golden)
python3 harness.py --repo-root . --profiles tests/profiles --update-expected

### Check expected (PASS/FAIL via hash)
python3 harness.py --repo-root . --profiles tests/profiles

Outputs:
- tests/results.json (aggregated reports + hashes)

## Profiles
- tests/profiles/docs_struct_n_demo.yaml
- tests/profiles/tickets_struct_n_demo.yaml
- tests/profiles/generic_struct_n_51_50.yaml

## Fixtures
- tests/fixtures/md/docs_demo.md
- tests/fixtures/csv/tickets_demo.csv
- tests/fixtures/json/groups_51_50.json

## Output schema (short)
report.json contains:
- meta (profile contract)
- extraction (counts + pre/post)
- ddr: {ok,ko,nc,ddr,e,div_rel}
- hash_sha256 (canonical JSON)


## v0.2 additions
- Boundary fixtures/profiles for n=0/1/2/4/5 on each adapter:
  - docs_struct_n_{n}_{n}
  - tickets_struct_n_{n}_{n}
  - generic_struct_n_{n}_{n}
- Ambiguous heading case (docs): docs_ambiguous_heading_demo
