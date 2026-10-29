import csv
import os

manifest_path = "outputs/am_thanh/manifest_500_am_thanh.csv"
cases_path = "outputs/fresh500_optimized_20261014/fresh_500_test_cases.csv"

with open(manifest_path, "r", encoding="utf-8-sig") as f:
    manifest_rows = list(csv.DictReader(f))

with open(cases_path, "r", encoding="utf-8-sig") as f:
    case_rows = {r["case_id"]: r for r in csv.DictReader(f)}

print(f"Manifest rows: {len(manifest_rows)}")
print(f"Case rows: {len(case_rows)}")

missing_files = 0
for r in manifest_rows:
    wav_path = os.path.join("outputs/am_thanh", r["wav_file"])
    if not os.path.exists(wav_path):
        missing_files += 1

print(f"Missing audio files: {missing_files}")

sample_vi = manifest_rows[0]
case_vi = case_rows.get(sample_vi["case_id"], {})
print("\nSample 1 (VI -> EN):")
print("  WAV:", sample_vi["wav_file"])
print("  Source:", sample_vi["source_text"])
print("  Reference:", case_vi.get("reference"))
print("  Lang:", sample_vi["source_lang"], "->", case_vi.get("target_lang"))

sample_en = manifest_rows[250]
case_en = case_rows.get(sample_en["case_id"], {})
print("\nSample 251 (EN -> VI):")
print("  WAV:", sample_en["wav_file"])
print("  Source:", sample_en["source_text"])
print("  Reference:", case_en.get("reference"))
print("  Lang:", sample_en["source_lang"], "->", case_en.get("target_lang"))
