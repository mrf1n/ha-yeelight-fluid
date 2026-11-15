/*
 * Yeelight Christmas Lights card for Home Assistant.
 *
 * Shipped with the yeelight_lights_ble integration and loaded automatically.
 * Usage:
 *   type: custom:yeelight-christmas-card
 *   entity: light.<your_lights>
 */

const DOMAIN = "yeelight_lights_ble";
const CARD_VERSION = "0.3.0";

// Music colour schemes (generated from music.py)
const SCHEMES = {"mood":[["happy","Happy",["#EA047E","#FF8861","#FFE75F","#8DD852","#00F5FF"]],["surprised","Surprised",["#19467A","#2C7FA6","#B1FDF9","#77FFA5","#06965E"]],["excited","Excited",["#EAE2B7","#FCBF49","#F77F00","#D62828","#003B59"]],["romantic","Romantic",["#FFBE7C","#FFF4CB","#E8B8FF","#FF8FB1","#E45887"]],["relaxed","Relaxed",["#F79256","#FBD1A2","#7DCFB6","#00B2CA","#1D4E89"]],["joyful","Joyful",["#FFEB3B","#00C853","#009688","#3F51B5","#F44336"]],["warm","Warm",["#FF577F","#FFCDD2","#FFD180","#FF884B","#F44336"]],["calm","Calm",["#B5FFFF","#40DFFF","#00BBFF","#0088CC","#0055AA"]],["tranquil","Tranquil",["#1B7A69","#66AF56","#6FB18D","#FFECCF","#424242"]]],"landscape":[["tropical_island","Tropical Island",["#00FFFF","#F9EF1A","#FF8C38","#8BC83D","#338650"]],["purple_jungle","Purple Jungle",["#730073","#D125A1","#FFC0E6","#D125A1","#730073"]],["sunset_desert","Sunset Desert",["#ACF5FF","#FFF1C6","#FFB51C","#DD7B43","#B7391E"]],["tropical_rainforest","Tropical Rainforest",["#FF1493","#FFD700","#32CD32","#1AA774","#007D76"]],["heart_of_ocean","Heart of the Ocean",["#1E90FF","#00BFFF","#87CEFA","#FFCFCF","#FF6868"]],["violet_seas","Violet Seas",["#FF47BF","#FF77D0","#FFA7E4","#BE7DFF","#A449FF"]],["blue_glacier","Blue Glacier",["#8180D1","#E6CCF8","#A5DCFF","#02A8DC","#0059C1"]],["sunrise_sea","Sunrise Sea",["#FFD700","#FF893E","#FB5C46","#5D3486","#282D97"]],["green_meadow","Green Meadow",["#00A3E9","#B5E1F4","#E7EA4C","#83AA1A","#2C7908"]],["golden_forest","Golden Forest",["#FFFF00","#FFD700","#FFA500","#F38600","#FF4500"]],["blue_mountains","Blue Mountains",["#06FFFF","#B4DEFF","#3F92FF","#0046AF","#EDAC49"]],["pink_garden","Pink Garden",["#00FFFF","#C0FFFF","#FFC0CB","#FF69B4","#FF1493"]],["volcano_cave","Volcano Cave",["#8F0045","#EB1120","#FF833E","#EB1120","#8F0045"]],["golden_leaves","Golden Leaves",["#FFD700","#FF8C00","#FF4500","#B47130","#498A15"]],["sunset_lake","Sunset Lake",["#FF6E40","#EB6C7B","#FC9BCF","#9A51E3","#524FEB"]]],"music":[["classical","Classical",["#264653","#2A9D8F","#E9C46A","#F4A261","#E76F51"]],["pop","Pop",["#FFBE0B","#FB5607","#FF006E","#8338EC","#3A86FF"]],["rock","Rock",["#444444","#DADADA","#E31A1A","#F8D500","#A5A5A5"]],["electronic","Electronic",["#1BE7FF","#6EEB83","#FFF61A","#DE14FF","#7B14FF"]],["antique","Antique",["#C5B56C","#98623C","#DBD6B3","#F1F0EA","#B9A882"]],["rap","Rap",["#120CCA","#C801D0","#F63C31","#C801D0","#120CCA"]],["jazz","Jazz",["#FFCC00","#FFDE5C","#FFEB99","#A486D5","#54318C"]],["country","Country",["#EE6055","#FF9B85","#FFD97D","#AAF683","#60D394"]],["metal","Metal",["#558A78","#853512","#EEAA23","#614433","#4A834C"]],["alternative","Alternative",["#CC2936","#FFE000","#50C7C7","#E5E5E5","#F9A71F"]]],"holiday":[["new_year","New Year",["#2A745A","#9A1616","#CC433A","#ED7744","#FFBF7B"]],["valentine","Valentine's Day",["#FFE5ED","#FFBAD8","#FF71A3","#FF3369","#FF103B"]],["carnival","Carnival",["#973EFF","#FF479A","#FFE651","#08DABB","#4D69FF"]],["april_fool","April Fool's Day",["#055FBE","#FFCA0D","#FF4040","#FFCA0D","#055FBE"]],["mother","Mother's Day",["#390E80","#B3005E","#E90064","#FF5F9E","#FFACAC"]],["father","Father's Day",["#0584DB","#77DFFF","#FFE7A8","#9BD95C","#00997C"]],["children","Children's Day",["#B2A4FF","#FF8DAF","#FFD095","#A8E7FF","#9EFFB4"]],["halloween","Halloween",["#530095","#CD113B","#FF7600","#FFA900","#FFF966"]],["world_cup","World Cup",["#FFF966","#DDF7E3","#81BC87","#196616","#0052A8"]],["thanksgiving","Thanksgiving",["#FFD199","#FFDC83","#FF9A61","#FF6636","#F7373F"]],["christmas","Christmas",["#F8D500","#FD5E53","#F9FCFB","#B0EACD","#21BF73"]]]};
const CATEGORIES = [
  ["mood", "Mood"],
  ["landscape", "Landscape"],
  ["music", "Music"],
  ["holiday", "Holiday"],
];
const RHYTHMS = [
  ["breath", "Breath"],
  ["shine", "Shine"],
  ["spectrum", "Spectrum"],
  ["converge", "Converge"],
];
const DYNAMICS = [
  ["none", "None"],
  ["translation", "Translation"],
  ["breath", "Breath"],
  ["flashing", "Flashing"],
  ["stack", "Stack"],
];
const DIRECTIONAL = new Set(["translation", "stack"]);
const PALETTE = [
  "#FF0000", "#FF6A00", "#FFC400", "#00C853", "#00B8D4",
  "#2962FF", "#AA00FF", "#FF4081", "#FFFFFF", "#FFB46B",
];
const TABS = [
  ["effects", "Modes"],
  ["music", "Music"],
  ["color", "Colour"],
  ["diy", "DIY"],
];
const PSEUDO_EFFECTS = new Set(["Music", "Custom"]);
const MAX_SLOTS = 10;
const PREVIEW_BULBS = 30;

function esc(text) {
  return String(text ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function hsToHex(h, s) {
  const f = (n) => {
    const k = (n + h / 60) % 6;
    const v = 1 - (s / 100) * Math.max(0, Math.min(k, 4 - k, 1));
    return Math.round(v * 255).toString(16).padStart(2, "0");
  };
  return `#${f(5)}${f(3)}${f(1)}`.toUpperCase();
}

class YeelightChristmasCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._tab = null;
    this._category = "mood";
    this._slot = 0;
    this._sig = "";
    this._dragging = false;
    this._diy = null;
  }

  static getStubConfig(hass) {
    const entry = Object.values(hass.entities || {}).find(
      (e) => e.platform === DOMAIN && e.entity_id.startsWith("light."),
    );
    return { entity: entry ? entry.entity_id : "light.christmas_lights" };
  }

  setConfig(config) {
    if (!config || !config.entity || !config.entity.startsWith("light.")) {
      throw new Error("Set 'entity' to the Christmas lights light entity");
    }
    this._config = config;
    this._sig = "";
    if (this._hass) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    const sig = this._signature();
    if (sig !== this._sig && !this._dragging) {
      this._sig = sig;
      this._render();
    }
  }

  getCardSize() {
    return 9;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6, rows: "auto" };
  }

  // ---------------------------------------------------------------- helpers
  _sibling(key) {
    const hass = this._hass;
    const light = hass.entities?.[this._config.entity];
    if (!light || !light.device_id) return undefined;
    const found = Object.values(hass.entities).find(
      (e) => e.device_id === light.device_id && e.platform === DOMAIN && e.translation_key === key,
    );
    return found ? found.entity_id : undefined;
  }

  _state(key) {
    const id = key === "light" ? this._config.entity : this._sibling(key);
    return id ? this._hass.states[id] : undefined;
  }

  _signature() {
    const keys = [
      "light", "effect", "effect_speed", "effect_direction", "music_mode",
      "music_effect", "music_scheme", "recent_colors",
    ];
    return keys
      .map((k) => {
        const s = this._state(k);
        return s ? `${s.state}|${s.last_updated}` : "-";
      })
      .join(";");
  }

  _call(domain, service, data) {
    return this._hass.callService(domain, service, data).catch((err) => {
      this._toast(err && err.message ? err.message : String(err));
    });
  }

  _toast(message) {
    this.dispatchEvent(new CustomEvent("hass-notification", {
      detail: { message }, bubbles: true, composed: true,
    }));
  }

  _loadDiy() {
    if (this._diy) return this._diy;
    let saved = null;
    try {
      saved = JSON.parse(localStorage.getItem(`yeelight-diy:${this._config.entity}`) || "null");
    } catch (_e) {
      saved = null;
    }
    this._diy = saved && Array.isArray(saved.slots) && saved.slots.length
      ? saved
      : { slots: ["#FF0000", "#FFFFFF", "#00C853"], dynamic: "none", speed: 50, direction: "up" };
    return this._diy;
  }

  _saveDiy() {
    try {
      localStorage.setItem(`yeelight-diy:${this._config.entity}`, JSON.stringify(this._diy));
    } catch (_e) {
      /* storage blocked: keep in memory only */
    }
  }

  _activeTab(light) {
    if (this._tab) return this._tab;
    const effect = light.attributes.effect;
    if (effect === "Music") return "music";
    if (effect === "Custom") return "diy";
    if (light.attributes.color_mode === "hs" && !effect) return "color";
    return "effects";
  }

  // ----------------------------------------------------------------- render
  _render() {
    const light = this._state("light");
    if (!light) {
      this.shadowRoot.innerHTML = `<style>${STYLE}</style>
        <ha-card><div class="empty">Entity ${esc(this._config.entity)} not found</div></ha-card>`;
      return;
    }
    const on = light.state === "on";
    const tab = this._activeTab(light);
    const pct = light.attributes.brightness ? Math.round((light.attributes.brightness / 255) * 100) : 0;
    const name = this._config.name || light.attributes.friendly_name || "Christmas Lights";
    const unavailable = light.state === "unavailable";

    this.shadowRoot.innerHTML = `
      <style>${STYLE}</style>
      <ha-card class="${on ? "is-on" : "is-off"}">
        <div class="header">
          <div class="bulbs" aria-hidden="true">${this._headerBulbs(on)}</div>
          <div class="title">
            <div class="name">${esc(name)}</div>
            <div class="status">${unavailable ? "Unavailable" : on ? this._statusText(light) : "Off"}</div>
          </div>
          <button class="power ${on ? "on" : ""}" data-action="power" aria-label="Power"
            ${unavailable ? "disabled" : ""}>${POWER_ICON}</button>
        </div>
        <div class="brightness">
          <span class="label">Brightness</span>
          <input type="range" min="1" max="100" value="${pct || 1}" data-action="brightness"
            aria-label="Brightness" ${on ? "" : "disabled"}>
          <span class="value">${on ? `${pct}%` : "–"}</span>
        </div>
        <div class="tabs" role="tablist">
          ${TABS.map(([key, label]) => `
            <button role="tab" class="tab ${tab === key ? "active" : ""}" data-action="tab"
              data-tab="${key}" aria-selected="${tab === key}">${label}</button>`).join("")}
        </div>
        <div class="panel">${this._panel(tab, light)}</div>
      </ha-card>`;
    this._bind();
  }

  _statusText(light) {
    const effect = light.attributes.effect;
    if (effect === "Music") return "Music flow";
    if (effect === "Custom") return "DIY";
    if (effect) return effect;
    return "Pure colour";
  }

  _headerBulbs(on) {
    const colors = ["#FF3B30", "#FFCC00", "#34C759", "#0A84FF", "#FF9F0A", "#BF5AF2", "#FF3B30"];
    return colors
      .map((c, i) => `<span class="bulb" style="--c:${on ? c : "var(--disabled-color, #888)"};--d:${i * 0.35}s"></span>`)
      .join("");
  }

  _panel(tab, light) {
    if (tab === "music") return this._musicPanel();
    if (tab === "color") return this._colorPanel(light);
    if (tab === "diy") return this._diyPanel();
    return this._effectsPanel(light);
  }

  _speedDirection(showSpeed = true) {
    const speed = this._state("effect_speed");
    const dir = this._state("effect_direction");
    const parts = [];
    if (showSpeed && speed && speed.state !== "unavailable") {
      parts.push(`
        <div class="row">
          <span class="label">Speed</span>
          <input type="range" min="1" max="100" value="${Math.round(Number(speed.state) || 50)}"
            data-action="speed" aria-label="Effect speed">
          <span class="value">${Math.round(Number(speed.state) || 0)}%</span>
        </div>`);
    }
    if (dir && dir.state !== "unavailable") {
      parts.push(`
        <div class="row">
          <span class="label">Direction</span>
          <div class="segmented">
            ${["up", "down"].map((d) => `
              <button class="${dir.state === d ? "active" : ""}" data-action="direction" data-value="${d}">
                ${d === "up" ? "Forward" : "Backward"}</button>`).join("")}
          </div>
        </div>`);
    }
    return parts.join("");
  }

  _effectsPanel(light) {
    const list = (light.attributes.effect_list || []).filter((e) => !PSEUDO_EFFECTS.has(e));
    const current = light.attributes.effect;
    return `
      <div class="chips">
        ${list.map((e) => `
          <button class="chip ${current === e ? "active" : ""}" data-action="effect" data-value="${esc(e)}">
            ${esc(e)}</button>`).join("")}
      </div>
      ${this._speedDirection()}`;
  }

  _musicPanel() {
    const sw = this._state("music_mode");
    const rhythm = this._state("music_effect");
    const scheme = this._state("music_scheme");
    const isOn = sw && sw.state === "on";
    const current = scheme ? scheme.state : "";
    const schemes = SCHEMES[this._category] || [];
    const custom = current === "custom" && scheme.attributes.colors
      ? `<div class="scheme active custom">
           <div class="swatches">${scheme.attributes.colors.map((c) =>
             `<span style="background:rgb(${c.join(",")})"></span>`).join("")}</div>
           <div class="scheme-name">Custom</div></div>`
      : "";
    return `
      <div class="row between">
        <div>
          <div class="strong">Music flow</div>
          <div class="hint">Lights react to the microphone on the controller</div>
        </div>
        <button class="toggle ${isOn ? "on" : ""}" data-action="music" role="switch"
          aria-checked="${isOn}" aria-label="Music mode" ${sw ? "" : "disabled"}><span></span></button>
      </div>
      <div class="section-title">Rhythm effect</div>
      <div class="segmented wide">
        ${RHYTHMS.map(([k, l]) => `
          <button class="${rhythm && rhythm.state === k ? "active" : ""}" data-action="rhythm"
            data-value="${k}">${l}</button>`).join("")}
      </div>
      <div class="section-title">Colour scheme</div>
      <div class="subtabs">
        ${CATEGORIES.map(([k, l]) => `
          <button class="${this._category === k ? "active" : ""}" data-action="category"
            data-value="${k}">${l}</button>`).join("")}
      </div>
      <div class="schemes">
        ${custom}
        ${schemes.map(([key, label, colors]) => `
          <button class="scheme ${current === key ? "active" : ""}" data-action="scheme" data-value="${key}">
            <div class="swatches">${colors.map((c) => `<span style="background:${c}"></span>`).join("")}</div>
            <div class="scheme-name">${esc(label)}</div>
          </button>`).join("")}
      </div>`;
  }

  _colorPanel(light) {
    const hs = light.attributes.hs_color;
    const marker = hs
      ? (() => {
          const rad = ((hs[0] - 90) * Math.PI) / 180;
          const r = (hs[1] / 100) * 50;
          return `left:${50 + r * Math.cos(rad)}%;top:${50 + r * Math.sin(rad)}%;`;
        })()
      : "display:none;";
    const recent = this._state("recent_colors");
    const recentOptions = recent ? recent.attributes.options || [] : [];
    return `
      <div class="wheel-wrap">
        <div class="wheel" data-action="wheel" role="slider" aria-label="Colour">
          <div class="wheel-fade"></div>
          <div class="marker" style="${marker}"></div>
        </div>
      </div>
      <div class="section-title">Quick colours</div>
      <div class="swatch-row">
        ${PALETTE.map((c) => `<button class="dot" style="background:${c}" data-action="color"
          data-value="${c}" aria-label="${c}"></button>`).join("")}
      </div>
      ${recentOptions.length ? `
        <div class="section-title">Recent</div>
        <div class="swatch-row">
          ${recentOptions.map((c) => `<button class="dot ${recent.state === c ? "active" : ""}"
            style="background:${esc(c)}" data-action="recent" data-value="${esc(c)}"
            aria-label="${esc(c)}"></button>`).join("")}
        </div>` : ""}`;
  }

  _diyPanel() {
    const diy = this._loadDiy();
    const slots = diy.slots;
    if (this._slot >= slots.length) this._slot = slots.length - 1;
    const bulbs = Array.from({ length: PREVIEW_BULBS }, (_, i) => slots[i % slots.length]);
    return `
      <div class="string anim-${diy.dynamic} dir-${diy.direction}"
        style="--speed:${(4.2 - (diy.speed / 100) * 3.6).toFixed(2)}s">
        <div class="wire"></div>
        ${bulbs.map((c, i) => `<span class="led" style="--c:${c};--i:${i}"></span>`).join("")}
      </div>
      <div class="section-title">Pattern <span class="hint">repeats along the string</span></div>
      <div class="slots">
        ${slots.map((c, i) => `<button class="slot ${i === this._slot ? "active" : ""}"
          style="background:${c}" data-action="slot" data-value="${i}" aria-label="Slot ${i + 1}"></button>`).join("")}
        ${slots.length < MAX_SLOTS ? `<button class="slot add" data-action="add-slot" aria-label="Add colour">+</button>` : ""}
        ${slots.length > 1 ? `<button class="slot remove" data-action="remove-slot" aria-label="Remove colour">−</button>` : ""}
      </div>
      <div class="swatch-row">
        ${PALETTE.map((c) => `<button class="dot" style="background:${c}" data-action="paint"
          data-value="${c}" aria-label="${c}"></button>`).join("")}
        <label class="dot picker" aria-label="Pick any colour">
          <input type="color" value="${slots[this._slot]}" data-action="paint-pick">
        </label>
      </div>
      <div class="section-title">Dynamic effect</div>
      <div class="segmented wide">
        ${DYNAMICS.map(([k, l]) => `<button class="${diy.dynamic === k ? "active" : ""}"
          data-action="dynamic" data-value="${k}">${l}</button>`).join("")}
      </div>
      ${diy.dynamic !== "none" ? `
        <div class="row">
          <span class="label">Speed</span>
          <input type="range" min="1" max="100" value="${diy.speed}" data-action="diy-speed" aria-label="Speed">
          <span class="value">${diy.speed}%</span>
        </div>` : ""}
      ${DIRECTIONAL.has(diy.dynamic) ? `
        <div class="row">
          <span class="label">Direction</span>
          <div class="segmented">
            ${["up", "down"].map((d) => `<button class="${diy.direction === d ? "active" : ""}"
              data-action="diy-direction" data-value="${d}">${d === "up" ? "Forward" : "Backward"}</button>`).join("")}
          </div>
        </div>` : ""}
      <div class="actions">
        <button class="secondary" data-action="random">Random colours</button>
        <button class="primary" data-action="apply">Apply to lights</button>
      </div>`;
  }

  // ----------------------------------------------------------------- events
  _bind() {
    const root = this.shadowRoot;
    root.querySelectorAll("[data-action]").forEach((el) => {
      const action = el.dataset.action;
      if (el.tagName === "INPUT" && el.type === "range") {
        el.addEventListener("pointerdown", () => { this._dragging = true; });
        el.addEventListener("input", () => {
          const out = el.parentElement.querySelector(".value");
          if (out) out.textContent = `${el.value}%`;
          if (action === "diy-speed") this._previewSpeed(el.value);
        });
        el.addEventListener("change", () => {
          this._dragging = false;
          this._onAction(action, el.value, el);
        });
      } else if (el.tagName === "INPUT" && el.type === "color") {
        el.addEventListener("change", () => this._onAction(action, el.value.toUpperCase(), el));
      } else if (action === "wheel") {
        el.addEventListener("click", (ev) => this._onWheel(ev, el));
      } else {
        el.addEventListener("click", () => this._onAction(action, el.dataset.value ?? el.dataset.tab, el));
      }
    });
  }

  _previewSpeed(value) {
    const string = this.shadowRoot.querySelector(".string");
    if (string) string.style.setProperty("--speed", `${(4.2 - (value / 100) * 3.6).toFixed(2)}s`);
  }

  _onWheel(ev, el) {
    const rect = el.getBoundingClientRect();
    const x = ev.clientX - rect.left - rect.width / 2;
    const y = ev.clientY - rect.top - rect.height / 2;
    const radius = rect.width / 2;
    const sat = Math.min(100, Math.round((Math.hypot(x, y) / radius) * 100));
    const hue = Math.round(((Math.atan2(y, x) * 180) / Math.PI + 90 + 360) % 360);
    this._call("light", "turn_on", { entity_id: this._config.entity, hs_color: [hue, sat] });
    const marker = el.querySelector(".marker");
    if (marker) {
      marker.style.display = "";
      marker.style.left = `${50 + (x / radius) * 50}%`;
      marker.style.top = `${50 + (y / radius) * 50}%`;
      marker.style.background = hsToHex(hue, sat);
    }
  }

  _onAction(action, value) {
    const entity = this._config.entity;
    const diy = this._diy;
    switch (action) {
      case "power":
        return this._call("light", "toggle", { entity_id: entity });
      case "brightness":
        return this._call("light", "turn_on", { entity_id: entity, brightness_pct: Number(value) });
      case "tab":
        this._tab = value;
        return this._render();
      case "effect":
        return this._call("light", "turn_on", { entity_id: entity, effect: value });
      case "speed":
        return this._call("number", "set_value", { entity_id: this._sibling("effect_speed"), value: Number(value) });
      case "direction":
        return this._call("select", "select_option", { entity_id: this._sibling("effect_direction"), option: value });
      case "music": {
        const sw = this._state("music_mode");
        return this._call("switch", sw && sw.state === "on" ? "turn_off" : "turn_on", { entity_id: sw.entity_id });
      }
      case "rhythm":
        return this._call("select", "select_option", { entity_id: this._sibling("music_effect"), option: value });
      case "category":
        this._category = value;
        return this._render();
      case "scheme":
        return this._call("select", "select_option", { entity_id: this._sibling("music_scheme"), option: value });
      case "color":
        return this._call("light", "turn_on", { entity_id: entity, rgb_color: hexToRgb(value) });
      case "recent":
        return this._call("select", "select_option", { entity_id: this._sibling("recent_colors"), option: value });
      case "slot":
        this._slot = Number(value);
        return this._render();
      case "add-slot":
        diy.slots.push(diy.slots[diy.slots.length - 1]);
        this._slot = diy.slots.length - 1;
        this._saveDiy();
        return this._render();
      case "remove-slot":
        diy.slots.splice(this._slot, 1);
        this._slot = Math.max(0, this._slot - 1);
        this._saveDiy();
        return this._render();
      case "paint":
      case "paint-pick":
        diy.slots[this._slot] = value;
        if (action === "paint" && this._slot < diy.slots.length - 1) this._slot += 1;
        this._saveDiy();
        return this._render();
      case "dynamic":
        diy.dynamic = value;
        this._saveDiy();
        return this._render();
      case "diy-speed":
        diy.speed = Number(value);
        this._saveDiy();
        return this._render();
      case "diy-direction":
        diy.direction = value;
        this._saveDiy();
        return this._render();
      case "random":
        return this._applyDiy(true);
      case "apply":
        return this._applyDiy(false);
      default:
        return undefined;
    }
  }

  _applyDiy(random) {
    const diy = this._loadDiy();
    const data = { entity_id: this._config.entity, dynamic_effect: diy.dynamic };
    if (random) data.random = true;
    else data.colors = diy.slots.map(hexToRgb);
    if (diy.dynamic !== "none") data.speed = diy.speed;
    if (DIRECTIONAL.has(diy.dynamic)) data.direction = diy.direction;
    return this._call(DOMAIN, "set_custom_effect", data);
  }
}

const POWER_ICON = `<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
  <path fill="currentColor" d="M13 3h-2v10h2V3zm4.83 2.17-1.42 1.42A6.92 6.92 0 0 1 19 12a7 7 0 1 1-11.41-5.41L6.17 5.17A8.93 8.93 0 0 0 3 12a9 9 0 0 0 18 0c0-2.74-1.23-5.18-3.17-6.83z"/></svg>`;

const STYLE = `
  :host { --accent: var(--primary-color, #03a9f4); --xmas-red: #E53935; --xmas-green: #2E7D32; }
  ha-card { padding: 16px; overflow: hidden; }
  .empty { padding: 8px; color: var(--secondary-text-color); }
  button { font: inherit; color: inherit; cursor: pointer; }
  button:disabled { cursor: default; opacity: .5; }
  .header { display: flex; align-items: center; gap: 12px; position: relative; padding-top: 18px; }
  .bulbs { position: absolute; top: -4px; left: -16px; right: -16px; height: 22px; display: flex;
    justify-content: space-around; border-top: 2px solid var(--divider-color, #444); border-radius: 50% / 0 0 100% 100%; }
  .bulb { width: 8px; height: 12px; margin-top: 4px; border-radius: 50% 50% 50% 50% / 40% 40% 60% 60%;
    background: var(--c); box-shadow: 0 0 8px var(--c); animation: twinkle 2.4s ease-in-out infinite; animation-delay: var(--d); }
  .is-off .bulb { box-shadow: none; animation: none; opacity: .35; }
  @keyframes twinkle { 50% { opacity: .55; } }
  .title { flex: 1; min-width: 0; }
  .name { font-size: 1.15rem; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .status { color: var(--secondary-text-color); font-size: .875rem; }
  .power { width: 44px; height: 44px; border-radius: 50%; border: none; display: grid; place-items: center;
    background: var(--secondary-background-color, rgba(127,127,127,.15)); color: var(--secondary-text-color); }
  .power.on { background: var(--accent); color: var(--text-primary-color, #fff); }
  .brightness, .row { display: flex; align-items: center; gap: 12px; margin-top: 14px; }
  .row.between { justify-content: space-between; margin-top: 4px; }
  .label { width: 78px; flex: none; color: var(--secondary-text-color); font-size: .875rem; }
  .value { width: 40px; flex: none; text-align: right; font-variant-numeric: tabular-nums; font-size: .875rem; }
  input[type=range] { flex: 1; min-width: 0; accent-color: var(--accent); }
  .tabs { display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px; margin: 16px 0 12px;
    padding: 4px; border-radius: 12px; background: var(--secondary-background-color, rgba(127,127,127,.12)); }
  .tab { border: none; background: none; padding: 8px 4px; border-radius: 9px; font-size: .875rem; color: var(--secondary-text-color); }
  .tab.active { background: var(--card-background-color, #fff); color: var(--primary-text-color);
    box-shadow: 0 1px 3px rgba(0,0,0,.18); font-weight: 500; }
  .chips { display: flex; flex-wrap: wrap; gap: 8px; }
  .chip { border: 1px solid var(--divider-color, rgba(127,127,127,.3)); background: none; border-radius: 18px;
    padding: 7px 12px; font-size: .85rem; }
  .chip.active { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 16%, transparent); font-weight: 500; }
  .segmented { display: flex; flex: 1; gap: 4px; padding: 3px; border-radius: 10px;
    background: var(--secondary-background-color, rgba(127,127,127,.12)); }
  .segmented.wide { margin-top: 4px; }
  .segmented button { flex: 1; border: none; background: none; padding: 7px 4px; border-radius: 8px; font-size: .82rem;
    color: var(--secondary-text-color); }
  .segmented button.active { background: var(--card-background-color, #fff); color: var(--primary-text-color);
    box-shadow: 0 1px 3px rgba(0,0,0,.18); font-weight: 500; }
  .section-title { margin: 16px 0 8px; font-size: .8rem; text-transform: uppercase; letter-spacing: .06em;
    color: var(--secondary-text-color); }
  .section-title .hint { text-transform: none; letter-spacing: 0; margin-left: 6px; }
  .strong { font-weight: 500; }
  .hint { color: var(--secondary-text-color); font-size: .8rem; }
  .toggle { width: 46px; height: 26px; border-radius: 13px; border: none; padding: 0; position: relative; flex: none;
    background: var(--disabled-color, #9e9e9e); transition: background .2s; }
  .toggle span { position: absolute; top: 3px; left: 3px; width: 20px; height: 20px; border-radius: 50%; background: #fff;
    transition: transform .2s; }
  .toggle.on { background: var(--accent); }
  .toggle.on span { transform: translateX(20px); }
  .subtabs { display: flex; gap: 6px; overflow-x: auto; }
  .subtabs button { border: none; background: none; padding: 4px 10px; border-radius: 14px; font-size: .85rem;
    color: var(--secondary-text-color); white-space: nowrap; }
  .subtabs button.active { background: var(--primary-text-color); color: var(--card-background-color, #fff); }
  .schemes { display: grid; grid-template-columns: repeat(auto-fill, minmax(96px, 1fr)); gap: 8px; margin-top: 10px; }
  .scheme { border: 2px solid transparent; background: var(--secondary-background-color, rgba(127,127,127,.1));
    border-radius: 12px; padding: 6px; text-align: left; }
  .scheme.active { border-color: var(--accent); }
  .swatches { display: flex; height: 22px; border-radius: 7px; overflow: hidden; }
  .swatches span { flex: 1; }
  .scheme-name { font-size: .78rem; margin-top: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .wheel-wrap { display: flex; justify-content: center; padding: 4px 0; }
  .wheel { width: min(220px, 70vw); aspect-ratio: 1; border-radius: 50%; position: relative; cursor: crosshair;
    background: conic-gradient(red, yellow, lime, cyan, blue, magenta, red); }
  .wheel-fade { position: absolute; inset: 0; border-radius: 50%; background: radial-gradient(circle, #fff 0%, rgba(255,255,255,0) 70%); }
  .marker { position: absolute; width: 18px; height: 18px; margin: -11px 0 0 -11px; border-radius: 50%;
    border: 3px solid #fff; box-shadow: 0 0 0 1px rgba(0,0,0,.35), 0 2px 6px rgba(0,0,0,.35); pointer-events: none; }
  .swatch-row { display: flex; flex-wrap: wrap; gap: 10px; }
  .dot { width: 32px; height: 32px; border-radius: 50%; border: 2px solid var(--card-background-color, #fff);
    box-shadow: 0 0 0 1px var(--divider-color, rgba(127,127,127,.4)); padding: 0; position: relative; }
  .dot.active { box-shadow: 0 0 0 2px var(--accent); }
  .dot.picker { background: conic-gradient(red, yellow, lime, cyan, blue, magenta, red); overflow: hidden; cursor: pointer; }
  .dot.picker input { opacity: 0; width: 100%; height: 100%; cursor: pointer; }
  .string { position: relative; display: flex; justify-content: space-between; align-items: flex-start;
    height: 46px; padding: 0 2px; margin-bottom: 4px; }
  .wire { position: absolute; left: 0; right: 0; top: 6px; height: 14px; border-bottom: 2px solid var(--divider-color, #555);
    border-radius: 0 0 50% 50%; }
  .led { position: relative; width: 7px; height: 11px; margin-top: calc(12px + 6px * sin(var(--i) * 0.21rad));
    border-radius: 50% 50% 50% 50% / 40% 40% 60% 60%; background: var(--c); box-shadow: 0 0 7px var(--c); }
  .anim-breath .led { animation: breathe var(--speed) ease-in-out infinite; }
  .anim-flashing .led { animation: flash var(--speed) steps(1) infinite; animation-delay: calc(var(--i) * -0.13s); }
  .anim-translation .led { animation: slide var(--speed) linear infinite; animation-delay: calc(var(--i) * var(--speed) / -10); }
  .anim-translation.dir-down .led { animation-direction: reverse; }
  .anim-stack .led { animation: stack var(--speed) steps(1) infinite; animation-delay: calc(var(--i) * var(--speed) / 30); }
  .anim-stack.dir-down .led { animation-delay: calc((30 - var(--i)) * var(--speed) / 30); }
  @keyframes breathe { 50% { opacity: .15; box-shadow: none; } }
  @keyframes flash { 50% { opacity: .1; box-shadow: none; } }
  @keyframes slide { 0%, 100% { filter: brightness(1); } 50% { filter: brightness(.25); } }
  @keyframes stack { 0% { opacity: .12; box-shadow: none; } 50% { opacity: 1; } }
  .slots { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
  .slot { width: 36px; height: 36px; border-radius: 10px; border: 2px solid var(--card-background-color, #fff);
    box-shadow: 0 0 0 1px var(--divider-color, rgba(127,127,127,.4)); padding: 0; font-size: 1.2rem; }
  .slot.active { box-shadow: 0 0 0 3px var(--accent); }
  .slot.add, .slot.remove { background: none; color: var(--secondary-text-color); }
  .actions { display: flex; gap: 8px; margin-top: 18px; }
  .actions button { flex: 1; border-radius: 10px; padding: 10px; font-weight: 500; border: none; }
  .primary { background: var(--accent); color: var(--text-primary-color, #fff); }
  .secondary { background: var(--secondary-background-color, rgba(127,127,127,.15)); }
  @media (prefers-reduced-motion: reduce) { .bulb, .led { animation: none !important; } }
`;

if (!customElements.get("yeelight-christmas-card")) {
  customElements.define("yeelight-christmas-card", YeelightChristmasCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "yeelight-christmas-card",
    name: "Yeelight Christmas Lights",
    description: "Power, brightness and all lighting modes for Yeelight Christmas String Lights.",
    preview: true,
    documentationURL: "https://github.com/mrf1n/ha-yeelight-lights-ble",
  });
  console.info(`%c YEELIGHT-CHRISTMAS-CARD %c ${CARD_VERSION} `, "background:#c62828;color:#fff", "background:#2e7d32;color:#fff");
}
