import os, json, re

base = os.path.dirname(os.path.abspath(__file__))
char_file = os.path.join(base, '..', 'history', 'characters', 'zz_eu5_characters.txt')
backup_file = os.path.join(base, '_backup_dynasty_merge_20261018_141112', 'zz_eu5_characters.txt')
merge_map_file = os.path.join(base, 'dynasty_merge_map.json')

# Load merge map
with open(merge_map_file, 'r', encoding='utf-8') as f:
    merge_data = json.load(f)
merge_map = merge_data['merge_map']  # child_dyn -> parent_dyn
print(f"Merge map entries: {len(merge_map)}")

# Check current file: read raw bytes
with open(char_file, 'rb') as f:
    raw = f.read()
print(f"Current file size: {len(raw)}")
print(f"CR bytes: {raw.count(0x0D)}")
print(f"LF bytes: {raw.count(0x0A)}")

# Find first dynasty field in raw bytes
idx = raw.find(b'dynasty')
if idx >= 0:
    snippet = raw[idx-10:idx+40]
    print(f"First dynasty at byte {idx}")
    print(f"Context bytes: {snippet!r}")

# Read as text (utf-8-sig strips BOM)
with open(char_file, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Check line ending style
has_crlf = '\r\n' in content
has_lf_only = '\n' in content.replace('\r\n', '')
print(f"Has CRLF: {has_crlf}")
print(f"Has LF-only: {has_lf_only}")

# Now do the replacement properly
# Strategy: simple string replacement per dynasty key
# Each line like "	dynasty = ashikaga_dynasty" -> "	dynasty = house_ashikaga"
# But only for the 168 child dynasties in merge_map

replace_count = 0
for child_dyn, parent_dyn in merge_map.items():
    # The house key is house_<child_dyn without _dynasty suffix>
    house_key = 'house_' + child_dyn.replace('_dynasty', '')
    
    # Replace "dynasty = child_dyn" with "dynasty = house_key"
    # Be careful: only match exact dynasty key, not substring
    # Pattern: dynasty = <whitespace> child_dyn  (at word boundary)
    old_pattern = f'dynasty = {child_dyn}'
    new_pattern = f'dynasty = {house_key}'
    
    count = content.count(old_pattern)
    if count > 0:
        content = content.replace(old_pattern, new_pattern)
        replace_count += count
        
print(f"Total replacements made: {replace_count}")

# Verify
dynasty_fields = re.findall(r'dynasty\s*=\s*(\S+)', content)
house_count = sum(1 for d in dynasty_fields if d.startswith('house_'))
dyn_count = sum(1 for d in dynasty_fields if d.endswith('_dynasty'))
print(f"After replacement:")
print(f"  Total dynasty fields: {len(dynasty_fields)}")
print(f"  house_xxx: {house_count}")
print(f"  xxx_dynasty: {dyn_count}")

# Write back (preserve BOM, use LF since file was LF)
with open(char_file, 'w', encoding='utf-8-sig', newline='\n') as f:
    f.write(content)
print(f"File written. New size: {os.path.getsize(char_file)}")
