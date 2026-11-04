"""Adjust EU5 family emblem positions for CK3's square canvas."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
BACKUP = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261104_223630_coa_position')
SOURCE = BACKUP / 'mod/common/coat_of_arms/coat_of_arms/zzzz_eu5_family_arms.txt'
TARGET = ROOT / 'common/coat_of_arms/coat_of_arms/zzzz_eu5_family_arms.txt'
if TARGET.read_bytes() != SOURCE.read_bytes():
    raise RuntimeError('The current file differs from the backup')
text = SOURCE.read_text(encoding='utf-8-sig')
num = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)'
position = re.compile(r'(\bposition\s*=\s*\{\s*)(' + num + r')(\s+)(' + num + r')(\s*\})')
change = []
def fmt(x): return ('%.8f' % x).rstrip('0').rstrip('.') or '0'
def replace(m):
    before = float(m.group(2))
    after = 0.5 + (before - 0.5) * 1.5
    if abs(before-after) > 1e-9:
        change.append((before, after))
    return m.group(1) + fmt(after) + m.group(3) + m.group(4) + m.group(5)
out = position.sub(replace, text)
print('Positions changed:', len(change))
print('Positions beyond shield width:', sum(x < 0 or x > 1 for _, x in change))
if '--apply' in sys.argv:
    TARGET.write_text(out, encoding='utf-8-sig', newline='\n')
    (ROOT / 'gen_debug/eu5_family_coa_positions_20261104.json').write_text(
        json.dumps({'positions_changed': len(change), 'outside_canvas': sum(x < 0 or x > 1 for _, x in change)}, indent=2) + '\n', encoding='utf-8')
