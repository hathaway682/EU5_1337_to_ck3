"""Center visibly high, single-image family arms; use 源 for four Genji dynasties.

Reads the complete pre-change inputs in the F-drive backup. Only single-emblem,
single-instance, horizontally centered, unrotated designs with non-full-height
alpha artwork are eligible. Alpha bounding boxes determine their visual center.
Run without --apply to inspect counts; --apply writes the two backed-up files.
After this step, run center_eu5_family_layers_20261104.py to center eligible
composite designs whose layers share a common anchor.
"""
from pathlib import Path
from PIL import Image
import json
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
BACKUP = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261104_224146_coa_center_genji')
ARMS_REL = Path('common/coat_of_arms/coat_of_arms/zzzz_eu5_family_arms.txt')
LOC_REL = Path('localization/simp_chinese/zzzz_eu5_family_l_simp_chinese.yml')
arms_file, loc_file = ROOT / ARMS_REL, ROOT / LOC_REL
arms_src, loc_src = BACKUP / 'mod' / ARMS_REL, BACKUP / 'mod' / LOC_REL
for live, source in ((arms_file, arms_src), (loc_file, loc_src)):
    if live.read_bytes() != source.read_bytes():
        raise RuntimeError('Current input differs from backup: ' + str(live))
text = arms_src.read_text(encoding='utf-8-sig')
loc = loc_src.read_text(encoding='utf-8-sig')
num = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)'
top_re = re.compile(r'^([\w.\-]+)\s*=\s*\{', re.M)
emblem_re = re.compile(r'\b(colored_emblem|textured_emblem)\s*=\s*\{')
instance_re = re.compile(r'\binstance\s*=\s*\{')
position_re = re.compile(r'(\bposition\s*=\s*\{\s*)(' + num + r')(\s+)(' + num + r')(\s*\})')
scale_re = re.compile(r'\bscale\s*=\s*\{\s*(' + num + r')\s+(' + num + r')')
texture_re = re.compile(r'\btexture\s*=\s*"([^"]+\.dds)"')

def end_brace(data, start):
    depth = 1
    i = start
    while i < len(data) and depth:
        if data[i] == '{': depth += 1
        elif data[i] == '}': depth -= 1
        i += 1
    if depth: raise ValueError('Unbalanced block')
    return i - 1

def fmt(n): return ('%.6f' % n).rstrip('0').rstrip('.') or '0'
cache = {}
changes = []
spans = []
for top in top_re.finditer(text):
    stop = end_brace(text, top.end())
    body = text[top.end():stop]
    emblems = list(emblem_re.finditer(body))
    if len(emblems) != 1: continue
    emblem = emblems[0]
    e_end = end_brace(body, emblem.end())
    e_body = body[emblem.end():e_end]
    tex = texture_re.search(e_body)
    instances = list(instance_re.finditer(e_body))
    if not tex or len(instances) != 1: continue
    inst = instances[0]
    i_end = end_brace(e_body, inst.end())
    i_body = e_body[inst.end():i_end]
    pos, scale = position_re.search(i_body), scale_re.search(i_body)
    if not pos or not scale or re.search(r'\brotation\s*=', i_body): continue
    x, y, sy = float(pos.group(2)), float(pos.group(4)), float(scale.group(2))
    if abs(x - .5) > .015 or y >= .48 or sy <= 0: continue
    texture = tex.group(1)
    if texture not in cache:
        group = 'colored_emblems' if emblem.group(1) == 'colored_emblem' else 'textured_emblems'
        path = BACKUP / 'mod/gfx/coat_of_arms' / group / texture
        image = Image.open(path).convert('RGBA')
        bounds = image.getchannel('A').point(lambda a: 255 if a >= 10 else 0).getbbox()
        cache[texture] = (image.size, bounds)
    (w, h), bounds = cache[texture]
    if not bounds or (bounds[3] - bounds[1]) / h > .9: continue
    corrected = .5 - ((bounds[1] + bounds[3]) / (2 * h) - .5) * sy
    delta = corrected - y
    if delta < .02 or delta > .18: continue
    start = top.end() + emblem.end() + inst.end() + pos.start(4)
    end = top.end() + emblem.end() + inst.end() + pos.end(4)
    spans.append((start, end, fmt(corrected)))
    changes.append({'family': top.group(1), 'texture': texture,
                    'old_y': y, 'new_y': float(fmt(corrected)), 'alpha_bounds': bounds})
if not any(c['family'] == 'house_kyougoku' for c in changes):
    raise RuntimeError('Expected Kyogoku example was not selected')
out = text
for start, end, replacement in reversed(spans):
    out = out[:start] + replacement + out[end:]

names = ['seiwa_genji_dynasty', 'uda_genji_dynasty', 'saga_genji_dynasty', 'murakami_genji_dynasty']
for name in names:
    loc, count = re.subn(r'(?m)^(\s*eu5_family_' + name + r':\d*\s*)"[^"]*"', r'\1"源"', loc)
    if count != 1: raise RuntimeError('Expected one localization for ' + name)
print('Centered single emblems:', len(changes), '| Genji names:', len(names))
print('Kyogoku:', next(c for c in changes if c['family'] == 'house_kyougoku'))
if '--apply' in sys.argv:
    arms_file.write_text(out, encoding='utf-8-sig', newline='\n')
    loc_file.write_text(loc, encoding='utf-8-sig', newline='\n')
    (ROOT / 'gen_debug/eu5_family_centered_icons_20261104.json').write_text(
        json.dumps(changes, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
