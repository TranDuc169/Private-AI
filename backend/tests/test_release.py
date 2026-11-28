from summarize_evaluation import summarize
import pytest


def test_failed_and_missing_cases_remain_in_denominator():
    dataset={'cases':[dict(id='a',expected_file='a.pdf',expected_status='answered'),dict(id='b',expected_file='a.pdf',expected_status='answered'),dict(id='c',expected_file=None,expected_status='insufficient_context')]}
    report={'mode':'postgres','cases':[dict(id='a',http_status=503,elapsed_seconds=120,expected_source_rank=1,response={'status':'error'}),dict(id='c',http_status=200,elapsed_seconds=2,response={'status':'insufficient_context'})]}
    result=summarize(report,dataset)
    assert result['dataset_cases']==3 and result['attempted']==2
    assert result['missing_ids']==['b'] and result['failed_attempts']==1
    assert result['retrieval_denominator']==2 and result['retrieval_hit_at_5']==1
    assert result['outside_insufficient']==1 and result['status_matches']==1
    assert result['median_attempt_seconds']==61 and result['p95_attempt_seconds']==120
    assert result['human_content_score'] is None


def test_duplicate_retry_cannot_inflate_results():
    with pytest.raises(ValueError,match='Duplicate'):
        summarize({'mode':'models','cases':[{'id':'a'},{'id':'a'}]}, {'cases':[dict(id='a',expected_file=None,expected_status='insufficient_context')]})


def test_empty_run_has_no_latency_or_quality_claim():
    result=summarize({'mode':'postgres','cases':[]},{'cases':[dict(id='a',expected_file=None,expected_status='insufficient_context')]})
    assert result['p95_attempt_seconds'] is None
    assert result['successful_responses']==0 and result['missing_ids']==['a']


def test_release_package_excludes_private_files(tmp_path):
    from package_release import source_files
    for name in ('backend/.env','backend/storage/private.pdf','backend/.venv/secret.txt',
                 'docs/evidence/week12/.env','backend/app/__pycache__/private.pyc'):
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('private')
    public=tmp_path/'backend/app/main.py';public.parent.mkdir(parents=True,exist_ok=True);public.write_text('public')
    paths={str(p.relative_to(tmp_path)).replace('\\','/') for p in source_files(tmp_path)}
    assert 'backend/app/main.py' in paths
    assert not any(p.endswith('.env') or '/storage/' in p or '/.venv/' in p or '__pycache__' in p for p in paths)
