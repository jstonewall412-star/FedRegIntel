import importlib.util, json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('post_x',Path(__file__).parents[1]/'scripts/post_x.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ENV={k:'v' for k in m.KEYS}

class PostXTests(unittest.TestCase):
    def run_with(self, state):
        folder=tempfile.TemporaryDirectory(); self.addCleanup(folder.cleanup); data=Path(folder.name)
        (data/'social.json').write_text(json.dumps({'posts':[{'url':'u1','x':'one'},{'url':'u2','x':'two'}]}))
        (data/'x_posted.json').write_text(json.dumps(state))
        with patch.object(m,'DATA',data), patch.dict(os.environ,ENV), patch.object(m,'post',return_value='123') as post:
            self.assertEqual(m.main(),0)
        return post, json.loads((data/'x_posted.json').read_text())

    def test_skips_recent_links_and_records_new(self):
        post,state=self.run_with({'u1':'2999-01-01T00:00:00+00:00','old':'2000-01-01T00:00:00+00:00'})
        post.assert_called_once()
        self.assertEqual(post.call_args[0][0],'two')
        self.assertEqual(set(state),{'u1','u2'})

    def test_off_without_secrets(self):
        with patch.dict(os.environ,{},clear=True), patch.object(m,'post') as post:
            folder=tempfile.TemporaryDirectory(); self.addCleanup(folder.cleanup)
            (Path(folder.name)/'social.json').write_text('{"posts":[]}')
            with patch.object(m,'DATA',Path(folder.name)): self.assertEqual(m.main(),0)
        post.assert_not_called()

    def test_oauth_header_has_signature(self):
        h=m.oauth_header('POST',m.ENDPOINT,'ck','cs','tk','ts')
        for field in ['oauth_consumer_key="ck"','oauth_token="tk"','oauth_signature_method="HMAC-SHA1"','oauth_signature=']:
            self.assertIn(field,h)
if __name__=='__main__': unittest.main()
