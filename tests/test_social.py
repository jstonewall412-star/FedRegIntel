import importlib.util, json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]/'scripts'))
spec=importlib.util.spec_from_file_location('social',Path(__file__).parents[1]/'scripts/build_social.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
rule=lambda n,count,closes='2026-10-20',title='A rule',**x:{'document_number':n,'title':title,'type':'Proposed Rule','comments_close_on':closes,
    'comments_count':count,'agencies':[{'name':'Agriculture Department'},{'name':'Forest Service'}],**x}

class SocialTests(unittest.TestCase):
    def build(self, rules, counts=None, previous=None, videos=None):
        folder=tempfile.TemporaryDirectory(); self.addCleanup(folder.cleanup); data=Path(folder.name)
        (data/'open_rules.json').write_text(json.dumps({'documents':rules}))
        (data/'comment_counts.json').write_text(json.dumps(counts or {}))
        (data/'videos.json').write_text(json.dumps({'videos':videos or []}))
        if previous: (data/'social.json').write_text(json.dumps(previous))
        with patch.object(m,'DATA',data): return m.build('2026-10-03')

    def test_trending_is_biggest_rise_not_biggest_total(self):
        out=self.build([rule('big',5000),rule('rising',900)],{'2026-10-02':{'big':4990,'rising':100}})
        post=out['posts'][0]
        self.assertEqual((post['kind'],post['document_number']),('trending','rising'))
        self.assertIn('(+800 since yesterday)',post['x']); self.assertIn("Forest Service's proposed rule",post['x'])
        self.assertIn('https://fedregintel.com/rules/rising/',post['x'])

    def test_skips_routine_closed_and_recent_picks(self):
        rules=[rule('ad',9000,title='Airworthiness Directives; Boeing'),rule('closed',8000,closes='2026-10-01'),rule('recent',7000),rule('ok',10)]
        out=self.build(rules,previous={'date':'2026-10-02','history':[{'date':'2026-10-02','trending':['recent']}]})
        self.assertEqual(out['posts'][0]['document_number'],'ok')

    def test_deadline_post_and_lengths(self):
        long_title='Very long title '*20
        out=self.build([rule('a',50,closes='2026-10-04',title=long_title),rule('b',60)])
        kinds={p['kind']:p for p in out['posts']}
        self.assertIn('closes tomorrow',kinds['deadline']['x'])
        for p in out['posts']:
            self.assertLessEqual(len(p['bluesky']),300)
            self.assertLessEqual(len(p['x'])-len(p['url'])+23,280)
            self.assertTrue(p['x'].endswith(p['url']))

    def test_same_day_rerun_keeps_its_pick(self):
        out=self.build([rule('top',900),rule('next',800)],previous={'date':'2026-10-03','history':[{'date':'2026-10-03','trending':['top']}]})
        self.assertEqual(out['posts'][0]['document_number'],'top')

    def test_history_records_pick(self):
        out=self.build([rule('a',5)])
        self.assertEqual(out['history'][-1],{'date':'2026-10-03','trending':['a']})
if __name__=='__main__': unittest.main()
