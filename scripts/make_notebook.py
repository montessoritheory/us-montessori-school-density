"""Write and run notebooks/starter.ipynb. Needs nbformat, nbconvert and ipykernel."""
import os
import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
nb = nbf.v4.new_notebook()
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
nb.cells = [
    md("# US Montessori School Density, 2023-24\n\nA starter notebook for the dataset by [Montessori School Finder](https://www.montessorischoolfinder.com/). Montessori private schools per 10,000 children under 5, by state and county. License CC BY 4.0."),
    md("## Load The Tables"),
    code("import pandas as pd\nimport matplotlib.pyplot as plt\n\nINK, BLUE, GREEN, MUTED = '#0f172a', '#2563eb', '#059669', '#64748b'\nBASE = '../data'  # or the raw.githubusercontent.com address of the data folder\nstates = pd.read_csv(f'{BASE}/by_state.csv')\ncounties = pd.read_csv(f'{BASE}/by_county.csv', dtype={'county_fips': str})\nsummary = pd.read_csv(f'{BASE}/national_summary.csv').set_index('metric')\nsummary.loc[['montessori_private_schools', 'children_under_5', 'schools_per_10k_under5', 'children_under_5_per_school']]"),
    md("## The Densest States\n\nRank 1 has the most schools per child. Small states can move a lot on a single school, so read the count next to the rate."),
    code("states.sort_values('rank')[['rank', 'state_name', 'montessori_schools', 'children_under_5', 'schools_per_10k_under5']].head(10)"),
    md("## Many Schools Or Many Per Child?\n\nThe two rankings differ. California and Texas lead on count, New Hampshire and Montana lead on rate."),
    code("fig, ax = plt.subplots(figsize=(9, 6))\nax.scatter(states.montessori_schools, states.schools_per_10k_under5, s=60, color=GREEN, alpha=.85)\nfor _, r in states.iterrows():\n    if r['rank'] <= 5 or r.montessori_schools >= 100 or r['rank'] >= 49:\n        ax.annotate(r.state, (r.montessori_schools, r.schools_per_10k_under5), xytext=(5, 4), textcoords='offset points', fontsize=10, color=INK)\nax.axhline(float(summary.loc['schools_per_10k_under5', 'value']), color=BLUE, ls='--', lw=1)\nax.set_xscale('log'); ax.set_xlabel('Montessori private schools (log scale)'); ax.set_ylabel('Schools per 10,000 children under 5')\nax.spines[['top', 'right']].set_visible(False); plt.show()"),
    md("## The Densest Counties\n\nOnly counties with at least 5,000 children under 5 have a rate."),
    code("counties[counties.rate_shown].head(10)[['county_name', 'state', 'montessori_schools', 'children_under_5', 'schools_per_10k_under5']]"),
    md("## Counties By Rate"),
    code("r = counties[counties.rate_shown]\nfig, ax = plt.subplots(figsize=(9, 4.5))\nax.hist(r.schools_per_10k_under5, bins=30, color=BLUE)\nax.axvline(r.schools_per_10k_under5.median(), color=INK, ls='--', lw=1)\nax.set_xlabel('Schools per 10,000 children under 5'); ax.set_ylabel('Counties')\nax.spines[['top', 'right']].set_visible(False); plt.show()\nprint(f'{len(r)} counties with a rate, median {r.schools_per_10k_under5.median():.2f}')"),
    md("## Read With Care\n\nPrivate schools that offer kindergarten or above only. Public Montessori schools and programs for children under 5 only are not counted. See the README for the full list of limits."),
]
nb.metadata['kernelspec'] = {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}
ExecutePreprocessor(timeout=300, kernel_name='python3').preprocess(nb, {'metadata': {'path': f'{ROOT}/notebooks'}})
nbf.write(nb, f'{ROOT}/notebooks/starter.ipynb')
print('notebook written')
