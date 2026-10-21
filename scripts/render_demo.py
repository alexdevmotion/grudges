"""Render the README walkthrough from a sanitized capture and verified controls.

Run: python scripts/render_demo.py (Pillow and DejaVu Sans fonts required).
This renders an edited walkthrough, not a real-time screen recording.
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'docs/assets'
DATA = json.loads((ASSETS / 'demo-data.json').read_text())
FONT = Path('/usr/share/fonts/truetype/dejavu')
def font(size, mono=False, bold=False):
    name = 'DejaVuSansMono' if mono else 'DejaVuSans'
    return ImageFont.truetype(str(FONT / (name + ('-Bold' if bold else '') + '.ttf')), size)

controls = {r['agent']: r for r in DATA['controls']}
def control(agent):
    r = controls[agent]
    return f"{agent}: fixed {r['solved']}/{r['scored']} · attempts {r['solved']}/{r['scored']} · no errors"

scenes = [
 ('01 / CAPTURE', 'Don’t lose the failure.', 'A tiny local fixture. A mistake worth keeping.',
  ['$ grudges save --session demo '+chr(92), '  --note "Keep the amount editable until blur."', '', *DATA['capture'].splitlines()],
  'Starting code + failed attempt, pinned locally.'),
 ('02 / REPLAY', 'Make failure repeatable.', 'Try the bundled starter pack. No API key needed.',
  ['$ grudges run --pack starter -a nop -k 1', '',
   control('nop'), '',
   '$ grudges run --pack starter -a oracle -k 1', '',
   control('oracle')],
  'Broken starting code fails. Reference fixes pass.'),
 ('03 / COMPARE', 'New model? Same receipts.', 'Your next step: replay a reviewed task across models.',
  ['$ grudges run path/to/task -a codex '+chr(92), '  -m MODEL_A -m MODEL_B -k 3', '',
   '# Or test your project rules', '$ grudges run path/to/task -a codex '+chr(92),
   '  -m YOUR_MODEL_ID --rules ./AGENTS.md -k 3'],
  'As captured → with rules. Every attempt accounted for.'),
]

def render(index, progress):
    label,title,subtitle,lines,note = scenes[index]
    im=Image.new('RGB',(1000,600),'#111b25');d=ImageDraw.Draw(im)
    amber='#ffc578';light='#f7f2e8';muted='#a2b1bf';green='#a8dfb2'
    d.text((38,25),'grudges',font=font(23,bold=True),fill=light)
    d.text((710,33),'KEEP RECEIPTS.',font=font(15,mono=True),fill=amber)
    d.line((38,68,962,68),fill='#33404b')
    d.text((38,88),label,font=font(15,mono=True),fill=amber)
    d.text((36,118),title,font=font(42,bold=True),fill=light)
    d.text((38,177),subtitle,font=font(19),fill=muted)
    d.rounded_rectangle((36,220,964,502),radius=16,fill='#1b2935',outline='#3b4c5b')
    for j,color in enumerate(['#ed8b7e','#ffc578','#a8dfb2']):
        d.ellipse((57+j*20,239,67+j*20,249),fill=color)
    d.text((137,235),'demo-repo  /  terminal',font=font(13,mono=True),fill=muted)
    # Reveal commands/outputs in sequence; hold complete frames for reading.
    reveal = min(len(lines), int(progress * (len(lines)+4))+1)
    for j,line in enumerate(lines[:reveal]):
        color=amber if line.startswith('$') else green if ('exact starting' in line or 'no errors' in line) else light
        d.text((58,275+j*28),line,font=font(16,mono=True),fill=color)
    d.text((38,523),note,font=font(19,bold=True),fill=light)
    d.text((38,562),'Edited walkthrough · local fixture + verified controls · no model calls',font=font(13),fill=muted)
    for j in range(3):
        x=830+j*44
        d.rounded_rectangle((x,565,x+32,571),radius=3,fill=amber if j==index else '#3b4c5b')
    return im

frames=[]
for index in range(len(scenes)):
    for n in range(48):
        frames.append(render(index,n/32))
frames[47].save(ASSETS/'demo.png')
frames[0].save(ASSETS/'demo.gif',save_all=True,append_images=frames[1:],duration=125,loop=0,optimize=True)
for i in range(3):
    render(i,1).save(Path('/tmp')/f'grudges-demo-scene-{i}.png')
print(f'{len(frames)} frames, 18 seconds, {(ASSETS/"demo.gif").stat().st_size:,} bytes')
