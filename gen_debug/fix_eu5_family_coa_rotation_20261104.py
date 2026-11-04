"""Fix the earlier 90-degree axis error in existing EU5 family arms."""
from pathlib import Path
import re

root = Path(__file__).resolve().parent.parent
backup = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261104_223418_coa_rotation')
source = backup / 'mod/common/coat_of_arms/coat_of_arms/zzzz_eu5_family_arms.txt'
target = root / 'common/coat_of_arms/coat_of_arms/zzzz_eu5_family_arms.txt'
if target.read_bytes() != source.read_bytes():
    raise RuntimeError('Current file differs from the backed-up input')
text = source.read_text(encoding='utf-8-sig')
num = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)'
pattern = re.compile(r'(\binstance\s*=\s*\{\s*position\s*=\s*\{[^{}]*\}\s*rotation\s*=\s*-?90(?:\.0+)?\s*scale\s*=\s*\{\s*)(' + num + r')(\s+)(' + num + r')(\s*\})')
def fmt(v):
    return ('%.8f' % v).rstrip('0').rstrip('.') or '0'
def repl(m):
    return m.group(1) + fmt(float(m.group(2)) * 1.5) + m.group(3) + fmt(float(m.group(4)) / 1.5) + m.group(5)
out, count = pattern.subn(repl, text)
if count != 10:
    raise RuntimeError('Expected 10 previously adjusted quarter-turn instances, found ' + str(count))
target.write_text(out, encoding='utf-8-sig', newline='\n')
print('Fixed quarter-turn instances:', count)
