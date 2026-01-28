Exemple (local)
---------------
python scripts/run_ddr.py --test-matrix examples/TEST_MATRIX.example.md --out outputs --with-e

Résultat attendu (structure)
----------------------------
- outputs/extraction_report.json : compte A=4, B=3
- outputs/ddr_report.json : DDR=PARTIAL avec ok=[MAD], ko=[mean,median,p90,p99]
- outputs/e_report.json : E=INCOMPATIBLE (car au moins un invariant KO)
