import importlib.util, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('refresh',Path(__file__).parents[1]/'scripts/refresh_data.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ArchiveTests(unittest.TestCase):
    def test_temporary_youtube_404_retries_then_recovers(self):
        from urllib.error import HTTPError
        from unittest.mock import MagicMock
        response=MagicMock()
        response.__enter__.return_value.read.return_value=b'feed'
        error=HTTPError('https://www.youtube.com/feeds/videos.xml',404,'Not Found',{},None)
        with patch.object(m.urllib.request,'urlopen',side_effect=[error,response]) as request, patch.object(m.time,'sleep') as sleep:
            self.assertEqual(m.fetch(error.url),b'feed')
            self.assertEqual(request.call_count,2)
            sleep.assert_called_once_with(5)

    def test_retries_are_bounded(self):
        with patch.object(m.urllib.request,'urlopen',side_effect=TimeoutError) as request, patch.object(m.time,'sleep'):
            with self.assertRaises(TimeoutError): m.fetch('https://www.youtube.com/feeds/videos.xml')
            self.assertEqual(request.call_count,4)

    def test_snapshot_grace_expires_and_does_not_change_timestamp(self):
        with tempfile.TemporaryDirectory() as folder:
            data=Path(folder); p=data/'videos.json'
            for hours, expected in [(24,True),(37,False)]:
                original=json.dumps({'channel_id':m.CHANNEL,'videos':[{'id':'old'}], 'updated_at':(m.datetime.now(m.timezone.utc)-m.timedelta(hours=hours)).isoformat()})
                p.write_text(original)
                with patch.object(m,'DATA',data): self.assertEqual(m.recent_video_snapshot(),expected)
                self.assertEqual(p.read_text(),original)
    def test_merge_retains_old_video_and_updates_existing(self):
        with tempfile.TemporaryDirectory() as folder:
            data=Path(folder)
            (data/'videos.json').write_text(json.dumps({'videos':[{'id':'old','title':'Old','published':'2026-01-01'},{'id':'new','title':'Before','published':'2026-02-01','duration':'PT1M'}]}))
            feed=f'''<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015"><yt:channelId>{m.CHANNEL[2:]}</yt:channelId><entry><yt:videoId>new</yt:videoId><title>Updated &amp; correct</title><published>2026-02-01</published></entry></feed>'''.encode()
            with patch.object(m,'DATA',data),patch.object(m,'fetch',return_value=feed): m.refresh_videos()
            videos=json.loads((data/'videos.json').read_text())['videos']
            self.assertEqual([v['id'] for v in videos],['new','old'])
            self.assertEqual(videos[0]['title'],'Updated & correct')
            self.assertEqual(videos[0]['duration'],'PT1M')
    def test_wrong_channel_does_not_overwrite_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            data=Path(folder); p=data/'videos.json';original='{"videos": []}';p.write_text(original)
            with patch.object(m,'DATA',data),patch.object(m,'fetch',return_value=b'<feed/>'):
                with self.assertRaises(ValueError): m.refresh_videos()
            self.assertEqual(p.read_text(),original)
    def test_outage_does_not_overwrite_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            data=Path(folder);p=data/'videos.json';original='{"videos": []}';p.write_text(original)
            with patch.object(m,'DATA',data),patch.object(m,'fetch',side_effect=TimeoutError):
                with self.assertRaises(TimeoutError): m.refresh_videos()
            self.assertEqual(p.read_text(),original)
class RuleArchiveTests(unittest.TestCase):
    def test_remember_skips_routine_and_keeps_first_seen(self):
        archive={'2026-1':{'document_number':'2026-1','title':'Old title','first_seen':'2026-09-01','final_checked':'2026-09-30'}}
        m.remember(archive,[{'document_number':'2026-1','title':'New title'},{'document_number':'2026-2','title':'Safety Zone; Port of Miami'}],'2026-10-03')
        self.assertEqual(list(archive),['2026-1'])
        self.assertEqual((archive['2026-1']['title'],archive['2026-1']['first_seen'],archive['2026-1']['final_checked']),('New title','2026-09-01','2026-09-30'))
    def test_final_rule_is_earliest_later_rule_and_checks_are_weekly(self):
        proposal=lambda **x:{'type':'Proposed Rule','comments_close_on':'2026-09-01','publication_date':'2026-07-01','regulation_id_numbers':['1234-AB56'],**x}
        archive={'a':proposal(),'b':proposal(final_checked='2026-10-01'),'c':proposal(comments_close_on='2026-11-01')}
        results={'count':3,'results':[{'title':'Final','document_number':'2026-9','html_url':'u','publication_date':'2026-09-20'},
                            {'title':'Later fix','document_number':'2026-10','html_url':'v','publication_date':'2026-09-25'},
                            {'title':'Before comments closed','document_number':'2026-7','html_url':'w','publication_date':'2026-08-15'}]}
        with patch.object(m,'fr',return_value=results) as fr:
            self.assertEqual(m.find_final_rules(archive,'2026-10-03'),1)
        fr.assert_called_once()
        self.assertEqual(archive['a']['final_rule']['document_number'],'2026-9')
        self.assertEqual(archive['a']['final_checked'],'2026-10-03')
        self.assertNotIn('final_rule',archive['b']); self.assertNotIn('final_rule',archive['c'])
    def test_catch_all_rin_is_ignored(self):
        archive={'a':{'type':'Proposed Rule','comments_close_on':'2026-09-01','publication_date':'2026-07-01','regulation_id_numbers':['2120-AA66']}}
        with patch.object(m,'fr',return_value={'count':400,'results':[{'title':'Other airspace','publication_date':'2026-09-20'}]}):
            self.assertEqual(m.find_final_rules(archive,'2026-10-03'),0)
        self.assertEqual(archive['a']['final_checked'],'2026-10-03')
    def test_lookup_outage_keeps_what_it_has(self):
        archive={'a':{'type':'Proposed Rule','comments_close_on':'2026-09-01','publication_date':'2026-07-01','regulation_id_numbers':['1']}}
        with patch.object(m,'fr',side_effect=TimeoutError):
            self.assertEqual(m.find_final_rules(archive,'2026-10-03'),0)
        self.assertNotIn('final_checked',archive['a'])
if __name__=='__main__': unittest.main()
