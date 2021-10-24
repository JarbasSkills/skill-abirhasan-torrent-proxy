from os.path import join, dirname

import requests
from ovos_plugin_common_play.ocp import MediaType, PlaybackType
from ovos_utils.parse import fuzzy_match
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill, \
    ocp_search, ocp_play


class AbirhasanTorrentProxySkill(OVOSCommonPlaybackSkill):
    def __init__(self):
        super(AbirhasanTorrentProxySkill, self).__init__(
            "AbirhasanTorrentProxy")
        self.supported_media = [MediaType.GENERIC, MediaType.MOVIE,
                                MediaType.ADULT]
        self.tpb_icon = join(dirname(__file__), "ui", "tpb.svg")
        self.leetx_icon = join(dirname(__file__), "ui", "1337X.svg")

    @staticmethod
    def calc_score(phrase, torrent, media_type, idx=0, base_score=0):
        removes = ["WEBRip", "x265", "HDR", "DTS", "HD", "BluRay", "uhd",
                   "1080p", "720p", "BRRip", "XviD", "MP3", "2160p",
                   "h264", "AAC", "REMUX", "SDR", "hevc", "x264",
                   "REMASTERED", "SUBBED", "DVDRip"]
        removes = [r.lower() for r in removes]
        clean_name = torrent["title"].replace(".", " ").replace("-", " ")
        clean_name = " ".join([w for w in clean_name.split()
                               if w and w.lower() not in removes])
        score = base_score - idx
        score += fuzzy_match(phrase.lower(), clean_name) * 100
        if media_type == MediaType.MOVIE:
            score += 15
        return score

    @staticmethod
    def search_abirhasan(query, endpoint):
        url = "https://api.abirhasan.wtf/" + endpoint
        results = requests.get(url, params={"query": query}).json()
        for r in results["results"]:
            yield {"title": r["Name"],
                   "magnet": r["Magnet"],
                   "image": r.get("Poster"),
                   "category": r["Category"],
                   "seeders": int(r["Seeders"])}

    @ocp_search()
    def search_133tx(self, phrase, media_type):
        base_score = 0
        if self.voc_match(phrase, "torrent"):
            phrase = self.remove_voc(phrase, "torrent")
            base_score = 40

        adult = False
        # no accidental porn results!
        if self.voc_match(phrase, "porn") or media_type == MediaType.ADULT:
            phrase = self.remove_voc(phrase, "porn")
            adult = True

        idx = 0
        for torr in self.search_abirhasan(phrase, endpoint="1337x"):
            if adult and torr["category"] != "XXX":
                continue
            elif torr["category"] != "Movies":
                continue
            if torr["seeders"] < 1:
                continue
            score = self.calc_score(phrase, torr, media_type, idx, base_score)
            yield {
                "title": torr["title"],
                "match_confidence": score,
                "media_type": MediaType.VIDEO,
                "uri": torr["magnet"],
                "image": torr.get("image") or self.leetx_icon,
                "playback": PlaybackType.SKILL,
                "skill_icon": self.leetx_icon,
                "skill_id": self.skill_id
            }
            idx += 1

    @ocp_search()
    def search_piratebay(self, phrase, media_type):
        base_score = 0
        if self.voc_match(phrase, "torrent"):
            phrase = self.remove_voc(phrase, "torrent")
            base_score = 40

        adult = False
        # no accidental porn results!
        if self.voc_match(phrase, "porn") or media_type == MediaType.ADULT:
            phrase = self.remove_voc(phrase, "porn")
            adult = True

        idx = 0
        for torr in self.search_abirhasan(phrase, endpoint="piratebay"):
            if adult and torr["category"] != "Porn":
                continue
            elif torr["category"] != "Video":
                continue
            if torr["seeders"] < 1:
                continue
            score = self.calc_score(phrase, torr, media_type, idx, base_score)
            yield {
                "title": torr["title"],
                "match_confidence": score,
                "media_type": MediaType.VIDEO,
                "uri": torr["magnet"],
                "image": torr.get("image") or self.tpb_icon,
                "playback": PlaybackType.SKILL,
                "skill_icon": self.tpb_icon,
                "skill_id": self.skill_id
            }
            idx += 1

    @ocp_play()
    def stream_torrent(self, message):
        self.bus.emit(message.forward("skill.peerflix.play", message.data))


def create_skill():
    return AbirhasanTorrentProxySkill()
