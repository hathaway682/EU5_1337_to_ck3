"""Center single EU5 family icons missed by the unscaled-bounds cutoff.

Only a single, unrotated, horizontally centered emblem on a solid field is
considered. Its visible alpha bounds are evaluated after instance scaling.
Bare solid rectangles are excluded. Backed-up inputs remain on F:.
"""
from pathlib import Path
from PIL import Image
import json
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
BACKUP = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261105_003333_coa_center_scaled')
REL = Path('common/coat_of_arms/coat_of_arms/zzzz_eu5_family_arms.txt')
SOURCE, TARGET = BACKUP / 'mod' / REL, ROOT / REL
if SOURCE.read_bytes() != TARGET.read_bytes(): raise RuntimeError('Current arms differ from backup')
text = SOURCE.read_text(encoding='utf-8-sig')
num = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)'
top_re = re.compile(r'^([\w.\-]+)\s*=\s*\{', re.M)
emblem_re = re.compile(r'\b(colored_emblem|textured_emblem)\s*=\s*\{')
instance_re = re.compile(r'\binstance\s*=\s*\{')
position_re = re.compile(r'\bposition\s*=\s*\{\s*(' + num + r')\s+(' + num + r')\s*\}')
scale_re = re.compile(r'\bscale\s*=\s*\{\s*(' + num + r')\s+(' + num + r')')
texture_re = re.compile(r'\btexture\s*=\s*"([^"]+\.dds)"')
pattern_re = re.compile(r'\bpattern\s*=\s*"([^"]+\.dds)"')

def end_brace(s, start):
    level = 1
    i = start
    while i < len(s) and level:
        if s[i] == '{': level += 1
        elif s[i] == '}': level -= 1
        i += 1
    if level: raise ValueError('Unbalanced block')
    return i - 1
def fmt(n): return ('%.6f' % n).rstrip('0').rstrip('.') or '0'
cache, changes, spans = {}, [], []
for top in top_re.finditer(text):
    body_end = end_brace(text, top.end())
    body = text[top.end():body_end]
    pattern = pattern_re.search(body)
    if not pattern or pattern.group(1) != 'eu5dyn_pattern_solid.dds': continue
    emblems = list(emblem_re.finditer(body))
    if len(emblems) != 1 or re.search(r'\bmask\s*=', body): continue
    e = emblems[0]
    e_body = body[e.end():end_brace(body, e.end())]
    tex = texture_re.search(e_body)
    instances = list(instance_re.finditer(e_body))
    if not tex or tex.group(1).endswith('ce_solid.dds') or len(instances) != 1: continue
    inst = instances[0]
    inner = e_body[inst.end():end_brace(e_body, inst.end())]
    pos, scale = position_re.search(inner), scale_re.search(inner)
    if not pos or not scale or re.search(r'\brotation\s*=', inner): continue
    x, y, sy = float(pos.group(1)), float(pos.group(2)), float(scale.group(2))
    if abs(x-.5) > .015 or y >= .48 or sy == 0: continue
    name = tex.group(1)
    if name not in cache:
        group = 'colored_emblems' if e.group(1) == 'colored_emblem' else 'textured_emblems'
        image = Image.open(BACKUP / 'mod/gfx/coat_of_arms' / group / name).convert('RGBA')
        bbox = image.getchannel('A').point(lambda a: 255 if a >= 10 else 0).getbbox()
        cache[name] = (image.size, bbox)
    (w, h), bbox = cache[name]
    if not bbox or (bbox[3]-bbox[1])/h * abs(sy) > .9: continue
    desired = .5 - ((bbox[1]+bbox[3])/(2*h)-.5) * sy
    if not (.02 <= desired-y <= .18): continue
    begin = top.end() + e.end() + inst.end() + pos.start(2)
    end = top.end() + e.end() + inst.end() + pos.end(2)
    spans.append((begin, end, fmt(desired)))
    changes.append({'family': top.group(1), 'texture': name, 'old_y': y,
                    'new_y': float(fmt(desired)), 'alpha_bounds': bbox,
                    'scaled_visible_height': round((bbox[3]-bbox[1])/h * abs(sy), 6)})
if not {'house_ashikaga', 'house_kou'} <= {c['family'] for c in changes}:
    raise ValueError('Both screenshot families must be selected')
out = text
for start, end, replacement in sorted(spans, reverse=True):
    out = out[:start] + replacement + out[end:]
print('Eligible central icons:', len(changes))
print('Screenshots:', [(c['family'], c['old_y'], c['new_y']) for c in changes
                       if c['family'] in ('house_ashikaga', 'house_kou')])
if '--apply' in sys.argv:
    TARGET.write_text(out, encoding='utf-8-sig', newline='\n')
    (ROOT / 'gen_debug/eu5_family_scaled_icons_20261105.json').write_text(
        json.dumps(changes, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
