"""Build static, crawlable pages from the data snapshots: one per video (with its transcript), one per
rule we have listed for comment (open or closed), the index pages and sitemap.xml.
Usage: python scripts/build_pages.py _site"""
import html, json, re, sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
SITE = 'https://fedregintel.com'
BOOK = 'https://www.amazon.com/dp/B0HL97PYTB'
CSS = '/assets/site.css?v=pages-20261009'
VIDEO_ID = re.compile(r'^[A-Za-z0-9_-]{11}$')
DOC_NUMBER = re.compile(r'^[A-Za-z0-9-]{1,40}$')
LINK = re.compile(r'https?://[^\s<>"]+')
esc = lambda s: html.escape(str(s or ''), quote=True)
# Narrow technical items (one aircraft model, one bridge, one state plan) get no page; same list as the
# show's register_script.py ROUTINE, so the site and the show leave out the same things.
ROUTINE = ('Airworthiness Directives', 'Safety Zone', 'Drawbridge Operation', 'Special Local Regulation',
           'Air Plan Approval', 'Approval and Promulgation', 'Establishment of Class', 'Amendment of Class',
           'Modification of Class', 'Revocation of Class', 'Establishment, Modification', 'Anchorage',
           'Pesticide Tolerance', 'Tolerance Exemption', 'Fisheries of the')

def routine(d):
    title = d.get('title') or ''
    return any(title.startswith(r) or f'; {r}' in title for r in ROUTINE)

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

def page(path, title, description, body, structured=None, robots=None):
    canonical = SITE + path
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(description)}"><meta name="theme-color" content="#102f35">{f'<meta name="robots" content="{robots}">' if robots else ''}<link rel="canonical" href="{esc(canonical)}"><meta property="og:type" content="website"><meta property="og:site_name" content="FedReg Intel"><meta property="og:url" content="{esc(canonical)}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta name="twitter:card" content="summary_large_image"><link rel="stylesheet" href="{CSS}">{ld_json(structured) if structured else ''}</head>
<body><header><div class="shell nav"><a class="brand" href="/"><span class="brand-mark" aria-hidden="true">F<span>R</span></span><span>FEDREG <b>INTEL</b><small>THE PUBLIC PARTICIPATION BRIEF</small></span></a><nav aria-label="Main navigation"><a href="/rules/">Open for comment</a><a href="/rules/#closing-this-week">Upcoming deadlines</a><a href="/videos/">Video briefings</a><a href="/#book">The book</a><a href="/#newsletter">Email list</a><a class="nav-cta" href="https://www.youtube.com/@FedRegIntel?sub_confirmation=1" target="_blank" rel="noopener">Subscribe ↗</a></nav></div></header>
<main class="shell static-page">{body}</main>
<footer class="shell"><a class="footer-brand" href="/">FEDREG INTEL</a><p>Independent educational coverage. Not a government website or legal advice. Verify information against the official publication on <a href="https://www.govinfo.gov/">GovInfo</a>.</p><div><a href="/privacy.html">Privacy policy</a><a href="https://www.youtube.com/@FedRegIntel">YouTube</a><a href="https://bsky.app/profile/fedregintel.com" rel="me noopener">Bluesky</a><a href="https://x.com/FedRegIntel" rel="me noopener">X</a><a href="mailto:hello@fedregintel.com">Contact</a></div></footer>
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

def build_videos(out, videos, transcripts, rule_pages):
    urls = []
    for v in videos:
        path = f'/videos/{v["id"]}/'
        about = v.get('description') or ''
        script = transcripts.get(v['id']) or {}
        paragraphs = [p for p in script.get('transcript') or [] if isinstance(p, str) and p.strip()]
        covered = [rule_pages[n] for n in script.get('documents') or [] if n in rule_pages]
        body = (f'<p class="crumbs"><a href="/">Home</a> / <a href="/videos/">Videos</a></p><p class="eyebrow">{series(v["title"])} · {esc(long_date(v["published"]))}</p><h1 class="page-title">{esc(v["title"])}</h1>'
                f'<div class="embed"><iframe src="https://www.youtube-nocookie.com/embed/{v["id"]}" title="{esc(v["title"])}" loading="lazy" allow="accelerometer; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div>'
                f'<p class="rule-links"><a href="https://www.youtube.com/watch?v={v["id"]}" target="_blank" rel="noopener">Watch on YouTube ↗</a><a href="/rules/">Rules open for comment →</a></p>'
                + (f'<div class="description">{linkify(about)}</div>' if about else '')
                + (f'<h2>Rules in this video</h2><ul class="rule-index">{"".join(rule_item(d) for d in covered)}</ul>' if covered else '')
                + (f'<section class="transcript" aria-labelledby="transcript-title"><h2 id="transcript-title">Transcript</h2><p class="muted">Narrated by an AI presenter with a synthetic voice. Check the official documents for current dates and details.</p>'
                   + ''.join(f'<p>{esc(p)}</p>' for p in paragraphs) + '</section>' if paragraphs else '')
                + f'<p class="aside-note">Want the full method? <a href="{BOOK}" target="_blank" rel="noopener"><em>How to Comment on Federal Rules</em></a> walks through finding a proposal and writing a comment that counts.</p>')
        structured = {'@context': 'https://schema.org', '@type': 'VideoObject', 'name': v['title'],
                      'description': snippet(about, 500) or v['title'], 'thumbnailUrl': f'https://i.ytimg.com/vi/{v["id"]}/hqdefault.jpg',
                      'uploadDate': v['published'], 'embedUrl': f'https://www.youtube.com/embed/{v["id"]}',
                      'url': SITE + path, 'publisher': {'@type': 'Organization', 'name': 'FedReg Intel', 'url': SITE + '/'}}
        if paragraphs:
            structured['transcript'] = '\n\n'.join(paragraphs)
        write(out, path, page(path, f'{v["title"]} | FedReg Intel' if 'FedReg Intel' not in v['title'] else v['title'],
                              snippet(about) or f'FedReg Intel video: {v["title"]}', body, structured))
        urls.append((path, v['published']))
    body = ('<p class="crumbs"><a href="/">Home</a> / Videos</p><p class="eyebrow">THE VIDEO BRIEFING ROOM</p><h1 class="page-title">Every FedReg Intel video</h1>'
            '<p class="section-intro">Federal Rules Open for Comment briefings and Rulemaking 101 explainers, newest first.</p>'
            f'<div class="video-grid">{"".join(video_card(v) for v in videos)}</div>')
    write(out, '/videos/', page('/videos/', 'Federal Register Video Briefings and Rulemaking 101 | FedReg Intel',
                                'Plain-English video briefings on federal rules open for public comment, plus Rulemaking 101 explainers on how federal rulemaking works.', body))
    return urls

def agencies(d):
    return ' / '.join(a.get('name') or a.get('raw_name') or '' for a in d.get('agencies') or [] if a.get('name') or a.get('raw_name'))

def rule_item(d, day=None):
    """One line in a rule list. With day, closed rules say so; without it, just the deadline."""
    when = 'Closed' if day and d['comments_close_on'] < day else 'Comments due'
    return (f'<li class="closing-item"><small>{when} {esc(long_date(d["comments_close_on"]))} · {esc(agencies(d))}</small>'
            f'<a href="/rules/{d["document_number"]}/">{esc(d["title"])}</a></li>')

def next_step(d, kind, closes, is_open):
    if is_open:
        return (f'<div class="aside-note"><h2>How to comment</h2><p>Comments are due <strong>{esc(closes)}</strong>. Submit through the link above or follow the instructions in the document\'s ADDRESSES section. Say who you are, how the rule affects you, and what should change, with evidence. Comments are usually public, so leave out anything private.</p>'
                f'<p>New to this? Watch <a href="/videos/">Rulemaking 101</a> or read <a href="{BOOK}" target="_blank" rel="noopener"><em>How to Comment on Federal Rules</em></a>.</p></div>')
    final = d.get('final_rule') or {}
    if final:
        return (f'<div class="aside-note"><h2>Rule published</h2><p>After the comment period, the agency published a rule under the same regulation identifier (RIN) on <strong>{esc(long_date(final.get("publication_date")))}</strong>: '
                f'<a href="{esc(final.get("html_url"))}" target="_blank" rel="noopener">{esc(final.get("title"))} ↗</a>. Read it to see what was decided and how the agency addressed public comments.</p></div>')
    if kind == 'Proposed rule':
        what = ('The agency now reviews the comments. If it goes ahead, it publishes a final rule in the Federal Register that responds to significant comments. '
                'We link it here when it appears.')
    else:
        what = 'This rule is already final; the agency reviews the comments and may revise it in a later document.'
    return (f'<div class="aside-note"><h2>What happens next</h2><p>The comment period closed on <strong>{esc(closes)}</strong>. {what} '
            'See <a href="/rules/">what is open for comment now</a>.</p></div>')

def rule_page(d, day, videos):
    path = f'/rules/{d["document_number"]}/'
    kind = 'Final rule' if d.get('type') == 'Rule' else 'Proposed rule'
    closes = long_date(d['comments_close_on'])
    is_open = d['comments_close_on'] >= day
    links = [f'<a href="{esc(d["html_url"])}" target="_blank" rel="noopener">Read on FederalRegister.gov ↗</a>' if d.get('html_url') else '',
             f'<a href="{esc(d["pdf_url"])}" target="_blank" rel="noopener">Official PDF ↗</a>' if d.get('pdf_url') else '',
             f'<a href="{esc(d["comment_url"])}" target="_blank" rel="noopener">Comment on Regulations.gov ↗</a>' if is_open and d.get('comment_url') else '']
    effective = f'<span>Effective {esc(long_date(d["effective_on"]))}</span>' if d.get('effective_on') else ''
    crumbs = '<a href="/">Home</a> / <a href="/rules/">Open for comment</a>' + ('' if is_open else ' / <a href="/rules/archive/">Closed</a>')
    status = f'<span class="badge deadline">COMMENTS DUE {esc(closes.upper())}</span>' if is_open else f'<span class="badge">COMMENTS CLOSED {esc(closes.upper())}</span>'
    seen = ''.join(f'<li class="closing-item"><a href="/videos/{v["id"]}/">{esc(v["title"])}</a></li>' for v in videos)
    body = (f'<p class="crumbs">{crumbs}</p><article class="rule"><div class="badges"><span class="badge {"final" if kind == "Final rule" else ""}">{kind.upper()}</span>{status}</div>'
            f'<h1 class="page-title">{esc(d["title"])}</h1><p class="agency-name">{esc(agencies(d))}</p>'
            + (f'<p class="abstract">{esc(d["abstract"])}</p>' if d.get('abstract') else '')
            + f'<div class="rule-meta"><span>Published {esc(long_date(d.get("publication_date")))}</span><span>Document {esc(d["document_number"])}</span>{effective}</div>'
            f'<div class="rule-links">{"".join(links)}</div></article>{next_step(d, kind, closes, is_open)}'
            + (f'<h2>Covered in</h2><ul class="rule-index">{seen}</ul>' if seen else '')
            + f'<p class="source-note">From the Federal Register as of {esc(long_date(day))}. Deadlines can change; the official document governs. Not legal advice.</p>')
    if is_open:
        title, lead = f'Comment by {closes}: {snippet(d["title"], 80)} | FedReg Intel', f'{kind}, comments due {closes}. '
    else:
        title, lead = f'{snippet(d["title"], 90)} (comments closed {closes}) | FedReg Intel', f'{kind}; comments closed {closes}. '
    return path, page(path, title, lead + snippet(d.get('abstract') or d['title'], 120), body)

def build_rules(out, rules, day, covered_by):
    urls = []
    for d in rules:
        path, text = rule_page(d, day, covered_by.get(d['document_number'], []))
        write(out, path, text)
        urls.append((path, (d.get('final_rule') or {}).get('publication_date') or d.get('publication_date') or day))
    open_rules = sorted((d for d in rules if d['comments_close_on'] >= day), key=lambda d: (d['comments_close_on'], d['title']))
    closed = sorted((d for d in rules if d['comments_close_on'] < day), key=lambda d: (d['comments_close_on'], d['title']), reverse=True)
    month_ago = (date.fromisoformat(day) - timedelta(days=30)).isoformat()
    recent = [d for d in closed if d['comments_close_on'] >= month_ago]
    week = [d for d in open_rules if d['comments_close_on'] <= week_out(day)]
    later = [d for d in open_rules if d['comments_close_on'] > week_out(day)]
    def section(title, docs, anchor=""):
        attribute = f' id="{anchor}"' if anchor else ""
        return f'<h2{attribute}>{title} ({len(docs)})</h2><ul class="rule-index">{"".join(rule_item(d, day) for d in docs)}</ul>' if docs else ''
    body = ('<p class="crumbs"><a href="/">Home</a> / Open for comment</p><p class="eyebrow">THE RULEMAKING DESK</p><h1 class="page-title">Federal rules open for public comment</h1>'
            f'<p class="section-intro">{len(open_rules)} rules and proposed rules in the Federal Register are accepting public comments as of {esc(long_date(day))}, soonest deadline first. Updated daily. Narrow technical items, such as airworthiness directives and single-site safety zones, are left out; <a href="https://www.federalregister.gov/documents/search">search FederalRegister.gov</a> for those.</p>'
            + (section('Closing in the next 7 days', week, 'closing-this-week') + section('Closing later', later) if open_rules else '<p class="empty">No open comment periods in the current snapshot. Check FederalRegister.gov directly.</p>')
            + section('Closed in the last 30 days', recent)
            + (f'<p><a class="text-link" href="/rules/archive/">All {len(closed)} closed comment periods →</a></p>' if closed else ''))
    write(out, '/rules/', page('/rules/', 'Federal Rules Open for Public Comment, by Deadline | FedReg Intel',
                               f'{len(open_rules)} federal rules and proposed rules open for public comment, sorted by deadline, with links to comment on Regulations.gov. Updated daily.', body))
    body = ('<p class="crumbs"><a href="/">Home</a> / <a href="/rules/">Open for comment</a> / Closed</p><p class="eyebrow">THE RULEMAKING DESK</p><h1 class="page-title">Closed comment periods</h1>'
            '<p class="section-intro">Federal rules whose public comment periods have ended, most recent first. Each page links the final rule once the agency publishes it.</p>'
            + (f'<ul class="rule-index">{"".join(rule_item(d, day) for d in closed)}</ul>' if closed else '<p class="empty">None yet.</p>'))
    write(out, '/rules/archive/', page('/rules/archive/', 'Closed Federal Comment Periods and Final Rules | FedReg Intel',
                                       'Federal rules whose public comment periods have closed, with links to the final rule when the agency publishes one.', body))
    return urls + [('/rules/archive/', day)]

def week_out(day):
    return (date.fromisoformat(day) + timedelta(days=7)).isoformat()

def sitemap(out, entries):
    rows = ''.join(f'  <url><loc>{esc(SITE + p)}</loc>{f"<lastmod>{m[:10]}</lastmod>" if m else ""}</url>\n' for p, m in entries)
    (out / 'sitemap.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{rows}</urlset>\n', encoding='utf-8')

def build_social_page(out, day):
    """Today's ready-to-paste posts (data/social.json) with copy buttons. Kept out of search and the sitemap."""
    social = load('social.json', {})
    labels = {'trending': 'Trending rule', 'deadline': 'Closing soon', 'video': 'New video'}
    def box(label, text, limit, length=None, rows=5):
        return (f'<label class="social-box"><span>{label} <small>{length if length is not None else len(text)} characters (limit {limit})</small></span>'
                f'<textarea readonly rows="{rows}">{esc(text)}</textarea><button type="button" class="secondary" data-copy>Copy</button></label>')
    cards = ''.join(f'<section class="aside-note"><h2>{labels.get(p["kind"], p["kind"])}</h2>'
                    + box('X / Threads', p['x'], 280, p.get('x_length')) + box('Bluesky', p['bluesky'], 300) + box('LinkedIn / Facebook', p['long'], 3000)
                    + '</section>' for p in social.get('posts', []))
    if social.get('youtube'):
        cards = ('<section class="aside-note"><h2>YouTube channel post (all picks)</h2>'
                 '<p>Paste into YouTube Studio, then Create, then Create post. YouTube has no API for channel posts.</p>'
                 + box('YouTube', social['youtube'], 5000, rows=12) + '</section>') + cards
    body = ('<p class="crumbs"><a href="/">Home</a> / Social desk</p><p class="eyebrow">SOCIAL DESK</p><h1 class="page-title">Today&#39;s posts</h1>'
            f'<p class="section-intro">Generated {esc(long_date(social.get("date")))} from the Federal Register and Regulations.gov comment counts. '
            'Check the deadline on the linked page before posting.</p>'
            + (cards or '<p class="empty">No posts today.</p>')
            + '<script>document.addEventListener("click",e=>{const b=e.target.closest("[data-copy]");if(!b)return;'
              'const t=b.previousElementSibling;t.select();navigator.clipboard?.writeText(t.value);b.textContent="Copied";'
              'setTimeout(()=>b.textContent="Copy",1500);});</script>')
    write(out, '/social/', page('/social/', 'Social desk | FedReg Intel', 'Daily posts about federal rules open for comment.', body, robots='noindex'))

def build(out, day=None):
    day = day or today()
    out = Path(out)
    videos = [v for v in load('videos.json', {}).get('videos', []) if VIDEO_ID.match(v.get('id') or '') and v.get('title') and v.get('published')]
    transcripts = load('transcripts.json', {}).get('videos', {})
    # The archive keeps every rule we have listed; the current open snapshot wins for anything in both.
    merged = {**load('rules_archive.json', {}).get('documents', {}),
              **{d.get('document_number'): d for d in load('open_rules.json', {}).get('documents', [])}}
    rules = [d for n, d in merged.items() if DOC_NUMBER.match(n or '') and d.get('title') and d.get('comments_close_on') and not routine(d)]
    by_number = {d['document_number']: d for d in rules}
    covered_by = {}
    for v in videos:
        for n in (transcripts.get(v['id']) or {}).get('documents') or []:
            if n in by_number:
                covered_by.setdefault(n, []).append(v)
    entries = [('/', day), ('/rules/', day), ('/videos/', day), ('/privacy.html', None)]
    entries += build_rules(out, rules, day, covered_by) + build_videos(out, videos, transcripts, by_number)
    sitemap(out, entries)
    build_social_page(out, day)
    open_count = sum(d['comments_close_on'] >= day for d in rules)
    print(f'Built {len(rules)} rule pages ({open_count} open) and {len(videos)} video pages '
          f'({sum(v["id"] in transcripts for v in videos)} with transcripts)')
    return open_count, len(videos)

if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else '_site')
