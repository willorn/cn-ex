/**
 * cn-ex — China province level map
 * Experience inspired by JapanEx (https://zhung.com.tw/japanex/)
 * Share state via ?l= + localStorage fallback
 */

const STORAGE_KEY = 'cn-ex-levels';
const LEVEL_PARAM = 'l';
const TITLE_PARAM = 't';
const PROVINCE_COUNT = 34;

/** Fixed order must never change once published (URL compatibility). */
const PROVINCES = [
  '黑龙江', '甘肃', '吉林', '内蒙古', '山东', '河北', '北京', '天津',
  '西藏', '新疆', '河南', '安徽', '山西', '湖北', '青海', '辽宁',
  '广东', '江苏', '江西', '浙江', '福建', '上海', '陕西', '湖南',
  '广西', '香港', '澳门', '贵州', '重庆', '四川', '云南', '宁夏',
  '台湾', '海南',
];

const MAP_BG = '#B4CDEA';

/** Sequential cold→warm by footprint depth (export + legend source of truth). */
const LEVELS = {
  5: { label: '住居', full: '住居（居住过）', color: '#C0394A' },
  4: { label: '宿泊', full: '宿泊（住宿过）', color: '#D96B42' },
  3: { label: '访问', full: '访问（游玩过）', color: '#E2B24A' },
  2: { label: '接地', full: '接地（休息、换车等）', color: '#5E9E98' },
  1: { label: '通过', full: '通过（路过）', color: '#8FA6C4' },
  0: { label: '没去过', full: '没去过', color: '#F3F5F7' },
};

const MAP_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1134 976" role="img" aria-label="中国省级制霸地图">
  <rect id="map-bg" x="0" y="0" width="1134" height="976" fill="#B4CDEA"/>
  <text id="title" x="425" y="119">中国制霸</text>
  <g id="regions"><path id="黑龙江" d="M1100,33v158H894V33H1100z" /><path id="甘肃" d="M585,191v371H351V191H585z" /><path id="吉林" d="M894,191v85h206v-85H894z" /><path id="内蒙古" d="M894,33H738v158H499v227h227l168-108V33z" /><path id="山东" d="M779,446v92h139v-92H779z" /><path id="河北" d="M861,310H726v180h117v-95h18V310z" /><path id="北京" d="M763 336h80v52H763Z"/><path id="天津" d="M763,388h80v43h-80V388z" /><path id="西藏" d="M389,770H35V466h354V770z" /><path id="新疆" d="M35,466V87h316v379H35z" /><path id="河南" d="M779,490H654v117h125V490z" /><path id="安徽" d="M852,538h-73v138h73V538z" /><path id="山西" d="M654,418v108h72V418H654z" /><path id="湖北" d="M779,688v-81H654v81H779z" /><path id="青海" d="M442,626V395H228v231H442z" /><path id="辽宁" d="M861,276v119h154V276H861z" /><path id="广东" d="M823,788H679v81h144V788z" /><path id="江苏" d="M899,538v87h-62v-87H899z" /><path id="江西" d="M852,806V676H749v130H852z" /><path id="浙江" d="M852,625l74,1v107h-74V625z" /><path id="福建" d="M823,733v107h73V733H823z" /><path id="上海" d="M882 602h72v47H882Z"/><path id="陕西" d="M585,653h69V418h-69V653z" /><path id="湖南" d="M654,688h95v100h-95V688z" /><path id="广西" d="M679,788H537v81h142V788z" /><path id="香港" d="M758 856h42v33H758Z"/><path id="澳门" d="M701 856h45v33H701Z"/><path id="贵州" d="M654,709H537v79h117V709z" /><path id="重庆" d="M565 653h89v56H565Z"/><path id="四川" d="M565,737v-84h20v-91H389v175H565z" /><path id="云南" d="M537,737H389v115h148V737z" /><path id="宁夏" d="M585,418h-86v96h86V418z" /><path id="台湾" d="M918 788h45v87H918Z"/><path id="海南" d="M615 897h78v46H615Z"/></g>
  <path id="曾母暗沙" d="M827 941L827 897L908 897L908 941"/>
  <g id="labels"><text x="659" y="266">内蒙古</text><text x="951" y="123">黑龙江</text><text x="966" y="242">吉林</text><text x="906" y="347">辽宁</text><text x="773" y="371">北京</text><text x="773" y="419">天津</text><text x="751" y="469">河北</text><text x="861" y="488">山</text><text x="861" y="518">东</text><text x="685" y="579">河南</text><text x="684" y="658">湖北</text><text x="684" y="733">湖</text><text x="684" y="763">南</text><text x="846" y="575">江</text><text x="846" y="605">苏</text><text x="888" y="635">上海</text><text x="872" y="685">浙</text><text x="872" y="715">江</text><text x="844" y="783">福</text><text x="844" y="813">建</text><text x="925" y="826">台</text><text x="925" y="856">湾</text><text x="625" y="930">海南</text><text x="721" y="842">广东</text><text x="772" y="736">江</text><text x="772" y="766">西</text><text x="793" y="603">安</text><text x="793" y="633">徽</text><text x="674" y="466">山</text><text x="674" y="496">西</text><text x="604" y="536">陕</text><text x="604" y="566">西</text><text x="527" y="460">宁</text><text x="527" y="490">夏</text><text x="411" y="304">甘</text><text x="411" y="334">肃</text><text x="301" y="520">青海</text><text x="453" y="660">四川</text><text x="432" y="805">云南</text><text x="579" y="839">广西</text><text x="566" y="759">贵州</text><text x="579" y="691">重庆</text><text x="104" y="639">西藏</text><text x="163" y="288">新疆</text><text x="767" y="880" class=fs24>港</text><text x="711" y="880" class=fs24>澳</text></g>
  <text id="score" x="35" y="883">分数: 0</text>
  <g id="legend">
    <path class="legend-swatch" data-level="5" fill="#C0394A" d="M983 450h120v50H983Z"/>
    <path class="legend-swatch" data-level="4" fill="#D96B42" d="M983 500h120v50H983Z"/>
    <path class="legend-swatch" data-level="3" fill="#E2B24A" d="M983 550h120v50H983Z"/>
    <path class="legend-swatch" data-level="2" fill="#5E9E98" d="M983 600h120v50H983Z"/>
    <path class="legend-swatch" data-level="1" fill="#8FA6C4" d="M983 650h120v50H983Z"/>
    <path class="legend-swatch" data-level="0" fill="#F3F5F7" d="M983 700h120v50H983Z"/>
    <path class="legend-border" fill="none" stroke="#333" stroke-width="4" d="M983 448h120v304H983Z"/>
    <text x="1000" y="484">住居 5</text>
    <text x="1000" y="534">宿泊 4</text>
    <text x="1000" y="584">访问 3</text>
    <text x="1000" y="634">接地 2</text>
    <text x="1000" y="684">通过 1</text>
    <text x="998" y="734">没去过</text>
  </g>
  <text id="credit" x="37" y="937">cn-ex</text>
</svg>
`;

const $ = (sel, root = document) => root.querySelector(sel);

const mapHost = $('#map-host');
const picker = $('#picker');
const pickerName = $('#picker-name');
const pickerSearch = $('#picker-search');
const pickerClose = $('#picker-close');
const toastEl = $('#toast');
const statusHint = $('#status-hint');
const exportModal = $('#export-modal');
const exportImg = $('#export-img');
const exportDownload = $('#export-download');

mapHost.innerHTML = MAP_SVG;

const svg = mapHost.querySelector('svg');
const regions = $('#regions', svg);
const scoreEl = $('#score', svg);
const titleEl = $('#title', svg);
const provinceEls = PROVINCES.map((id) => {
  const el = svg.getElementById(id);
  if (!el) console.warn('missing province path', id);
  return el;
});

let activeProvince = null;
let toastTimer = 0;

function clampLevel(n) {
  const v = Number.parseInt(n, 10);
  if (!Number.isFinite(v) || v < 0) return 0;
  if (v > 5) return 5;
  return v;
}

function applyPaletteToMapChrome() {
  svg?.querySelectorAll('.legend-swatch[data-level]').forEach((node) => {
    const lv = clampLevel(node.getAttribute('data-level'));
    node.setAttribute('fill', LEVELS[lv].color);
  });
  const mapBgEl = svg?.querySelector('#map-bg');
  if (mapBgEl) mapBgEl.setAttribute('fill', MAP_BG);
}

function normalizeLevels(raw) {
  const s = String(raw || '').replace(/\D/g, '');
  const chars = Array.from({ length: PROVINCE_COUNT }, (_, i) => {
    const c = s[i];
    return c === undefined ? '0' : String(clampLevel(c));
  });
  return chars.join('');
}

function getLevelsString() {
  return provinceEls
    .map((el) => (el?.getAttribute('data-level') || '0'))
    .join('');
}

function setLevelsString(raw, { silentUrl = false } = {}) {
  const levels = normalizeLevels(raw);
  provinceEls.forEach((el, i) => {
    if (!el) return;
    el.setAttribute('data-level', levels[i] || '0');
  });
  updateScore();
  persist(levels, { silentUrl });
  return levels;
}

function scoreOf(levels = getLevelsString()) {
  return [...levels].reduce((sum, c) => sum + clampLevel(c), 0);
}

function updateScore() {
  const s = scoreOf();
  if (scoreEl) scoreEl.textContent = `分数: ${s}`;
  return s;
}

function readQueryLevels() {
  const params = new URLSearchParams(window.location.search);
  const l = params.get(LEVEL_PARAM);
  return l == null || l === '' ? null : normalizeLevels(l);
}

function readQueryTitle() {
  const params = new URLSearchParams(window.location.search);
  const t = params.get(TITLE_PARAM);
  return t && t.trim() ? t.trim().slice(0, 32) : '';
}

function applyTitle(name) {
  if (!titleEl) return;
  titleEl.textContent = name || '中国制霸';
}

function persist(levels = getLevelsString(), { silentUrl = false } = {}) {
  try {
    localStorage.setItem(STORAGE_KEY, levels);
  } catch {
    /* private mode etc. */
  }

  if (silentUrl) return;

  const params = new URLSearchParams(window.location.search);
  params.set(LEVEL_PARAM, levels);
  const title = readQueryTitle();
  if (title) params.set(TITLE_PARAM, title);
  else params.delete(TITLE_PARAM);

  const qs = params.toString();
  const next = `${window.location.pathname}?${qs}${window.location.hash || ''}`;
  const current = `${window.location.pathname}${window.location.search}${window.location.hash || ''}`;
  if (next !== current) {
    history.replaceState(null, '', next);
  }
}

function loadInitial() {
  const fromUrl = readQueryLevels();
  const fromStore = (() => {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch {
      return null;
    }
  })();

  applyTitle(readQueryTitle());

  if (fromUrl) {
    setLevelsString(fromUrl, { silentUrl: false });
    statusHint.textContent = '已从链接 ?l= 恢复标记';
    return;
  }
  if (fromStore) {
    setLevelsString(fromStore, { silentUrl: false });
    statusHint.textContent = '已从本地存储恢复；改动会同步到地址栏';
    return;
  }
  setLevelsString('0'.repeat(PROVINCE_COUNT), { silentUrl: false });
  statusHint.textContent = '点省份设置等级；状态写入 ?l= 与本地存储';
}

function hidePicker() {
  picker.hidden = true;
  picker.classList.remove('is-open');
  activeProvince = null;
}

function showPicker(provinceEl, clientX, clientY) {
  activeProvince = provinceEl;
  const name = provinceEl.id;
  pickerName.textContent = name;
  pickerSearch.href = `https://www.google.com/search?q=${encodeURIComponent(name + ' 旅游')}`;
  pickerSearch.title = `搜索：${name}`;

  const current = clampLevel(provinceEl.getAttribute('data-level') || 0);
  picker.querySelectorAll('.picker-item').forEach((item) => {
    const lv = clampLevel(item.getAttribute('data-level'));
    item.classList.toggle('is-selected', lv === current);
  });

  picker.hidden = false;
  picker.classList.remove('is-open');
  // measure off-screen first
  picker.style.left = '-9999px';
  picker.style.top = '0px';

  const stage = picker.parentElement.getBoundingClientRect();
  const pr = picker.getBoundingClientRect();
  let left = clientX - stage.left - pr.width / 2;
  let top = clientY - stage.top - pr.height / 2;
  left = Math.max(8, Math.min(left, stage.width - pr.width - 8));
  top = Math.max(8, Math.min(top, stage.height - pr.height - 8));
  picker.style.left = `${left}px`;
  picker.style.top = `${top}px`;

  // next frame fade-in like JapanEx
  requestAnimationFrame(() => picker.classList.add('is-open'));
}

function toast(msg) {
  toastEl.textContent = msg;
  toastEl.hidden = false;
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => {
    toastEl.hidden = true;
  }, 1800);
}

async function copyShareLink() {
  persist();
  const url = window.location.href;
  try {
    await navigator.clipboard.writeText(url);
    toast('链接已复制');
  } catch {
    window.prompt('复制链接：', url);
  }
}

function resetAll() {
  if (!window.confirm('清空所有省份标记？')) return;
  setLevelsString('0'.repeat(PROVINCE_COUNT));
  toast('已清空');
}

function svgToBlobUrl() {
  const clone = svg.cloneNode(true);
  // ensure solid fills for export (computed styles may not travel)
  clone.querySelectorAll('#regions path').forEach((p) => {
    const lv = clampLevel(p.getAttribute('data-level') || 0);
    p.setAttribute('fill', LEVELS[lv].color);
    p.setAttribute('stroke', '#333');
    p.setAttribute('stroke-width', '4');
  });
  const bg = clone.querySelector('#map-bg');
  if (bg) bg.setAttribute('fill', MAP_BG);
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
  clone.setAttribute('width', '1134');
  clone.setAttribute('height', '976');
  const xml = new XMLSerializer().serializeToString(clone);
  const blob = new Blob([xml], { type: 'image/svg+xml;charset=utf-8' });
  return URL.createObjectURL(blob);
}

async function saveImage() {
  document.body.classList.add('is-exporting');
  const url = svgToBlobUrl();
  try {
    const img = new Image();
    img.decoding = 'async';
    await new Promise((resolve, reject) => {
      img.onload = resolve;
      img.onerror = reject;
      img.src = url;
    });

    const scale = 2;
    const w = 1134 * scale;
    const h = 976 * scale;
    const canvas = document.createElement('canvas');
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = MAP_BG;
    ctx.fillRect(0, 0, w, h);
    ctx.drawImage(img, 0, 0, w, h);

    const pngUrl = await new Promise((resolve) => {
      canvas.toBlob((b) => resolve(URL.createObjectURL(b)), 'image/png');
    });

    exportImg.src = pngUrl;
    exportDownload.href = pngUrl;
    exportModal.hidden = false;
  } catch (err) {
    console.error(err);
    toast('导出失败，可再试一次');
  } finally {
    URL.revokeObjectURL(url);
    document.body.classList.remove('is-exporting');
  }
}

// events
regions?.addEventListener('click', (e) => {
  const path = e.target.closest('path');
  if (!path || path.parentElement?.id !== 'regions') return;
  e.stopPropagation();
  showPicker(path, e.clientX, e.clientY);
});


pickerClose?.addEventListener('click', (e) => {
  e.stopPropagation();
  hidePicker();
});
pickerSearch?.addEventListener('click', (e) => {
  e.stopPropagation();
});

picker.addEventListener('click', (e) => {
  e.stopPropagation();
  const btn = e.target.closest('.picker-item[data-level]');
  if (!btn || !activeProvince) return;
  const level = clampLevel(btn.getAttribute('data-level'));
  activeProvince.setAttribute('data-level', String(level));
  updateScore();
  persist();
  hidePicker();
});

document.addEventListener('click', () => hidePicker());
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    hidePicker();
    exportModal.hidden = true;
  }
});

$('#btn-copy').addEventListener('click', (e) => {
  e.stopPropagation();
  copyShareLink();
});
$('#btn-save').addEventListener('click', (e) => {
  e.stopPropagation();
  saveImage();
});
$('#btn-reset').addEventListener('click', (e) => {
  e.stopPropagation();
  resetAll();
});
$('#export-close').addEventListener('click', () => {
  exportModal.hidden = true;
});
exportModal.addEventListener('click', (e) => {
  if (e.target === exportModal) exportModal.hidden = true;
});

// boot
applyPaletteToMapChrome();
loadInitial();

// expose for debug
window.CnEx = {
  getLevels: getLevelsString,
  setLevels: setLevelsString,
  score: () => scoreOf(),
  provinces: PROVINCES,
};
