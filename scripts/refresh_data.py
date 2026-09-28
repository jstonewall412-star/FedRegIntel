"""Public feeds only. No YouTube credentials, API keys, or paid services required."""
import json, sys, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
CHANNEL = 'UC9VwALJt5kVlHWQ0rRV1LOg'
FIELDS = ['title','type','abstract','document_number','html_url','pdf_url','publication_date','agencies','comments_close_on','comment_url','effective_on']
def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent':'FedRegIntel/1.0 (+https://fedregintel.com)'})
    with urllib.request.urlopen(request, timeout=45) as response: return response.read()
def save(name,data):
    target=DATA/name
    temp=target.with_suffix('.tmp')
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    temp.replace(target)
def fr(conditions=None, count=100):
    params=[('per_page',str(count)),('order','newest')]+[('fields[]',f) for f in FIELDS]
    params+=conditions or []
    return json.loads(fetch('https://www.federalregister.gov/api/v1/documents.json?'+urllib.parse.urlencode(params)))
def refresh_rules():
    now=datetime.now(timezone.utc)
    day=now.astimezone(ZoneInfo('America/New_York')).date()
    types=[('conditions[type][]','RULE'),('conditions[type][]','PRORULE')]
    recent=fr(types)
    latest=recent['results'][0]['publication_date']
    issue=fr(types+[('conditions[publication_date][is]',latest)],1)
    closing=fr(types+[('conditions[comment_date][gte]',day.isoformat()),('conditions[comment_date][lte]',(day+timedelta(days=7)).isoformat())],1000)
    documents={d['document_number']:d for d in recent['results']+closing['results']}
    save('rules.json',dict(updated_at=now.isoformat(),latest_date=latest,issue_count=issue['count'],documents=list(documents.values())))
    print('Saved',len(documents),'rule records')
def refresh_videos():
    path=DATA/'videos.json'
    old=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'videos':[]}
    archive={v['id']:v for v in old['videos']}
    feed=ET.fromstring(fetch('https://www.youtube.com/feeds/videos.xml?channel_id='+CHANNEL))
    ns={'a':'http://www.w3.org/2005/Atom','yt':'http://www.youtube.com/xml/schemas/2015','m':'http://search.yahoo.com/mrss/'}
    if feed.findtext('yt:channelId',namespaces=ns) not in (CHANNEL, CHANNEL[2:]): raise ValueError('Unexpected YouTube channel')
    for entry in feed.findall('a:entry',ns):
        video_id=entry.findtext('yt:videoId',namespaces=ns)
        thumb=entry.find('m:group/m:thumbnail',ns)
        archive[video_id]={**archive.get(video_id,{}),'id':video_id,'title':entry.findtext('a:title',namespaces=ns),'published':entry.findtext('a:published',namespaces=ns),'url':'https://www.youtube.com/watch?v='+video_id,'thumbnail':thumb.attrib['url'] if thumb is not None else 'https://i.ytimg.com/vi/'+video_id+'/hqdefault.jpg'}
    save('videos.json',dict(channel_id=CHANNEL,channel_url='https://www.youtube.com/@FedRegIntel',updated_at=datetime.now(timezone.utc).isoformat(),videos=sorted(archive.values(),key=lambda x:x['published'],reverse=True)))
    print('Saved',len(archive),'public video records')
if __name__=='__main__':
    DATA.mkdir(exist_ok=True)
    failures=[]
    for task in [refresh_rules,refresh_videos]:
        try: task()
        except Exception as exc:
            failures.append(task.__name__)
            print(task.__name__+' failed; keeping its last successful snapshot: '+str(exc),file=sys.stderr)
    if failures: sys.exit(1)
