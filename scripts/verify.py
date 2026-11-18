"""Checks for the US Montessori School Density tables. Run after build_dataset.py. Exit code 1 on any failure."""
import os, sys
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = pd.read_csv(f'{ROOT}/data/by_state.csv')
c = pd.read_csv(f'{ROOT}/data/by_county.csv', dtype={'county_fips': str})
src_state = pd.read_csv(f'{ROOT}/source/by_state_2023_24.csv')
src_school_total = 2070
ok = True


def check(label, cond, detail=''):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + label, detail)


check('state schools sum to national total of the source', s.montessori_schools.sum() == src_state.montessori_schools.sum() == src_school_total, s.montessori_schools.sum())
check('county schools sum to national total', c.montessori_schools.sum() == src_school_total, c.montessori_schools.sum())
check('51 rows in by_state (50 states and DC)', len(s) == 51)
check('FIPS are 5 characters', c.county_fips.str.len().eq(5).all())
check('rates only where children_under_5 >= 5000', (c.rate_shown == (c.children_under_5 >= 5000)).all() and c.schools_per_10k_under5.notna().eq(c.rate_shown).all())
check('state rate matches schools / children * 10000',
      ((10000 * s.montessori_schools / s.children_under_5).round(2) - s.schools_per_10k_under5).abs().max() < 1e-9)

# Cross-check against the Census state file, a separate release (civilian population, age 0 to 4, 2023).
cv = pd.read_csv(f'{ROOT}/raw/sc-est2023-agesex-civ.csv')
cv = cv[(cv.SUMLEV == 40) & (cv.SEX == 0) & (cv.AGE <= 4)].groupby('NAME').POPEST2023_CIV.sum()
m = s.set_index('state_name').children_under_5
diff = ((m - cv.reindex(m.index)) / cv.reindex(m.index) * 100)
check('county-built state populations within 1 percent of the Census state file (civilian)', diff.abs().max() < 1, f'max gap {diff.abs().max():.2f} pct')
for name in ['California', 'Texas', 'New Hampshire', 'Virginia', 'Mississippi']:
    print(f'  spot check {name}: this dataset {m[name]:,}  Census state file {cv[name]:,}  gap {diff[name]:+.2f} pct')
sys.exit(0 if ok else 1)
