"""Summarize one RAG run; keep human quality scores blank until reviewed."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import median


def summarize(report, dataset):
    expected = {c['id']: c for c in dataset['cases']}
    records = report['cases']
    ids = [c['id'] for c in records]
    if len(set(ids)) != len(ids) or not set(ids) <= set(expected):
        raise ValueError('Duplicate or unknown case IDs; do not combine retries silently.')
    successful = [c for c in records if not c.get('error_code') and
                  (report['mode'] != 'postgres' or c.get('http_status') == 200) and
                  c.get('response', {}).get('status') in ('answered', 'insufficient_context')]
    scoped = {k for k,v in expected.items() if v['expected_file'] is not None}
    outside = set(expected) - scoped
    times = sorted(c['elapsed_seconds'] for c in records if isinstance(c.get('elapsed_seconds'), (int,float)))
    return {
        'dataset_cases':len(expected), 'attempted':len(records),
        'missing_ids':sorted(set(expected)-set(ids)),
        'successful_responses':len(successful), 'failed_attempts':len(records)-len(successful),
        'status_matches':sum(c['response']['status']==expected[c['id']]['expected_status'] for c in successful),
        'retrieval_hit_at_5':sum(c['id'] in scoped and isinstance(c.get('expected_source_rank'),int) and 1<=c['expected_source_rank']<=5 for c in records),
        'retrieval_denominator':len(scoped),
        'outside_insufficient':sum(c['id'] in outside and c['response']['status']=='insufficient_context' for c in successful),
        'outside_denominator':len(outside),
        'median_attempt_seconds':median(times) if times else None,
        'p95_attempt_seconds':times[math.ceil(.95*len(times))-1] if times else None,
        'latency_definition':'retrieval plus chat attempt, including recorded failures; nearest-rank p95',
        'public_data_unchanged':report.get('public_data_unchanged'),
        'human_content_score':None, 'human_source_score':None,
        'human_review':'pending; HTTP, status matches and retrieval are not semantic accuracy',
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path)
    parser.add_argument('--dataset',required=True,type=Path)
    parser.add_argument('--output-dir',required=True,type=Path)
    args=parser.parse_args()
    report=json.loads(args.report.read_text(encoding='utf-8'))
    raw=args.dataset.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=report['dataset_sha256']:
        raise SystemExit('Dataset does not match recorded SHA256.')
    dataset=json.loads(raw);summary=summarize(report,dataset)
    args.output_dir.mkdir(parents=True,exist_ok=False)
    (args.output_dir/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    records={c['id']:c for c in report['cases']}
    with (args.output_dir/'review.csv').open('w',newline='',encoding='utf-8-sig') as stream:
        writer=csv.writer(stream)
        writer.writerow(['id','question','reference','http_status','status','answer','sources','content_0_1_2','sources_0_1_2','reviewer','notes'])
        for case in dataset['cases']:
            r=records.get(case['id'],{});response=r.get('response',{})
            values=[case['id'],case['question'],case['reference'],r.get('http_status',''),response.get('status',''),response.get('answer',''),json.dumps(response.get('sources',[]),ensure_ascii=False),'','','','' if r else 'NOT RUN']
            writer.writerow(["'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@')) else v for v in values])
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
