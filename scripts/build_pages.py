"""Build static, crawlable pages from the data snapshots: one per video, one per rule open for comment,
two index pages and sitemap.xml. Usage: python scripts/build_pages.py _site"""
import html, json, re, sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
SITE = 'https://fedregintel.com'
BOOK = 'https://www.amazon.com/dp/B0HL97PYTB'
CSS = '/assets/site.css?v=pages-20261003'
VIDEO_ID = re.compile(r'^[A-Za-z0-9_-]{11}$')
DOC_NUMBER = re.compile(r'^[A-Za-z0-9-]{1,40}$')
LINK = re.compile(r'https?://[^\s<>"]+')
esc = lambda s: html.escape(str(s or ''), quote=True)

def today():
    return datetime.now(ZoneInfo('America/New_York')).date().isoformat()

def long_date(s):
    if not s: return 'Not specified'
    d = datetime.fromisoformat(s[:10])
    return f'{d:%B} {d.day}, {d.year}'

def load(name, default):
    try: return json.loads((DATA / name).read_text(encoding='utf-8'))
    except (OSError, ValueError): return default

def snippet(text, limit=155):
    text = ' '.join(str(text or '').split())
    return text if len(text) <= limit else text[:limit - 1].rsplit(' ', 1)[0] + '…'

def linkify(text):
    """Escape plain text, then turn bare URLs into links (trailing punctuation stays outside the link)."""
    out, last = [], 0
    for m in LINK.finditer(text):
        address = m.group(0).rstrip('.,;:!?)')
        out += [esc(text[last:m.start()]), f'<a href="{esc(address)}" rel="noopener">{esc(address)}</a>']
        last = m.start() + len(address)
    return ''.join(out + [esc(text[last:])])

def ld_json(data):
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace('<', '\\u003c') + '</script>'

def page(path, title, description, body, structured=None):
    canonical = SITE + path
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(description)}"><meta name="theme-color" content="#102f35"><link rel="canonical" href="{esc(canonical)}"><meta property="og:type" content="website"><meta property="og:site_name" content="FedReg Intel"><meta property="og:url" content="{esc(canonical)}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta name="twitter:card" content="summary_large_image"><link rel="stylesheet" href="{CSS}">{ld_json(structured) if structured else ''}</head>
<body><header><div class="shell nav"><a class="brand" href="/"><span class="brand-mark" aria-hidden="true">F<span>R</span></span><span>FEDREG <b>INTEL</b><small>THE PUBLIC PARTICIPATION BRIEF</small></span></a><nav aria-label="Main navigation"><a href="/rules/">Open for comment</a><a href="/videos/">Video briefings</a><a href="/#book">The book</a><a href="/#newsletter">Email list</a><a class="nav-cta" href="https://www.youtube.com/@FedRegIntel?sub_confirmation=1" target="_blank" rel="noopener">Subscribe ↗</a></nav></div></header>
<main class="shell static-page">{body}</main>
<footer class="shell"><a class="footer-brand" href="/">FEDREG INTEL</a><p>Independent educational coverage. Not a government website or legal advice. Verify information against the official publication on <a href="https://www.govinfo.gov/">GovInfo</a>.</p><div><a href="/privacy.html">Privacy policy</a><a href="https://www.youtube.com/@FedRegIntel">YouTube</a><a href="mailto:hello@fedregintel.com">Contact</a></div></footer>
</body></html>
'''

def write(out, path, text):
    target = out / path.strip('/') / 'index.html'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding='utf-8')

def series(title):
    return 'RULEMAKING 101' if re.search('rulemaking 101', title, re.I) else 'DAILY BRIEFING'

def video_card(v):
    return (f'<article class="video-card"><a class="video-image" href="/videos/{v["id"]}/"><img src="https://i.ytimg.com/vi/{v["id"]}/hqdefault.jpg" alt="" loading="lazy" width="480" height="270"><span class="play-icon" aria-hidden="true">▶</span></a>'
            f'<div class="video-body"><p><span>{series(v["title"])}</span><time datetime="{esc(v["published"])}">{esc(long_date(v["published"]))}</time></p><h3><a href="/videos/{v["id"]}/">{esc(v["title"])}</a></h3></div></article>')

def build_videos(out, videos):
    urls = []
    for v in videos:
        path = f'/videos/{v["id"]}/'
        about = v.get('description') or ''
        body = (f'<p class="crumbs"><a href="/">Home</a> / <a href="/videos/">Videos</a></p><p class="eyebrow">{series(v["title"])} · {esc(long_date(v["published"]))}</p><h1 class="page-title">{esc(v["title"])}</h1>'
                f'<div class="embed"><iframe src="https://www.youtube-nocookie.com/embed/{v["id"]}" title="{esc(v["title"])}" loading="lazy" allow="accelerometer; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div>'
                f'<p class="rule-links"><a href="https://www.youtube.com/watch?v={v["id"]}" target="_blank" rel="noopener">Watch on YouTube ↗</a><a href="/rules/">Rules open for comment →</a></p>'
                + (f'<div class="description">{linkify(about)}</div>' if about else '')
                + f'<p class="aside-note">Want the full method? <a href="{BOOK}" target="_blank" rel="noopener"><em>How to Comment on Federal Rules</em></a> walks through finding a proposal and writing a comment that counts.</p>')
        structured = {'@context': 'https://schema.org', '@type': 'VideoObject', 'name': v['title'],
                      'description': snippet(about, 500) or v['title'], 'thumbnailUrl': f'https://i.ytimg.com/vi/{v["id"]}/hqdefault.jpg',
                      'uploadDate': v['published'], 'embedUrl': f'https://www.youtube.com/embed/{v["id"]}',
                      'url': SITE + path, 'publisher': {'@type': 'Organization', 'name': 'FedReg Intel', 'url': SITE + '/'}}
        write(out, path, page(path, f'{v["title"]} | FedReg Intel' if 'FedReg Intel' not in v['title'] else v['title'],
                              snippet(about) or f'FedReg Intel video: {v["title"]}', body, structured))
        urls.append((path, v['published'][:10]))
    body = ('<p class="crumbs"><a href="/">Home</a> / Videos</p><p class="eyebrow">THE VIDEO BRIEFING ROOM</p><h1 class="page-title">Every FedReg Intel video</h1>'
            '<p class="section-intro">Federal Rules Open for Comment briefings and Rulemaking 101 explainers, newest first.</p>'
            f'<div class="video-grid">{"".join(video_card(v) for v in videos)}</div>')
    write(out, '/videos/', page('/videos/', 'Federal Register Video Briefings and Rulemaking 101 | FedReg Intel',
                                'Plain-English video briefings on federal rules open for public comment, plus Rulemaking 101 explainers on how federal rulemaking works.', body))
    return urls

def agencies(d):
    return ' / '.join(a.get('name') or a.get('raw_name') or '' for a in d.get('agencies') or [] if a.get('name') or a.get('raw_name'))

def build_rules(out, rules, day):
    urls = []
    for d in rules:
        path = f'/rules/{d["document_number"]}/'
        kind = 'Final rule' if d.get('type') == 'Rule' else 'Proposed rule'
        due = long_date(d['comments_close_on'])
        links = [f'<a href="{esc(d["html_url"])}" target="_blank" rel="noopener">Read on FederalRegister.gov ↗</a>' if d.get('html_url') else '',
                 f'<a href="{esc(d["pdf_url"])}" target="_blank" rel="noopener">Official PDF ↗</a>' if d.get('pdf_url') else '',
                 f'<a href="{esc(d["comment_url"])}" target="_blank" rel="noopener">Comment on Regulations.gov ↗</a>' if d.get('comment_url') else '']
        body = (f'<p class="crumbs"><a href="/">Home</a> / <a href="/rules/">Open for comment</a></p><article class="rule"><div class="badges"><span class="badge {"final" if kind == "Final rule" else ""}">{kind.upper()}</span><span class="badge deadline">COMMENTS DUE {esc(due.upper())}</span></div>'
                f'<h1 class="page-title">{esc(d["title"])}</h1><p class="agency-name">{esc(agencies(d))}</p>'
                + (f'<p class="abstract">{esc(d["abstract"])}</p>' if d.get('abstract') else '')
                + f'<div class="rule-meta"><span>Published {esc(long_date(d.get("publication_date")))}</span><span>Document {esc(d["document_number"])}</span>{f"<span>Effective {esc(long_date(d["effective_on"]))}</span>" if d.get("effective_on") else ""}</div>'
                f'<div class="rule-links">{"".join(links)}</div></article>'
                f'<div class="aside-note"><h2>How to comment</h2><p>Comments are due <strong>{esc(due)}</strong>. Submit through the link above or follow the instructions in the document\'s ADDRESSES section. Say who you are, how the rule affects you, and what should change, with evidence. Comments are usually public, so leave out anything private.</p>'
                f'<p>New to this? Watch <a href="/videos/">Rulemaking 101</a> or read <a href="{BOOK}" target="_blank" rel="noopener"><em>How to Comment on Federal Rules</em></a>.</p></div>'
                f'<p class="source-note">From the Federal Register as of {esc(long_date(day))}. Deadlines can change; the official document governs. Not legal advice.</p>')
        description = f'{kind}, comments due {due}. ' + snippet(d.get('abstract') or d['title'], 120)
        write(out, path, page(path, f'Comment by {due}: {snippet(d["title"], 80)} | FedReg Intel', description, body))
        urls.append((path, (d.get('publication_date') or day)[:10]))
    week = [d for d in rules if d['comments_close_on'] <= week_out(day)]
    later = [d for d in rules if d['comments_close_on'] > week_out(day)]
    item = lambda d: (f'<li class="closing-item"><small>Due {esc(long_date(d["comments_close_on"]))} · {esc(agencies(d))}</small>'
                      f'<a href="/rules/{d["document_number"]}/">{esc(d["title"])}</a></li>')
    section = lambda title, docs: f'<h2>{title} ({len(docs)})</h2><ul class="rule-index">{"".join(map(item, docs))}</ul>' if docs else ''
    body = ('<p class="crumbs"><a href="/">Home</a> / Open for comment</p><p class="eyebrow">THE RULEMAKING DESK</p><h1 class="page-title">Federal rules open for public comment</h1>'
            f'<p class="section-intro">{len(rules)} rules and proposed rules in the Federal Register are accepting public comments as of {esc(long_date(day))}, soonest deadline first. Updated daily.</p>'
            + (section('Closing in the next 7 days', week) + section('Closing later', later) if rules else '<p class="empty">No open comment periods in the current snapshot. Check FederalRegister.gov directly.</p>'))
    write(out, '/rules/', page('/rules/', 'Federal Rules Open for Public Comment, by Deadline | FedReg Intel',
                               f'{len(rules)} federal rules and proposed rules open for public comment, sorted by deadline, with links to comment on Regulations.gov. Updated daily.', body))
    return urls

def week_out(day):
    return (date.fromisoformat(day) + timedelta(days=7)).isoformat()

def sitemap(out, entries):
    rows = ''.join(f'  <url><loc>{esc(SITE + p)}</loc>{f"<lastmod>{m}</lastmod>" if m else ""}</url>\n' for p, m in entries)
    (out / 'sitemap.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{rows}</urlset>\n', encoding='utf-8')

def build(out, day=None):
    day = day or today()
    out = Path(out)
    videos = [v for v in load('videos.json', {}).get('videos', []) if VIDEO_ID.match(v.get('id') or '') and v.get('title') and v.get('published')]
    rules = sorted((d for d in load('open_rules.json', {}).get('documents', [])
                    if DOC_NUMBER.match(d.get('document_number') or '') and d.get('title') and (d.get('comments_close_on') or '') >= day),
                   key=lambda d: (d['comments_close_on'], d['title']))
    entries = [('/', day), ('/rules/', day), ('/videos/', day), ('/privacy.html', None)]
    entries += build_rules(out, rules, day) + build_videos(out, videos)
    sitemap(out, entries)
    print(f'Built {len(rules)} rule pages and {len(videos)} video pages')
    return len(rules), len(videos)

if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else '_site')
