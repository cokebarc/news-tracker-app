# streamlit_app.py
# -*- coding: utf-8 -*-
"""
Basit Haber Takip Uygulaması (Streamlit + SQLite + RSS)
- Geniş preset liste
- User-Agent ile sağlam RSS çekme (requests + feedparser)
- Canlı ilerleme çubuğu ve anlık kaynak günlüğü
- Per-feed rapor ve hata görünürlüğü
- Anahtar kelime filtresi (son X dakika)
- 5 dakikada bir otomatik yenileme (opsiyonel)
"""
import hashlib
import sqlite3
from datetime import datetime, timedelta, timezone
import re
from typing import List, Tuple

import pandas as pd
import feedparser
import streamlit as st
import requests

DB_PATH = "news.db"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"

PRESET_FEEDS = {
    "AA - Son Dakika": "https://www.aa.com.tr/tr/rss/default?cat=guncel",
    "Anadolu Ajansı - Ekonomi": "https://www.aa.com.tr/tr/rss/default?cat=ekonomi",
    "BBC Türkçe": "https://www.bbc.com/turkce/index.xml",
    "DW Türkçe": "https://www.dw.com/tr/temel/s-13190?maca=tr-rss-turkce-1010-rdf",
    "TRT Haber": "https://www.trthaber.com/xml_mobile.php?tur=manset",
    "İHA - Son Dakika": "https://www.iha.com.tr/rss/sondakika.xml",
    "DHA - Son Dakika": "https://www.dha.com.tr/rss/son-dakika",
    "Reuters World": "http://feeds.reuters.com/Reuters/worldNews",
    "AP World": "https://apnews.com/hub/ap-top-news?utm_source=apnews.com&utm_medium=referral&utm_campaign=rss&utm_id=apnews.com",
    "The Guardian World": "https://www.theguardian.com/world/rss",
    "NYTimes World": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "ABC Haber":"https://abcgazetesi.com.tr/rss",
    "A Haber":"https://www.ahaber.com.tr/rss/gundem.xml",
    "Açık Gazete":"https://www.acikgazete.com/feed/",
    "Akşam":"https://www.aksam.com.tr/rss/rss.asp",
    "Al Ain Türkçe":"https://tr.al-ain.com/feed",
    "Agos":"https://www.agos.com.tr/rss",
    "Artı Gerçek":"https://artigercek.com/service/rss.php",
    "Aydınlık":"https://www.aydinlik.com.tr/feed",
    "Aykırı":"https://www.aykiri.com.tr/rss.xml",
    "Ayandon":"https://www.ayandon.com.tr/rss.xml",
    "BBC Türkçe (Yeni)":"https://feeds.bbci.co.uk/turkce/rss.xml",
    "Bengütürk":"https://www.benguturk.com/rss",
    "Beyaz Gazete":"https://beyazgazete.com/rss/guncel.xml",
    "BHA":"https://bha.net.tr/rss",
    "Bianet":"https://bianet.org/biamag.rss",
    "Bir Gazete":"https://www.birgazete.com/feed",
    "BirGün":"https://www.birgun.net/rss/home",
    "CNN Türk":"https://www.cnnturk.com/feed/rss/all/news",
    "Cumhuriyet":"https://www.cumhuriyet.com.tr/rss/son_dakika.xml",
    "CGTN Türk":"https://www.cgtnturk.com/rss",
    "Demokrat Haber":"https://www.demokrathaber.org/rss",
    "Diken":"https://www.diken.com.tr/feed/",
    "Diriliş Postası":"https://www.dirilispostasi.com/rss",
    "Diyanet Haber":"https://www.diyanethaber.com.tr/rss",
    "Dijital Gaste":"https://www.dijitalgaste.com/rss",
    "dikGAZETE":"https://www.dikgazete.com/xml/rss.xml",
    "Doğru Haber":"https://dogruhaber.com.tr/rss",
    "Dokuz8 Haber":"https://www.dokuz8haber.net/rss",
    "Dünya":"https://www.dunya.com/rss?dunya",
    "DW Haber":"https://rss.dw.com/rdf/rss-tur-all",
    "En Politik":"https://www.enpolitik.com/rss.xml",
    "Elips Haber":"https://www.elipshaber.com/rss",
    "Ekonomim":"https://www.ekonomim.com/export/rss",
    "Ekol TV":"https://www.ekoltv.com.tr/service/rss.php",
    "En Son Haber":"https://www.ensonhaber.com/rss/ensonhaber.xml",
    "Evrensel":"https://www.evrensel.net/rss/haber.xml",
    "F5 Haber":"https://www.f5haber.com/export/rss",
    "Fayn":"https://www.fayn.press/rss/",
    "Gazete Duvar":"https://www.gazeteduvar.com.tr/export/rss",
    "Gazete.net":"https://gazete.net/rss",
    "Gazete Pencere":"https://www.gazetepencere.com/service/rss.php",
    "Gerçek Gündem":"https://www.gercekgundem.com/rss",
    "GZT":"https://www.gzt.com/rss",
    "Haber 3":"https://www.haber3.com/rss",
    "Haber 7":"https://i12.haber7.net/sondakika/newsstand/latest.xml",
    "Haber":"https://www.haber.com/rss",
    "Haberler":"https://rss.haberler.com/RssNew.aspx",
    "Haber Global":"https://haberglobal.com.tr/rss",
    "Habertürk":"https://www.haberturk.com/rss",
    "Haberet":"https://www.haberet.com/export/rss",
    "Halk TV":"https://halktv.com.tr/service/rss.php",
    "Haberport":"https://www.haberport.com/rss/latest-posts",
    "Haberiniz":"https://haberiniz.com.tr/feed/",
    "Hürriyet":"https://www.hurriyet.com.tr/rss/anasayfa",
    "İklim Haber":"https://www.iklimhaber.org/feed/",
    "Independent Türkçe":"https://www.indyturk.com/rss.xml",
    "İnternet Haber":"https://www.internethaber.com/rss",
    "İşin Detayı":"https://www.isindetayi.com/rss/gundem",
    "İşçi Haber":"https://www.iscihaber.net/rss/news",
    "İlke TV":"https://ilketv.com.tr/feed/",
    "Journo":"https://journo.com.tr/feed",
    "Karar":"https://www.karar.com/service/rss.php",
    "Kamudan Haber":"https://www.kamudanhaber.net/rss",
    "Kısa Dalga":"https://kisadalga.net/service/rss.php",
    "Korkusuz":"https://www.korkusuz.com.tr/feeds/rss",
    "KRT TV":"https://www.krttv.com.tr/rss",
    "Medya Gazete":"https://www.medyagazete.com/rss/genel-0",
    "Megabayt Gündem":"https://www.megabayt.com/rss/categorynews/gundem",
    "Milli Gazete":"https://www.milligazete.com.tr/rss",
    "Mynet":"https://www.mynet.com/haber/rss/sondakika",
    "Muhalif":"https://www.muhalif.com.tr/rss/genel-0",
    "NewsLab Turkey":"https://www.newslabturkey.org/feed/",
    "NTV":"https://www.ntv.com.tr/gundem.rss",
    "OdaTV":"https://www.odatv.com/rss.xml",
    "Sabah":"https://www.sabah.com.tr/rss/gundem.xml",
    "Serbestiyet":"https://serbestiyet.com/feed/",
    "Sözcü":"https://www.sozcu.com.tr/feeds-rss-category-sozcu",
    "Sözcü Son Dakika":"https://www.sozcu.com.tr/feeds-son-dakika",
    "soL Haber":"https://haber.sol.org.tr/rss.xml",
    "Star":"https://www.star.com.tr/rss/rss.asp",
    "T24":"https://t24.com.tr/rss",
    "Teyit":"https://teyit.org/feed?lang=tr",
    "Tele1":"https://www.tele1.com.tr/rss",
    "Timeturk":"https://www.timeturk.com/rss/",
    "Türkiye Gazetesi":"https://www.turkiyegazetesi.com.tr/feed",
    "Türkgün":"https://www.turkgun.com/rss/news",
    "TGRT Haber":"https://www.tgrthaber.com/rss/manset",
    "Ulusal Kanal":"https://www.ulusal.com.tr/rss",
    "Ulusal Post":"https://www.ulusalpost.com/service/rss.php",
    "Veryansın TV":"https://www.veryansintv.com/feed",
    "Yeni Akit":"https://www.yeniakit.com.tr/rss/haber/gundem",
    "Yeni Asır":"https://www.yeniasir.com.tr/rss/anasayfa.xml",
    "Yeniçağ":"https://www.yenicaggazetesi.com.tr/service/rss.php",
    "Yeni Şafak":"https://www.yenisafak.com/rss?xml=gundem",
    "Yeni Yaşam":"https://yeniyasamgazetesi9.com/feed/",
    "Yeşil Gazete":"https://yesilgazete.org/feed/",
    "Yurt Gazetesi":"https://www.yurtgazetesi.com.tr/service/rss.php",
}

# ------------------ DB helpers ------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""CREATE TABLE IF NOT EXISTS feeds(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        url TEXT NOT NULL UNIQUE,
        tag TEXT DEFAULT ''
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS items(
        id TEXT PRIMARY KEY,
        feed_title TEXT,
        title TEXT,
        link TEXT,
        published_utc TEXT,
        summary TEXT,
        tag TEXT,
        read INTEGER DEFAULT 0,
        starred INTEGER DEFAULT 0,
        inserted_at_utc TEXT
    )""")
    conn.commit()
    return conn

def add_feed(conn, title, url, tag=""):
    conn.execute("INSERT OR IGNORE INTO feeds(title,url,tag) VALUES(?,?,?)", (title, url, tag))
    conn.commit()

def remove_feed(conn, url):
    conn.execute("DELETE FROM feeds WHERE url=?", (url,))
    conn.commit()

def list_feeds(conn):
    return pd.read_sql_query("SELECT * FROM feeds ORDER BY title", conn)

def item_id_from(link, title, published):
    key = f"{link}|{title}|{published}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

def insert_item(conn, item) -> int:
    cols = ["id","feed_title","title","link","published_utc","summary","tag","read","starred","inserted_at_utc"]
    vals = [item.get(c) for c in cols]
    cur = conn.execute(
        f"INSERT OR IGNORE INTO items({','.join(cols)}) VALUES({','.join(['?']*len(cols))})", vals
    )
    return cur.rowcount  # 1: eklendi, 0: zaten vardı

def fetch_feed(url: str, timeout: int = 20):
    """Request ile indir (UA + redirect), sonra feedparser.parse(content)."""
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": UA}, allow_redirects=True)
        r.raise_for_status()
        content = r.content
        parsed = feedparser.parse(content)
        return parsed, None
    except Exception as e:
        return None, str(e)

def pull_all_with_live_progress(conn, feeds_df, default_tag: str = "", timeout: int = 15):
    """
    Kaynakları tek tek çekerken canlı ilerleme ve log gösterir.
    Dönüş: {"total_seen":int, "total_inserted":int, "per_feed":[...], "errors":[(...), ...]}
    """
    report = {"total_seen": 0, "total_inserted": 0, "per_feed": [], "errors": []}
    total = len(feeds_df)
    if total == 0:
        return report

    progress = st.progress(0.0, text="Başlıyor...")
    try:
        status_ctx = st.status("Kaynaklardan çekiliyor...", expanded=True)
        use_status_cm = True
    except Exception:
        status_ctx = st.container()
        use_status_cm = False

    def _write(msg: str):
        if use_status_cm:
            with status_ctx:
                st.write(msg)
        else:
            status_ctx.write(msg)

    for i, (_, row) in enumerate(feeds_df.iterrows()):
        title_feed = row["title"]
        url = row["url"]
        tag = (row.get("tag") or "") or default_tag

        progress.progress(i / total, text=f"{i}/{total} • {title_feed} çekiliyor…")
        _write(f"⏳ **{title_feed}** → {url}")

        parsed, err = fetch_feed(url, timeout=timeout)
        if err or parsed is None:
            report["per_feed"].append({"feed": title_feed, "url": url, "seen": 0, "inserted": 0, "status": "ERROR"})
            report["errors"].append((title_feed, url, err or "unknown error"))
            _write(f"❌ {title_feed}: {err}")
            progress.progress((i + 1) / total, text=f"{i+1}/{total} • {title_feed} (hata)")
            continue

        seen = 0
        inserted = 0
        for e in parsed.entries:
            seen += 1
            title = (e.get("title") or "").strip()
            link = (e.get("link") or "").strip()
            summary = e.get("summary", "") or e.get("description", "") or ""
            if e.get("published_parsed"):
                pubdt = datetime(*e.published_parsed[:6], tzinfo=timezone.utc).isoformat()
            elif e.get("updated_parsed"):
                pubdt = datetime(*e.updated_parsed[:6], tzinfo=timezone.utc).isoformat()
            else:
                pubdt = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
            iid = item_id_from(link, title, pubdt[:19])
            inserted += insert_item(conn, {
                "id": iid,
                "feed_title": title_feed,
                "title": title,
                "link": link,
                "published_utc": pubdt,
                "summary": summary,
                "tag": tag,
                "read": 0,
                "starred": 0,
                "inserted_at_utc": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
            })
        conn.commit()

        report["total_seen"] += seen
        report["total_inserted"] += inserted
        report["per_feed"].append({"feed": title_feed, "url": url, "seen": seen, "inserted": inserted, "status": "OK" if seen else "EMPTY"})
        _write(f"✅ **{title_feed}**: {inserted} yeni / {seen} görüldü")
        progress.progress((i + 1) / total, text=f"{i+1}/{total} • {title_feed} bitti")

    if use_status_cm:
        status_ctx.update(label=f"Tamamlandı: {report['total_inserted']} yeni / {report['total_seen']} görüldü ({total} kaynak)", state="complete")
    else:
        status_ctx.write(f"**Tamamlandı:** {report['total_inserted']} yeni / {report['total_seen']} görüldü ({total} kaynak)")

    rep_df = pd.DataFrame(report["per_feed"])
    st.dataframe(rep_df, use_container_width=True, hide_index=True)
    if report["errors"]:
        with st.expander("⚠️ Hata veren kaynaklar", expanded=False):
            for (fname, furl, msg) in report["errors"]:
                st.write(f"• **{fname}** — {furl}")
                st.code(str(msg))
    return report

def query_items(conn, search="", tag="", only_unread=False, only_starred=False, date_from=None, date_to=None, limit=500):
    sql = "SELECT * FROM items WHERE 1=1"
    params = []
    if search:
        sql += " AND (title LIKE ? OR summary LIKE ?)"
        like = f"%{search}%"
        params += [like, like]
    if tag:
        sql += " AND tag=?"
        params.append(tag)
    if only_unread:
        sql += " AND read=0"
    if only_starred:
        sql += " AND starred=1"
    if date_from:
        sql += " AND datetime(published_utc) >= datetime(?)"
        params.append(date_from)
    if date_to:
        sql += " AND datetime(published_utc) <= datetime(?)"
        params.append(date_to)
    sql += " ORDER BY datetime(published_utc) DESC LIMIT ?"
    params.append(limit)
    return pd.read_sql_query(sql, conn, params=params)

def mark_item(conn, item_id, field, value):
    conn.execute(f"UPDATE items SET {field}=? WHERE id=?", (value, item_id))
    conn.commit()

def export_csv(df, filename="news_export.csv"):
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    return filename

# ------------------ UI ------------------
st.set_page_config(page_title="Haber Takip", page_icon="📰", layout="wide")
st.title("📰 Haber Takip Uygulaması (RSS)")

conn = get_conn()

# ---- Sidebar ----
with st.sidebar:
    st.header("Ayarlar")
    tzinfo = timezone(timedelta(hours=3))  # Europe/Istanbul
    auto_refresh = st.checkbox("Otomatik yenile (5 dakikada bir)", value=False)
    if auto_refresh:
        st.markdown("<meta http-equiv='refresh' content='300'>", unsafe_allow_html=True)
    auto_pull = st.checkbox("Oto-yenilemede RSS çek", value=False)
    st.markdown("---")

    st.subheader("Anahtar Kelime / Zaman Penceresi")
    keywords = st.text_input("Virgülle ayırın",
                             value="beyaz kod, sağlıkta şiddet, hastane, şehir hastanesi, devlet hastanesi, acil servis, MHRS")
    time_window_min = st.number_input("Son X dakika içinde ara", min_value=5, max_value=10080, value=60, step=5)
    st.caption("Eşleşme paneli, son X dakika içindeki haberlerden anahtar kelime eşleşmelerini çıkarır.")
    st.markdown("---")

# ---- Preset + Tekil + Toplu ekleme ----
with st.sidebar:
    if st.button("📥 Öntanımlı Kaynakları Ekle"):
        for k, v in PRESET_FEEDS.items():
            add_feed(conn, k, v, tag="genel")
        st.success("Kaynaklar eklendi.")
        st.rerun()

    st.subheader("Yeni Kaynak Ekle")
    new_title = st.text_input("Kaynak Adı", value="")
    new_url = st.text_input("RSS URL", value="")
    new_tag = st.text_input("Etiket (opsiyonel)", value="")
    if st.button("➕ Ekle"):
        if new_title and new_url:
            add_feed(conn, new_title.strip(), new_url.strip(), new_tag.strip())
            st.success("Kaynak eklendi.")
            st.rerun()
        else:
            st.error("Lütfen başlık ve URL girin.")

    st.subheader("Toplu Kaynak Ekle")
    bulk_txt = st.text_area("Metin (satır başına 'Site Adı<TAB>URL' ya da 'Site Adı,URL')",
                            placeholder="ABC Haber\thttps://abcgazetesi.com.tr/rss\nA Haber\thttps://www.ahaber.com.tr/rss/gundem.xml",
                            height=120)
    bulk_file = st.file_uploader("veya CSV yükle (headers: name,url)", type=["csv"])
    if st.button("➕ Toplu Ekle"):
        added = 0
        rows: List[Tuple[str,str]] = []
        if bulk_txt.strip():
            for line in bulk_txt.splitlines():
                line = line.strip()
                if not line:
                    continue
                if "\t" in line:
                    name, url = [x.strip() for x in line.split("\t", 1)]
                elif "," in line:
                    name, url = [x.strip() for x in line.split(",", 1)]
                else:
                    continue
                rows.append((name, url))
        if bulk_file is not None:
            dfu = pd.read_csv(bulk_file)
            for _, r in dfu.iterrows():
                rows.append((str(r.get("name") or r.get("title") or "").strip(),
                             str(r.get("url") or "").strip()))
        for name, url in rows:
            if name and url:
                try:
                    add_feed(conn, name, url, tag="genel")
                    added += 1
                except Exception:
                    pass
        st.success(f"Toplam {added} kaynak işlendi (yinelenenler atlandı).")
        st.rerun()

    st.subheader("Kayıtlı Kaynaklar")
    feeds_df = list_feeds(conn)
    st.dataframe(feeds_df, use_container_width=True, hide_index=True, height=260)

    remove_url = st.text_input("Silinecek Kaynak URL")
    if st.button("🗑️ Kaynağı Sil"):
        if remove_url:
            remove_feed(conn, remove_url.strip())
            st.success("Kaynak silindi.")
            st.rerun()
        else:
            st.error("URL girin.")

# Oto-yenilemede otomatik çekme
if auto_refresh and auto_pull and not feeds_df.empty:
    try:
        rep = pull_all_with_live_progress(conn, feeds_df)
        st.caption(f"🔄 Oto-çek: {rep['total_inserted']} yeni / {rep['total_seen']} görüldü.")
    except Exception as e:
        st.caption(f"⚠️ Oto-çek hata: {e}")

st.divider()
left, right = st.columns([1, 3])

# ------------------ Sol Kolon ------------------
with left:
    st.subheader("Veri Çek")
    timeout_sec = st.slider("Feed başına zaman aşımı (sn)", min_value=5, max_value=30, value=15, step=1,
                            help="Bazı siteler yavaş; bekleme süresi.")
    if st.button("🔄 Haberleri Çek (Tüm Kaynaklar)"):
        feeds_df = list_feeds(conn)
        if feeds_df.empty:
            st.warning("Önce en az bir kaynak ekleyin.")
        else:
            rep = pull_all_with_live_progress(conn, feeds_df, timeout=timeout_sec)
            st.success(f"Toplam: {rep['total_inserted']} yeni / {rep['total_seen']} görüldü.")

    st.subheader("Filtreler")
    tag = st.text_input("Etiket")
    search = st.text_input("Arama (başlık/özet)")
    only_unread = st.checkbox("Sadece okunmamış", value=False)
    only_starred = st.checkbox("Sadece yıldızlı", value=False)
    date_from = st.date_input("Başlangıç Tarihi", value=None)
    date_to = st.date_input("Bitiş Tarihi", value=None)

    q_from = f"{date_from} 00:00:00" if date_from else None
    q_to = f"{date_to} 23:59:59" if date_to else None

    if st.button("🔍 Listele / Yenile"):
        st.session_state["last_query"] = {
            "tag": tag,
            "search": search,
            "only_unread": only_unread,
            "only_starred": only_starred,
            "date_from": q_from,
            "date_to": q_to,
        }

    if "last_query" not in st.session_state:
        st.session_state["last_query"] = {
            "tag": "",
            "search": "",
            "only_unread": False,
            "only_starred": False,
            "date_from": None,
            "date_to": None
        }

    st.subheader("Dışa Aktar")
    if st.button("📤 Sonuçları CSV Olarak Kaydet"):
        q = st.session_state["last_query"]
        df = query_items(conn, **q, limit=5000)
        fname = export_csv(df, "news_export.csv")
        st.success(f"Kaydedildi: {fname}")
        with open(fname, "rb") as f:
            st.download_button("İndir (CSV)", f, file_name="news_export.csv")

# ------------------ Sağ Kolon ------------------
with right:
    st.subheader("Haberler")
    q = st.session_state.get("last_query", {})
    df = query_items(conn, **q, limit=5000)

    # --- Son X dakika + anahtar kelime eşleşmeleri ---
    kw = [k.strip().lower() for k in (keywords or "").split(",") if k.strip()]
    st.markdown("#### 🔔 Son Eşleşmeler")
    if df.empty:
        st.info("Henüz kayıt yok. Soldan kaynak ekleyip 'Haberleri Çek' butonuna basın.")
        recent_hits = pd.DataFrame()
    else:
        try:
            now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
            cutoff = now_utc - timedelta(minutes=int(time_window_min))
            df["published_dt"] = pd.to_datetime(df["published_utc"], errors="coerce", utc=True)
            recent = df[df["published_dt"] >= cutoff].copy()
        except Exception:
            recent = df.copy()

        def _hit_row(row):
            t = (row.get("title") or "") + " " + (row.get("summary") or "")
            t = t.lower()
            return any(k in t for k in kw) if kw else False

        recent["matched"] = recent.apply(_hit_row, axis=1)
        recent_hits = recent[recent["matched"]]

        if recent_hits.empty:
            st.info(f"Son {time_window_min} dakika içinde anahtar kelime eşleşmesi yok.")
        else:
            st.success(f"Son {time_window_min} dakikada {len(recent_hits)} eşleşme bulundu.")
            st.dataframe(recent_hits[["feed_title", "title", "published_utc", "link"]],
                         use_container_width=True, hide_index=True)
            st.download_button("📤 Eşleşmeler (CSV)",
                               data=recent_hits.to_csv(index=False).encode("utf-8-sig"),
                               file_name="rss_matches.csv", mime="text/csv")

    # --- Tüm Sonuçlar: anahtar kelime zorunlu ---
    st.markdown("#### Tüm Sonuçlar (anahtar kelime eşleşenler)")
    if df.empty:
        st.info("Liste boş.")
    else:
        if not kw:
            st.warning("Anahtar kelime girmediniz. Soldan anahtar kelimeleri ekleyin.")
        else:
            text_col = df[["title", "summary"]].fillna("").agg(" ".join, axis=1).str.lower()
            pattern = "|".join(re.escape(k) for k in kw if k)
            mask = text_col.str.contains(pattern, regex=True)
            df_filtered = df[mask].copy()

            if df_filtered.empty:
                st.info("Anahtar kelimelerle eşleşen sonuç bulunamadı.")
            else:
                def highlight(title):
                    t = title or ""
                    return f"🟡 {t}"
                for _, row in df_filtered.iterrows():
                    with st.expander(f"{highlight(row['title'])}"):
                        pub = row['published_utc']
                        try:
                            dt_local = datetime.fromisoformat(pub.replace("Z", "+00:00")).astimezone(timezone(timedelta(hours=3)))
                            pub_str = dt_local.strftime("%d.%m.%Y %H:%M")
                        except Exception:
                            pub_str = pub
                        st.write(f"**Kaynak:** {row['feed_title']}  |  **Yayın:** {pub_str}")
                        st.write(f"[Habere Git]({row['link']})")
                        if row.get('summary'):
                            st.write(row['summary'][:800] + ("..." if len(row['summary']) > 800 else ""))

                        b1, b2, b3 = st.columns(3)
                        with b1:
                            if st.button(("✅ Okundu" if row['read'] else "Okundu Olarak İşaretle"), key=f"read-{row['id']}"):
                                mark_item(conn, row['id'], "read", 1 if not row['read'] else 0)
                                st.rerun()
                        with b2:
                            if st.button(("⭐ Kaldır" if row['starred'] else "⭐ Yıldızla"), key=f"star-{row['id']}"):
                                mark_item(conn, row['id'], "starred", 1 if not row['starred'] else 0)
                                st.rerun()
                        with b3:
                            if st.button("🔗 Kopyala (Link)", key=f"copy-{row['id']}"):
                                st.code(row['link'], language="text")
                                st.success("Link kopyalamak için kod bloğunu seçip Ctrl+C yapın.")
