"""Post the next N entries of data/promo_queue.json to Bluesky and record them in data/promo_posted.json.
Usage: python scripts/post_promo_queue.py [--count N] [--dry-run]
Same secrets as post_bluesky.py. Posts are spaced 20 seconds apart. Every link in a post is made clickable."""
import argparse, json, os, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from post_bluesky import call, DATA

def facets(text):
    out = []
    raw = text.encode('utf-8')
    for m in re.finditer(rb'https?://[^\s]+', raw):
        url = m.group(0).decode('utf-8').rstrip('.,)')
        out.append({'index': {'byteStart': m.start(), 'byteEnd': m.start() + len(url.encode('utf-8'))},
                    'features': [{'$type': 'app.bsky.richtext.facet#link', 'uri': url}]})
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--count', type=int, default=8)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    queue = json.loads((DATA / 'promo_queue.json').read_text(encoding='utf-8'))['posts']
    state_path = DATA / 'promo_posted.json'
    posted = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {}
    todo = [p for p in queue if p['id'] not in posted][:args.count]
    print(f'{len(todo)} to post; {len(queue) - len(posted)} remain in the queue.')
    if args.dry_run or not todo:
        for p in todo: print('-', p['id'], p['bluesky'][:80])
        return 0
    handle, password = (os.environ.get(k, '').strip().lstrip('@') for k in ('BLUESKY_HANDLE', 'BLUESKY_APP_PASSWORD'))
    if not (handle and password):
        print('No Bluesky secrets.'); return 1
    session = call('com.atproto.server.createSession', {'identifier': handle, 'password': password})
    token, did = session['accessJwt'], session['did']
    for p in todo:
        record = {'$type': 'app.bsky.feed.post', 'text': p['bluesky'], 'langs': ['en'],
                  'createdAt': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'), 'facets': facets(p['bluesky'])}
        result = call('com.atproto.repo.createRecord', {'repo': did, 'collection': 'app.bsky.feed.post', 'record': record}, token)
        posted[p['id']] = result.get('uri', '')
        state_path.write_text(json.dumps(posted, indent=1), encoding='utf-8')
        print('Posted', p['id'])
        time.sleep(20)
    return 0

if __name__ == '__main__':
    sys.exit(main())
