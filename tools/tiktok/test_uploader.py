import hashlib, importlib.util, json, time, unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse
spec = importlib.util.spec_from_file_location('uploader', Path(__file__).with_name('uploader.py'))
app = importlib.util.module_from_spec(spec); spec.loader.exec_module(app)

class UploaderTests(unittest.TestCase):
    def test_pkce_state_and_exact_callback(self):
        client = app.Client(); client.key = 'example-key'; client.secret = 'example-secret'
        first = parse_qs(urlparse(client.authorize_url()).query)
        self.assertEqual(first['redirect_uri'], [app.CALLBACK])
        self.assertEqual(first['code_challenge'][0], hashlib.sha256(client.oauth['verifier'].encode()).hexdigest())
        self.assertEqual(set(first['scope'][0].split(',')), {'user.info.basic', 'video.upload'})
        second = parse_qs(urlparse(client.authorize_url()).query)
        self.assertNotEqual(first['state'], second['state'])

    def test_bad_callback_cannot_call_api(self):
        client = app.Client(); client.key = 'example'; client.secret = 'example'; client.authorize_url()
        with patch.object(client, 'api') as api:
            with self.assertRaises(app.ApiError): client.callback({'state': ['wrong'], 'code': ['example']})
            api.assert_not_called()
        self.assertIsNone(client.oauth)

    def test_scope_refusal_does_not_store_tokens(self):
        client = app.Client(); client.key = 'example'; client.secret = 'example'; client.authorize_url()
        state = client.oauth['state']
        with patch.object(client, 'api', return_value={'access_token': 'example', 'scope': 'user.info.basic'}):
            with self.assertRaises(app.ApiError): client.callback({'state': [state], 'code': ['example']})
        self.assertFalse(client.tokens)

    def test_upload_blocked_without_connection_or_invalid_file(self):
        client = app.Client()
        with self.assertRaises(app.ApiError): client.init_upload(b'not an mp4')
        client.profile = {'display_name': 'Example'}
        with patch.object(client, 'api') as api:
            with self.assertRaises(app.ApiError): client.init_upload(b'not an mp4')
            api.assert_not_called()

    def test_unknown_upload_host_never_receives_video(self):
        client = app.Client(); client.profile = {'display_name': 'Example'}
        video = b'\x00\x00\x00\x18ftyp' + b'0' * 20
        with patch.object(client, 'api', return_value={'data': {'publish_id': 'example', 'upload_url': 'https://attacker.invalid/video/'}}), patch.object(app, 'urlopen') as upload:
            with self.assertRaises(app.ApiError): client.init_upload(video)
            upload.assert_not_called()

    def test_duplicate_attempt_is_held_and_upload_targets_draft(self):
        client = app.Client(); client.profile = {'display_name': 'Example'}
        video = b'\x00\x00\x00\x18ftyp' + b'0' * 20
        with patch.object(client, 'api', side_effect=app.ApiError('network uncertain')) as api:
            with self.assertRaises(app.ApiError): client.init_upload(video)
            self.assertEqual(api.call_args.args[0], '/v2/post/publish/inbox/video/init/')
            with self.assertRaises(app.ApiError): client.init_upload(video)
            self.assertEqual(api.call_count, 1)

    def test_ui_escapes_profile_and_requires_per_upload_consent(self):
        source = Path(__file__).with_name('ui.html').read_text()
        self.assertIn('name="consent" value="yes" required', source)
        self.assertIn('type="password"', source)
        self.assertNotIn('/post/publish/video/init/', Path(__file__).with_name('uploader.py').read_text())

if __name__ == '__main__': unittest.main()
