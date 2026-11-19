/**
 * OmenGlow — Interactive Photorealistic HP OMEN 16 Keyboard Component
 * Accurate to the physical HP OMEN 16 (Ryzen 7 / RTX / 165Hz edition):
 * Tenkeyless 4-Zone layout with dedicated Nav columns, inverted-T arrow keys,
 * power & OMEN diamond buttons, secondary function glyphs, tactile bumps, and underglow.
 */

// HP OMEN 16 Key Layout Definition (Accurate to HP OMEN 16 Laptop Chassis)
// Format: [Label, Code, WidthUnits, ZoneIndex, SpecialTag, SubIcon]
// Standard alphanumeric key = 1.0 unit.
// Main Typing Block = 15.0 units | Separation Gap = 0.4 units | Right Nav Cluster = 3.0 units
// Total row width = 18.4 units across all 6 rows.
// HP OMEN 16 Key Layout Definition (Accurate to HP OMEN 16 Hardware Architecture)
// Format: [Label, Code, WidthUnits, ZoneIndex, SpecialTag, SubIcon]
// Zone 0: WASD Only (W, A, S, D)
// Zone 1: Left Section (Leaving WASD: Esc-F4, `~-4, Tab, Q, E, Caps, LShift, Z-C, LCtrl-LAlt)
// Zone 2: Center / Middle Section (F5-F10, 5-0, R-O, F-L, V-M, Comma, Period, Space, RAlt, Menu)
// Zone 3: Right / Navigation / Arrows (F11-F12, - =, Backspace, P, [ ], \, Enter, Nav keys, Arrows)
const OMEN_KEYBOARD_LAYOUT = [
    // Row 0: Function Keys, Power, Delete + Gap + OMEN Diamond, Calc, PrtSc (18.4 units)
    [
        ["ESC", "Escape", 1.0, 1, "fkey", ""],
        ["F1", "F1", 1.0, 1, "fkey", "⧉"],
        ["F2", "F2", 1.0, 1, "fkey", "🔅"],
        ["F3", "F3", 1.0, 1, "fkey", "🔆"],
        ["F4", "F4", 1.0, 1, "fkey", "⌨"],
        ["F5", "F5", 1.0, 2, "fkey", "🔇"],
        ["F6", "F6", 1.0, 2, "fkey", "🔉"],
        ["F7", "F7", 1.0, 2, "fkey", "🔊"],
        ["F8", "F8", 1.0, 2, "fkey", "⏮"],
        ["F9", "F9", 1.0, 2, "fkey", "⏯"],
        ["F10", "F10", 1.0, 2, "fkey", "⏭"],
        ["F11", "F11", 1.0, 3, "fkey", "🔒"],
        ["F12", "F12", 1.0, 3, "fkey", "⊞"],
        ["⏻", "Power", 1.0, 3, "power-key", ""],
        ["DELETE", "Delete", 1.0, 3, "fkey", ""],
        ["", "", 0.4, -1, "gap", ""],
        ["◆", "OmenKey", 1.0, 3, "omen-key", ""],
        ["🖩", "LaunchCalculator", 1.0, 3, "calc-key", ""],
        ["PRT SC", "PrintScreen", 1.0, 3, "fkey", ""]
    ],
    // Row 1: Number Row & Backspace + Gap + Insert, Home, PgUp (18.4 units)
    [
        ["`", "Backquote", 1.0, 1, "dual", "~"],
        ["1", "Digit1", 1.0, 1, "dual", "!"],
        ["2", "Digit2", 1.0, 1, "dual", "@"],
        ["3", "Digit3", 1.0, 1, "dual", "#"],
        ["4", "Digit4", 1.0, 1, "dual", "$"],
        ["5", "Digit5", 1.0, 2, "dual", "%"],
        ["6", "Digit6", 1.0, 2, "dual", "^"],
        ["7", "Digit7", 1.0, 2, "dual", "&"],
        ["8", "Digit8", 1.0, 2, "dual", "*"],
        ["9", "Digit9", 1.0, 2, "dual", "("],
        ["0", "Digit0", 1.0, 2, "dual", ")"],
        ["-", "Minus", 1.0, 3, "dual", "_"],
        ["=", "Equal", 1.0, 3, "dual", "+"],
        ["BACKSPACE", "Backspace", 2.0, 3, "backspace-key", "⟵"],
        ["", "", 0.4, -1, "gap", ""],
        ["INSERT", "Insert", 1.0, 3, "nav-key", ""],
        ["HOME", "Home", 1.0, 3, "nav-key", ""],
        ["PG UP", "PageUp", 1.0, 3, "nav-key", ""]
    ],
    // Row 2: QWERTY Row & Backslash + Gap + Pause, End, PgDn (18.4 units)
    [
        ["TAB", "Tab", 1.5, 1, "tab-key", "⇥"],
        ["Q", "KeyQ", 1.0, 1, "", ""],
        ["W", "KeyW", 1.0, 0, "wasd", ""],
        ["E", "KeyE", 1.0, 1, "", ""],
        ["R", "KeyR", 1.0, 2, "", ""],
        ["T", "KeyT", 1.0, 2, "", ""],
        ["Y", "KeyY", 1.0, 2, "", ""],
        ["U", "KeyU", 1.0, 2, "", ""],
        ["I", "KeyI", 1.0, 2, "", ""],
        ["O", "KeyO", 1.0, 2, "", ""],
        ["P", "KeyP", 1.0, 3, "", ""],
        ["[", "BracketLeft", 1.0, 3, "dual", "{" ],
        ["]", "BracketRight", 1.0, 3, "dual", "}" ],
        ["\\", "Backslash", 1.5, 3, "dual", "|" ],
        ["", "", 0.4, -1, "gap", ""],
        ["PAUSE", "Pause", 1.0, 3, "nav-key", ""],
        ["END", "End", 1.0, 3, "nav-key", ""],
        ["PG DN", "PageDown", 1.0, 3, "nav-key", ""]
    ],
    // Row 3: Home Row & Enter + Gap + Empty Chassis Spacer (18.4 units)
    [
        ["CAPS LOCK", "CapsLock", 1.75, 1, "caps-key", ""],
        ["A", "KeyA", 1.0, 0, "wasd", ""],
        ["S", "KeyS", 1.0, 0, "wasd", ""],
        ["D", "KeyD", 1.0, 0, "wasd", ""],
        ["F", "KeyF", 1.0, 2, "tactile", ""],
        ["G", "KeyG", 1.0, 2, "", ""],
        ["H", "KeyH", 1.0, 2, "", ""],
        ["J", "KeyJ", 1.0, 2, "tactile", ""],
        ["K", "KeyK", 1.0, 2, "", ""],
        ["L", "KeyL", 1.0, 2, "", ""],
        [";", "Semicolon", 1.0, 3, "dual", ":"],
        ["'", "Quote", 1.0, 3, "dual", "\""],
        ["ENTER", "Enter", 2.25, 3, "enter-key", "↵"],
        ["", "", 0.4, -1, "gap", ""],
        ["", "", 3.0, -1, "spacer", ""]
    ],
    // Row 4: Shift Row & Inverted-T Up Arrow (18.4 units)
    [
        ["SHIFT", "ShiftLeft", 2.25, 1, "shift-key", "⇧"],
        ["Z", "KeyZ", 1.0, 1, "", ""],
        ["X", "KeyX", 1.0, 1, "", ""],
        ["C", "KeyC", 1.0, 1, "", ""],
        ["V", "KeyV", 1.0, 2, "", ""],
        ["B", "KeyB", 1.0, 2, "", ""],
        ["N", "KeyN", 1.0, 2, "", ""],
        ["M", "KeyM", 1.0, 2, "", ""],
        [",", "Comma", 1.0, 2, "dual", "<"],
        [".", "Period", 1.0, 2, "dual", ">"],
        ["/", "Slash", 1.0, 3, "dual", "?"],
        ["SHIFT", "ShiftRight", 2.75, 3, "shift-key", "⇧"],
        ["", "", 0.4, -1, "gap", ""],
        ["", "", 1.0, -1, "spacer", ""],
        ["↑", "ArrowUp", 1.0, 3, "arrow-key", ""],
        ["", "", 1.0, -1, "spacer", ""]
    ],
    // Row 5: Spacebar & Full Inverted-T Arrows (18.4 units)
    [
        ["CTRL", "ControlLeft", 1.25, 1, "mod-key", ""],
        ["FN", "FnLeft", 1.25, 1, "mod-key", ""],
        ["⊞", "MetaLeft", 1.25, 1, "win-key", ""],
        ["ALT", "AltLeft", 1.25, 1, "mod-key", ""],
        ["", "Space", 6.0, 2, "space-key", ""],
        ["ALT", "AltRight", 1.0, 2, "mod-key", ""],
        ["≡", "ContextMenu", 1.0, 2, "mod-key", ""],
        ["FN", "FnRight", 1.0, 3, "mod-key", ""],
        ["CTRL", "ControlRight", 1.0, 3, "mod-key", ""],
        ["", "", 0.4, -1, "gap", ""],
        ["←", "ArrowLeft", 1.0, 3, "arrow-key", ""],
        ["↓", "ArrowDown", 1.0, 3, "arrow-key", ""],
        ["→", "ArrowRight", 1.0, 3, "arrow-key", ""]
    ]
];

class OmenKeyboardWidget {
    constructor(containerId, onZoneSelectCallback) {
        this.container = document.getElementById(containerId);
        this.onZoneSelect = onZoneSelectCallback;
        this.selectedZones = new Set([0, 1, 2, 3]);
        this.zoneColors = [
            [255, 0, 80],
            [0, 200, 255],
            [140, 0, 255],
            [0, 255, 170]
        ];

        this.keyElements = new Map(); // code -> DOM element
        this.zoneKeyLists = [[], [], [], []];

        this.init();
    }

    init() {
        this.container.innerHTML = "";

        // Keyboard Chassis Wrapper
        const chassis = document.createElement("div");
        chassis.className = "keyboard-chassis";

        // Ambient Underglow Surface Glow Behind Chassis
        this.underglowLayer = document.createElement("div");
        this.underglowLayer.className = "chassis-underglow";
        chassis.appendChild(this.underglowLayer);

        // HP OMEN Top Deck Speaker Grille Mesh
        const speakerGrille = document.createElement("div");
        speakerGrille.className = "chassis-speaker-grille";
        chassis.appendChild(speakerGrille);

        // Keycap Matrix
        const matrix = document.createElement("div");
        matrix.className = "key-matrix";

        OMEN_KEYBOARD_LAYOUT.forEach((row, rIdx) => {
            const rowDiv = document.createElement("div");
            rowDiv.className = `key-row row-${rIdx}`;

            row.forEach(keyDef => {
                const [label, code, width, zone, special, subIcon] = keyDef;

                if (special === "gap") {
                    const gapEl = document.createElement("div");
                    gapEl.className = "key-gap";
                    gapEl.style.flex = `${width} ${width} 0px`;
                    rowDiv.appendChild(gapEl);
                    return;
                }

                if (special === "spacer" || zone === -1) {
                    const spacerEl = document.createElement("div");
                    spacerEl.className = "key-spacer";
                    spacerEl.style.flex = `${width} ${width} 0px`;
                    rowDiv.appendChild(spacerEl);
                    return;
                }

                const keyEl = document.createElement("div");
                keyEl.className = `keycap zone-${zone}`;
                if (special === "wasd") keyEl.classList.add("wasd-key");
                if (special === "power-key") keyEl.classList.add("power-key-cap");
                if (special === "omen-key") keyEl.classList.add("omen-key-cap");
                if (special === "calc-key") keyEl.classList.add("calc-key-cap");
                if (special === "arrow-key") keyEl.classList.add("arrow-key-cap");
                if (special === "space-key") keyEl.classList.add("space-key-cap");

                keyEl.dataset.code = code;
                keyEl.dataset.zone = zone;
                keyEl.style.flex = `${width} ${width} 0px`;

                const content = document.createElement("div");
                content.className = "key-content";

                if (subIcon) {
                    const subSpan = document.createElement("span");
                    subSpan.className = "key-sub-icon";
                    subSpan.textContent = subIcon;
                    content.appendChild(subSpan);
                }

                if (label) {
                    const labelSpan = document.createElement("span");
                    labelSpan.className = "key-label";
                    labelSpan.textContent = label;
                    content.appendChild(labelSpan);
                }

                if (special === "tactile" || label === "W") {
                    const bump = document.createElement("span");
                    bump.className = "tactile-bump";
                    content.appendChild(bump);
                }

                keyEl.appendChild(content);

                // Click on key selects its zone
                keyEl.addEventListener("click", (e) => {
                    e.stopPropagation();
                    this.handleKeyClick(zone);
                    this.triggerKeyRipple(keyEl);
                    if (zone >= 0 && zone < 4) {
                        fetch("/api/reactive/trigger", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ zone })
                        }).catch(() => {});
                    }
                });

                rowDiv.appendChild(keyEl);
                this.keyElements.set(code, keyEl);
                if (zone >= 0 && zone < 4) {
                    this.zoneKeyLists[zone].push(keyEl);
                }
            });

            matrix.appendChild(rowDiv);
        });

        chassis.appendChild(matrix);

        // HP OMEN Bottom Palmrest Deck (Bang & Olufsen, Touchpad & Badges)
        const palmrest = document.createElement("div");
        palmrest.className = "chassis-palmrest";
        palmrest.innerHTML = `
            <div class="palmrest-brand">BANG &amp; OLUFSEN</div>
            <div class="palmrest-touchpad"></div>
            <div class="palmrest-badges">
                <div class="badge-tag badge-ryzen">
                    <span class="badge-ryzen-text">AMD</span>
                    <span class="badge-ryzen-sub">RYZEN</span>
                    <span class="badge-ryzen-series">7000 SERIES 7</span>
                </div>
                <div class="badge-tag badge-rtx">
                    <span class="badge-nvidia-text">NVIDIA</span>
                    <span class="badge-rtx-text">GEFORCE RTX</span>
                </div>
                <div class="badge-tag badge-hz">
                    <span class="badge-hz-val">165Hz</span>
                    <span class="badge-hz-sub">REFRESH RATE</span>
                </div>
            </div>
        `;
        chassis.appendChild(palmrest);

        this.container.appendChild(chassis);

        // Setup live keyboard typing detection
        this.setupPhysicalTypingListeners();
        this.updateLighting(this.zoneColors);
    }

    handleKeyClick(zone) {
        if (this.onZoneSelect) {
            this.onZoneSelect(zone);
        }
    }

    setSelectedZones(zones) {
        this.selectedZones = new Set(zones);
        // Highlight active zones on keyboard
        for (let z = 0; z < 4; z++) {
            const isSelected = this.selectedZones.has(z);
            this.zoneKeyLists[z].forEach(key => {
                key.classList.toggle("zone-selected", isSelected);
            });
        }
    }

    updateLighting(colors) {
        if (!colors || colors.length < 4) return;
        this.zoneColors = colors;

        // Update each zone's keycaps with glowing underglow and translucent skirt border
        for (let z = 0; z < 4; z++) {
            const [r, g, b] = colors[z];
            const rgbStr = `${r}, ${g}, ${b}`;
            const glowColor = `rgba(${rgbStr}, 0.85)`;
            const underglowColor = `rgba(${rgbStr}, 0.28)`;

            this.zoneKeyLists[z].forEach(key => {
                key.style.setProperty("--zone-color", `rgb(${rgbStr})`);
                key.style.setProperty("--zone-glow", glowColor);
                key.style.setProperty("--zone-underglow", underglowColor);
            });
        }

        // Update ambient reflection beneath chassis
        const c0 = `rgb(${colors[0][0]}, ${colors[0][1]}, ${colors[0][2]})`;
        const c1 = `rgb(${colors[1][0]}, ${colors[1][1]}, ${colors[1][2]})`;
        const c2 = `rgb(${colors[2][0]}, ${colors[2][1]}, ${colors[2][2]})`;
        const c3 = `rgb(${colors[3][0]}, ${colors[3][1]}, ${colors[3][2]})`;

        this.underglowLayer.style.background = `linear-gradient(90deg, 
            ${c0} 0%, 
            ${c1} 33%, 
            ${c2} 66%, 
            ${c3} 100%)`;
    }

    setupPhysicalTypingListeners() {
        window.addEventListener("keydown", (e) => {
            const el = this.keyElements.get(e.code);
            if (el) {
                el.classList.add("key-pressed");
                this.triggerKeyRipple(el);
            }
        });

        window.addEventListener("keyup", (e) => {
            const el = this.keyElements.get(e.code);
            if (el) {
                el.classList.remove("key-pressed");
            }
        });
    }

    triggerKeyRipple(keyElement) {
        // Create expanding radiant ring on key press
        const ripple = document.createElement("div");
        ripple.className = "key-ripple";
        keyElement.appendChild(ripple);
        setTimeout(() => ripple.remove(), 600);
    }
}