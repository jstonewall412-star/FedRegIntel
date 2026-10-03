"""Post today's social desk (data/social.json) to X, mirroring the Bluesky posts.

Off until the account owner adds four GitHub Actions secrets from the X developer portal (the app needs
Read and Write permission): X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET.
X's free API tier can't read the account's timeline, so links already posted are remembered in
data/x_posted.json (committed by the workflow) and skipped for two days.
Usage: python scripts/post_x.py [--dry-run]"""
import base64, hashlib, hmac, json, os, secrets, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data'
ENDPOINT = 'https://api.x.com/2/tweets'
KEYS = ('X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_TOKEN_SECRET')

def quote(s):
    return urllib.parse.quote(str(s), safe='~')

def oauth_header(method, url, key, key_secret, token, token_secret):
    """OAuth 1.0a user-context signature. The JSON body is not part of the signature."""
    params = {'oauth_consumer_key': key, 'oauth_nonce': secrets.token_hex(16), 'oauth_signature_method': 'HMAC-SHA1',
              'oauth_timestamp': str(int(time.time())), 'oauth_token': token, 'oauth_version': '1.0'}
    base = '&'.join([method, quote(url), quote('&'.join(f'{quote(k)}={quote(v)}' for k, v in sorted(params.items())))])
    signing_key = f'{quote(key_secret)}&{quote(token_secret)}'.encode()
    params['oauth_signature'] = base64.b64encode(hmac.new(signing_key, base.encode(), hashlib.sha1).digest()).decode()
    return 'OAuth ' + ', '.join(f'{quote(k)}="{quote(v)}"' for k, v in sorted(params.items()))

def post(text, creds):
    request = urllib.request.Request(ENDPOINT, data=json.dumps({'text': text}).encode(), method='POST',
                                     headers={'Content-Type': 'application/json', 'Authorization': oauth_header('POST', ENDPOINT, *creds)})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())['data']['id']

def main(dry_run=False):
    creds = [os.environ.get(k, '').strip() for k in KEYS]
    posts = json.loads((DATA / 'social.json').read_text(encoding='utf-8')).get('posts', [])
    if dry_run or not all(creds):
        print('X posting is off (missing ' + ', '.join(k for k, v in zip(KEYS, creds) if not v) + ').' if not dry_run else 'Dry run.')
        for p in posts: print('-', p['x'])
        return 0
    state_file = DATA / 'x_posted.json'
    try: state = json.loads(state_file.read_text(encoding='utf-8'))
    except (OSError, ValueError): state = {}
    cutoff = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    state = {url: when for url, when in state.items() if when >= cutoff}
    failed = 0
    for p in posts:
        if p['url'] in state:
            print('Already posted:', p['url']); continue
        try:
            print('Posted: https://x.com/FedRegIntel/status/' + post(p['x'], creds))
            state[p['url']] = datetime.now(timezone.utc).isoformat()
        except urllib.error.HTTPError as exc:
            failed += 1
            print(f'X refused the post (HTTP {exc.code}): {exc.read().decode(errors="replace")[:300]}')
            if exc.code in (401, 403):
                print('Check that the four X secrets belong to @FedRegIntel and the app has Read and Write permission.')
                break
    state_file.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
    return 1 if failed else 0

if __name__ == '__main__':
    sys.exit(main('--dry-run' in sys.argv))
