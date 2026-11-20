/**
 * OmenFLUX — Main Web Studio Controller
 * Handles SSE live telemetry, REST API synchronization, zone selections,
 * effects deck, and preset management.
 */

let keyboard = null;
let colorWheel = null;

let selectedZones = new Set([0, 1, 2, 3]);
let currentZoneColors = [
    [255, 0, 80],
    [0, 200, 255],
    [140, 0, 255],
    [0, 255, 170]
];
let currentOwner = "OMENFLUX";
let currentOlsRunning = true;
let currentOlsPid = null;
let currentEffect = "Static";
let currentSpeed = 1.0;
let currentBrightness = 1.0;
let activeProfileName = "";
let cachedEffectsList = [];
let cachedProfilesData = [];

document.addEventListener("DOMContentLoaded", () => {
    initApp();
    setupHeartbeat();
});

function setupHeartbeat() {
    setInterval(() => {
        fetch("/api/heartbeat", { method: "POST" }).catch(() => {});
    }, 2000);
}

function initApp() {
    // 1. Initialize Keyboard Component
    keyboard = new OmenKeyboardWidget("keyboardContainer", (clickedZone) => {
        selectSingleZone(clickedZone);
    });

    // 2. Initialize Color Wheel Component
    colorWheel = new ColorWheel("colorWheelCanvas", (r, g, b) => {
        handleColorWheelChange(r, g, b);
    });

    // 3. Connect UI Controls
    setupEventListeners();

    // 4. Connect Server-Sent Events (SSE) Stream
    connectSseStream();

    // 5. Fetch Initial Status
    fetchStatus();
}

function setupEventListeners() {
    // Handover Buttons (Always Visible Dual Switch)
    document.getElementById("btnTakeControl").addEventListener("click", takeControl);
    document.getElementById("btnReleaseOls").addEventListener("click", releaseToOls);

    // Zone Filter Buttons
    document.querySelectorAll(".zone-pill").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const z = btn.dataset.zone;
            if (z === "all") {
                selectAllZones();
            } else {
                selectSingleZone(parseInt(z, 10));
            }
        });
    });

    // Zone Indicator Swatches Click (Right End)
    document.querySelectorAll(".zone-indicator-swatch").forEach(swatch => {
        swatch.addEventListener("click", () => {
            const z = swatch.dataset.zone;
            if (z !== undefined) {
                selectSingleZone(parseInt(z, 10));
            }
        });
    });

    // Speed & Brightness Sliders
    const sliderSpeed = document.getElementById("sliderSpeed");
    sliderSpeed.addEventListener("input", (e) => {
        const val = parseFloat(e.target.value);
        document.getElementById("valSpeed").textContent = `${val.toFixed(1)}x`;
        postEffectUpdate({ speed: val });
    });

    const sliderBri = document.getElementById("sliderBrightness");
    sliderBri.addEventListener("input", (e) => {
        const val = parseFloat(e.target.value);
        document.getElementById("valBrightness").textContent = `${Math.round(val * 100)}%`;
        postEffectUpdate({ brightness: val });
    });

    // Color Value Slider
    const sliderVal = document.getElementById("sliderWheelValue");
    if (sliderVal) {
        sliderVal.addEventListener("input", (e) => {
            const val = parseFloat(e.target.value);
            const label = document.getElementById("labelWheelValue");
            if (label) label.textContent = `${Math.round(val * 100)}%`;
            colorWheel.setValue(val);
        });
    }

    // Hex Input
    const hexInput = document.getElementById("inputHex");
    if (hexInput) {
        hexInput.addEventListener("input", (e) => {
            const hex = e.target.value.trim();
            if (/^#[0-9A-Fa-f]{6}$/.test(hex)) {
                const swatch = document.getElementById("hexSwatchPreview");
                if (swatch) {
                    swatch.style.backgroundColor = hex;
                    swatch.style.boxShadow = `0 0 8px ${hex}`;
                }
            }
        });
        hexInput.addEventListener("change", (e) => {
            const hex = e.target.value.trim();
            if (/^#[0-9A-Fa-f]{6}$/.test(hex)) {
                const r = parseInt(hex.slice(1, 3), 16);
                const g = parseInt(hex.slice(3, 5), 16);
                const b = parseInt(hex.slice(5, 7), 16);
                colorWheel.setColorRgb(r, g, b);
                applyRgbToSelectedZones(r, g, b);
            }
        });
    }

    // Harmonizer Presets
    document.querySelectorAll(".palette-chip").forEach(chip => {
        chip.addEventListener("click", () => {
            const palette = JSON.parse(chip.dataset.palette);
            applyHarmoniousPalette(palette);
        });
    });

    // Randomize Buttons
    const btnRandPal = document.getElementById("btnRandomizePalette");
    if (btnRandPal) btnRandPal.addEventListener("click", randomizePalette);

    const btnRandFull = document.getElementById("btnRandomizeFull");
    if (btnRandFull) btnRandFull.addEventListener("click", randomizeFull);

    // Profile Save Button
    document.getElementById("btnSaveProfile").addEventListener("click", () => {
        const name = prompt("Enter a name for this custom profile:");
        if (name && name.trim()) {
            saveCurrentProfile(name.trim());
        }
    });

    // Autostart Toggle Button
    const btnAutostart = document.getElementById("btnToggleAutostart");
    if (btnAutostart) {
        btnAutostart.addEventListener("click", async () => {
            const currentlyActive = btnAutostart.classList.contains("active");
            const newState = !currentlyActive;
            try {
                const res = await fetch("/api/settings/autostart", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ enabled: newState })
                });
                const data = await res.json();
                updateAutostartDisplay(data.autostart);
            } catch (e) {
                console.error("Failed to toggle autostart:", e);
            }
        });
    }

    // Window Actions (Background & Quit)
    const btnBg = document.getElementById("btnRunBackground");
    if (btnBg) {
        btnBg.addEventListener("click", () => {
            window.close();
        });
    }

    const btnQuit = document.getElementById("btnExitApp");
    if (btnQuit) {
        btnQuit.addEventListener("click", async () => {
            if (confirm("Quit OmenFLUX and hand control back to OMEN Light Studio?")) {
                try {
                    await fetch("/api/app/quit", { method: "POST" });
                } catch (e) {}
                window.close();
            }
        });
    }
}

// -------------------------------------------------------------
// Handover & System Status
// -------------------------------------------------------------

function isOmenFluxOwner(owner) {
    if (!owner) return false;
    const str = String(owner).toUpperCase();
    return str.includes("OMENFLUX") || str.includes("OMENPULSE") || str.includes("OMENGLOW") || str.includes("STANDALONE");
}
const isOmenPulseOwner = isOmenFluxOwner;
const isOmenGlowOwner = isOmenFluxOwner;

async function fetchStatus() {
    try {
        const res = await fetch("/api/status");
        const data = await res.json();
        updateFullUiState(data);
    } catch (err) {
        console.warn("Status fetch failed:", err);
    }
}

function updateFullUiState(data) {
    if (!data) return;

    if (data.owner !== undefined) currentOwner = data.owner;
    if (data.ols_running !== undefined) currentOlsRunning = data.ols_running;
    if (data.ols_pid !== undefined) currentOlsPid = data.ols_pid || currentOlsPid;
    if (data.zone_colors) currentZoneColors = data.zone_colors;
    if (data.effect) currentEffect = data.effect;
    if (data.speed !== undefined) currentSpeed = data.speed;
    if (data.brightness !== undefined) currentBrightness = data.brightness;

    // 1. Update Handover Cockpit
    updateHandoverDisplay(currentOwner, currentOlsRunning, currentOlsPid);

    // 2. Update Sliders
    if (data.speed !== undefined) {
        const sliderSpeed = document.getElementById("sliderSpeed");
        if (sliderSpeed) sliderSpeed.value = data.speed;
        const valSpeed = document.getElementById("valSpeed");
        if (valSpeed) valSpeed.textContent = `${Number(data.speed).toFixed(1)}x`;
    }

    if (data.brightness !== undefined) {
        const sliderBri = document.getElementById("sliderBrightness");
        if (sliderBri) sliderBri.value = data.brightness;
        const valBri = document.getElementById("valBrightness");
        if (valBri) valBri.textContent = `${Math.round(data.brightness * 100)}%`;
    }

    // 3. Render Effects List
    if (data.effects_list && data.effects_list.length > 0) {
        cachedEffectsList = data.effects_list;
    }
    if (cachedEffectsList && cachedEffectsList.length > 0) {
        renderEffectsList(cachedEffectsList, currentEffect);
    }

    // 4. Render Profiles List
    if (data.profiles_data && data.profiles_data.length > 0) {
        cachedProfilesData = data.profiles_data;
    } else if (data.profiles && data.profiles.length > 0) {
        cachedProfilesData = data.profiles.map(p => (typeof p === "string" ? { name: p } : p));
    }
    if (cachedProfilesData && cachedProfilesData.length > 0) {
        renderProfilesList(cachedProfilesData);
    }

    // 5. Update Zone Swatches & Color Picker
    if (currentZoneColors) {
        updateZoneSwatches(currentZoneColors);
        const activeColor = (selectedZones && selectedZones.size === 1)
            ? currentZoneColors[[...selectedZones][0]]
            : currentZoneColors[0];
        if (activeColor && colorWheel) {
            const [r, g, b] = activeColor;
            colorWheel.setColorRgb(r, g, b);
            updateHexInput(r, g, b);
        }
    }

    // 6. Update Autostart Status
    if (data.autostart !== undefined) {
        updateAutostartDisplay(data.autostart);
    }

    // 7. Update Keyboard
    if (keyboard) {
        keyboard.updateLighting(data.live_colors || currentZoneColors);
    }
}

function updateHandoverDisplay(owner, olsRunning, olsPid) {
    currentOwner = owner;
    if (olsPid) currentOlsPid = olsPid;

    const btnTake = document.getElementById("btnTakeControl");
    const btnRelease = document.getElementById("btnReleaseOls");
    const badgeOls = document.getElementById("badgeOlsStatus");
    const dotOls = document.querySelector(".telemetry-dot");

    const inControl = isOmenGlowOwner(owner);

    if (inControl) {
        if (btnTake) btnTake.classList.add("active");
        if (btnRelease) btnRelease.classList.remove("active");
        if (badgeOls) {
            badgeOls.textContent = currentOlsPid ? `OLS Suspended (PID ${currentOlsPid})` : "OLS Suspended";
        }
        if (dotOls) {
            dotOls.style.background = "#FFB300";
            dotOls.style.boxShadow = "0 0 10px #FFB300";
        }
    } else {
        if (btnTake) btnTake.classList.remove("active");
        if (btnRelease) btnRelease.classList.add("active");
        if (badgeOls) {
            badgeOls.textContent = currentOlsPid ? `OLS Active (PID ${currentOlsPid})` : "OLS Active";
        }
        if (dotOls) {
            dotOls.style.background = "#00E676";
            dotOls.style.boxShadow = "0 0 10px #00E676";
        }
    }
}

function updateAutostartDisplay(enabled) {
    const btn = document.getElementById("btnToggleAutostart");
    const label = document.getElementById("labelAutostart");
    if (!btn || !label) return;
    if (enabled) {
        btn.classList.add("active");
        label.textContent = "🚀 STARTUP: ON";
    } else {
        btn.classList.remove("active");
        label.textContent = "💤 STARTUP: OFF";
    }
}

async function takeControl() {
    try {
        const res = await fetch("/api/handover/take", { method: "POST" });
        const data = await res.json();
        updateHandoverDisplay(data.owner, true, data.ols_pid || currentOlsPid);
    } catch (e) {
        console.error("Take control failed:", e);
    }
}

async function releaseToOls() {
    try {
        const res = await fetch("/api/handover/release", { method: "POST" });
        const data = await res.json();
        updateHandoverDisplay(data.owner, true, data.ols_pid || currentOlsPid);
    } catch (e) {
        console.error("Release to OLS failed:", e);
    }
}

// -------------------------------------------------------------
// Real-time SSE Stream
// -------------------------------------------------------------

function connectSseStream() {
    const sse = new EventSource("/api/stream");

    sse.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === "frame" && data.colors) {
                keyboard.updateLighting(data.colors);
            } else if (data.type === "owner") {
                currentOwner = data.owner;
                if (data.ols_pid) currentOlsPid = data.ols_pid;
                updateHandoverDisplay(data.owner, data.ols_running ?? currentOlsRunning, data.ols_pid || currentOlsPid);
            } else if (data.type === "init") {
                updateFullUiState(data);
            }
        } catch (e) {
            console.error("SSE parse error:", e);
        }
    };

    sse.onerror = () => {
        console.warn("SSE reconnecting...");
    };
}

// -------------------------------------------------------------
// Zone Selection & Color Handling
// -------------------------------------------------------------

function selectAllZones() {
    selectedZones = new Set([0, 1, 2, 3]);
    keyboard.setSelectedZones(selectedZones);
    updateZonePillStyles();
}

function selectSingleZone(z) {
    selectedZones = new Set([z]);
    keyboard.setSelectedZones(selectedZones);
    updateZonePillStyles();

    const [r, g, b] = currentZoneColors[z];
    colorWheel.setColorRgb(r, g, b);
    updateHexInput(r, g, b);
}

function updateZonePillStyles() {
    document.querySelectorAll(".zone-pill").forEach(pill => {
        const z = pill.dataset.zone;
        if (z === "all") {
            pill.classList.toggle("active", selectedZones.size === 4);
        } else {
            pill.classList.toggle("active", selectedZones.size === 1 && selectedZones.has(parseInt(z, 10)));
        }
    });

    document.querySelectorAll(".zone-indicator-swatch").forEach(swatch => {
        const z = swatch.dataset.zone;
        if (z !== undefined) {
            const zNum = parseInt(z, 10);
            const isSelected = selectedZones.size === 4 || selectedZones.has(zNum);
            swatch.classList.toggle("active", isSelected);
        }
    });
}

function handleColorWheelChange(r, g, b) {
    updateHexInput(r, g, b);
    applyRgbToSelectedZones(r, g, b);
}

function updateHexInput(r, g, b) {
    const hex = "#" + [r, g, b].map(x => x.toString(16).padStart(2, "0")).join("").toUpperCase();
    const hexEl = document.getElementById("inputHex");
    if (hexEl) hexEl.value = hex;
    const rgbEl = document.getElementById("valRgb");
    if (rgbEl) rgbEl.textContent = `RGB(${r}, ${g}, ${b})`;
    const swatch = document.getElementById("hexSwatchPreview");
    if (swatch) {
        swatch.style.backgroundColor = hex;
        swatch.style.boxShadow = `0 0 8px ${hex}`;
    }
    if (typeof colorWheel !== "undefined" && colorWheel) {
        const sliderVal = document.getElementById("sliderWheelValue");
        const labelVal = document.getElementById("labelWheelValue");
        if (sliderVal) sliderVal.value = colorWheel.value;
        if (labelVal) labelVal.textContent = `${Math.round(colorWheel.value * 100)}%`;
    }
}

async function applyRgbToSelectedZones(r, g, b) {
    for (const z of selectedZones) {
        currentZoneColors[z] = [r, g, b];
        await fetch("/api/color/zone", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ zone: z, r, g, b })
        });
    }
    updateZoneSwatches(currentZoneColors);
    updateHandoverDisplay("OmenFLUX", true, currentOlsPid);
}

function updateZoneSwatches(colors) {
    for (let z = 0; z < 4; z++) {
        const [r, g, b] = colors[z];
        const el = document.getElementById(`swatchZone${z}`);
        if (el) {
            el.style.backgroundColor = `rgb(${r}, ${g}, ${b})`;
            el.style.boxShadow = `0 0 10px rgba(${r}, ${g}, ${b}, 0.8)`;
        }
    }
}

// -------------------------------------------------------------
// Harmonious Palettes & Randomizers
// -------------------------------------------------------------

async function applyHarmoniousPalette(palette) {
    if (!palette || palette.length < 4) return;
    currentZoneColors = palette;
    try {
        const res = await fetch("/api/color/all", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ colors: palette })
        });
        if (!res.ok) {
            // Fallback per-zone write if bulk route was unavailable
            for (let z = 0; z < 4; z++) {
                const [r, g, b] = palette[z];
                await fetch("/api/color/zone", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ zone: z, r, g, b })
                });
            }
        }
    } catch (e) {
        console.error("applyHarmoniousPalette error:", e);
    }
    updateZoneSwatches(palette);
    if (keyboard) {
        keyboard.updateLighting(palette);
    }
    if (colorWheel) {
        colorWheel.setColorRgb(...palette[0]);
        updateHexInput(...palette[0]);
    }
    updateHandoverDisplay("OmenFLUX", true, currentOlsPid);
}

function generateHarmonicPalette() {
    const baseH = Math.random() * 360;
    const mode = Math.floor(Math.random() * 5);

    // Aesthetic tone styles:
    // 0: Soft Pastel / Ethereal Light (35%) - light, airy, soft pastel tones (pink, lavender, mint, ice, peach)
    // 1: Radiant Tint / Ice Shimmer (25%) - clean, glowing lighter tones
    // 2: Zone Tactical Accent (15%) - WASD accent pops out against lighter ambient keyboard backdrop
    // 3: Vivid / Neon (25%) - classic saturated hues
    const styleRoll = Math.random();
    let style = "vivid";
    if (styleRoll < 0.35) {
        style = "pastel";
    } else if (styleRoll < 0.60) {
        style = "radiant_tint";
    } else if (styleRoll < 0.75) {
        style = "zone_accent";
    } else {
        style = "vivid";
    }

    const palette = [];
    for (let i = 0; i < 4; i++) {
        let h = baseH;
        if (mode === 0) h = (baseH + i * 35) % 360;             // Analogous
        else if (mode === 1) h = (baseH + (i % 3) * 120) % 360; // Triadic
        else if (mode === 2) h = (baseH + (i % 2 === 0 ? 0 : 180) + (i >= 2 ? 30 : 0)) % 360; // Complementary split
        else if (mode === 3) h = (baseH + i * 90) % 360;        // Tetradic / Square
        else h = (baseH + (i === 0 ? 0 : (i === 1 ? 150 : (i === 2 ? 210 : 35)))) % 360; // Split Complementary

        let s, v;
        if (style === "pastel") {
            // Lighter pastel tones (soft, bright, elegant)
            s = 0.20 + Math.random() * 0.28; // 0.20 to 0.48 saturation
            v = 0.95 + Math.random() * 0.05; // 0.95 to 1.00 value
        } else if (style === "radiant_tint") {
            // Lighter luminous tints (crisp, candy/ice tones)
            s = 0.40 + Math.random() * 0.25; // 0.40 to 0.65 saturation
            v = 0.92 + Math.random() * 0.08;
        } else if (style === "zone_accent") {
            // Zone 0 (WASD) is vivid accent; other zones are lighter ethereal tones
            if (i === 0) {
                s = 0.85 + Math.random() * 0.15;
                v = 0.95 + Math.random() * 0.05;
            } else {
                s = 0.22 + Math.random() * 0.28;
                v = 0.94 + Math.random() * 0.06;
            }
        } else {
            // Classic vivid / saturated
            s = 0.80 + Math.random() * 0.20;
            v = 0.90 + Math.random() * 0.10;
        }

        const [r, g, b] = colorWheel.hsvToRgb(h, s, v);
        palette.push([r, g, b]);
    }
    return palette;
}

function randomizePalette() {
    const btn = document.getElementById("btnRandomizePalette");
    if (btn) {
        btn.classList.add("btn-spinning");
        setTimeout(() => btn.classList.remove("btn-spinning"), 600);
    }
    const palette = generateHarmonicPalette();
    applyHarmoniousPalette(palette);
    document.querySelectorAll(".profile-card").forEach(c => c.classList.remove("active"));
    activeProfileName = "";
}

async function randomizeFull() {
    const btn = document.getElementById("btnRandomizeFull");
    if (btn) {
        btn.classList.add("btn-spinning");
        setTimeout(() => btn.classList.remove("btn-spinning"), 800);
    }

    // 1. Generate harmonious 4-zone palette
    const palette = generateHarmonicPalette();

    // 2. Pick dynamic animated procedural effect (excluding static, off, and exclusive modes)
    const dynamicEffects = (cachedEffectsList && cachedEffectsList.length > 0)
        ? cachedEffectsList.filter(e => !["Static", "Stealth", "Off", "Apex Overdrive", "Vanguard Protocol"].includes(e))
        : ["Breathing", "Color Wave", "Spectrum Cycle", "Prismatic Aurora", "Plasma Pulse", "Cyber Glitch", "Cosmic Starlight", "Solar Flare", "Binary Cascade"];
    
    const chosenEffect = dynamicEffects[Math.floor(Math.random() * dynamicEffects.length)];
    const randomSpeed = parseFloat((0.8 + Math.random() * 1.5).toFixed(1)); // 0.8x to 2.3x

    // 3. Apply palette to zones and wait for backend sync
    await applyHarmoniousPalette(palette);

    // 4. Update effect & speed
    currentEffect = chosenEffect;
    currentSpeed = randomSpeed;

    const sliderSpeed = document.getElementById("sliderSpeed");
    if (sliderSpeed) sliderSpeed.value = randomSpeed;
    const valSpeed = document.getElementById("valSpeed");
    if (valSpeed) valSpeed.textContent = `${randomSpeed.toFixed(1)}x`;

    // Highlight card in effects deck and scroll smoothly into view
    document.querySelectorAll(".effect-card").forEach(card => {
        const nameEl = card.querySelector(".effect-name");
        if (nameEl && nameEl.textContent === chosenEffect) {
            card.classList.add("active");
            card.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "nearest" });
        } else {
            card.classList.remove("active");
        }
    });

    const ind = document.getElementById("exclusiveEffectIndicator");
    if (ind) ind.style.display = "none";

    document.querySelectorAll(".profile-card").forEach(c => c.classList.remove("active"));
    activeProfileName = "";

    await postEffectUpdate({ effect: chosenEffect, speed: randomSpeed });
}

// -------------------------------------------------------------
// Effects Deck
// -------------------------------------------------------------

function renderEffectsList(effects, activeEffect) {
    const deck = document.getElementById("effectsDeck");
    deck.innerHTML = "";

    const indicator = document.getElementById("exclusiveEffectIndicator");
    if (indicator) {
        indicator.style.display = (activeEffect === "Apex Overdrive") ? "inline-block" : "none";
    }

    const effectIcons = {
        "Static": "💡",
        "Breathing": "🫁",
        "Color Wave": "🌊",
        "Spectrum Cycle": "🌈",
        "Rainbow Cycle": "🌈",
        "Heartbeat": "💓",
        "Knight Rider Scanner": "🚨",
        "Prismatic Aurora": "🌌",
        "Northern Lights": "🌌",
        "Plasma Pulse": "🔮",
        "Cyber Glitch": "⚡",
        "Cosmic Starlight": "✨",
        "Starlight Twinkle": "✨",
        "Starfield Twinkle": "✨",
        "Solar Flare": "🔥",
        "Fire & Embers": "🔥",
        "Emergency Glitch": "🚨",
        "Emergency Strobe": "🚨",
        "Binary Cascade": "🟢",
        "Digital Cascade": "🟢",
        "Matrix Green": "🟢",
        "Audio Pulse (Ambient)": "🎼",
        "Reactive Ripple": "⌨️",
        "Reactive Typing": "⌨️"
    };

    (effects || []).forEach(name => {
        const card = document.createElement("div");
        card.className = "effect-card";
        if (name === activeEffect) card.classList.add("active");

        const iconSpan = document.createElement("span");
        iconSpan.className = "effect-icon";
        iconSpan.textContent = effectIcons[name] || "✨";
        card.appendChild(iconSpan);

        const nameSpan = document.createElement("span");
        nameSpan.className = "effect-name";
        nameSpan.textContent = name;
        card.appendChild(nameSpan);

        card.addEventListener("click", () => {
            document.querySelectorAll(".effect-card").forEach(c => c.classList.remove("active"));
            card.classList.add("active");
            const ind = document.getElementById("exclusiveEffectIndicator");
            if (ind) ind.style.display = "none";
            postEffectUpdate({ effect: name });
        });

        deck.appendChild(card);
    });
}

async function postEffectUpdate(params) {
    try {
        await fetch("/api/effect", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(params)
        });
        updateHandoverDisplay("OmenFLUX", true, currentOlsPid);
    } catch (e) {
        console.error("Effect update error:", e);
    }
}

// -------------------------------------------------------------
// Profiles Vault Management & Handover
// -------------------------------------------------------------

function getProfileIcon(name) {
    const n = (name || "").toLowerCase();
    if (n.includes("apex") || n.includes("vanguard")) return "🛡️";
    if (n.includes("sakura") || n.includes("blossom")) return "🌸";
    if (n.includes("quantum") || n.includes("prism")) return "🔮";
    if (n.includes("crimson") || n.includes("omen")) return "💎";
    if (n.includes("cyberpunk")) return "🌆";
    if (n.includes("tokyo")) return "🗼";
    if (n.includes("abyssal") || n.includes("trench") || n.includes("ocean")) return "🦑";
    if (n.includes("inferno") || n.includes("forge")) return "🌋";
    if (n.includes("glacial") || n.includes("tundra") || n.includes("ice") || n.includes("frost")) return "❄️";
    if (n.includes("acid") || n.includes("wasteland") || n.includes("toxic") || n.includes("biohazard")) return "☣️";
    if (n.includes("synthwave") || n.includes("1984") || n.includes("sunset") || n.includes("vaporwave")) return "🌇";
    if (n.includes("horizon") || n.includes("event")) return "🕳️";
    if (n.includes("bioluminescence")) return "🌿";
    if (n.includes("blood moon") || n.includes("blood")) return "🌑";
    if (n.includes("chrome") || n.includes("symphony")) return "🎼";
    if (n.includes("ghost") || n.includes("recon")) return "🎯";
    if (n.includes("hyperdrive") || n.includes("jump") || n.includes("space")) return "🚀";
    if (n.includes("valkyrie")) return "⚔️";
    if (n.includes("solar") || n.includes("corona")) return "☀️";
    if (n.includes("deep space")) return "🚀";
    if (n.includes("reactive") || n.includes("typing") || n.includes("ripple")) return "⌨️";
    if (n.includes("strobe") || n.includes("emergency")) return "🚨";
    if (n.includes("rainbow") || n.includes("spectrum")) return "🌈";
    if (n.includes("stealth") || n.includes("off") || n.includes("dark")) return "🌑";
    return "🎨";
}

function renderProfilesList(profiles) {
    const listEl = document.getElementById("profilesVault");
    if (!listEl) return;
    listEl.innerHTML = "";

    const countBadge = document.getElementById("profilesCountBadge");
    if (countBadge && Array.isArray(profiles)) {
        countBadge.textContent = `(${profiles.length})`;
    }

    (profiles || []).forEach(item => {
        const name = typeof item === "string" ? item : item.name;
        const colors = item.zone_colors || [[255, 255, 255], [255, 255, 255], [255, 255, 255], [255, 255, 255]];
        const effect = item.effect || "Static";

        const card = document.createElement("div");
        card.className = "profile-card";
        if (name === activeProfileName) card.classList.add("active");

        const body = document.createElement("div");
        body.className = "profile-card-body";

        const iconSpan = document.createElement("span");
        iconSpan.className = "profile-icon";
        iconSpan.textContent = getProfileIcon(name);
        body.appendChild(iconSpan);

        const meta = document.createElement("div");
        meta.className = "profile-meta";

        const nameSpan = document.createElement("span");
        nameSpan.className = "profile-name";
        nameSpan.textContent = name;
        nameSpan.title = `${name} (${effect})`;
        meta.appendChild(nameSpan);

        const tagSpan = document.createElement("span");
        tagSpan.className = "profile-effect-tag";
        if (effect === "Apex Overdrive" || effect === "Vanguard Protocol" || name === "Apex Vanguard") {
            tagSpan.classList.add("exclusive-tag");
            tagSpan.textContent = "⚡ Apex Overdrive";
            tagSpan.title = "Exclusive High-Octane Combo Engine — Only available on Apex Vanguard";
        } else {
            tagSpan.textContent = effect;
        }
        meta.appendChild(tagSpan);

        body.appendChild(meta);
        card.appendChild(body);

        const bar = document.createElement("div");
        bar.className = "profile-bar";
        const c0 = colors[0] || [255, 255, 255];
        const c1 = colors[1] || [255, 255, 255];
        const c2 = colors[2] || [255, 255, 255];
        const c3 = colors[3] || [255, 255, 255];
        bar.style.background = `linear-gradient(90deg, rgb(${c0.join(',')}) 0%, rgb(${c1.join(',')}) 33%, rgb(${c2.join(',')}) 66%, rgb(${c3.join(',')}) 100%)`;
        card.appendChild(bar);

        // Click to activate profile
        card.addEventListener("click", () => {
            document.querySelectorAll(".profile-card").forEach(c => c.classList.remove("active"));
            card.classList.add("active");
            activeProfileName = name;
            loadProfile(name);
        });

        // Right-click to delete custom profiles
        card.addEventListener("contextmenu", (e) => {
            e.preventDefault();
            if (confirm(`Delete custom profile '${name}'?`)) {
                deleteProfile(name);
            }
        });

        listEl.appendChild(card);
    });
}

async function loadProfile(name) {
    try {
        const res = await fetch("/api/profile/load", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name })
        });
        const data = await res.json();
        if (data.success && data.profile) {
            activeProfileName = name;
            updateFullUiState({
                owner: "OmenFLUX",
                ols_running: true,
                ols_pid: currentOlsPid,
                effect: data.profile.effect,
                speed: data.profile.speed,
                brightness: data.profile.brightness,
                live_colors: data.profile.zone_colors
            });
            updateHandoverDisplay("OmenFLUX", true, currentOlsPid);
        }
    } catch (e) {
        console.error("Load profile failed:", e);
    }
}

async function saveCurrentProfile(name) {
    try {
        const res = await fetch("/api/profile/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name,
                zone_colors: currentZoneColors,
                effect: currentEffect,
                speed: currentSpeed,
                brightness: currentBrightness
            })
        });
        const data = await res.json();
        if (data.success && data.profiles) {
            activeProfileName = name;
            renderProfilesList(data.profiles);
        }
    } catch (e) {
        console.error("Save profile error:", e);
    }
}

async function deleteProfile(name) {
    try {
        const res = await fetch("/api/profile/delete", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name })
        });
        const data = await res.json();
        if (data.success && data.profiles) {
            renderProfilesList(data.profiles);
        }
    } catch (e) {
        console.error("Delete profile error:", e);
    }
}
