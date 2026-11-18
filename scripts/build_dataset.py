"""Build the US Montessori School Density tables.

Inputs
  source/by_state_2023_24.csv   Montessori private schools by state (NCES PSS 2023-24, Montessori School Finder compilation)
  source/by_county_2023_24.csv  the same by county
  source/private_school_universe_totals.csv  all private schools in each PSS file (national only)
  raw/cc-est2023-agesex-all.csv U.S. Census Bureau, County Population Estimates by age and sex, Vintage 2023
Outputs
  data/by_state.csv, data/by_county.csv, data/national_summary.csv
Run  python scripts/build_dataset.py [--download]
"""
import os, sys, urllib.request
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, RAW, OUT = f'{ROOT}/source', f'{ROOT}/raw', f'{ROOT}/data'
CENSUS_URL = 'https://www2.census.gov/programs-surveys/popest/datasets/2020-2023/counties/asrh/cc-est2023-agesex-all.csv'
RAW_FILE = f'{RAW}/cc-est2023-agesex-all.csv'
MSF = 'https://www.montessorischoolfinder.com/locations/united-states'
MIN_POP = 5000          # a county rate is published only when children under 5 >= MIN_POP
VINTAGE = 'Vintage 2023, July 1, 2023'

if '--download' in sys.argv or not os.path.exists(RAW_FILE):
    os.makedirs(RAW, exist_ok=True)
    urllib.request.urlretrieve(CENSUS_URL, RAW_FILE)

# ---- population (resident population, ages 0 to 4) ----
pop = pd.read_csv(RAW_FILE, encoding='latin-1', dtype={'STATE': str, 'COUNTY': str})
pop = pop[pop.YEAR == 5].copy()                      # YEAR 5 = 7/1/2023 estimate (Census file layout)
pop['county_fips'] = pop.STATE.str.zfill(2) + pop.COUNTY.str.zfill(3)
assert len(pop) == 3144 and pop.county_fips.is_unique

# ---- Montessori counts ----
st = pd.read_csv(f'{SRC}/by_state_2023_24.csv')
co = pd.read_csv(f'{SRC}/by_county_2023_24.csv', dtype={'county_fips': str})

# ---- by state ----
sp = pop.groupby('STATE', as_index=False).agg(children_under_5=('UNDER5_TOT', 'sum'), total_population=('POPESTIMATE', 'sum'),
                                              state_name=('STNAME', 'first'))
sp['state_fips'] = sp.STATE.str.zfill(2)
s = st.rename(columns={'students_prek': 'prek_enrollment', 'state_name': 'state_name_pss'}).merge(
    sp[['state_fips', 'state_name', 'children_under_5', 'total_population']],
    left_on='state_name_pss', right_on='state_name', how='left', validate='1:1')
assert s.children_under_5.notna().all(), 'state name mismatch'
s['schools_per_10k_under5'] = (10000 * s.montessori_schools / s.children_under_5).round(2)
s['children_under_5_per_school'] = (s.children_under_5 / s.montessori_schools).round(0).astype(int)
s['rank'] = (s.montessori_schools / s.children_under_5).rank(ascending=False, method='min').astype(int)
s['rank_by_count'] = s.montessori_schools.rank(ascending=False, method='min').astype(int)
s['prek_enrollment'] = s.prek_enrollment.astype('Int64')
s['msf_url'] = MSF + '/' + s.state_name.str.lower().str.replace(' ', '-') + '/'
s['population_vintage'] = VINTAGE
s = s.sort_values('rank')[['rank', 'state', 'state_name', 'state_fips', 'montessori_schools', 'children_under_5',
                           'schools_per_10k_under5', 'children_under_5_per_school', 'rank_by_count', 'prek_enrollment',
                           'ams_member', 'ami_member', 'total_population', 'population_vintage', 'msf_url']]
s.to_csv(f'{OUT}/by_state.csv', index=False, lineterminator=chr(10))

# ---- by county ----
c = co.merge(pop[['county_fips', 'STNAME', 'CTYNAME', 'UNDER5_TOT', 'POPESTIMATE']], on='county_fips', how='left', validate='1:1')
assert c.UNDER5_TOT.notna().all(), 'county FIPS not in Census file'
c = c.rename(columns={'STNAME': 'state_name', 'CTYNAME': 'county_name', 'UNDER5_TOT': 'children_under_5',
                      'POPESTIMATE': 'total_population'})
c['rate_shown'] = c.children_under_5 >= MIN_POP
c['schools_per_10k_under5'] = (10000 * c.montessori_schools / c.children_under_5).where(c.rate_shown).round(2)
c['rank_among_rated'] = (c.montessori_schools / c.children_under_5).where(c.rate_shown).rank(ascending=False, method='min').astype('Int64')
c = c.sort_values(['rank_among_rated', 'montessori_schools'], ascending=[True, False], na_position='last')
c = c[['county_fips', 'county_name', 'state', 'state_name', 'montessori_schools', 'children_under_5', 'rate_shown',
       'schools_per_10k_under5', 'rank_among_rated', 'total_population']]
c.to_csv(f'{OUT}/by_county.csv', index=False, lineterminator=chr(10))

# ---- national summary ----
tot = pd.read_csv(f'{SRC}/private_school_universe_totals.csv').query("survey_year == '2023-24'").iloc[0]
n_sch, n_kid = int(s.montessori_schools.sum()), int(s.children_under_5.sum())
rated = c[c.rate_shown]
none = pop[~pop.county_fips.isin(c.county_fips)]
rows = [
    ('montessori_private_schools', n_sch, 'Montessori private schools, NCES PSS 2023-24, 50 states and DC'),
    ('children_under_5', n_kid, 'Resident children under 5, Census estimate of July 1, 2023, 50 states and DC'),
    ('schools_per_10k_under5', round(10000 * n_sch / n_kid, 2), 'National rate, schools per 10,000 children under 5'),
    ('children_under_5_per_school', round(n_kid / n_sch), 'Children under 5 for each Montessori private school'),
    ('state_median_schools_per_10k_under5', round(float(s.schools_per_10k_under5.median()), 2), 'Median of the 51 state rates (50 states and DC)'),
    ('states_with_a_school', int((s.montessori_schools > 0).sum()), 'States and DC with at least one school'),
    ('counties_with_a_school', len(c), 'Counties with at least one school'),
    ('counties_without_a_school', len(none), 'Counties with no Montessori private school in the PSS file (not listed in by_county.csv)'),
    ('counties_without_a_school_5k_children', int((none.UNDER5_TOT >= MIN_POP).sum()), f'Of those, counties with at least {MIN_POP:,} children under 5'),
    ('share_of_children_in_counties_without_a_school_pct', round(100 * none.UNDER5_TOT.sum() / n_kid, 1), 'Share of US children under 5 who live in a county with no Montessori private school in the file'),
    ('counties_with_rate', len(rated), f'Of those, counties with at least {MIN_POP:,} children under 5, where a rate is published'),
    ('schools_in_counties_with_rate', int(rated.montessori_schools.sum()), 'Schools located in counties where a rate is published'),
    ('private_schools_in_file', int(tot.private_schools_in_file), 'All private schools in the PSS 2023-24 file (national only, no state split)'),
    ('montessori_share_of_private_schools_pct', round(100 * n_sch / tot.private_schools_in_file, 2), 'National share only. A state share cannot be built from this source'),
    ('prek_enrollment_in_montessori_schools', int(s.prek_enrollment.sum()), 'Prekindergarten pupils enrolled in these schools (PSS)'),
    ('population_vintage', VINTAGE, 'U.S. Census Bureau Population Estimates, Vintage 2023 county file, YEAR code 5'),
    ('pss_wave', '2023-24', 'NCES Private School Universe Survey wave'),
]
pd.DataFrame(rows, columns=['metric', 'value', 'note']).to_csv(f'{OUT}/national_summary.csv', index=False, lineterminator=chr(10))

# ---- checks ----
assert s.montessori_schools.sum() == co.montessori_schools.sum() == c.montessori_schools.sum() == 2070
assert len(s) == 51 and s.msf_url.is_unique
print('schools', n_sch, 'children', n_kid, 'rate', round(10000 * n_sch / n_kid, 3))
print('states', len(s), 'counties', len(c), 'rated', len(rated))
