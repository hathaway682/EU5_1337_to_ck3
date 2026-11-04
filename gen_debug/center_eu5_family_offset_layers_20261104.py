"""Center layered single-anchor EU5 family emblems without separating layers.

Read the pre-change snapshot from F:. Unrotated layers must share a vertical anchor and remain near the
center; separate fixed border/divider emblems are allowed. The union of
the visible alpha bounds is centered while each layer receives the same shift.
Afterwards, run center_eu5_family_offset_layers_20261104.py to handle central
compositions whose layers share a vertical anchor but have small horizontal offsets.
Follow with center_eu5_family_vertical_layers_20261104.py for slightly offset
vertical layers and fixed, full-surface solid backgrounds.
"""
from pathlib import Path
from PIL import Image
import json
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
BACKUP = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261104_224953_coa_offset_layers')
REL = Path('common/coat_of_arms/coat_of_arms/zzzz_eu5_family_arms.txt')
SOURCE, TARGET = BACKUP / 'mod' / REL, ROOT / REL
if SOURCE.read_bytes() != TARGET.read_bytes():
    raise RuntimeError('Current input differs from the backup')
text = SOURCE.read_text(encoding='utf-8-sig')
num = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)'
top_re = re.compile(r'^([\w.\-]+)\s*=\s*\{', re.M)
emblem_re = re.compile(r'\b(colored_emblem|textured_emblem)\s*=\s*\{')
instance_re = re.compile(r'\binstance\s*=\s*\{')
position_re = re.compile(r'\bposition\s*=\s*\{\s*(' + num + r')\s+(' + num + r')\s*\}')
scale_re = re.compile(r'\bscale\s*=\s*\{\s*(' + num + r')\s+(' + num + r')')
texture_re = re.compile(r'\btexture\s*=\s*"([^"]+\.dds)"')

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
cache = {}
changes, spans = [], []
for top in top_re.finditer(text):
    body_end = end_brace(text, top.end())
    body = text[top.end():body_end]
    emblems = list(emblem_re.finditer(body))
    if not emblems: continue
    layers, rejected = [], False
    for e in emblems:
        e_end = end_brace(body, e.end())
        e_body = body[e.end():e_end]
        tex = texture_re.search(e_body)
        if not tex:
            rejected = True
            break
        instances = list(instance_re.finditer(e_body))
        is_border = bool(re.search(r'(?:ce|te)_(?:border|divider)', tex.group(1)))
        if not instances:
            if is_border: continue
            rejected = True
            break
        for inst in instances:
            i_end = end_brace(e_body, inst.end())
            inner = e_body[inst.end():i_end]
            pos, scale = position_re.search(inner), scale_re.search(inner)
            if not pos or not scale or re.search(r'\brotation\s*=', inner):
                rejected = True
                break
            x, y, sy = float(pos.group(1)), float(pos.group(2)), float(scale.group(2))
            if is_border and abs(x-.5) < .001 and abs(y-.5) < .001:
                continue
            if sy <= 0:
                rejected = True
                break
            begin = top.end() + e.end() + inst.end() + pos.start(2)
            end = top.end() + e.end() + inst.end() + pos.end(2)
            layers.append({'name': tex.group(1), 'type': e.group(1), 'x': x, 'y': y,
                           'sy': sy, 'start': begin, 'end': end})
        if rejected: break
    if rejected or len(layers) < 2: continue
    anchor_x, anchor_y = layers[0]['x'], layers[0]['y']
    if abs(anchor_x-.5) > .08 or anchor_y >= .48: continue
    if any(abs(layer['x']-.5) > .08 or abs(layer['y']-anchor_y) > .005 for layer in layers): continue
    bottom, upper = 10.0, -10.0
    for layer in layers:
        name = layer['name']
        if name not in cache:
            group = 'colored_emblems' if layer['type'] == 'colored_emblem' else 'textured_emblems'
            image = Image.open(BACKUP / 'mod/gfx/coat_of_arms' / group / name).convert('RGBA')
            bounds = image.getchannel('A').point(lambda a: 255 if a >= 10 else 0).getbbox()
            cache[name] = (image.size, bounds)
        (w, h), bounds = cache[name]
        if not bounds:
            rejected = True
            break
        top_y = layer['y'] + (bounds[1]/h-.5)*layer['sy']
        bottom_y = layer['y'] + (bounds[3]/h-.5)*layer['sy']
        bottom, upper = min(bottom, top_y), max(upper, bottom_y)
    if rejected or upper-bottom > .9: continue
    delta = .5 - (bottom+upper)/2
    if delta < .02 or delta > .18: continue
    for layer in layers:
        spans.append((layer['start'], layer['end'], fmt(layer['y'] + delta)))
    changes.append({'family': top.group(1), 'layers': len(layers),
                    'anchor': [anchor_x, anchor_y], 'shift_y': float(fmt(delta)),
                    'textures': [layer['name'] for layer in layers]})
if not any(c['family'] == 'ottomans_dynasty' for c in changes):
    raise RuntimeError('Expected Ottoman example not selected')
out = text
for start, end, replacement in sorted(spans, reverse=True):
    out = out[:start] + replacement + out[end:]
print('Composite arms:', len(changes), 'layers:', len(spans))
print('Examples:', [(c['family'], c['layers'], c['shift_y']) for c in changes[:8]])
if '--apply' in sys.argv:
    TARGET.write_text(out, encoding='utf-8-sig', newline='\n')
    (ROOT / 'gen_debug/eu5_family_centered_offset_layers_20261104.json').write_text(
        json.dumps(changes, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
