import os, json, re

base = os.path.dirname(os.path.abspath(__file__))
char_file = os.path.join(base, '..', 'history', 'characters', 'zz_eu5_characters.txt')
houses_file = os.path.join(base, '..', 'common', 'dynasty_houses', 'zz_eu5_merged_houses.txt')
dyn_file = os.path.join(base, '..', 'common', 'dynasties', 'zz_eu5_dynasties.txt')
merge_map_file = os.path.join(base, 'dynasty_merge_map.json')

# Load merge map
with open(merge_map_file, 'r', encoding='utf-8') as f:
    merge_data = json.load(f)
merge_map_raw = merge_data['merge_map']  # child_dyn -> {parent_dyn, root, desc_count}
child_dyns = set(merge_map_raw.keys())
parent_dyns = set(v['parent_dyn'] for v in merge_map_raw.values())

print("=" * 60)
print("VERIFICATION REPORT")
print("=" * 60)

# 1. Check house definitions
with open(houses_file, 'r', encoding='utf-8-sig') as f:
    house_content = f.read()
house_keys = re.findall(r'(house_\w+)\s*=\s*\{', house_content)
house_key_set = set(house_keys)
print(f"\n1. HOUSE DEFINITIONS ({len(house_keys)} found)")
# Check each child dyn has a house
missing_houses = []
for child_dyn in sorted(child_dyns):
    expected_house = 'house_' + child_dyn.replace('_dynasty', '')
    if expected_house not in house_key_set:
        missing_houses.append(expected_house)
if missing_houses:
    print(f"   MISSING houses: {missing_houses}")
else:
    print(f"   All {len(child_dyns)} child dynasties have house definitions")

# 2. Check dynasty definitions are commented out
with open(dyn_file, 'r', encoding='utf-8-sig') as f:
    dyn_content = f.read()
active_dyns = set(re.findall(r'^(\w+_dynasty)\s*=\s*\{', dyn_content, re.MULTILINE))
merged_but_active = child_dyns & active_dyns
print(f"\n2. DYNASTY DEFINITIONS ({len(active_dyns)} active)")
if merged_but_active:
    print(f"   ERROR: {len(merged_but_active)} merged dynasties still active:")
    for d in sorted(merged_but_active):
        print(f"     {d}")
else:
    print(f"   All {len(child_dyns)} merged dynasties properly commented out")

# 3. Check character file references
with open(char_file, 'r', encoding='utf-8-sig') as f:
    char_content = f.read()
char_dynasty_refs = re.findall(r'dynasty\s*=\s*(\S+)', char_content)
house_refs = [d for d in char_dynasty_refs if d.startswith('house_')]
dyn_refs = [d for d in char_dynasty_refs if d.endswith('_dynasty') and not d.startswith('house_')]
other_refs = [d for d in char_dynasty_refs if not d.startswith('house_') and not d.endswith('_dynasty')]

print(f"\n3. CHARACTER FILE DYNASTY REFERENCES ({len(char_dynasty_refs)} total)")
print(f"   house_xxx: {len(house_refs)}")
print(f"   xxx_dynasty (unmerged): {len(dyn_refs)}")
print(f"   other: {len(other_refs)}")

# 4. Check that house refs in character file all have definitions
house_ref_set = set(house_refs)
undefined_houses = house_ref_set - house_key_set
print(f"\n4. HOUSE REFERENCE VALIDATION")
if undefined_houses:
    print(f"   ERROR: {len(undefined_houses)} house references without definition:")
    for h in sorted(undefined_houses):
        print(f"     {h}")
else:
    print(f"   All {len(house_ref_set)} unique house references have definitions")

# 5. Check that no merged dynasty is still referenced in character file
still_referenced = set(dyn_refs) & child_dyns
print(f"\n5. MERGED DYNASTY STILL REFERENCED IN CHARACTERS")
if still_referenced:
    print(f"   ERROR: {len(still_referenced)} merged dynasties still referenced:")
    for d in sorted(still_referenced):
        count = dyn_refs.count(d)
        print(f"     {d} ({count} references)")
else:
    print(f"   None - all merged dynasty references replaced with house_xxx")

# 6. Summary of parent dynasties that should still be active
print(f"\n6. PARENT DYNASTY STATUS")
parent_active = parent_dyns & active_dyns
parent_inactive = parent_dyns - active_dyns
print(f"   Active parent dynasties: {len(parent_active)}/{len(parent_dyns)}")
if parent_inactive:
    print(f"   WARNING: {len(parent_inactive)} parent dynasties not found active:")
    for d in sorted(parent_inactive):
        print(f"     {d}")

# 7. Check house definitions point to correct parent
house_parents = re.findall(r'house_\w+\s*=\s*\{[^}]*?dynasty\s*=\s*(\w+)', house_content, re.DOTALL)
print(f"\n7. HOUSE -> PARENT DYNASTY MAPPING")
invalid_parents = [p for p in house_parents if p not in parent_dyns and p not in active_dyns]
if invalid_parents:
    print(f"   WARNING: {len(set(invalid_parents))} houses point to non-existent parent dynasties:")
    for p in sorted(set(invalid_parents)):
        print(f"     {p}")
else:
    print(f"   All house parent references valid")

print("\n" + "=" * 60)
errors = len(missing_houses) + len(merged_but_active) + len(undefined_houses) + len(still_referenced)
if errors == 0:
    print("RESULT: ALL CHECKS PASSED")
else:
    print(f"RESULT: {errors} ERRORS FOUND")
print("=" * 60)
