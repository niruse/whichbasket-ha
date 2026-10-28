/* shopping-compare-web-card — the supermarket list and where it costs least, from the price comparison website
 * (the shopping_compare_web integration does the talking; this card only talks to Home Assistant).
 *
 *   type: custom:shopping-compare-web-card
 *   view: full | list | compare | summary      (default full: the list and the comparison as two tabs)
 *   entry_id: <config entry>                    (only with more than one set-up)
 *   title: <text>
 *
 * Text reaches the page only as text (textContent, text nodes): no HTML strings, no inline handlers.
 */
const DOMAIN = "shopping_compare_web";
const CHAIN_COLORS = { shufersal: "#d71920", rami_levy: "#0a4da2", carrefour: "#1e5bc6", victory: "#f28c00", mahsanei_hashuk: "#2e9e44" };
const CHAIN_NAMES = { shufersal: ["שופרסל", "Shufersal"], rami_levy: ["רמי לוי", "Rami Levy"], carrefour: ["קרפור", "Carrefour"],
  victory: ["ויקטורי", "Victory"], mahsanei_hashuk: ["מחסני השוק", "Mahsanei HaShuk"] };
const LOCALES = { he: "he-IL", en: "en-IL", ru: "ru-RU" };
const T = {
  he: {
    title: "השוואת מחירים לסופר", tab_list: "רשימה", tab_compare: "השוואה", items: "{n} פריטים", empty: "הרשימה ריקה. חפשו מוצר והוסיפו.",
    search: "חיפוש מוצר", search_go: "חיפוש", searching: "מחפשים…", no_results: "לא נמצאו מוצרים.", add_text: "הוספה כמו שהוא: {text}",
    added: "נוסף: {name}", removed: "הוסר: {name}", qty: "כמות של {name}", less: "פחות {name}", more: "עוד {name}", remove: "הסרת {name}", remove_q: "להסיר את {name} מהרשימה?", remove_yes: "הסרה", cancel: "ביטול",
    sold_at: "נמכר ב: {chains}", not_at: "לא נמכר ב: {chains}", cheapest: "הכי זול", pay: "סה״כ",
    whole: "כל הרשימה (החסרים מסניף זול אחר): {total}", found: "✓ {found} מתוך {all}", missing: "✗ חסרים {n}",
    other_n: "⚠ {n} בגודל אחר (לא נספרו)", unsure_n: "{n} התאמות לא בטוחות", open_cart: "פתיחת העגלה ב{chain}", cart_before: "לפני שממשיכים ל{chain}", cart_go: "הבנתי, לפתיחת העגלה",
    cart_check: "חשוב: האחריות לבדוק את העגלה היא שלכם. לפני התשלום ודאו באתר של {chain} שכל המוצרים נכנסו, ושהגדלים, הכמויות והמחירים נכונים. המחיר הקובע הוא זה שבאתר הרשת או בקופה.",
    best: "הכי זול: {branch}", saving: "חיסכון: {n}", no_compare: "עוד אין השוואה.", compare_now: "השוואה עכשיו", comparing: "משווים…",
    updated: "המחירים עודכנו: {time}", site_down: "אין חיבור לאתר. מוצגת ההשוואה האחרונה.", busy: "האתר עמוס, ננסה שוב בעוד דקה.",
    no_branches: "לא נבחרו סניפים. אפשר לבחור בהגדרות האינטגרציה.", partial: "חלק מהמוצרים עוד מותאמים. ההשוואה תתעדכן עוד רגע.",
    item: "מוצר", not_sold: "לא נמכר", not_checked: "עוד לא נבדק", other_size: "גודל אחר", not_counted: "לא נספר בסכום",
    asked: "ברשימה: {size}", sizes_differ: "גדלים שונים בין הרשתות", similar: "מוצר דומה", unsure: "התאמה לא בטוחה",
    yours: "הבחירה שלכם", by_admin: "לפי האתר", change: "שינוי", change_label: "בחירת מוצר אחר ב{chain} עבור {name}",
    fix_title: "{name} ב{chain}", fix_now: "עכשיו: {name}, {price}", fix_none: "אין כרגע מוצר מתאים ברשת הזו.",
    fix_search: "חיפוש מוצר ב{chain}", fix_not_sold: "לא נמכר ב{chain}", fix_auto: "חזרה להתאמה האוטומטית", close: "סגירה",
    fix_note: "הבחירה חלה מיד על הרשימה שלכם. היא נשלחת גם למנהל האתר כהצעה, ותחול על כולם רק אחרי שיאשר אותה.",
    fix_note_private: "הבחירה חלה רק על הרשימה שלכם.", now: "עכשיו", not_here: "לא בסניף שבחרתם", saved: "נשמר",
    not_set_up: "האינטגרציה \"השוואת מחירים לסופר\" לא מוגדרת.", error: "שגיאה: {n}", pack_of: "מארז {n}",
    legend: "≈ מוצר דומה: לא אותו ברקוד, נבחר לפי השם. ⚠ גודל אחר: לא נספר בסכום עד שתבחרו בו.", branches: "{n} סניפים",
    ideas: "רעיון לשיפור", new_tab: "נפתח בלשונית חדשה",
  },
  en: {
    title: "Supermarket price compare", tab_list: "List", tab_compare: "Compare", items: "{n} items", empty: "The list is empty. Search for a product to add.",
    search: "Search for a product", search_go: "Search", searching: "Searching…", no_results: "No products found.", add_text: "Add as typed: {text}",
    added: "Added: {name}", removed: "Removed: {name}", qty: "Quantity of {name}", less: "One less {name}", more: "One more {name}", remove: "Remove {name}", remove_q: "Remove {name} from the list?", remove_yes: "Remove", cancel: "Cancel",
    sold_at: "Sold at: {chains}", not_at: "Not sold at: {chains}", cheapest: "Cheapest", pay: "Total",
    whole: "The whole list (missing items from a cheaper branch): {total}", found: "✓ {found} of {all}", missing: "✗ {n} missing",
    other_n: "⚠ {n} in another size (not counted)", unsure_n: "{n} uncertain matches", open_cart: "Open the cart at {chain}", cart_before: "Before you go to {chain}", cart_go: "I understand, open the cart",
    cart_check: "Important: checking the cart is your responsibility. Before paying, make sure on {chain}'s site that every product went in and that the sizes, quantities and prices are right. The price that counts is the one on the chain's site or at the till.",
    best: "Cheapest: {branch}", saving: "Saving: {n}", no_compare: "No comparison yet.", compare_now: "Compare now", comparing: "Comparing…",
    updated: "Prices updated: {time}", site_down: "Can't reach the site. Showing the last comparison.", busy: "The site is busy, trying again in a minute.",
    no_branches: "No branches chosen. Choose them in the integration's settings.", partial: "Some products are still being matched. The comparison updates in a moment.",
    item: "Product", not_sold: "Not sold", not_checked: "Not checked yet", other_size: "Another size", not_counted: "Not in the total",
    asked: "On your list: {size}", sizes_differ: "Different sizes in different chains", similar: "Similar product", unsure: "Uncertain match",
    yours: "Your choice", by_admin: "Set by the site", change: "Change", change_label: "Choose another product at {chain} for {name}",
    fix_title: "{name} at {chain}", fix_now: "Now: {name}, {price}", fix_none: "No matching product at this chain yet.",
    fix_search: "Search {chain}", fix_not_sold: "Not sold at {chain}", fix_auto: "Back to the automatic match", close: "Close",
    fix_note: "Your choice applies to your list at once. It is also sent to the site's admin as a suggestion, and applies to everyone only once the admin approves it.",
    fix_note_private: "Your choice applies to your list only.", now: "Now", not_here: "Not in your branch", saved: "Saved",
    not_set_up: "The Supermarket price compare integration isn't set up.", error: "Error: {n}", pack_of: "pack of {n}",
    legend: "≈ Similar product: not the same barcode, matched by name. ⚠ Another size: not counted until you choose it.", branches: "{n} branches",
    ideas: "Suggest an idea", new_tab: "opens in a new tab",
  },
  ru: {
    title: "Сравнение цен в супермаркетах", tab_list: "Список", tab_compare: "Сравнение", items: "Товаров: {n}", empty: "Список пуст. Найдите товар и добавьте его.",
    search: "Поиск товара", search_go: "Найти", searching: "Ищем…", no_results: "Товары не найдены.", add_text: "Добавить как есть: {text}",
    added: "Добавлено: {name}", removed: "Удалено: {name}", qty: "Количество: {name}", less: "Меньше: {name}", more: "Больше: {name}", remove: "Удалить {name}", remove_q: "Удалить {name} из списка?", remove_yes: "Удалить", cancel: "Отмена",
    sold_at: "Продаётся в: {chains}", not_at: "Не продаётся в: {chains}", cheapest: "Дешевле всего", pay: "Итого",
    whole: "Весь список (недостающее из другого дешёвого филиала): {total}", found: "✓ {found} из {all}", missing: "✗ нет: {n}",
    other_n: "⚠ другого размера: {n} (не учтены)", unsure_n: "Неточных совпадений: {n}", open_cart: "Открыть корзину: {chain}", cart_before: "Перед переходом в {chain}", cart_go: "Понятно, открыть корзину",
    cart_check: "Важно: проверить корзину — ваша ответственность. Перед оплатой убедитесь на сайте {chain}, что все товары добавлены, а размеры, количество и цены верны. Действует цена на сайте сети или на кассе.",
    best: "Дешевле всего: {branch}", saving: "Экономия: {n}", no_compare: "Сравнения пока нет.", compare_now: "Сравнить сейчас", comparing: "Сравниваем…",
    updated: "Цены обновлены: {time}", site_down: "Нет связи с сайтом. Показано последнее сравнение.", busy: "Сайт занят, попробуем через минуту.",
    no_branches: "Филиалы не выбраны. Выберите их в настройках интеграции.", partial: "Часть товаров ещё подбирается. Сравнение скоро обновится.",
    item: "Товар", not_sold: "Нет", not_checked: "Ещё не проверено", other_size: "Другой размер", not_counted: "Не входит в сумму",
    asked: "В списке: {size}", sizes_differ: "В разных сетях разный размер", similar: "Похожий товар", unsure: "Неточное совпадение",
    yours: "Ваш выбор", by_admin: "Выбрано сайтом", change: "Изменить", change_label: "Выбрать другой товар в {chain} для «{name}»",
    fix_title: "{name}: {chain}", fix_now: "Сейчас: {name}, {price}", fix_none: "Подходящего товара в этой сети пока нет.",
    fix_search: "Поиск товара в {chain}", fix_not_sold: "Не продаётся в {chain}", fix_auto: "Вернуть автоматический выбор", close: "Закрыть",
    fix_note: "Ваш выбор сразу применяется к вашему списку. Он также отправляется администратору сайта как предложение и станет общим только после его одобрения.",
    fix_note_private: "Ваш выбор применяется только к вашему списку.", now: "Сейчас", not_here: "Нет в вашем филиале", saved: "Сохранено",
    not_set_up: "Интеграция «Сравнение цен в супермаркетах» не настроена.", error: "Ошибка: {n}", pack_of: "упаковка {n}",
    legend: "≈ Похожий товар: другой штрихкод, подобран по названию. ⚠ Другой размер: не учитывается, пока вы его не выберете.", branches: "Филиалов: {n}",
    ideas: "Предложить идею", new_tab: "откроется в новой вкладке",
  },
};
const SIZE_UNITS = { he: { g: "גרם", kg: "ק״ג", ml: "מ״ל", l: "ליטר", pcs: "יח׳", m: "מ׳" },
  en: { g: "g", kg: "kg", ml: "ml", l: "l", pcs: "pcs", m: "m" }, ru: { g: "г", kg: "кг", ml: "мл", l: "л", pcs: "шт.", m: "м" } };

function h(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v === true ? "" : String(v));
  }
  for (const c of children.flat()) {
    if (c === null || c === undefined || c === false) continue;
    node.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return node;
}

class ShoppingCompareWebCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._tab = "list";
    this._results = null;
    this._fix = null;
    this._status = "";
  }

  static getStubConfig() { return { view: "full" }; }

  setConfig(config) {
    const view = ["full", "list", "compare", "summary"].includes(config && config.view) ? config.view : "full";
    this._config = { ...config, view };
    this._tab = view === "compare" ? "compare" : "list";
    if (this._snap) this._render();
  }

  getCardSize() { return this._config && this._config.view === "summary" ? 3 : 10; }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    const lang = (hass.locale && hass.locale.language) || hass.language || "he";
    const next = T[lang.slice(0, 2)] ? lang.slice(0, 2) : "en";
    if (next !== this._lang) { this._lang = next; if (this._snap) this._render(); }
    // the green, amber and red text keep their contrast on a dark theme too
    this.classList.toggle("dark", Boolean(hass.themes && hass.themes.darkMode));
    if (first || !this._unsub) this._subscribe();
  }

  connectedCallback() { if (this._hass && !this._unsub) this._subscribe(); }

  disconnectedCallback() {
    if (this._unsub) { Promise.resolve(this._unsub).then((u) => typeof u === "function" && u()).catch(() => {}); }
    this._unsub = null;
  }

  // ---- talking to the integration ---------------------------------------------------------------------
  _msg(type, extra = {}) {
    const m = { type: `${DOMAIN}/${type}`, ...extra };
    if (this._config && this._config.entry_id) m.entry_id = String(this._config.entry_id);
    return m;
  }

  _shadow() { return this.shadowRoot; }

  _subscribe() {
    if (this._subscribing || !this._hass || !this._hass.connection) return;
    if (this._retryAt && Date.now() < this._retryAt) return;      // not set up: ask again in a while, not on every update
    this._subscribing = true;
    this._retryAt = Date.now() + 30000;
    this._unsub = this._hass.connection.subscribeMessage((snap) => { this._error = null; this._retryAt = 0; this._snap = snap; this._render(); }, this._msg("subscribe"))
      .catch((err) => { this._unsub = null; this._error = (err && err.code) === "not_set_up" ? "not_set_up" : "error"; this._render(); })
      .finally(() => { this._subscribing = false; });
  }

  async _call(type, extra = {}) {
    try {
      return await this._hass.connection.sendMessagePromise(this._msg(type, extra));
    } catch (err) {
      this._say((err && err.code) === "busy" ? this._t("busy") : this._t("error", { n: (err && err.message) || "?" }));
      throw err;
    }
  }

  // ---- words and numbers ------------------------------------------------------------------------------
  _t(key, vars = {}) {
    const table = T[this._lang] || T.en;
    let text = table[key] ?? T.en[key] ?? key;
    for (const [k, v] of Object.entries(vars)) text = text.split(`{${k}}`).join(String(v));
    return text;
  }

  _money(v) {
    return new Intl.NumberFormat(LOCALES[this._lang] || "he-IL", { style: "currency", currency: "ILS" }).format(Number(v) || 0);
  }

  _chain(key) { const n = CHAIN_NAMES[key]; return n ? n[this._lang === "he" ? 0 : 1] : String(key || ""); }

  _branch(b) {
    const info = b || {};
    const chain = CHAIN_NAMES[info.chain] ? this._chain(info.chain) : (this._lang === "he" ? info.chain_name : info.chain_name_en || info.chain_name) || "";
    return `${chain} · ${info.name || ""}`.replace(/ · $/, "");
  }

  _name(p) {
    if (this._lang === "en" && p.name_en) return { text: p.name_en, lang: "en" };
    if (this._lang === "ru" && p.name_ru) return { text: p.name_ru, lang: "ru" };
    return { text: p.name || "", lang: "he" };
  }

  _amount(v, unit) {
    const u = SIZE_UNITS[this._lang] || SIZE_UNITS.he;
    const n = (x) => new Intl.NumberFormat(LOCALES[this._lang] || "he-IL", { maximumFractionDigits: 2 }).format(x);
    if (unit === "g" && v >= 1000) return `${n(v / 1000)} ${u.kg}`;
    if (unit === "ml" && v >= 1000) return `${n(v / 1000)} ${u.l}`;
    return `${n(v)} ${u[unit] || ""}`.trim();
  }

  _size(s) {
    if (!s || typeof s !== "object") return "";
    const ok = (v) => Number.isFinite(v) && v > 0;
    const count = Number.isInteger(s.count) && s.count > 1 ? s.count : 0;
    if (count && ok(s.each)) return `${count} × ${this._amount(s.each, s.unit)}`;
    if (ok(s.total)) return count && s.unit !== "pcs" ? `${this._t("pack_of", { n: count })} · ${this._amount(s.total, s.unit)}` : this._amount(s.total, s.unit);
    return count ? this._amount(count, "pcs") : "";
  }

  _say(text) {
    this._status = text;
    const live = this.shadowRoot && this.shadowRoot.getElementById("live");
    if (live) { live.textContent = ""; setTimeout(() => { live.textContent = text; }, 50); }
  }

  // counted: priced and of the size the line asks for (an automatic match of another size isn't added up)
  _counts(c) { return Boolean(c) && c.counted !== false; }

  // ---- drawing --------------------------------------------------------------------------------------------
  _render() {
    const root = this._shadow();
    const active = root.activeElement;
    // a box being typed in keeps its text and caret through a redraw (a new comparison may arrive meanwhile)
    const keep = active && (active.id === "q" || active.id === "fq") ? { id: active.id, start: active.selectionStart } : null;
    // any other control keeps the focus through a redraw by its focus key (a new comparison redraws the whole card)
    const fk = !keep && active && active.getAttribute ? active.getAttribute("data-fk") : null;
    const dir = this._lang === "he" ? "rtl" : "ltr";
    const card = h("ha-card", { dir, lang: this._lang });
    const view = this._config ? this._config.view : "full";
    if (this._error && !this._snap) {
      card.append(h("div", { class: "pad error", text: this._t(this._error === "not_set_up" ? "not_set_up" : "error", { n: "" }) }));
    } else if (!this._snap) {
      card.append(h("div", { class: "pad muted", text: "…" }));
    } else if (view === "summary") {
      card.append(this._header(), this._summary());
    } else {
      card.append(this._header());
      if (view === "full") card.append(this._tabs());
      const tab = view === "full" ? this._tab : view;
      card.append(tab === "compare" ? this._compare() : this._list());
    }
    card.append(h("p", { id: "live", class: "sr", role: "status", "aria-live": "polite" }));
    root.replaceChildren(h("style", { text: CSS }), card, ...(this._fix ? [this._fixSheet()] : []), ...(this._ask ? [this._askSheet()] : []),
      ...(this._cart ? [this._cartSheet()] : []));
    if (keep) {
      const box = root.getElementById(keep.id);
      if (box) { box.focus(); try { box.setSelectionRange(keep.start, keep.start); } catch (e) { /* type */ } }
    }
    if (this._focusAfter) {
      const target = this._focusAfter();
      this._focusAfter = null;
      if (target) target.focus();
    } else if (fk) {
      const again = [...root.querySelectorAll("[data-fk]")].find((x) => x.getAttribute("data-fk") === fk);
      if (again) again.focus();
    }
  }

  _header() {
    const s = this._snap;
    const best = s.result && s.result.branches.find((b) => b.cheapest);
    const title = (this._config && this._config.title) || this._t("title");
    return h("div", { class: "head" },
      h("div", { class: "titles" }, h("h2", { text: title }),
        h("span", { class: "muted", text: [s.city && (this._lang === "he" ? s.city.he : s.city.en || s.city.he), this._t("items", { n: s.lines.length })].filter(Boolean).join(" · ") })),
      best ? h("div", { class: "best" }, h("span", { text: this._t("cheapest") }), h("b", { text: this._branch(best) }), h("b", { class: "num", text: this._money(best.fair) })) : null);
  }

  _tabs() {
    const tab = (name, label) => h("button", { type: "button", role: "tab", class: this._tab === name ? "tab on" : "tab", "data-fk": `tab:${name}`,
      "aria-selected": String(this._tab === name), onclick: () => { this._tab = name; this._render(); } }, label);
    return h("div", { class: "tabs", role: "tablist" }, tab("list", this._t("tab_list")), tab("compare", this._t("tab_compare")));
  }

  _notes() {
    const s = this._snap;
    const out = [];
    if (s.error === "busy") out.push(h("p", { class: "note warn", text: this._t("busy") }));
    else if (s.error) out.push(h("p", { class: "note warn", text: this._t("site_down") }));
    if (!s.branches.length) out.push(h("p", { class: "note warn", text: this._t("no_branches") }));
    if (s.result && s.result.partial) out.push(h("p", { class: "note", text: this._t("partial") }));
    return out;
  }

  // ---- the list ------------------------------------------------------------------------------------------
  _list() {
    const s = this._snap;
    const box = h("div", { class: "body" });
    const input = h("input", { id: "q", type: "text", enterkeyhint: "search", maxlength: "60", autocomplete: "off",
      placeholder: this._t("search"), "aria-label": this._t("search"), value: this._q || "" });
    input.addEventListener("input", () => { this._q = input.value; });
    const form = h("form", { class: "search", role: "search" }, input, h("button", { type: "submit", class: "btn" }, this._t("search_go")));
    form.addEventListener("submit", (e) => { e.preventDefault(); this._search(input.value.trim()); });
    box.append(form);
    if (this._results) box.append(this._searchResults());
    box.append(...this._notes());
    if (!s.lines.length) {
      box.append(h("p", { class: "empty", text: this._t("empty") }));
      return box;
    }
    const ul = h("ul", { class: "lines" });
    for (const line of s.lines) ul.append(this._line(line));
    box.append(ul, this._footer());
    return box;
  }

  async _search(q) {
    if (!q) { this._results = null; this._render(); return; }
    this._results = { q, rows: null };
    this._render();
    try {
      const rows = await this._call("search", { query: q.slice(0, 60) });
      if (this._results && this._results.q === q) { this._results.rows = Array.isArray(rows) ? rows : []; this._render(); }
    } catch (e) { if (this._results && this._results.q === q) { this._results.rows = []; this._render(); } }
  }

  _searchResults() {
    const r = this._results;
    const box = h("div", { class: "results" });
    if (!r.rows) { box.append(h("p", { class: "muted", text: this._t("searching") })); return box; }
    const ul = h("ul", { class: "products" });
    for (const p of r.rows.slice(0, 24)) ul.append(this._product(p));
    ul.append(h("li", {}, h("button", { type: "button", class: "product text",
      onclick: () => this._add({ key: `t:${r.q}`.slice(0, 200), name: r.q.slice(0, 120) }) }, this._t("add_text", { text: r.q }))));
    if (!r.rows.length) box.append(h("p", { class: "muted", text: this._t("no_results") }));
    box.append(ul, h("button", { type: "button", class: "link", onclick: () => { this._results = null; this._render(); } }, this._t("close")));
    return box;
  }

  _avail(chains, compact = false) {
    const sold = (Array.isArray(chains) ? chains : []).filter((c) => typeof c === "string");
    if (!sold.length) return null;
    const mine = [...new Set(this._snap.branches.map((b) => b.chain).filter(Boolean))];
    const lacking = mine.filter((c) => !sold.includes(c));
    const text = [this._t("sold_at", { chains: sold.map((c) => this._chain(c)).join(", ") }),
      lacking.length ? this._t("not_at", { chains: lacking.map((c) => this._chain(c)).join(", ") }) : ""].filter(Boolean).join(". ");
    const tags = h("span", { class: compact ? "avail compact" : "avail", "aria-hidden": "true" },
      sold.map((c) => h("span", { class: "atag" }, h("i", { class: "dot", style: `background:${CHAIN_COLORS[c] || "#888"}` }), this._chain(c))),
      lacking.map((c) => h("span", { class: "atag no" }, h("b", { text: "✗" }), this._chain(c))));
    return h("span", { class: "availwrap" }, h("span", { class: "sr", text: text }), tags);
  }

  _product(p) {
    const name = this._name(p);
    const prices = Object.values(p.prices || {}).filter(Number.isFinite);
    const price = prices.length ? (Math.min(...prices) === Math.max(...prices) ? this._money(prices[0]) : `${this._money(Math.min(...prices))}+`) : this._t("not_here");
    return h("li", {}, h("button", { type: "button", class: "product", "data-fk": `add:${p.key}`, onclick: () => this._add(p) },
      h("span", { class: "pname", lang: name.lang, text: name.text }),
      this._size(p.size) ? h("small", { text: this._size(p.size) }) : null,
      h("b", { class: "num", text: price }), this._avail(p.chains, true)));
  }

  async _add(p) {
    const product = { key: p.key, name: p.name };
    for (const k of ["name_en", "name_ru", "barcode"]) if (typeof p[k] === "string" && p[k]) product[k] = p[k];
    if (p.weighted === true) product.weighted = true;
    if (Array.isArray(p.chains)) product.chains = p.chains.filter((c) => CHAIN_NAMES[c]).slice(0, 10);
    try {
      await this._call("add", { product, qty: 1 });
      this._say(this._t("added", { name: this._name(p).text }));
    } catch (e) { /* said */ }
  }

  // − takes a step off; at the least amount (1, or half a kilo) it is a bin. Every removal asks first.
  _line(line) {
    const name = this._name(line);
    const step = line.weighted ? 0.5 : 1;
    const last = line.qty - step < step / 2;
    const set = (qty) => this._call("qty", { uid: line.uid, qty: Math.max(step, Math.round(qty * 100) / 100) }).catch(() => {});
    const less = h("button", { type: "button", class: last ? "icon less last" : "icon less", "data-fk": `less:${line.uid}`,
      "aria-label": this._t(last ? "remove" : "less", { name: name.text }),
      onclick: () => (last ? this._askRemove(line, name.text, "less") : set(line.qty - step)) }, last ? "🗑" : "−");
    const del = h("button", { type: "button", class: "icon del", "data-fk": `del:${line.uid}`, "aria-label": this._t("remove", { name: name.text }),
      onclick: () => this._askRemove(line, name.text, "del") }, "✕");
    less.dataset.uid = line.uid;
    del.dataset.uid = line.uid;
    return h("li", { class: "line" },
      h("div", { class: "grow" }, h("b", { lang: name.lang, text: name.text }), this._avail(line.chains), this._chips(line)),
      h("div", { class: "ctl" },                          // the amount and the ✕ stay together when the line wraps
        h("div", { class: "stepper" }, less,
          h("span", { class: "qty", "aria-label": this._t("qty", { name: name.text }), text: String(line.qty) }),
          h("button", { type: "button", class: "icon", "data-fk": `more:${line.uid}`, "aria-label": this._t("more", { name: name.text }),
            onclick: () => set(line.qty + step) }, "+")),
        del));
  }

  // ---- "are you sure?" -----------------------------------------------------------------------------------
  _askRemove(line, label, from) {
    const uids = this._snap.lines.map((x) => x.uid);
    this._ask = { uid: line.uid, label, from, at: uids.indexOf(line.uid) };
    this._render();
    const cancel = this.shadowRoot.getElementById("ask-cancel");   // Enter alone removes nothing
    if (cancel) cancel.focus();
  }

  _closeAsk(yes) {
    const a = this._ask;
    this._ask = null;
    if (!a) return;
    const buttons = (cls) => [...this.shadowRoot.querySelectorAll(`.line button.${cls}`)];
    if (yes) {
      this._call("remove", { uid: a.uid }).then(() => this._say(this._t("removed", { name: a.label }))).catch(() => {});
      // the focus goes to the next line's bin once the list is drawn again without it
      this._focusAfter = () => { const left = buttons("del").filter((x) => x.dataset.uid !== a.uid); return left[Math.min(a.at, left.length - 1)] || null; };
    } else {
      this._focusAfter = () => buttons(a.from).find((x) => x.dataset.uid === a.uid) || null;
    }
    this._render();
  }

  _askSheet() {
    const a = this._ask;
    const sheet = h("div", { class: "sheet ask", role: "alertdialog", "aria-modal": "true", "aria-labelledby": "ask-title",
      dir: this._lang === "he" ? "rtl" : "ltr" },
    h("h3", { id: "ask-title", text: this._t("remove_q", { name: a.label }) }),
    h("div", { class: "actions" },
      h("button", { type: "button", class: "btn danger", onclick: () => this._closeAsk(true) }, `🗑 ${this._t("remove_yes")}`),
      h("button", { type: "button", id: "ask-cancel", class: "btn", onclick: () => this._closeAsk(false) }, this._t("cancel"))));
    return this._modal(sheet, () => this._closeAsk(false));
  }

  // ---- before the chain's shop opens: checking the cart is the shopper's; the shop opens from the link here ----
  _cartAsk(b) {
    this._cart = { url: b.cart_url, chain: b.chain, id: b.id };
    this._render();
    const go = this.shadowRoot.getElementById("cart-go");
    if (go) go.focus();
  }

  _closeCart() {
    const c = this._cart;
    this._cart = null;
    if (c) this._focusAfter = () => [...this.shadowRoot.querySelectorAll("[data-fk]")].find((x) => x.getAttribute("data-fk") === `cart:${c.id}`) || null;
    this._render();
  }

  _cartSheet() {
    const c = this._cart;
    const chain = this._chain(c.chain);
    const sheet = h("div", { class: "sheet ask", role: "dialog", "aria-modal": "true", "aria-labelledby": "cart-title",
      "aria-describedby": "cart-text", dir: this._lang === "he" ? "rtl" : "ltr" },
    h("h3", { id: "cart-title", text: this._t("cart_before", { chain }) }),
    h("p", { id: "cart-text", class: "important", text: `⚠️ ${this._t("cart_check", { chain })}` }),
    h("div", { class: "actions" },
      h("a", { id: "cart-go", class: "btn primary", href: c.url, target: "_blank", rel: "noopener noreferrer",
        onclick: () => setTimeout(() => this._closeCart(), 0) }, this._t("cart_go")),
      h("button", { type: "button", class: "btn", onclick: () => this._closeCart() }, this._t("cancel"))));
    return this._modal(sheet, () => this._closeCart());
  }

  // a sheet over the card: a tap outside or Escape closes it, and Tab stays inside it
  _modal(sheet, close) {
    const shade = h("div", { class: "shade", onclick: (e) => { if (e.target === shade) close(); } }, sheet);
    shade.addEventListener("keydown", (e) => {
      if (e.key === "Escape") { e.stopPropagation(); close(); return; }
      if (e.key !== "Tab") return;
      const items = [...sheet.querySelectorAll("button, input, a[href]")].filter((x) => !x.disabled);
      if (!items.length) return;
      const first = items[0];
      const last = items[items.length - 1];
      const at = this.shadowRoot.activeElement;
      if (e.shiftKey && at === first) { e.preventDefault(); last.focus(); } else if (!e.shiftKey && at === last) { e.preventDefault(); first.focus(); }
    });
    return shade;
  }

  // every chosen branch's price for the line, cheapest first
  _chips(line) {
    const res = this._snap.result;
    const row = res && res.lines.find((x) => x.key === line.key);
    if (!row) return null;
    const cells = res.branches.map((b) => ({ b, c: row.per_branch[String(b.id)] }));
    const counted = cells.filter((x) => this._counts(x.c)).sort((a, b) => a.c.price - b.c.price);
    const other = cells.filter((x) => x.c && !this._counts(x.c)).length;
    const missing = cells.length - counted.length - other;
    const min = counted.length ? counted[0].c.price : null;
    return h("span", { class: "chips" },
      counted.slice(0, 6).map(({ b, c }) => h("span", { class: c.price === min ? "chip cheap" : "chip" },
        h("i", { class: "dot", style: `background:${CHAIN_COLORS[b.chain] || "#888"}` }), h("span", { class: "sr", text: `${this._branch(b)}: ` }),
        this._money(c.price), c.size_mismatch ? " ⚠" : "")),
      other ? h("span", { class: "chip warn", text: this._t("other_n", { n: other }) }) : null,
      missing ? h("span", { class: "chip miss", text: this._t("missing", { n: missing }) }) : null);
  }

  _footer() {
    const s = this._snap;
    const when = s.updated ? new Date(s.updated) : null;
    // the site's page for ideas and requests (the site's address is the integration's own, https only)
    const ideas = typeof s.site === "string" && /^https:\/\/[^/?#@\s]+$/.test(s.site)
      ? h("a", { class: "link", href: `${s.site}/ideas`, target: "_blank", rel: "noopener noreferrer" },
        this._t("ideas"), h("span", { class: "sr", text: ` (${this._t("new_tab")})` })) : null;
    return h("div", { class: "foot" },
      h("button", { type: "button", class: "btn", "data-fk": "compare", onclick: () => this._compareNow() }, this._t("compare_now")),
      when && !Number.isNaN(when.getTime()) ? h("span", { class: "muted", text: this._t("updated", {
        time: when.toLocaleString(LOCALES[this._lang] || "he-IL", { dateStyle: "short", timeStyle: "short" }) }) }) : null,
      ideas);
  }

  async _compareNow() {
    this._say(this._t("comparing"));
    try { await this._call("compare"); } catch (e) { /* said */ }
  }

  // ---- the comparison ------------------------------------------------------------------------------------
  _summary() {
    const s = this._snap;
    const box = h("div", { class: "body" }, ...this._notes());
    const res = s.result;
    if (!res || !res.branches.length) { box.append(h("p", { class: "muted", text: this._t("no_compare") }), this._footer()); return box; }
    const ranked = [...res.branches];
    const fair = ranked.map((b) => b.fair);
    const ul = h("ul", { class: "mini" });
    for (const b of ranked) {
      ul.append(h("li", { class: b.cheapest ? "win" : "" }, h("i", { class: "dot", style: `background:${CHAIN_COLORS[b.chain] || "#888"}` }),
        h("span", { class: "grow", text: this._branch(b) }), h("b", { class: "num", text: this._money(b.fair) }),
        b.missing ? h("small", { class: "miss", text: this._t("missing", { n: b.missing }) }) : null));
    }
    box.append(ul);
    if (ranked.length > 1 && !res.partial) box.append(h("p", { class: "note", text: this._t("saving", { n: this._money(Math.max(...fair) - Math.min(...fair)) }) }));
    box.append(this._footer());
    return box;
  }

  _compare() {
    const s = this._snap;
    const box = h("div", { class: "body" }, ...this._notes());
    const res = s.result;
    if (!res || !res.branches.length) { box.append(h("p", { class: "muted", text: this._t("no_compare") }), this._footer()); return box; }
    const all = res.lines.length;
    const cards = h("div", { class: "cards" });
    for (const b of res.branches) {
      cards.append(h("div", { class: b.cheapest ? "scard win" : "scard", style: `--chain:${CHAIN_COLORS[b.chain] || "#888"}` },
        h("b", { class: "sname", text: this._branch(b) }),
        b.cheapest ? h("span", { class: "badge", text: this._t("cheapest") }) : null,
        h("div", { class: "big num" }, this._money(b.total), h("small", { text: ` ${this._t("pay")}` })),
        b.fill_elsewhere > 0 ? h("small", { class: "muted", text: this._t("whole", { total: this._money(b.fair) }) }) : null,
        h("small", { class: "ok", text: this._t("found", { found: b.found, all }) }),
        b.missing ? h("small", { class: "miss", text: this._t("missing", { n: b.missing }) }) : null,
        b.other_size ? h("small", { class: "warn", text: this._t("other_n", { n: b.other_size }) }) : null,
        b.unsure ? h("small", { class: "muted", text: this._t("unsure_n", { n: b.unsure }) }) : null,
        b.cart_url ? h("button", { type: "button", class: "btn", "data-fk": `cart:${b.id}`, "aria-haspopup": "dialog",
          onclick: () => this._cartAsk(b) }, this._t("open_cart", { chain: this._chain(b.chain) })) : null));
    }
    box.append(cards);
    const head = h("tr", {}, h("th", { scope: "col", text: this._t("item") }),
      res.branches.map((b) => h("th", { scope: "col", style: `border-bottom-color:${CHAIN_COLORS[b.chain] || "#888"}`, text: this._branch(b) })));
    const body = h("tbody");
    for (const row of res.lines) {
      const line = s.lines.find((x) => x.key === row.key) || { name: row.name };
      const name = this._name(line);
      const costs = res.branches.map((b) => row.per_branch[String(b.id)]).filter((c) => this._counts(c)).map((c) => c.cost);
      const min = costs.length > 1 ? Math.min(...costs) : null;
      const specific = !row.key.startsWith("t:");
      const th = h("th", { scope: "row", class: "iname" }, h("span", { lang: name.lang, text: name.text }), h("small", { text: ` × ${row.qty}` }));
      if (row.size && res.branches.some((b) => (row.per_branch[String(b.id)] || {}).size_mismatch)) th.append(h("small", { class: "block", text: this._t("asked", { size: this._size(row.size) }) }));
      if (row.sizes_differ) th.append(h("small", { class: "block warn", text: `⚠ ${this._t("sizes_differ")}` }));
      const tr = h("tr", {}, th);
      for (const b of res.branches) {
        const c = row.per_branch[String(b.id)];
        const source = (row.sources || {})[b.chain] || (c && c.source);
        const cheap = this._counts(c) && c.cost === min;
        const td = h("td", { class: `cell${cheap ? " min" : ""}${c ? "" : " miss"}${c && !this._counts(c) ? " other" : ""}` });
        if (!c) td.append(this._t((row.pending || []).includes(b.chain) ? "not_checked" : "not_sold"));
        else {
          td.append(h("span", { class: "num", text: this._money(c.cost) }), h("small", { class: "block", lang: "he", text: c.name }));
          if (c.size_mismatch) {
            td.append(h("small", { class: "block warn", text: `⚠ ${this._t("other_size")}${this._size(c.size) ? `: ${this._size(c.size)}` : ""}` }));
            if (!this._counts(c)) td.append(h("small", { class: "block muted", text: this._t("not_counted") }));
          } else if (row.sizes_differ && this._size(c.size)) {
            td.append(h("small", { class: "block", text: this._size(c.size) }));
          }
          if (c.unsure && !c.size_mismatch) td.append(h("small", { class: "block warn", text: this._t("unsure") }));
          if (specific && !c.exact && (source === "auto" || source === "votes")) td.append(h("small", { class: "block muted", text: `≈ ${this._t("similar")}` }));
        }
        if (source === "yours") td.append(h("small", { class: "block muted", text: this._t("yours") }));
        else if (source === "admin") td.append(h("small", { class: "block muted", text: this._t("by_admin") }));
        if (!(c && c.exact) && !(row.pending || []).includes(b.chain)) {
          const btn = h("button", { type: "button", class: "fix", "data-key": row.key, "data-branch": String(b.id), "data-fk": `fix:${row.key}:${b.id}`,
            "aria-label": this._t("change_label", { chain: this._branch(b), name: name.text }), onclick: () => this._openFix(row, b, name.text) }, `✎ ${this._t("change")}`);
          td.append(btn);
        }
        tr.append(td);
      }
      body.append(tr);
    }
    box.append(h("div", { class: "tablewrap", role: "region", tabindex: "0", "aria-label": this._t("tab_compare") },
      h("table", {}, h("thead", {}, head), body)), h("p", { class: "note", text: this._t("legend") }), this._footer());
    return box;
  }

  // ---- choosing the product in one chain -------------------------------------------------------------------
  _openFix(row, b, label) {
    this._fix = { key: row.key, chain: b.chain, branch: b.id, label, q: (row.name || label || "").slice(0, 60), rows: null,
      votable: row.votable !== false };
    this._render();
    const input = this.shadowRoot.getElementById("fq");
    if (input) input.focus();
    this._fixSearch();
  }

  _closeFix(focusCell = true) {
    const f = this._fix;
    this._fix = null;
    if (f && focusCell) this._focusAfter = () => [...this.shadowRoot.querySelectorAll("button.fix")].find((x) => x.dataset.key === f.key && x.dataset.branch === String(f.branch));
    this._render();
  }

  async _fixSearch() {
    const f = this._fix;
    if (!f || !f.q) return;
    f.rows = null;
    this._drawFixResults();
    try {
      const rows = await this._call("chain_search", { chain: f.chain, query: f.q });
      if (this._fix === f) { f.rows = Array.isArray(rows) ? rows : []; this._drawFixResults(); }
    } catch (e) { if (this._fix === f) { f.rows = []; this._drawFixResults(); } }
  }

  _drawFixResults() {
    const f = this._fix;
    const box = this.shadowRoot.getElementById("fix-results");
    if (!f || !box) return;
    if (!f.rows) { box.replaceChildren(h("p", { class: "muted", text: this._t("searching") })); return; }
    if (!f.rows.length) { box.replaceChildren(h("p", { class: "muted", text: this._t("no_results") })); return; }
    const res = this._snap.result;
    const row = res && res.lines.find((x) => x.key === f.key);
    const current = row && row.per_branch[String(f.branch)];
    box.replaceChildren(h("ul", { class: "products" }, f.rows.map((p) => {
      const here = (p.prices || {})[String(f.branch)];
      const any = Object.values(p.prices || {}).filter(Number.isFinite);
      const price = Number.isFinite(here) ? this._money(here) : any.length ? this._money(Math.min(...any)) : this._t("not_here");
      const now = current && current.item === p.item;
      return h("li", {}, h("button", { type: "button", class: now ? "product on" : "product", onclick: () => this._choose(p.item) },
        h("span", { class: "pname", lang: "he", text: p.name }), this._size(p.size) ? h("small", { text: this._size(p.size) }) : null,
        h("b", { class: "num", text: price }), now ? h("span", { class: "badge", text: this._t("now") }) : null));
    })));
  }

  async _choose(item) {
    const f = this._fix;
    if (!f) return;
    try {
      await this._call("choose", { key: f.key, chain: f.chain, item });
      this._say(this._t("saved"));
      this._closeFix();
    } catch (e) { /* said */ }
  }

  _fixSheet() {
    const f = this._fix;
    const res = this._snap && this._snap.result;
    const row = res && res.lines.find((x) => x.key === f.key);
    const c = row && row.per_branch[String(f.branch)];
    const b = (res && res.branches.find((x) => x.id === f.branch)) || {};
    const chosen = Boolean(((this._snap.choices || {})[f.key] || {})[f.chain] !== undefined);
    const input = h("input", { id: "fq", type: "text", maxlength: "60", autocomplete: "off", enterkeyhint: "search", value: f.typed ?? f.q });
    input.addEventListener("input", () => { f.typed = input.value; });
    const form = h("form", { class: "search", role: "search" },
      h("label", { for: "fq", class: "block", text: this._t("fix_search", { chain: this._chain(f.chain) }) }),
      h("div", { class: "row" }, input, h("button", { type: "submit", class: "btn" }, this._t("search_go"))));
    form.addEventListener("submit", (e) => { e.preventDefault(); f.q = input.value.trim().slice(0, 60); this._fixSearch(); });
    const sheet = h("div", { class: "sheet", role: "dialog", "aria-modal": "true", "aria-labelledby": "fix-title", dir: this._lang === "he" ? "rtl" : "ltr" },
      h("div", { class: "sheethead" }, h("h3", { id: "fix-title", text: this._t("fix_title", { name: f.label, chain: this._branch(b) }) }),
        h("button", { type: "button", class: "icon", "aria-label": this._t("close"), onclick: () => this._closeFix() }, "✕")),
      h("p", { class: "note", text: c ? this._t("fix_now", { name: c.name, price: this._money(c.price) }) + (this._size(c.size) ? ` · ${this._size(c.size)}` : "") : this._t("fix_none") }),
      row && row.size ? h("p", { class: "note", text: this._t("asked", { size: this._size(row.size) }) }) : null,
      form, h("div", { id: "fix-results" }),
      h("div", { class: "actions" },
        h("button", { type: "button", class: "btn", onclick: () => this._choose(0) }, this._t("fix_not_sold", { chain: this._chain(f.chain) })),
        chosen ? h("button", { type: "button", class: "btn", onclick: () => this._choose(null) }, this._t("fix_auto")) : null),
      h("p", { class: "note small", text: this._t(f.votable ? "fix_note" : "fix_note_private") }));
    setTimeout(() => this._drawFixResults(), 0);
    return this._modal(sheet, () => this._closeFix());
  }
}

const CSS = `
:host{--sc-ok:#1b5e20;--sc-warn:#7a4a00;--sc-miss:#b71c1c}
:host(.dark){--sc-ok:#a5d6a7;--sc-warn:#ffcc80;--sc-miss:#ef9a9a}
ha-card{display:block;overflow:hidden;container-type:inline-size;color:var(--primary-text-color)}
.pad{padding:16px}.muted{color:var(--secondary-text-color)}.error{color:var(--error-color,#c62828)}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.head{display:flex;flex-wrap:wrap;gap:8px 16px;justify-content:space-between;align-items:center;padding:14px 16px 8px}
.titles{display:flex;flex-direction:column;min-width:0}.titles h2{margin:0;font-size:1.15rem}.titles span{font-size:.85rem}
.best{display:flex;flex-wrap:wrap;gap:4px 8px;align-items:baseline;padding:6px 12px;border-radius:12px;background:rgba(46,125,50,.12)}
.best span{color:var(--sc-ok);font-weight:600;font-size:.85rem}.num{font-variant-numeric:tabular-nums;white-space:nowrap}
.tabs{display:flex;border-bottom:1px solid var(--divider-color,#ddd)}
.tab{flex:1;min-height:44px;border:0;background:none;color:var(--secondary-text-color);font:inherit;font-weight:600;cursor:pointer;border-bottom:3px solid transparent}
.tab.on{color:var(--primary-color);border-bottom-color:var(--primary-color)}
.body{padding:8px 16px 16px;display:flex;flex-direction:column;gap:8px}
.search{display:flex;flex-direction:column;gap:6px}.search .row,.search:not(:has(.row)){display:flex;gap:8px;flex-direction:row}
.search input{flex:1;min-width:0;min-height:44px;font:inherit;font-size:16px;padding:0 12px;border-radius:10px;border:1px solid var(--divider-color,#ccc);background:var(--card-background-color,#fff);color:var(--primary-text-color)}
.btn{min-height:44px;padding:0 14px;border-radius:10px;border:1px solid var(--divider-color,#ccc);background:var(--card-background-color,#fff);color:var(--primary-text-color);font:inherit;font-weight:600;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;text-decoration:none}
.link{border:0;background:none;color:var(--primary-color);text-decoration:underline;font:inherit;cursor:pointer;min-height:36px}
.icon{min-width:40px;min-height:40px;border-radius:10px;border:1px solid var(--divider-color,#ccc);background:var(--card-background-color,#fff);color:var(--primary-text-color);font:inherit;font-size:1.1rem;cursor:pointer}
ul{list-style:none;margin:0;padding:0}
.products{display:flex;flex-direction:column;gap:6px}
.product{width:100%;display:flex;flex-wrap:wrap;gap:2px 10px;align-items:baseline;text-align:start;min-height:44px;padding:8px 12px;border-radius:10px;border:1px solid var(--divider-color,#ddd);background:var(--card-background-color,#fff);color:var(--primary-text-color);font:inherit;cursor:pointer}
.product.on{border-color:var(--primary-color);box-shadow:0 0 0 1px var(--primary-color)}.product.text{color:var(--primary-color);font-weight:600}
.pname{flex:1 1 12rem;min-width:0;font-weight:500}.product small{color:var(--secondary-text-color)}.product b{margin-inline-start:auto}
.lines{display:flex;flex-direction:column}
.line{display:flex;align-items:center;gap:8px 10px;flex-wrap:wrap;padding:10px 0;border-bottom:1px solid var(--divider-color,#eee)}
.grow{flex:1 1 12rem;min-width:0;display:flex;flex-direction:column;gap:4px}.grow b{font-weight:500}
.ctl{display:flex;align-items:center;gap:10px;margin-inline-start:auto}.stepper{display:flex;align-items:center;gap:6px}.qty{min-width:2.2em;text-align:center;font-weight:700}
.del{color:var(--secondary-text-color)}.less.last{color:var(--sc-miss);border-color:var(--sc-miss)}
.btn.danger{color:var(--sc-miss);border-color:var(--sc-miss)}.btn.primary{border:2px solid var(--primary-color);font-weight:700}
.important{margin:0;padding:10px 12px;border-radius:10px;background:rgba(242,140,0,.14);border-inline-start:4px solid #f28c00;color:var(--primary-text-color);line-height:1.5;font-weight:500}.sheet.ask{padding-top:16px}.sheet.ask h3{margin:0;font-size:1.05rem;line-height:1.4;overflow-wrap:anywhere}
.avail{display:flex;flex-wrap:wrap;gap:3px 4px}.avail.compact{flex-basis:100%}
.atag{display:inline-flex;align-items:center;gap:3px;font-size:12px;padding:0 6px;border-radius:7px;background:rgba(128,128,128,.12);white-space:nowrap}
.atag.no{opacity:.7;text-decoration:line-through;background:none}.atag.no b{color:var(--sc-miss);text-decoration:none;display:inline-block}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;flex:none}
.chips{display:flex;flex-wrap:wrap;gap:4px}
.chip{display:inline-flex;align-items:center;gap:4px;font-size:12px;padding:1px 8px;border-radius:9px;background:rgba(128,128,128,.12);font-variant-numeric:tabular-nums}
.chip.cheap{background:rgba(46,125,50,.16);color:var(--sc-ok);font-weight:700}.chip.warn{color:var(--sc-warn);background:rgba(242,140,0,.14)}.chip.miss{color:var(--sc-miss)}
.note{margin:0;font-size:.85rem;color:var(--secondary-text-color)}.note.warn{color:var(--sc-warn)}.note.small{font-size:.8rem}
.empty{color:var(--secondary-text-color);text-align:center;padding:20px 0}
.foot{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;margin-top:6px}.foot span{font-size:.8rem}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,210px),1fr));gap:10px}
.scard{display:flex;flex-direction:column;gap:3px;padding:12px;border-radius:14px;border:1px solid var(--divider-color,#ddd);border-top:3px solid var(--chain)}
.scard.win{box-shadow:0 0 0 2px var(--sc-ok)}.sname{font-size:.95rem}.big{font-size:1.5rem;font-weight:800}.big small{font-size:.8rem;font-weight:400;color:var(--secondary-text-color)}
.badge{align-self:flex-start;font-size:12px;font-weight:700;padding:0 8px;border-radius:7px;background:rgba(46,125,50,.16);color:var(--sc-ok)}
.ok{color:var(--sc-ok)}.miss{color:var(--sc-miss)}.warn{color:var(--sc-warn)}.block{display:block}
.scard .btn{margin-top:6px}
.tablewrap{overflow-x:auto;border:1px solid var(--divider-color,#ddd);border-radius:12px}
table{border-collapse:collapse;width:100%;font-size:.85rem;min-width:24rem}
th,td{padding:8px;border-top:1px solid var(--divider-color,#eee);vertical-align:top}
thead th{border-bottom:2px solid;text-align:center;font-weight:600}
.iname{text-align:start;font-weight:500;position:sticky;inset-inline-start:0;background:var(--card-background-color,#fff);z-index:1}
.iname small{font-weight:400;color:var(--secondary-text-color);font-size:12px}
.cell{text-align:center;min-width:88px}.cell small{font-size:12px;color:var(--secondary-text-color);max-width:140px;margin:0 auto;overflow:hidden;text-overflow:ellipsis}
.cell .warn{color:var(--sc-warn)}.cell.min{background:rgba(46,125,50,.12);font-weight:700}.cell.miss{color:var(--sc-miss)}.cell.other{background:rgba(242,140,0,.12)}
.fix{margin-top:4px;min-height:32px;min-width:44px;padding:0 8px;border-radius:8px;border:1px solid var(--divider-color,#ccc);background:var(--card-background-color,#fff);color:var(--primary-color);font:inherit;font-size:12px;cursor:pointer}
.mini li{display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid var(--divider-color,#eee)}.mini li.win b{color:var(--sc-ok)}.mini small{font-size:12px}
.shade{position:fixed;inset:0;background:rgba(0,0,0,.5);display:flex;align-items:flex-end;justify-content:center;z-index:10}
.sheet{width:min(36rem,100%);max-height:88vh;overflow:auto;background:var(--card-background-color,#fff);color:var(--primary-text-color);border-radius:16px 16px 0 0;padding:0 16px 16px;display:flex;flex-direction:column;gap:8px}
.sheethead{position:sticky;top:0;display:flex;justify-content:space-between;align-items:flex-start;gap:8px;padding:14px 0 8px;background:var(--card-background-color,#fff);border-bottom:1px solid var(--divider-color,#eee)}
.sheethead h3{margin:0;font-size:1.05rem;padding-top:6px}
.actions{display:flex;flex-wrap:wrap;gap:8px}.actions .btn{flex:1 1 auto}
@media (min-width:600px){.shade{align-items:center}.sheet{border-radius:16px}}
@container (max-width:420px){.head{padding:12px 12px 6px}.body{padding:8px 12px 12px}.big{font-size:1.3rem}}
:focus-visible{outline:3px solid var(--primary-color);outline-offset:2px}
`;

if (!customElements.get("shopping-compare-web-card")) customElements.define("shopping-compare-web-card", ShoppingCompareWebCard);
window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === "shopping-compare-web-card")) {
  window.customCards.push({ type: "shopping-compare-web-card", name: "Supermarket price compare",
    description: "The shopping list and where it costs least (views: full, list, compare, summary)", preview: false });
}
