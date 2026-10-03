"""Post today's social desk (data/social.json) to Bluesky.

Off until the account owner adds two GitHub Actions secrets: BLUESKY_HANDLE and BLUESKY_APP_PASSWORD
(an app password from Bluesky Settings > Privacy and security > App passwords, never the main password).
Skips any post whose link the account already posted in the last two days, so reruns don't duplicate.
Usage: python scripts/post_bluesky.py [--dry-run]"""
import json, os, sys, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data'
API = 'https://bsky.social/xrpc/'

def call(method, body=None, token=None, query=''):
    request = urllib.request.Request(API + method + query, data=json.dumps(body).encode() if body is not None else None,
                                     headers={'Content-Type': 'application/json', **({'Authorization': f'Bearer {token}'} if token else {})})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())

def link_facets(text, url):
    """Bluesky needs the link's position in UTF-8 bytes to make it clickable."""
    start = text.encode('utf-8').find(url.encode('utf-8'))
    if start < 0:
        return []
    return [{'index': {'byteStart': start, 'byteEnd': start + len(url.encode('utf-8'))},
             'features': [{'$type': 'app.bsky.richtext.facet#link', 'uri': url}]}]

def main(dry_run=False):
    handle, password = os.environ.get('BLUESKY_HANDLE'), os.environ.get('BLUESKY_APP_PASSWORD')
    social = json.loads((DATA / 'social.json').read_text(encoding='utf-8'))
    posts = social.get('posts', [])
    if dry_run or not (handle and password):
        print('Bluesky posting is off (no BLUESKY_HANDLE / BLUESKY_APP_PASSWORD secrets).' if not dry_run else 'Dry run.')
        for p in posts: print('-', p['bluesky'])
        return 0
    session = call('com.atproto.server.createSession', {'identifier': handle, 'password': password})
    token, did = session['accessJwt'], session['did']
    since = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    feed = call('app.bsky.feed.getAuthorFeed', token=token, query=f'?actor={did}&limit=30')['feed']
    already = {p['post']['record'].get('text', '') for p in feed if p['post']['record'].get('createdAt', '') >= since}
    for p in posts:
        if any(p['url'] in text for text in already):
            print('Already posted:', p['url']); continue
        record = {'$type': 'app.bsky.feed.post', 'text': p['bluesky'], 'langs': ['en'],
                  'createdAt': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'), 'facets': link_facets(p['bluesky'], p['url'])}
        result = call('com.atproto.repo.createRecord', {'repo': did, 'collection': 'app.bsky.feed.post', 'record': record}, token)
        print('Posted:', result.get('uri'))
    return 0

if __name__ == '__main__':
    sys.exit(main('--dry-run' in sys.argv))
