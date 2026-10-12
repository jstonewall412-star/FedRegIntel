"""Owner-run TikTok draft uploader. Python 3.12+, standard library only.
No public-post endpoint, disk credentials, automatic uploads, or HTTP request logging.
"""
import hashlib, hmac, html, json, secrets, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs
from urllib.request import Request, urlopen
from urllib.error import HTTPError

PORT = 8769
ORIGIN = f'http://127.0.0.1:{PORT}'
CALLBACK = ORIGIN + '/callback/'
SCOPES = 'user.info.basic,video.upload'
MAX_VIDEO = 64 * 1024 * 1024
ROOT = Path(__file__).parent

class ApiError(Exception):
    pass

class Client:
    def __init__(self):
        self.key = self.secret = ''
        self.tokens = {}
        self.profile = {}
        self.oauth = None
        self.pending = {}

    def api(self, path, data=None, form=False, authorized=True, method=None):
        headers = {'Accept': 'application/json'}
        if authorized:
            headers['Authorization'] = 'Bearer ' + self.access()
        payload = None
        if data is not None:
            payload = (urlencode(data) if form else json.dumps(data)).encode()
            headers['Content-Type'] = 'application/x-www-form-urlencoded' if form else 'application/json'
        try:
            with urlopen(Request('https://open.tiktokapis.com' + path, payload, headers, method=method), timeout=45) as response:
                result = json.load(response)
        except HTTPError as error:
            raise ApiError(f'TikTok returned HTTP {error.code}; check the app configuration and granted scopes.') from None
        except (OSError, ValueError):
            raise ApiError('TikTok could not be reached or returned an unreadable response.') from None
        error = result.get('error', {})
        if isinstance(error, str):
            raise ApiError('TikTok authorization was refused. Check your app credentials and callback.')
        if error.get('code') not in (None, 'ok'):
            raise ApiError('TikTok API error: ' + str(error.get('code', 'unknown'))[:100])
        return result

    def access(self):
        if not self.tokens.get('access_token'):
            raise ApiError('Connect your TikTok account first.')
        if time.time() >= self.tokens.get('expires_at', 0) - 60:
            result = self.api('/v2/oauth/token/', {'client_key': self.key, 'client_secret': self.secret,
                'grant_type': 'refresh_token', 'refresh_token': self.tokens['refresh_token']}, form=True, authorized=False)
            self.set_tokens(result)
        return self.tokens['access_token']

    def set_tokens(self, result):
        if not result.get('access_token'):
            raise ApiError('TikTok did not return an access token.')
        self.tokens = {**result, 'expires_at': time.time() + int(result.get('expires_in', 0))}

    def authorize_url(self):
        if not self.key or not self.secret:
            raise ApiError('Enter the sandbox client key and client secret on this computer first.')
        verifier = secrets.token_urlsafe(48)
        state = secrets.token_urlsafe(32)
        self.oauth = {'state': state, 'verifier': verifier, 'expires': time.time() + 600}
        # TikTok Desktop explicitly specifies SHA256 hex rather than base64url.
        return 'https://www.tiktok.com/v2/auth/authorize/?' + urlencode({'client_key': self.key,
            'response_type': 'code', 'scope': SCOPES, 'redirect_uri': CALLBACK, 'state': state,
            'code_challenge': hashlib.sha256(verifier.encode()).hexdigest(), 'code_challenge_method': 'S256'})

    def callback(self, query):
        attempt, self.oauth = self.oauth, None
        if not attempt or time.time() > attempt['expires'] or not hmac.compare_digest(query.get('state', [''])[0], attempt['state']):
            raise ApiError('Invalid or expired authorization state. Start Connect again.')
        if query.get('error') or not query.get('code'):
            raise ApiError('TikTok authorization was declined or did not return a code.')
        result = self.api('/v2/oauth/token/', {'client_key': self.key, 'client_secret': self.secret,
            'grant_type': 'authorization_code', 'redirect_uri': CALLBACK, 'code': query['code'][0],
            'code_verifier': attempt['verifier']}, form=True, authorized=False)
        granted = set(result.get('scope', '').split(','))
        if not set(SCOPES.split(',')).issubset(granted):
            raise ApiError('Both basic profile and draft-upload permissions must be granted.')
        self.set_tokens(result)
        self.profile = self.api('/v2/user/info/?fields=open_id,display_name,avatar_url')['data']['user']

    def init_upload(self, video):
        if not self.profile:
            raise ApiError('Connect and verify your TikTok profile first.')
        if not 12 <= len(video) <= MAX_VIDEO or video[4:8] != b'ftyp':
            raise ApiError('Select an MP4 file no larger than 64 MiB. Larger videos are not supported by this starter.')
        digest = hashlib.sha256(video).hexdigest()
        if digest in self.pending:
            raise ApiError('This video already has an upload attempt in this session. Check its status before retrying.')
        self.pending[digest] = {'status': 'initializing'}
        # Keep ambiguous attempts blocked; only disconnect/restart clears them.
        result = self.api('/v2/post/publish/inbox/video/init/', {'source_info': {
            'source': 'FILE_UPLOAD', 'video_size': len(video), 'chunk_size': len(video), 'total_chunk_count': 1}})['data']
        publish_id = result['publish_id']
        target = urlparse(result['upload_url'])
        if target.scheme != 'https' or not (target.hostname == 'open-upload.tiktokapis.com' or target.hostname == 'upload.us.tiktokapis.com') or target.username or target.password:
            raise ApiError('TikTok returned an unexpected upload host. Upload stopped.')
        self.pending[digest] = {'publish_id': publish_id, 'status': 'transferring'}
        try:
            with urlopen(Request(result['upload_url'], data=video, method='PUT', headers={
                'Content-Type': 'video/mp4', 'Content-Range': f'bytes 0-{len(video)-1}/{len(video)}'}), timeout=120) as response:
                if response.status != 201:
                    raise ApiError('TikTok did not confirm a complete upload. Check status before any retry.')
        except (OSError, HTTPError):
            self.pending[digest]['status'] = 'transfer_uncertain'
            raise ApiError('Transfer result is uncertain. Use Check status; do not upload again blindly.') from None
        self.pending[digest]['status'] = 'processing'
        return publish_id

    def status(self):
        results = []
        for entry in self.pending.values():
            if entry.get('publish_id'):
                data = self.api('/v2/post/publish/status/fetch/', {'publish_id': entry['publish_id']})['data']
                entry['status'] = data.get('status', 'unknown')
            results.append({'status': entry['status']})
        return results

    def disconnect(self):
        if self.tokens.get('access_token'):
            self.api('/v2/oauth/revoke/', {'client_key': self.key, 'client_secret': self.secret,
                'token': self.access()}, form=True, authorized=False)
        self.__init__()

CLIENT = Client()
CSRF = secrets.token_urlsafe(32)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def page(self, message='', status=200):
        name = CLIENT.profile.get('display_name', 'Not connected')
        source = (ROOT / 'ui.html').read_text(encoding='utf-8').replace('{{csrf}}', CSRF)
        source = source.replace('{{account}}', html.escape(name)).replace('{{message}}', html.escape(message))
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Referrer-Policy', 'same-origin')
        self.send_header('X-Frame-Options', 'DENY')
        self.end_headers()
        self.wfile.write(source.encode())

    def valid_host(self):
        return self.headers.get('Host') == f'127.0.0.1:{PORT}'

    def do_GET(self):
        if not self.valid_host():
            self.send_error(403); return
        url = urlparse(self.path)
        if url.path == '/callback/':
            try:
                CLIENT.callback(parse_qs(url.query)); self.page('Connected. Verify the account name before selecting a video.')
            except ApiError as error:
                self.page(str(error), 400)
        elif url.path == '/':
            self.page()
        else:
            self.send_error(404)

    def do_POST(self):
        if not self.valid_host() or self.headers.get('Origin') not in (None, ORIGIN):
            self.send_error(403); return
        try:
            size = int(self.headers.get('Content-Length', 0))
            if not 0 < size <= MAX_VIDEO + 65536:
                self.send_error(413); return
            payload = self.rfile.read(size)
            if self.path == '/upload':
                # Parse the browser's multipart form without deprecated cgi.
                from email.parser import BytesParser
                from email.policy import default
                msg = BytesParser(policy=default).parsebytes(('Content-Type: '+self.headers.get('Content-Type', '')+'\r\nMIME-Version: 1.0\r\n\r\n').encode()+payload)
                fields = {}
                for part in msg.iter_parts():
                    fields[part.get_param('name', header='content-disposition')] = part.get_payload(decode=True)
                if not hmac.compare_digest(fields.get('csrf', b'').decode(), CSRF) or fields.get('consent') != b'yes':
                    self.send_error(403); return
                CLIENT.init_upload(fields.get('video', b''))
                self.page('Video transferred. Check status, then open the TikTok inbox notification to review and publish. This is not a public-post confirmation.')
                return
            data = parse_qs(payload.decode())
            if not hmac.compare_digest(data.get('csrf', [''])[0], CSRF):
                self.send_error(403); return
            if self.path == '/configure':
                if CLIENT.tokens:
                    raise ApiError('Disconnect the current account before changing app credentials.')
                CLIENT.key = data.get('client_key', [''])[0].strip()
                CLIENT.secret = data.get('client_secret', [''])[0].strip()
                if not CLIENT.key or not CLIENT.secret:
                    raise ApiError('Both sandbox credentials are required.')
                self.page('Sandbox credentials loaded into memory. Nothing has been sent to TikTok yet.')
            elif self.path == '/connect':
                target = CLIENT.authorize_url()
                self.send_response(303); self.send_header('Location', target); self.send_header('Referrer-Policy', 'no-referrer'); self.end_headers()
            elif self.path == '/status':
                statuses = CLIENT.status()
                self.page('No upload attempts this session.' if not statuses else 'TikTok status: '+', '.join(s['status'] for s in statuses))
            elif self.path == '/disconnect':
                CLIENT.disconnect(); self.page('Access revoked and all app-session credentials cleared.')
            else:
                self.send_error(404)
        except ApiError as error:
            self.page(str(error), 400)
        except Exception:
            self.page('The operation could not complete. No success is assumed; check the current upload status before retrying.', 400)

if __name__ == '__main__':
    print('FedReg Intel draft uploader: '+ORIGIN+' (credentials remain in memory; Ctrl+C closes it)')
    HTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
