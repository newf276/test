import requests
import re
import urllib.parse
from collections import defaultdict

playlist_urls = [
    "https://raw.githubusercontent.com/newf276/test/refs/heads/master/DaddyLive.m3u8",
    "https://raw.githubusercontent.com/newf276/test/refs/heads/master/DaddyLiveEvents.m3u8",
    "https://raw.githubusercontent.com/newf276/test/refs/heads/master/udptv.m3u",
]

EPG_URL = "https://github.com/newf276/junk/raw/refs/heads/master/programme/home/master.xml.gz"

def unwrap_url(url):
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed.query)
    if 'url' in query_params:
        return query_params['url'][0]
    return url

def fetch_playlist(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return ""

def extract_group_title(extinf_line):
    match = re.search(r'group-title="(.*?)"', extinf_line)
    return match.group(1).strip() if match else "Unknown"

def parse_entries(content):
    lines = content.strip().splitlines()
    grouped_entries = defaultdict(list)
    seen_urls = set()
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            entry = [line]
            j = i + 1
            while j < len(lines) and lines[j].startswith("#EXTVLCOPT"):
                entry.append(lines[j].strip())
                j += 1
            if j < len(lines):
                url = unwrap_url(lines[j].strip())
                if url not in seen_urls:
                    entry.append(url)
                    group = extract_group_title(line)
                    grouped_entries[group].append(entry)
                    seen_urls.add(url)
                i = j + 1
            else:
                i = j
        else:
            i += 1
    return grouped_entries

def merge_playlists(urls, epg_url):
    merged_groups = defaultdict(list)

    for url in urls:
        content = fetch_playlist(url)
        if content:
            groups = parse_entries(content)
            for group_name, entries in groups.items():
                merged_groups[group_name].extend(entries)

    sorted_group_names = sorted(merged_groups.keys(), key=lambda g: g.lower())

    with open("MergedPlaylist.m3u8", "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U url-tvg="{epg_url}"\n\n')
        for group_name in sorted_group_names:
            f.write(f'#--- Group: {group_name} ---\n')
            for entry in merged_groups[group_name]:
                for line in entry:
                    f.write(f"{line}\n")
            f.write("\n")

    print("MergedPlaylist.m3u8 has been written with proxy URLs unwrapped.")

if __name__ == "__main__":
    merge_playlists(playlist_urls, EPG_URL)
