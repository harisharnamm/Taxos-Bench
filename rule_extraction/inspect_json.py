import json

file_path = '/Users/mypro16/Desktop/Tax Benchmarking/Data Corpus/irc_data/Subtitle_A__INCOME_TAXES_Sections_1_to_1564/Chapter_1__Normal_taxes_and_surtaxes_Sections_1_to/section_1.json'

with open(file_path, 'r') as f:
    data = json.load(f)

print(f"Keys: {list(data.keys())}")
if 'subsections' in data:
    print(f"Number of subsections: {len(data['subsections'])}")
    # Check keys of the first subsection
    if len(data['subsections']) > 0:
        print(f"Subsection keys: {list(data['subsections'][0].keys())}")
