"""Post the entries in data/extra_posts.json to Bluesky (one-off promo posts, manual run only).
Same sign-in and duplicate check as post_bluesky.py: skips any link the account already posted in the last two days.
Usage: python scripts/post_extra_bluesky.py [--dry-run]"""
import json, os, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from post_bluesky import call, link_facets, DATA

def main(dry_run=False):
    handle, password = (os.environ.get(k, '').strip().lstrip('@') for k in ('BLUESKY_HANDLE', 'BLUESKY_APP_PASSWORD'))
    posts = json.loads((DATA / 'extra_posts.json').read_text(encoding='utf-8'))['posts']
    if dry_run or not (handle and password):
        for p in posts: print('-', len(p['bluesky']), p['bluesky'])
        return 0
    session = call('com.atproto.server.createSession', {'identifier': handle, 'password': password})
    token, did = session['accessJwt'], session['did']
    since = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    feed = call('app.bsky.feed.getAuthorFeed', token=token, query=f'?actor={did}&limit=50')['feed']
    already = {p['post']['record'].get('text', '') for p in feed if p['post']['record'].get('createdAt', '') >= since}
    for p in posts:
        if any(p['url'] in text for text in already):
            print('Already posted:', p['url']); continue
        record = {'$type': 'app.bsky.feed.post', 'text': p['bluesky'], 'langs': ['en'],
                  'createdAt': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'), 'facets': link_facets(p['bluesky'], p['url'])}
        print('Posted:', call('com.atproto.repo.createRecord', {'repo': did, 'collection': 'app.bsky.feed.post', 'record': record}, token).get('uri'))
        time.sleep(20)
    return 0

if __name__ == '__main__':
    sys.exit(main('--dry-run' in sys.argv))
