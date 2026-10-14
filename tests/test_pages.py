import importlib.util, json, re, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('pages',Path(__file__).parents[1]/'scripts/build_pages.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
VIDEOS={'videos':[
    {'id':'abcdefghijk','title':'Rulemaking 101 <script>alert(1)</script>','published':'2026-10-01T10:00:00+00:00','description':'See https://example.gov/doc. Then comment.'},
    {'id':'../../etc/x','title':'Bad id','published':'2026-10-01T10:00:00+00:00'}]}
OPEN={'documents':[
    {'document_number':'2026-11111','title':'Open proposal','type':'Proposed Rule','comments_close_on':'2026-10-05','publication_date':'2026-09-05','abstract':'An "abstract" & more','agencies':[{'name':'Forest Service'}],'html_url':'https://www.federalregister.gov/d/2026-11111','comment_url':'https://www.regulations.gov/commenton/X'},
    {'document_number':'2026-22222','title':'Later rule','type':'Rule','comments_close_on':'2026-11-30','publication_date':'2026-09-30'},
    {'document_number':'2026-44444','title':'Airworthiness Directives; Airbus Helicopters','type':'Proposed Rule','comments_close_on':'2026-10-20'},
    {'document_number':'../evil','title':'Bad number','type':'Proposed Rule','comments_close_on':'2026-12-01'}]}
ARCHIVE={'documents':{
    '2026-33333':{'document_number':'2026-33333','title':'Closed proposal','type':'Proposed Rule','comments_close_on':'2026-09-20','publication_date':'2026-08-20','comment_url':'https://www.regulations.gov/commenton/OLD',
                  'final_rule':{'title':'Closed proposal, final','html_url':'https://www.federalregister.gov/d/2026-55555','publication_date':'2026-10-01'}},
    '2026-11111':{'document_number':'2026-11111','title':'Stale copy','type':'Proposed Rule','comments_close_on':'2026-09-01'}}}
TRANSCRIPTS={'videos':{'abcdefghijk':{'transcript':['First paragraph.','Second <b>paragraph</b>.'],'documents':['2026-11111','2026-99999']}}}

class PageTests(unittest.TestCase):
    def build(self, **files):
        data=tempfile.TemporaryDirectory(); out=tempfile.TemporaryDirectory()
        self.addCleanup(data.cleanup); self.addCleanup(out.cleanup)
        files={'videos.json':VIDEOS,'open_rules.json':OPEN,'rules_archive.json':ARCHIVE,'transcripts.json':TRANSCRIPTS,**files}
        for name,content in files.items(): (Path(data.name)/name).write_text(json.dumps(content))
        with patch.object(m,'DATA',Path(data.name)): counts=m.build(out.name,'2026-10-03')
        self.out=Path(out.name)
        return counts
    def read(self, path): return (self.out/path/'index.html').read_text(encoding='utf-8')

    def test_open_closed_routine_and_invalid(self):
        self.assertEqual(self.build(),(2,1))
        self.assertFalse((self.out/'rules/2026-44444').exists())
        self.assertFalse((self.out/'evil').exists()); self.assertFalse((self.out/'etc').exists())
        index=self.read('rules')
        self.assertLess(index.index('Open proposal'),index.index('Later rule'))
        self.assertIn('Closing in the next 7 days (1)',index)
        self.assertIn('Closed in the last 30 days (1)',index)
        self.assertIn('Closed proposal',self.read('rules/archive'))

    def test_open_snapshot_wins_over_archive(self):
        self.build()
        page=self.read('rules/2026-11111')
        self.assertIn('Open proposal',page); self.assertNotIn('Stale copy',page)
        self.assertIn('COMMENTS DUE OCTOBER 5, 2026',page)

    def test_closed_page_drops_comment_link_and_links_final_rule(self):
        self.build()
        page=self.read('rules/2026-33333')
        self.assertIn('COMMENTS CLOSED SEPTEMBER 20, 2026',page)
        self.assertNotIn('commenton/OLD',page)
        self.assertIn('Rule published',page)
        self.assertIn('https://www.federalregister.gov/d/2026-55555',page)

    def test_closed_page_without_final_rule_explains_next_step(self):
        archive={'documents':{'2026-33333':{**ARCHIVE['documents']['2026-33333'],'final_rule':None}}}
        self.build(**{'rules_archive.json':archive})
        self.assertIn('What happens next',self.read('rules/2026-33333'))

    def test_transcript_and_cross_links(self):
        self.build()
        video=self.read('videos/abcdefghijk')
        self.assertIn('<p>Second &lt;b&gt;paragraph&lt;/b&gt;.</p>',video)
        self.assertIn('href="/rules/2026-11111/"',video)
        self.assertNotIn('2026-99999',video)
        ld=json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',video,re.S).group(1))
        self.assertEqual(ld['transcript'],'First paragraph.\n\nSecond <b>paragraph</b>.')
        self.assertIn('href="/videos/abcdefghijk/"',self.read('rules/2026-11111'))

    def test_text_is_escaped_and_links_are_safe(self):
        self.build()
        video=self.read('videos/abcdefghijk')
        self.assertNotIn('<script>alert',video)
        self.assertIn('<a href="https://example.gov/doc" rel="noopener">https://example.gov/doc</a>.',video)
        rule=self.read('rules/2026-11111')
        self.assertIn('An &quot;abstract&quot; &amp; more',rule)
        self.assertIn('https://www.regulations.gov/commenton/X',rule)

    def test_structured_data_and_sitemap(self):
        self.build()
        video=self.read('videos/abcdefghijk')
        ld=json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',video,re.S).group(1))
        self.assertEqual((ld['@type'],ld['uploadDate']),('VideoObject','2026-10-01T10:00:00+00:00'))
        self.assertIn('<link rel="canonical" href="https://fedregintel.com/videos/abcdefghijk/">',video)
        sitemap=(self.out/'sitemap.xml').read_text(encoding='utf-8')
        for path in ['/','/rules/','/rules/archive/','/videos/','/rules/2026-11111/','/rules/2026-33333/','/videos/abcdefghijk/']:
            self.assertIn(f'<loc>https://fedregintel.com{path}</loc>',sitemap)
        self.assertIn('<lastmod>2026-10-01</lastmod>',sitemap)
        self.assertNotIn('2026-44444',sitemap)

    def test_missing_data_still_builds_index_pages(self):
        with tempfile.TemporaryDirectory() as data, tempfile.TemporaryDirectory() as out:
            with patch.object(m,'DATA',Path(data)): self.assertEqual(m.build(out,'2026-10-03'),(0,0))
            self.assertIn('No open comment periods',(Path(out)/'rules/index.html').read_text(encoding='utf-8'))
            self.assertTrue((Path(out)/'sitemap.xml').exists())
if __name__=='__main__': unittest.main()
