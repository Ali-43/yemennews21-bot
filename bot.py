import tweepy, requests, xml.etree.ElementTree as ET, time, re, html, os

API_KEY = os.environ.get("API_KEY") or "gDzUbGcMq8TDWUnw83qbHEUdT"
API_SECRET = os.environ.get("API_SECRET") or "rYBhwjDoGMhferwimOsLDYZ1xDQDSbxW4NgoYKxV12xDDFx1Pv"
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN") or "1692150311152943104-VinbTyLsn0PaILLgFW60H9BeHuNcm7"
ACCESS_SECRET = os.environ.get("ACCESS_SECRET") or "N6fAyyJcQAi1cyCqn4QwUD1Hz3aKLQN3Y0bnQQmh5tr2S"
BOT_TOKEN = os.environ.get("BOT_TOKEN") or "8803193784:AAFTeZN_m6FSkLk9RoFoQ3MYJBEVvzacGaU"
CHANNEL_ID = os.environ.get("CHANNEL_ID") or "@yemenynews_21"

SOURCES = ["MMY1444", "KamalCartoons", "Almasirah_YE", "Nasr__Amer"]
HASHTAGS = "#عاجل_الان #اليمن_ينتصر"

auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api_v1 = tweepy.API(auth)
client_v2 = tweepy.Client(consumer_key=API_KEY, consumer_secret=API_SECRET, access_token=ACCESS_TOKEN, access_token_secret=ACCESS_SECRET)

def clean(t): return html.unescape(re.sub('<[^<]+?>','',t or '')).strip()

def load_sent():
    try:
        with open("sent.txt","r") as f: return set(f.read().splitlines())
    except: return set()

def save_sent(guid):
    with open("sent.txt","a") as f: f.write(guid+"\n")

def fetch(u):
    instances = ["https://nitter.poast.org","https://nitter.privacydev.net","https://nitter.net","https://nitter.woodland.cafe","https://nitter.tiekoetter.com"]
    for inst in instances:
        try:
            url = f"{inst}/{u}/rss"
            print(f"Trying {url}")
            r=requests.get(url,timeout=20,headers={'User-Agent':'Mozilla/5.0'})
            print(f"Status {inst}: {r.status_code} len={len(r.content)}")
            if r.status_code!=200: continue
            root=ET.fromstring(r.content)
            items=[]
            for item in root.findall('.//item')[:5]:
                title=clean(item.findtext('title')); guid=item.findtext('guid') or item.findtext('link')
                enc=item.find('enclosure'); media=enc.attrib.get('url') if enc is not None else None
                text=title.split(":",1)[-1].strip() if ":" in title else title
                if len(text)>5: items.append((text,guid,media))
            if items:
                print(f"Found {len(items)} from {u} via {inst}")
                return items
        except Exception as e:
            print(f"Fail {inst} {e}")
            continue
    print(f"No items for {u}")
    return []

def split_text(t,lim=230):
    c=[]
    while len(t)>lim:
        cut=t.rfind(' ',0,lim)
        if cut==-1: cut=lim
        c.append(t[:cut]); t=t[cut:].strip()
    if t: c.append(t)
    return c

print("✅ بدأ الفحص...")
sent=load_sent()
print(f"Sent history: {len(sent)}")
new_posts=0
for u in SOURCES:
    for text,guid,media in fetch(u):
        if guid in sent:
            print(f"Skip already sent {guid[:30]}")
            continue
        chunks=split_text(text,230)
        first_text=f"{chunks[0]}\n\n{HASHTAGS}"
        try:
            mids=[]
            if media:
                try:
                    d=requests.get(media,timeout=15).content
                    open("tmp.jpg","wb").write(d)
                    m=api_v1.media_upload("tmp.jpg"); mids=[m.media_id]
                except: pass
            f=client_v2.create_tweet(text=first_text, media_ids=mids if mids else None)
            tid=f.data['id']
            for part in chunks[1:]:
                time.sleep(2)
                rep=client_v2.create_tweet(text=part, in_reply_to_tweet_id=tid)
                tid=rep.data['id']
            try:
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHANNEL_ID, "text":f"{text}\n\n{HASHTAGS}"},timeout=10)
            except: pass
            print(f"✅ نشر من {u}: {text[:60]}")
            save_sent(guid)
            new_posts+=1
        except Exception as e:
            print(f"Error {u}: {e}")
        time.sleep(8)
        if new_posts>=3: break
    if new_posts>=3: break

print(f"Done. نشر {new_posts} منشورات")
