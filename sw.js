/* ═══════════ 伽蓝经纬 · Service Worker ═══════════
   两级缓存（承姊妹站，无外部瓦片故无 TILES 层）：
   SHELL 外壳预存 · TEXTS 全文懒载（首查后整本离线）
   VERSION 与 index.html 的 ?v 同步递升（教训：勿加 ignoreSearch 把页面钉死旧版） */

const VERSION = "v10";
const SHELL = `qlg-${VERSION}-shell`;
const TEXTS = `qlg-${VERSION}-texts`;

const SHELL_FILES = [
  "./", "./index.html", "./manifest.json",
  "./css/main.css?v=10",
  "./vendor/leaflet.js", "./vendor/leaflet.css?v=10",
  "./data/site_data.js?v=10", "./data/stats.js?v=10", "./data/sections.js?v=10", "./data/songyun.js?v=10",
  "./icons/icon-192.png", "./icons/icon-512.png",
  "./js/config.js?v=10", "./js/map.js?v=10", "./js/rail.js?v=10",
  "./js/reader.js?v=10", "./js/search.js?v=10", "./js/stats.js?v=10",
  "./js/bookmarks.js?v=10", "./js/export.js?v=10", "./js/app.js?v=10",
];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(SHELL).then(c => c.addAll(SHELL_FILES)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(keys =>
      /* 精确保留本版两仓（承旗舰：endsWith(VERSION) 会误删自身 *-shell/*-texts——离线首验实证） */
      Promise.all(keys.filter(k => ![SHELL, TEXTS].includes(k)).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET") return;
  if (url.origin !== location.origin) return;

  /* 网络优先（防 SW 钉死旧版），失败回缓存，再失败回外壳 */
  e.respondWith(
    fetch(e.request).then(r => {
      if (/\/data\/(text|sections)/.test(url.pathname)) {
        const cp = r.clone();
        caches.open(TEXTS).then(c => c.put(e.request, cp));
      }
      return r;
    }).catch(() =>
      caches.match(e.request).then(hit => hit || caches.match("./index.html"))
    )
  );
});
