"""Check release archives without installing or executing bundled tasks."""
import sys
import tarfile
import zipfile
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'dist')
wheels = list(root.glob('*.whl'))
sdists = list(root.glob('*.tar.gz'))
assert len(wheels) == len(sdists) == 1, 'expected one wheel and one sdist'
with zipfile.ZipFile(wheels[0]) as archive:
    names = archive.namelist()
    for pack, count in [('starter', 8), ('starter-intent', 6)]:
        tasks = [n for n in names if n.startswith(f'grudges/packs/{pack}/') and n.endswith('/task.toml')]
        assert len(tasks) == count, (pack, tasks)
        for task in tasks:
            base = task.removesuffix('task.toml')
            for required in ['instruction.md', 'environment/Dockerfile', 'solution/solve.sh', 'tests/test.sh']:
                assert base + required in names, base + required
    assert any(n.endswith('/licenses/LICENSE') for n in names)
    assert any(n.endswith('/licenses/NOTICE') for n in names)
with tarfile.open(sdists[0]) as archive:
    members = archive.getmembers()
    assert all(not m.issym() and not m.islnk() for m in members), 'unexpected archive link'
    names += [m.name for m in members]
for name in names:
    assert not any(part in {'.git', '.grudges', '__pycache__'} for part in Path(name).parts), name
    assert not name.endswith(('.pyc', '.jsonl')), name
print('Wheel and sdist validated: 8 starter + 6 intent tasks, licenses, no capture artifacts.')
