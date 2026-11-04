"""Correct EU5 family heraldry for CK3's square CoA canvas.

Rebuild from the pre-correction backup; run with --apply after importing family
arms. An explicit instance is added where EU5 relied on the default instance.
The same transform is applied to non-solid pattern channels around their centre.
After rebuilding, run center_eu5_family_icons_20261104.py to position eligible
single central emblems and restore the requested simplified Chinese Genji names.
"""
from pathlib import Path
import json
import re
import struct
import sys
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
BACKUP = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261104_222922_family_coa_aspect')
INPUT = BACKUP / 'mod/common/coat_of_arms/coat_of_arms/zzzz_eu5_family_arms.txt'
OUTPUT = ROOT / 'common/coat_of_arms/coat_of_arms/zzzz_eu5_family_arms.txt'
GFX = BACKUP / 'mod/gfx/coat_of_arms'
DEST = ROOT / 'gfx/coat_of_arms/patterns'
original = INPUT.read_text(encoding='utf-8-sig')
if OUTPUT.read_bytes() != INPUT.read_bytes():
    raise RuntimeError('Current arms differ from the backed-up pre-correction file')

number = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)'
scale_re = re.compile(r'(\bscale\s*=\s*\{\s*)(' + number + r')(\s+)(' + number + r')(\s*\})')
position_re = re.compile(r'(\bposition\s*=\s*\{\s*)(' + number + r')(\s+)(' + number + r')(\s*\})')
rotation_re = re.compile(r'\brotation\s*=\s*(' + number + r')')
tex_re = re.compile(r'\btexture\s*=\s*"([^"]+\.dds)"')
pat_re = re.compile(r'(\bpattern\s*=\s*")(eu5dyn_[^"]+\.dds)(")')
emblem_re = re.compile(r'\b(?:colored|textured)_emblem\s*=\s*\{')
instance_re = re.compile(r'\binstance\s*=\s*\{')
stats = {'emblems': 0, 'instances': 0, 'implicit_instances': 0,
         'rotated_quarter_turns': 0, 'other_rotated_instances': 0,
         'square_texture_emblems_unchanged': 0, 'pattern_files': 0}

def number_text(value):
    return ('%.8f' % value).rstrip('0').rstrip('.') or '0'

def end_brace(s, pos):
    depth = 1
    i = pos
    while i < len(s) and depth:
        if s[i] == '{': depth += 1
        elif s[i] == '}': depth -= 1
        i += 1
    if depth:
        raise ValueError('Unbalanced block')
    return i - 1

def dimensions(name):
    raw = name.removeprefix('eu5dyn_')
    group = 'colored_emblems' if raw.startswith('ce_') else 'textured_emblems' if raw.startswith('te_') else 'patterns'
    path = GFX / group / name
    with path.open('rb') as f: header = f.read(20)
    if header[:4] != b'DDS ':
        raise ValueError('Invalid DDS: ' + str(path))
    h, w = struct.unpack_from('<II', header, 12)
    if not w or not h: raise ValueError('Empty DDS: ' + str(path))
    return w, h

def adjust_instance(inner, ratio):
    rot = rotation_re.search(inner)
    angle = float(rot.group(1)) if rot else 0.0
    quarter_turn = abs((angle + 90) % 180 - 90) > 89.999
    if quarter_turn: stats['rotated_quarter_turns'] += 1
    elif abs(angle % 180) > 0.0001: stats['other_rotated_instances'] += 1
    def replace(m):
        x, y = float(m.group(2)), float(m.group(4))
        # CK3 rotates the quad first, then applies width/height in screen axes.
        # A rotated emblem therefore still needs horizontal, not vertical, scale.
        x *= ratio
        return m.group(1) + number_text(x) + m.group(3) + number_text(y) + m.group(5)
    # EU5 positions are normalized on a 3:2 canvas. Transform the whole
    # composition about the centre along with the emblem width, otherwise
    # off-centre motifs move toward the middle of a square CK3 shield.
    def position_replace(m):
        x = 0.5 + (float(m.group(2)) - 0.5) * 1.5
        return m.group(1) + number_text(x) + m.group(3) + m.group(4) + m.group(5)
    inner = position_re.sub(position_replace, inner)
    updated, count = scale_re.subn(replace, inner)
    if count > 1: raise ValueError('Multiple scale values in one instance')
    if not count:
        new_scale = number_text(ratio) + ' 1'
        updated = updated.rstrip() + ' scale = { ' + new_scale + ' } '
    stats['instances'] += 1
    return updated

def adjust_emblem(inner):
    texture = tex_re.search(inner)
    if not texture: raise ValueError('Emblem without a texture')
    w, h = dimensions(texture.group(1))
    ratio = w / h
    if ratio == 1:
        stats['square_texture_emblems_unchanged'] += 1
    else:
        stats['emblems'] += 1
    chunks = []
    pos = 0
    count = 0
    while True:
        m = instance_re.search(inner, pos)
        if not m: break
        end = end_brace(inner, m.end())
        chunks.append(inner[pos:m.end()])
        chunks.append(adjust_instance(inner[m.end():end], ratio))
        pos = end
        count += 1
    chunks.append(inner[pos:])
    if count: return ''.join(chunks)
    if ratio == 1: return inner
    stats['implicit_instances'] += 1
    match = re.search(r'\n([ \t]*)$', inner)
    indent = match.group(1) if match else ''
    body = inner[:match.start()] if match else inner.rstrip()
    return body + '\n' + indent + '\tinstance = { position = { 0.5 0.5 } scale = { ' + number_text(ratio) + ' 1 } }\n' + indent

parts = []
pos = 0
while True:
    match = emblem_re.search(original, pos)
    if not match: break
    end = end_brace(original, match.end())
    parts.append(original[pos:match.end()])
    parts.append(adjust_emblem(original[match.end():end]))
    pos = end
parts.append(original[pos:])
updated = ''.join(parts)

patterns = set()
def pattern_name(m):
    name = m.group(2)
    if name == 'eu5dyn_pattern_solid.dds': return m.group(0)
    patterns.add(name)
    return m.group(1) + 'eu5dyn_aspect_' + name.removeprefix('eu5dyn_') + m.group(3)
updated = pat_re.sub(pattern_name, updated)
stats['pattern_files'] = len(patterns)
destinations = {name: DEST / ('eu5dyn_aspect_' + name.removeprefix('eu5dyn_')) for name in patterns}
if any(p.exists() for p in destinations.values()):
    raise FileExistsError('A corrected pattern already exists; back it up before replacing it')
print(json.dumps(stats, ensure_ascii=False, indent=2))

if '--apply' in sys.argv:
    DEST.mkdir(parents=True, exist_ok=True)
    for name, dest in sorted(destinations.items()):
        image = Image.open(GFX / 'patterns' / name).convert('RGBA')
        w, h = image.size
        new_w = round(w * w / h)
        # Resize channels independently to preserve the material's RGBA masks.
        channels = [c.resize((new_w, h), Image.Resampling.BILINEAR).crop(((new_w-w)//2, 0, (new_w-w)//2+w, h)) for c in image.split()]
        fixed = Image.merge('RGBA', channels)
        fixed.save(dest, format='DDS')
        if ImageChops.difference(fixed, Image.open(dest).convert('RGBA')).getbbox() is not None:
            raise ValueError('DDS channel round-trip differs: ' + str(dest))
    OUTPUT.write_text(updated, encoding='utf-8-sig', newline='\n')
    (ROOT / 'gen_debug/eu5_family_coa_aspect_20261104.json').write_text(
        json.dumps({'stats': stats, 'pattern_textures': sorted(patterns)}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
