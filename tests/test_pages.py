import importlib.util, json, re, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('pages',Path(__file__).parents[1]/'scripts/build_pages.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
VIDEOS={'videos':[
    {'id':'abcdefghijk','title':'Rulemaking 101 <script>alert(1)</script>','published':'2026-10-01T10:00:00+00:00','description':'See https://example.gov/doc. Then comment.'},
    {'id':'../../etc/x','title':'Bad id','published':'2026-10-01T10:00:00+00:00'}]}
RULES={'documents':[
    {'document_number':'2026-11111','title':'Open proposal','type':'Proposed Rule','comments_close_on':'2026-10-05','publication_date':'2026-09-05','abstract':'An "abstract" & more','agencies':[{'name':'Forest Service'}],'html_url':'https://www.federalregister.gov/d/2026-11111','comment_url':'https://www.regulations.gov/commenton/X'},
    {'document_number':'2026-22222','title':'Later rule','type':'Rule','comments_close_on':'2026-11-30','publication_date':'2026-09-30'},
    {'document_number':'2026-33333','title':'Already closed','type':'Proposed Rule','comments_close_on':'2026-10-02'},
    {'document_number':'../evil','title':'Bad number','type':'Proposed Rule','comments_close_on':'2026-12-01'}]}

class PageTests(unittest.TestCase):
    def build(self):
        self.data=tempfile.TemporaryDirectory(); self.out=tempfile.TemporaryDirectory()
        self.addCleanup(self.data.cleanup); self.addCleanup(self.out.cleanup)
        data=Path(self.data.name)
        (data/'videos.json').write_text(json.dumps(VIDEOS)); (data/'open_rules.json').write_text(json.dumps(RULES))
        with patch.object(m,'DATA',data): counts=m.build(self.out.name,'2026-10-03')
        return counts, Path(self.out.name)

    def test_builds_only_open_rules_and_valid_ids(self):
        (rules,videos),out=self.build()
        self.assertEqual((rules,videos),(2,1))
        self.assertTrue((out/'rules/2026-11111/index.html').exists())
        self.assertFalse((out/'rules/2026-33333').exists())
        self.assertFalse((out/'evil').exists()); self.assertFalse((out/'etc').exists())
        index=(out/'rules/index.html').read_text(encoding='utf-8')
        self.assertLess(index.index('Open proposal'),index.index('Later rule'))
        self.assertIn('Closing in the next 7 days (1)',index)

    def test_text_is_escaped_and_links_are_safe(self):
        _,out=self.build()
        video=(out/'videos/abcdefghijk/index.html').read_text(encoding='utf-8')
        self.assertNotIn('<script>alert',video)
        self.assertIn('<a href="https://example.gov/doc" rel="noopener">https://example.gov/doc</a>.',video)
        rule=(out/'rules/2026-11111/index.html').read_text(encoding='utf-8')
        self.assertIn('An &quot;abstract&quot; &amp; more',rule)
        self.assertIn('https://www.regulations.gov/commenton/X',rule)

    def test_structured_data_and_sitemap(self):
        _,out=self.build()
        video=(out/'videos/abcdefghijk/index.html').read_text(encoding='utf-8')
        ld=json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',video,re.S).group(1))
        self.assertEqual((ld['@type'],ld['uploadDate']),('VideoObject','2026-10-01T10:00:00+00:00'))
        self.assertIn('<link rel="canonical" href="https://fedregintel.com/videos/abcdefghijk/">',video)
        sitemap=(out/'sitemap.xml').read_text(encoding='utf-8')
        for path in ['/','/rules/','/videos/','/rules/2026-11111/','/videos/abcdefghijk/']:
            self.assertIn(f'<loc>https://fedregintel.com{path}</loc>',sitemap)
        self.assertNotIn('2026-33333',sitemap)

    def test_missing_data_still_builds_index_pages(self):
        with tempfile.TemporaryDirectory() as data, tempfile.TemporaryDirectory() as out:
            with patch.object(m,'DATA',Path(data)): self.assertEqual(m.build(out,'2026-10-03'),(0,0))
            self.assertIn('No open comment periods',(Path(out)/'rules/index.html').read_text(encoding='utf-8'))
            self.assertTrue((Path(out)/'sitemap.xml').exists())
if __name__=='__main__': unittest.main()
