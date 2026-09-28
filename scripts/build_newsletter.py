"""Build provider-neutral email drafts from the public video archive. Never sends mail."""
import argparse
import calendar
import json
from datetime import datetime
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://fedregintel.com/'
BOOK = 'https://www.amazon.com/dp/B0HL97PYTB'

def month_videos(videos, month):
    datetime.strptime(month, '%Y-%m')
    return sorted([v for v in videos if datetime.fromisoformat(v['published'].replace('Z', '+00:00')).astimezone(ZoneInfo('America/New_York')).strftime('%Y-%m') == month], key=lambda v: v['published'], reverse=True)

def render(title, paragraphs, links):
    body = ''.join('<p style="line-height:1.7">'+escape(p)+'</p>' for p in paragraphs)
    body += ''.join('<p><a style="color:#236b57" href="'+escape(url, quote=True)+'">'+escape(label)+'</a></p>' for label, url in links)
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><body style="margin:0;background:#f7f8f3;font-family:Arial,sans-serif;color:#14363a"><div style="max-width:600px;margin:auto;padding:32px"><p style="letter-spacing:2px">FEDREG INTEL · THE MONTHLY BRIEF</p><h1>'+escape(title)+'</h1>'+body+'<hr><p style="font-size:12px">You subscribed to FedReg Intel updates and book promotions. Independent educational coverage, not legal advice.</p><p style="font-size:12px">{{MAILING_ADDRESS}}<br><a href="{{UNSUBSCRIBE_URL}}">Unsubscribe</a></p></div></body></html>'

def build(month, output):
    archive = json.loads((ROOT/'data/videos.json').read_text(encoding='utf-8'))
    videos = month_videos(archive['videos'], month)
    dt = datetime.strptime(month, '%Y-%m')
    label = calendar.month_name[dt.month]+' '+str(dt.year)
    output.mkdir(parents=True, exist_ok=True)
    welcome = [
        'Thanks for joining FedReg Intel. Federal decisions shape everyday life, and understanding the process makes it easier to participate.',
        'Once a month, we’ll send a roundup of our published videos, practical ways to follow federal rulemaking, and news about our books. You can unsubscribe at any time.',
        'Start with the rule dashboard: search a topic you care about, check the comment deadline, and read the official document. Our video archive offers briefings and explainers to help you get oriented.',
        'Want a step-by-step companion? How to Comment on Federal Rules by Jarrett Paul Dudley walks through finding proposals and writing a clear, useful comment. The link below is a promotion for our book.',
        'Have a topic you’d like us to cover? Reply to this email. — Jarrett Paul Dudley, FedReg Intel']
    common = [('Explore the rule dashboard', SITE+'#rules'), ('Watch FedReg Intel', SITE+'#videos'), ('Buy How to Comment on Federal Rules on Amazon', BOOK)]
    monthly = [f'Here’s what we published in {label}: {len(videos)} videos in the FedReg Intel public archive.',
        'Catch up on the episodes below, then visit the dashboard to find current proposals and comment deadlines. An older episode’s deadline may have passed; always check the official source.',
        'Build your commenting skills with How to Comment on Federal Rules by Jarrett Paul Dudley. This book promotion supports our work and gives you a practical guide to participating in the process. Pricing and available editions are listed on Amazon.']
    if not videos:
        monthly[0] = f'No videos published in {label} are currently indexed in our archive. You can still explore previous episodes and the live rule dashboard.'
    for name, title, paras, links in [('welcome', 'Welcome to FedReg Intel', welcome, common), ('monthly-'+month, label+' · Your FedReg Intel roundup', monthly, [(v['title'],v['url']) for v in videos]+common)]:
        (output/(name+'.html')).write_text(render(title,paras,links),encoding='utf-8')
        (output/(name+'.txt')).write_text(title+'\n\n'+'\n\n'.join(paras)+'\n\n'+'\n'.join(t+': '+u for t,u in links)+'\n\nYou subscribed to FedReg Intel updates and book promotions.\n{{MAILING_ADDRESS}}\nUnsubscribe: {{UNSUBSCRIBE_URL}}\n',encoding='utf-8')
    print(f'Built welcome and {month} draft with {len(videos)} videos; no emails sent.')

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--month', required=True, help='Completed month, YYYY-MM')
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args()
    build(args.month,args.output)
