with open('scripts/section_3_4_database.py', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'render_data_dictionary_table(' in l and i > 20:
        table_name = lines[i+2].strip().strip('",\'')
        print(f"Table: {table_name}")
