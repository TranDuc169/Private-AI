"""Package backend source and release evidence, never local secrets or databases."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ('backend/app', 'backend/alembic', 'backend/tests', 'docs/course',
               'docs/evaluation', 'docs/evidence/week12')
FILES = ('backend/requirements.txt', 'backend/requirements.lock.txt',
         'backend/requirements-dev.txt', 'backend/.env.example', 'backend/Dockerfile',
         'backend/alembic.ini', 'backend/conftest.py', 'backend/check_db.py',
         'backend/setup_auth.py', 'backend/test_postgres.py', 'backend/evaluate_rag.py',
         'backend/evaluate_retrieval.py', 'backend/summarize_evaluation.py',
         'backend/package_release.py', 'backend/load_demo_course.py',
         'compose.yaml', 'compose.release.yaml', '.env.example', '.env.release.example',
         '.dockerignore', 'docs/WEEK12.md', 'docs/RELEASE.md')


def source_files(root=ROOT):
    files = {root / name for name in FILES}
    for directory in DIRECTORIES:
        files.update(p for p in (root / directory).rglob('*') if p.is_file())
    return sorted(p for p in files if not p.is_symlink() and p.resolve().is_relative_to(root.resolve()) and
                  '__pycache__' not in p.parts and p.suffix not in ('.pyc', '.tmp') and
                  not (p.name.startswith('.env') and not p.name.endswith('.example')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    files = source_files()
    missing = [str(p.relative_to(ROOT)) for p in files if not p.is_file()]
    if missing:
        raise SystemExit('Missing release files: ' + ', '.join(missing))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    manifest = {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    with ZipFile(args.output, 'x', compression=ZIP_DEFLATED) as archive:
        for p in files:
            archive.write(p, 'private-ai-backend/' + p.relative_to(ROOT).as_posix())
        archive.writestr('private-ai-backend/RELEASE_MANIFEST.json', json.dumps(manifest, indent=2)+'\n')
    print(f'{len(files)} files: {args.output}')


if __name__ == '__main__':
    main()
