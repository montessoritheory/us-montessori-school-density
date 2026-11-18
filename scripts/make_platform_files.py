"""Write ../huggingface/README.md and ../kaggle/dataset-metadata.json from README.md and data_dictionary.csv."""
import csv, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.dirname(ROOT)
readme = open(f'{ROOT}/README.md', encoding='utf8').read()
GH = 'https://raw.githubusercontent.com/montessoritheory/us-montessori-school-density/main'
HF = 'https://huggingface.co/datasets/montessoritheory/us-montessori-school-density/resolve/main'
TITLE = 'US Montessori School Density by State and County, 2023-24'

# ---------- Hugging Face ----------
head = """---
license: cc-by-4.0
pretty_name: US Montessori School Density by State and County, 2023-24
language:
- en
tags:
- montessori
- education
- private-schools
- early-childhood
- school-density
- nces
- census
- united-states
- tabular
size_categories:
- n<1K
source_datasets:
- original
configs:
- config_name: by_state
  data_files: data/by_state.csv
  default: true
- config_name: by_county
  data_files: data/by_county.csv
- config_name: national_summary
  data_files: data/national_summary.csv
---

"""
body = readme.split('\n', 1)[1]                                   # drop the H1 line, repeated below
body = re.sub(r'\[!\[License.*\n', '', body, count=1)              # badge line
body = body.replace('(images/', f'({HF}/images/')
open(f'{PKG}/huggingface/README.md', 'w', encoding='utf8').write(head + f'# {TITLE}\n' + body)

# ---------- Kaggle ----------
dd = list(csv.DictReader(open(f'{ROOT}/data_dictionary.csv', encoding='utf8')))
files = {
    'by_state.csv': '51 rows, 50 states and DC. Montessori private schools, children under 5, schools per 10,000 children under 5, ranks, prekindergarten enrollment and the Montessori School Finder state page.',
    'by_county.csv': '570 counties with at least one Montessori private school. Rate published for the 434 counties with at least 5,000 children under 5.',
    'national_summary.csv': 'National totals and checks behind the headline numbers, one metric per row.',
}
TYPES = {'str': 'string', 'integer': 'integer', 'float': 'number', 'bool': 'boolean'}
resources = []
for fn, desc in files.items():
    resources.append({'path': f'data/{fn}', 'description': desc, 'schema': {'fields': [
        {'name': r['column'], 'description': r['description'], 'type': TYPES[r['type']]} for r in dd if r['file'] == fn]}})
short = open(f'{ROOT}/README.md', encoding='utf8').read()
desc = re.sub(r'\[!\[License.*\n', '', short.split('\n', 1)[1], count=1).replace('(images/', f'({GH}/images/')
meta = {
    'title': TITLE,
    'subtitle': 'Montessori private schools per 10,000 children under 5, by state and county',
    'id': 'mariamontessori/us-montessori-school-density',
    'licenses': [{'name': 'CC-BY-4.0'}],
    'keywords': ['education', 'primary and secondary schools', 'united states', 'children', 'tabular'],
    'description': f'# {TITLE}\n' + desc,
    'resources': resources,
}
json.dump(meta, open(f'{PKG}/kaggle/dataset-metadata.json', 'w', encoding='utf8'), indent=1, ensure_ascii=False)
print('platform files written')
