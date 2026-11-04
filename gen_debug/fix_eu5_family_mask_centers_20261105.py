"""Align EU5 circular field masks and frames on the square CK3 CoA canvas.

The four centered pattern variants are new DDS files. For arms using these
patterns, the original EU5 layer offsets are restored relative to a centered
circle. Separately, unmasked central-frame compositions are moved as a unit.
All inputs are backed up on F:. Default dry-run; --apply commits the results.
Afterward run center_eu5_family_scaled_icons_20261105.py to include central
icons whose source alpha bounds nearly fill the texture but render smaller.
"""
from pathlib import Path
from PIL import Image, ImageChops
import json
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
BACKUP = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261105_000836_coa_masks')
REL = Path('common/coat_of_arms/coat_of_arms/zzzz_eu5_family_arms.txt')
SOURCE, TARGET = BACKUP / 'mod' / REL, ROOT / REL
ORIGINAL = BACKUP / 'source/original_eu5_family_arms.txt'
if SOURCE.read_bytes() != TARGET.read_bytes():
    raise RuntimeError('Current arms differ from the backed-up input')
text = SOURCE.read_text(encoding='utf-8-sig')
original = ORIGINAL.read_text(encoding='utf-8-sig')
number = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)'
top_re = re.compile(r'^([\w.\-]+)\s*=\s*\{', re.M)
emblem_re = re.compile(r'\b(?:colored_emblem|textured_emblem)\s*=\s*\{')
instance_re = re.compile(r'\binstance\s*=\s*\{')
pos_re = re.compile(r'\bposition\s*=\s*\{\s*(' + number + r')\s+(' + number + r')\s*\}')
scale_re = re.compile(r'\bscale\s*=\s*\{\s*(' + number + r')\s+(' + number + r')')
texture_re = re.compile(r'\btexture\s*=\s*"([^"]+\.dds)"')
pattern_re = re.compile(r'\bpattern\s*=\s*"([^"]+\.dds)"')
patterns = ['eu5dyn_aspect_pattern_mena_round_frame_shield.dds',
            'eu5dyn_aspect_pattern_mena_round_frame_shield_inner.dds',
            'eu5dyn_aspect_pattern_mena_round_frame_shield_inner_02.dds',
            'eu5dyn_aspect_pattern_round_frame_shield_ordinary_india.dds']
pattern_map = {name: name.replace('eu5dyn_aspect_', 'eu5dyn_centered_', 1) for name in patterns}

def end_brace(s, start):
    depth, i = 1, start
    while i < len(s) and depth:
        if s[i] == '{': depth += 1
        elif s[i] == '}': depth -= 1
        i += 1
    if depth: raise ValueError('Unbalanced block')
    return i - 1
def fmt(n): return ('%.6f' % n).rstrip('0').rstrip('.') or '0'
def blocks(s):
    return {m.group(1): (m.end(), end_brace(s, m.end())) for m in top_re.finditer(s)}
def emblems(body):
    result = []
    for m in emblem_re.finditer(body):
        end = end_brace(body, m.end())
        contents = body[m.end():end]
        tex = texture_re.search(contents)
        if not tex: raise ValueError('Emblem without texture')
        instances = []
        for inst in instance_re.finditer(contents):
            inst_end = end_brace(contents, inst.end())
            inner = contents[inst.end():inst_end]
            pos, scale = pos_re.search(inner), scale_re.search(inner)
            if not pos or not scale: return None
            instances.append({'x': float(pos.group(1)), 'y': float(pos.group(2)),
                              'sy': float(scale.group(2)),
                              'begin': m.end() + inst.end() + pos.start(2),
                              'end': m.end() + inst.end() + pos.end(2)})
        result.append({'name': tex.group(1), 'instances': instances,
                       'masked': bool(re.search(r'\bmask\s*=', contents))})
    return result

old_blocks = blocks(original)
current_blocks = blocks(text)
spans, report, skipped = [], [], []
for key, (begin, end) in current_blocks.items():
    body = text[begin:end]
    pat = pattern_re.search(body)
    if not pat: continue
    if pat.group(1) not in pattern_map and (pat.group(1) != 'eu5dyn_pattern_solid.dds' or
                                              re.search(r'\bmask\s*=', body) or 'frame' not in body):
        continue
    current = emblems(body)
    if current is None:
        skipped.append({'family': key, 'reason': 'instance_uses_implicit_position_or_scale'})
        continue
    if pat.group(1) in pattern_map:
        old_begin, old_end = old_blocks[key]
        previous = emblems(original[old_begin:old_end])
        if previous is None:
            skipped.append({'family': key, 'reason': 'original_instance_uses_implicit_position_or_scale'})
            continue
        if len(previous) != len(current): raise ValueError('Emblem count mismatch: ' + key)
        spans.append((begin + pat.start(1), begin + pat.end(1), pattern_map[pat.group(1)]))
        changed = 0
        for old, cur in zip(previous, current):
            if old['name'] != cur['name']: raise ValueError('Emblem identity mismatch: ' + key)
            if not old['instances']: continue  # originally implicit background
            if len(old['instances']) != len(cur['instances']): raise ValueError('Instance mismatch: ' + key)
            for oi, ci in zip(old['instances'], cur['instances']):
                # A full-canvas solid remains a background even when masked.
                if cur['name'].endswith('ce_solid.dds') and abs(oi['sy']) >= .99: continue
                new_y = oi['y'] + .04
                if abs(new_y-ci['y']) > 1e-7:
                    spans.append((begin + ci['begin'], begin + ci['end'], fmt(new_y)))
                    changed += 1
        report.append({'family': key, 'mode': 'circular_mask', 'positions_changed': changed})
        continue
    anchors = []
    for e in current:
        if 'frame' not in e['name']: continue
        for i in e['instances']:
            if abs(i['x']-.5) <= .015 and .40 <= i['y'] < .48 and abs(i['sy']) >= .45:
                anchors.append(i['y'])
    if not anchors or max(anchors)-min(anchors) > .005: continue
    delta = .5 - sum(anchors)/len(anchors)
    changed = 0
    for e in current:
        for i in e['instances']:
            if e['name'].endswith('ce_solid.dds') and abs(i['sy']) >= .99: continue
            if re.search(r'(?:ce|te)_(?:border|divider)', e['name']): continue
            spans.append((begin + i['begin'], begin + i['end'], fmt(i['y'] + delta)))
            changed += 1
    report.append({'family': key, 'mode': 'central_frame', 'positions_changed': changed,
                   'shift_y': float(fmt(delta))})

if not {'deramku_dynasty', 'walashma_dynasty'} <= {c['family'] for c in report}:
    raise ValueError('Expected screenshot families are absent')
out = text
for start, end, replacement in sorted(spans, reverse=True):
    out = out[:start] + replacement + out[end:]
pattern_dest = ROOT / 'gfx/coat_of_arms/patterns'
if any((pattern_dest / name).exists() for name in pattern_map.values()):
    raise FileExistsError('A centered pattern already exists')
print('Circular-mask families:', sum(x['mode']=='circular_mask' for x in report))
print('Other central-frame families:', [(x['family'], x['positions_changed']) for x in report if x['mode']=='central_frame'])
print('Pattern changes:', len(pattern_map), 'all replacements:', len(spans))
print('Skipped uncertain definitions:', skipped)
if '--apply' in sys.argv:
    for source, dest in pattern_map.items():
        image = Image.open(BACKUP / 'mod/gfx/coat_of_arms/patterns' / source).convert('RGBA')
        w, h = image.size
        bbox = image.getchannel('G').point(lambda a: 255 if a > 128 else 0).getbbox()
        if not bbox: raise ValueError('No mask: ' + source)
        shift = round(h/2 - (bbox[1]+bbox[3])/2)
        if shift <= 0 or shift > h//8: raise ValueError('Unexpected mask center: ' + source)
        fixed = Image.new('RGBA', (w, h))
        fixed.paste(image.crop((0, 0, w, h-shift)), (0, shift))
        fixed.paste(image.crop((0, 0, w, 1)).resize((w, shift), Image.Resampling.NEAREST), (0, 0))
        new_bbox = fixed.getchannel('G').point(lambda a: 255 if a > 128 else 0).getbbox()
        if abs((new_bbox[1]+new_bbox[3])/2-h/2) > 1: raise ValueError('Mask did not center: ' + source)
        dest_path = pattern_dest / dest
        fixed.save(dest_path, format='DDS')
        saved = Image.open(dest_path).convert('RGBA')
        if any(ImageChops.difference(a,b).getbbox() for a,b in zip(fixed.split(), saved.split())):
            raise ValueError('DDS channel round-trip mismatch: ' + str(dest_path))
    TARGET.write_text(out, encoding='utf-8-sig', newline='\n')
    (ROOT / 'gen_debug/eu5_family_mask_centers_20261105.json').write_text(
        json.dumps({'families': report, 'pattern_map': pattern_map, 'skipped': skipped}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
