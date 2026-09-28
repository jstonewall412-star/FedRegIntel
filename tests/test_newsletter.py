import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('newsletter',Path(__file__).resolve().parents[1]/'scripts/build_newsletter.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class NewsletterTests(unittest.TestCase):
    def test_eastern_month_boundary(self):
        videos=[{'published':'2026-10-01T02:00:00Z','title':'September'}, {'published':'2026-10-01T05:00:00Z','title':'October'}]
        self.assertEqual([v['title'] for v in module.month_videos(videos,'2026-09')],['September'])

    def test_escape_titles_and_preserve_unsubscribe_placeholder(self):
        html=module.render('A < B',['A & B'],[('A < B','https://example.com/?a=1&b=2')])
        self.assertIn('A &lt; B',html)
        self.assertIn('{{UNSUBSCRIBE_URL}}',html)
        self.assertIn('{{MAILING_ADDRESS}}',html)

if __name__ == '__main__': unittest.main()
