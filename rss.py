import requests
import json
import datetime
from time import sleep
from email.utils import formatdate
import sys

class Podcast:
    id = ""
    title = ""
    description = ""
    link = ""
    cover = ""
    author = ""
    categories = []
    feed = ""
    station = ""
    episodes = []

class Episode:
    id = ""
    title = ""
    description = ""
    link = ""
    date = datetime.datetime.now()
    duration = 0 # in seconds
    audio_link = ""
    audio_length = 0
    audio_type = ""

def main():
    podcast_url = sys.argv[1]
    podcast = get_podcast(podcast_url)
    feed = transform_into_rss_feed(podcast)
    with open(f"./{podcast_url.split('/')[-1]}.xml", "w") as f:
        f.write(feed)
        print(f"\n\n✅ {podcast.title} successfully saved in {podcast_url.split('/')[-1]}.xml")

def get_podcast(url: str):
    res = requests.get(url)
    data1, data2 = res.text.split("\n")[-6:-4]

    data1 = data1.split(">")[1]
    data1 = data1.split("<")[0]
    data1 = json.loads(data1)
    data1 = data1["body"]
    data1 = json.loads(data1)

    data2 = data2.split(">")[1]
    data2 = data2.split("<")[0]
    data2 = json.loads(data2)
    data2 = data2["body"]
    data2 = json.loads(data2)
    data2 = data2["content"]

    podcast = Podcast()
    podcast.id = data2["id"]
    podcast.title = data2["title"]
    podcast.description = data2["standFirst"]
    podcast.link = data1["seo"]["seoCanonicalUrl"]
    podcast.cover = data2["visual"]["src"]
    podcast.author = data1["brand"]["title"]
    podcast.categories = [theme["title"] for theme in data2["themes"]]
    podcast.feed = data2["podcast"]["rss"]
    podcast.station = data1["brand"]["id"]

    get_episodes(podcast, data2["expressions"], 0)

    return podcast

def get_episodes(podcast: Podcast, expressions, index: int):
    for item in expressions["items"]:
        try:
            if "manifestations" in item and len(item["manifestations"]) > 0:
                index += 1
                episode = Episode()
                episode.id = item["id"]
                episode.title = item["episodeSerieTitle"] if "episodeSerieTitle" in item else item["title"]
                episode.description = item["standFirst"]
                episode.link = "https://www.radiofrance.fr/" + item["path"]
                episode.date = datetime.datetime.fromtimestamp(item["publishedDate"] / 1e3)

                manifestation = item["manifestations"][0]
                episode.duration = manifestation["duration"]
                episode.audio_link = manifestation["url"]
                audio_info = {}
                try:
                    audio_info = requests.head(manifestation["url"])
                    episode.audio_length = int(audio_info.headers["Content-Length"])
                    episode.audio_type = audio_info.headers["Content-Type"]
                except:
                    sleep(1)
                    audio_info = requests.head(manifestation["url"])
                    episode.audio_length = int(audio_info.headers["Content-Length"])
                    episode.audio_type = audio_info.headers["Content-Type"]

                print(end="\x1b[2K")
                print(f"[{index}] {episode.title}", end="\r")

                podcast.episodes.append(episode)
        except:
            print(end="\x1b[2K")
            print(f"[❌] {episode.title}")

    if expressions["next"]:
        res = requests.get(f"https://www.radiofrance.fr/api/v2.1/concepts/{podcast.id}/expressions?pageCursor={expressions['next']}&includeFutureExpressionsWithManifestations=true")
        get_episodes(podcast, res.json(), index)

def transform_into_rss_feed(podcast: Podcast):
    episodes_feed = ""
    def add_category(feed_categories: str, i: int):
        if i == len(podcast.categories) - 1:
            feed_categories += f"<itunes:category text=\"{podcast.categories[i]}\" />"
        else:
            feed_categories += f"<itunes:category text=\"{podcast.categories[i]}\">"
            feed_categories = add_category(feed_categories, i + 1)
            feed_categories += "</itunes:category>"
        return feed_categories
    feed_categories = add_category("", 0)

    for episode in podcast.episodes:
        episodes_feed += f"""<item>
            <title>{episode.title}</title>
            <link>{episode.link}</link>
            <description>{episode.description}</description>
            <author>podcast@radiofrance.com (Radio France)</author>
            <category>{" ".join(podcast.categories)}</category>
            <enclosure url="{episode.audio_link}" length="{episode.audio_length}" type="{episode.audio_type}" />
            <guid isPermaLink="false">{episode.id}</guid>
            <pubDate>{formatdate(float(episode.date.strftime('%s')))}</pubDate>
            <itunes:title>{episode.title}</itunes:title>
            <itunes:image href={podcast.cover} />
            <itunes:author>{podcast.author}</itunes:author>
            <itunes:explicit>no</itunes:explicit>
            <itunes:keywords>{",".join(episode.title.split(" "))}</itunes:keywords>
            <itunes:subtitle>{episode.title}</itunes:subtitle>
            <itunes:summary>{episode.description}</itunes:summary>
            <itunes:duration>{"{:0>8}".format(str(datetime.timedelta(seconds=episode.duration)))}</itunes:duration>
            <googleplay:block>yes</googleplay:block>
        </item>
        """

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:pa="http://podcastaddict.com" xmlns:podcastRF="http://radiofrance.fr/Lancelot/Podcast#" xmlns:googleplay="http://www.google.com/schemas/play-podcasts/1.0" version="2.0">
    <channel>
        <title>{podcast.title}</title>
        <link>{podcast.link}</link>
        <description>{podcast.description}</description>
        <language>fr</language>
        <copyright>Radio France</copyright>
        <lastBuildDate>{formatdate(float(datetime.datetime.now().strftime('%s')))}</lastBuildDate>
        <generator>Radio France</generator>
        <image>
            <url>{podcast.cover}</url>
            <title>{podcast.title}</title>
            <link>{podcast.link}</link>
        </image>
        {feed_categories}
        <itunes:author>{podcast.author}</itunes:author>
        <itunes:explicit>no</itunes:explicit>
        <itunes:image href="{podcast.cover}" />
        <itunes:owner>
            <itunes:email>podcast@radiofrance.com</itunes:email>
            <itunes:name>Radio France</itunes:name>
        </itunes:owner>
        <itunes:subtitle>{podcast.title}</itunes:subtitle>
        <itunes:summary>{podcast.description}</itunes:summary>
        <itunes:new-feed-url>{podcast.feed}</itunes:new-feed-url>
        <pa:new-feed-url>{podcast.feed}</pa:new-feed-url>
        <podcastRF:originStation>{podcast.station}</podcastRF:originStation>
        <googleplay:block>yes</googleplay:block>
        {episodes_feed}
    </channel>
</rss>
    """

    return feed

if __name__ == "__main__":
    main()
