"""Import the five verified demo PDFs into a NEW workspace using your own account.

Never writes directly to the database. Credentials are prompted locally, not saved.
"""
import argparse
from datetime import datetime
from getpass import getpass
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

import httpx

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api',default='http://127.0.0.1:8000')
    args=parser.parse_args()
    if urlparse(args.api).hostname not in ('localhost','127.0.0.1','::1'):
        raise SystemExit('This local demo importer only accepts a localhost API.')
    manifest=json.loads((ROOT/'docs/course/manifest.json').read_text(encoding='utf-8'))
    for doc in manifest['documents']:
        path=ROOT/'docs/course'/doc['path']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=doc['sha256']:
            raise SystemExit('Demo PDF differs from manifest: '+doc['filename'])
    email=input('Email tai khoan da dang ky tren web: ').strip()
    password=getpass('Mat khau (khong hien ky tu khi go): ')
    with httpx.Client(base_url=args.api.rstrip('/'),timeout=660,trust_env=False) as client:
        def call(method,path,**kwargs):
            result=client.request(method,path,**kwargs)
            if not result.is_success:
                try: detail=result.json().get('detail','Request failed')
                except ValueError: detail='API did not return JSON'
                raise SystemExit(f'HTTP {result.status_code}: {detail}. Workspace/files already created are kept; retry from the web.')
            return result.json()
        token=call('POST','/auth/login',json={'email':email,'password':password})['access_token']
        del password
        client.headers['Authorization']='Bearer '+token
        name='CSDL - Demo '+datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        workspace=call('POST','/workspaces',json={'name':name})
        base='/workspaces/'+workspace['id']+'/documents'
        print('Created new workspace:',name,flush=True)
        for doc in manifest['documents']:
            pdf=ROOT/'docs/course'/doc['path']
            with pdf.open('rb') as stream:
                uploaded=call('POST',base,files={'file':(pdf.name,stream,'application/pdf')})
            path=base+'/'+uploaded['id']
            processed=call('POST',path+'/process')
            if processed['status']!='ready': raise SystemExit('PDF processing failed: '+str(processed.get('error_message')))
            indexed=call('POST',path+'/index')
            if indexed['index_status']!='ready': raise SystemExit('Indexing failed: '+str(indexed.get('index_error')))
            print('READY:',pdf.name,'|',doc['topic'],'| chunks:',indexed['chunk_count'],flush=True)
    print('Open the web app, refresh/login if needed, select the new workspace, and ask a database question.')
    print('Running this command again creates another workspace; it does not overwrite existing data.')


if __name__=='__main__':
    try: main()
    except httpx.HTTPError: raise SystemExit('Cannot reach local API. Check backend, database and Ollama, then retry.') from None
