"""Pick today's social posts from the data snapshots and write data/social.json.

Each post names a rule by its official title and agency, states facts from the Federal Register and
Regulations.gov (deadline, public comment count), and links its page on fedregintel.com. Picks:
  trending  - the open rule whose public comment count rose most since the last snapshot
  deadline  - the most-commented rule closing within two days
  video     - a video published in the last 36 hours
Rules picked as trending in the last 3 days are skipped so the feed doesn't repeat itself.
Usage: python scripts/build_social.py"""
import json, re, sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_pages import DATA, SITE, routine, snippet, today

X_LIMIT, BLUESKY_LIMIT, X_LINK = 280, 300, 23   # X counts every link as 23 characters
LINKISH = re.compile(r'https?://\S+|\b[\w-]+(?:\.[\w-]+)*\.(?:com|org|net|gov|edu|us|io|co|info|app)\b(?:/\S*)?', re.I)

def x_length(text):
    """X's weighted count: links, including bare domains like Regulations.gov, count 23; most Latin text is
    1 per character; emoji, '…' and other symbols count 2."""
    light = ((0, 4351), (8192, 8205), (8208, 8223), (8242, 8247))
    links = LINKISH.findall(text)
    rest = LINKISH.sub('', text)
    return X_LINK * len(links) + sum(1 if any(a <= ord(c) <= b for a, b in light) else 2 for c in rest)

def load(name, default):
    try: return json.loads((DATA / name).read_text(encoding='utf-8'))
    except (OSError, ValueError): return default

def short_date(s):
    d = date.fromisoformat(s[:10])
    return f'{d:%b} {d.day}'

def agency(d):
    names = [a.get('name') or a.get('raw_name') for a in d.get('agencies') or []]
    names = [n for n in names if n]
    return names[-1] if names else 'A federal agency'

def kind(d):
    return 'final rule' if d.get('type') == 'Rule' else 'proposed rule'

def fit(make, limit, link_cost=None):
    """make(title_length) -> text; shrink the quoted title until the post fits the platform."""
    for n in (110, 90, 70, 55, 40):
        text = make(n)
        length = len(text) if link_cost is None else x_length(text)
        if length <= limit:
            return text
    return make(30)

def rule_post(d, lead, day, youtube_lead):
    url = f'{SITE}/rules/{d["document_number"]}/'
    closes = short_date(d['comments_close_on'])
    count = d.get('comments_count')
    counted = f' {count:,} public comments posted on Regulations.gov so far.' if count else ''
    make = lambda n: (f'{lead} {agency(d)}\'s {kind(d)}, "{snippet(d["title"], n)}".{counted} '
                      f'Comments close {closes}. Read it and weigh in: {url}')
    long_text = (f'{lead} {agency(d)}\'s {kind(d)}, "{d["title"]}".{counted} Comments close {closes}. '
                 f'The page links the official document and the comment form: {url}')
    youtube = (f"{youtube_lead} {agency(d)}'s {kind(d)}, \"{d['title']}.\""
               + (f' {count:,} public comments on Regulations.gov.' if count else '')
               + ('' if closes in youtube_lead else f' Comments close {closes}.') + f' {url}')
    return {'document_number': d['document_number'], 'url': url, 'x': fit(make, X_LIMIT, X_LINK),
            'bluesky': fit(make, BLUESKY_LIMIT), 'long': long_text, 'youtube': youtube}

def pick(day, open_rules, counts, recent):
    rules = [d for d in open_rules if not routine(d) and (d.get('comments_close_on') or '') >= day]
    earlier = [k for k in sorted(counts) if k < day]
    before = counts[earlier[-1]] if earlier else {}
    def rise(d):
        now, then = d.get('comments_count') or 0, before.get(d['document_number'])
        return (now - then if then is not None else 0, now)
    fresh = [d for d in rules if d['document_number'] not in recent and d.get('comments_count')]
    trending = max(fresh, key=rise, default=None)
    soon = (date.fromisoformat(day) + timedelta(days=2)).isoformat()
    closing = [d for d in rules if d['comments_close_on'] <= soon and d is not trending]
    deadline = max(closing, key=lambda d: d.get('comments_count') or 0, default=None)
    return trending, rise(trending)[0] if trending else 0, deadline

def build(day=None):
    day = day or today()
    previous = load('social.json', {})
    # earlier days only: a rerun later the same day must not skip that day's own pick
    recent = [n for p in previous.get('history', []) if (date.fromisoformat(day) - timedelta(days=3)).isoformat() <= p['date'] < day
              for n in p.get('trending', [])]
    trending, gained, deadline = pick(day, load('open_rules.json', {}).get('documents', []), load('comment_counts.json', {}), recent)
    posts = []
    if trending:
        lead = (f'📈 Gaining public comments ({gained:+,} since yesterday):' if gained > 0 else '📈 Among the most-commented rules open now:')
        youtube_lead = f'📈 Gaining comments ({gained:+,} since yesterday):' if gained > 0 else '📈 Most-commented:'
        posts.append({'kind': 'trending', **rule_post(trending, lead, day, youtube_lead)})
    if deadline:
        when = 'today' if deadline['comments_close_on'] == day else 'tomorrow' if deadline['comments_close_on'] == (date.fromisoformat(day) + timedelta(days=1)).isoformat() else 'soon'
        posts.append({'kind': 'deadline', **rule_post(deadline, f'⏰ Comment period closes {when}:', day,
                                                      f'⏰ Closing {short_date(deadline["comments_close_on"])}:')})
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=36)).isoformat()
    for v in load('videos.json', {}).get('videos', [])[:3]:
        if v.get('published', '') >= cutoff:
            url = f'{SITE}/videos/{v["id"]}/'
            text = f'🎥 New: {v["title"]}. Watch with the transcript and sources: {url}'
            posts.append({'kind': 'video', 'url': url, 'x': text, 'bluesky': text, 'long': text,
                          'youtube': f'🎥 New video: {v["title"]} https://youtu.be/{v["id"]}'})
            break
    for p in posts:
        p['x_length'] = x_length(p['x'])
    # one combined channel post: YouTube has no API for channel posts, so this one is pasted by hand
    blank = "\n\n"
    youtube = ("Today's federal rules to watch 🗳" + blank + blank.join(p["youtube"] for p in posts)
               + f"{blank}Every rule open for comment, by deadline: {SITE}/rules/") if posts else ""
    history = [p for p in previous.get('history', []) if p['date'] != day][-30:]
    history.append({'date': day, 'trending': [trending['document_number']] if trending else []})
    out = {'date': day, 'generated_at': datetime.now(timezone.utc).isoformat(), 'posts': posts, 'youtube': youtube,
           'posted': previous.get('posted', {}) if previous.get('date') == day else {}, 'history': history}
    (DATA / 'social.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Social desk: {len(posts)} posts for {day}')
    return out

if __name__ == '__main__':
    build()
