/**
 * OmenGlow — Interactive Circular HSV Color Wheel & Chroma Harmonizer
 */

class ColorWheel {
    constructor(canvasId, onChangeCallback) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext("2d");
        this.onChange = onChangeCallback;

        this.hue = 0.0;        // 0 - 360
        this.saturation = 1.0; // 0 - 1
        this.value = 1.0;      // 0 - 1

        this.radius = this.canvas.width / 2;
        this.isDragging = false;

        this.init();
    }

    init() {
        this.drawWheel();
        this.setupEvents();
    }

    drawWheel() {
        const { ctx, radius } = this;
        const width = this.canvas.width;
        const height = this.canvas.height;
        const cx = width / 2;
        const cy = height / 2;

        ctx.clearRect(0, 0, width, height);

        // Render circular HSV wheel
        const image = ctx.createImageData(width, height);
        const data = image.data;

        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const dx = x - cx;
                const dy = y - cy;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist <= radius) {
                    let angle = Math.atan2(dy, dx) * (180 / Math.PI);
                    if (angle < 0) angle += 360;

                    const sat = dist / radius;
                    const [r, g, b] = this.hsvToRgb(angle, sat, this.value);

                    const idx = (y * width + x) * 4;
                    data[idx] = r;
                    data[idx + 1] = g;
                    data[idx + 2] = b;
                    data[idx + 3] = 255;
                }
            }
        }

        ctx.putImageData(image, 0, 0);

        // Draw selector handle
        const selAngle = this.hue * (Math.PI / 180);
        const selDist = this.saturation * radius;
        const hx = cx + Math.cos(selAngle) * selDist;
        const hy = cy + Math.sin(selAngle) * selDist;

        ctx.beginPath();
        ctx.arc(hx, hy, 7, 0, Math.PI * 2);
        ctx.strokeStyle = "#FFFFFF";
        ctx.lineWidth = 3;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(hx, hy, 5, 0, Math.PI * 2);
        ctx.fillStyle = this.getHex();
        ctx.fill();
    }

    setupEvents() {
        const handleMove = (e) => {
            if (!this.isDragging) return;
            const rect = this.canvas.getBoundingClientRect();
            const cx = rect.width / 2;
            const cy = rect.height / 2;
            const x = e.clientX - rect.left - cx;
            const y = e.clientY - rect.top - cy;

            let angle = Math.atan2(y, x) * (180 / Math.PI);
            if (angle < 0) angle += 360;

            const dist = Math.sqrt(x * x + y * y);
            const radius = rect.width / 2;
            const sat = Math.min(1.0, dist / radius);

            this.hue = angle;
            this.saturation = sat;
            this.drawWheel();

            if (this.onChange) {
                const [r, g, b] = this.getRgb();
                this.onChange(r, g, b);
            }
        };

        this.canvas.addEventListener("mousedown", (e) => {
            this.isDragging = true;
            handleMove(e);
        });

        window.addEventListener("mousemove", handleMove);
        window.addEventListener("mouseup", () => {
            this.isDragging = false;
        });
    }

    setValue(val) {
        this.value = Math.max(0.0, Math.min(1.0, val));
        this.drawWheel();
        if (this.onChange) {
            const [r, g, b] = this.getRgb();
            this.onChange(r, g, b);
        }
    }

    setColorRgb(r, g, b) {
        const [h, s, v] = this.rgbToHsv(r, g, b);
        this.hue = h;
        this.saturation = s;
        this.value = v;
        this.drawWheel();
    }

    getRgb() {
        return this.hsvToRgb(this.hue, this.saturation, this.value);
    }

    getHex() {
        const [r, g, b] = this.getRgb();
        return "#" + [r, g, b].map(x => x.toString(16).padStart(2, "0")).join("");
    }

    hsvToRgb(h, s, v) {
        const c = v * s;
        const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
        const m = v - c;
        let r = 0, g = 0, b = 0;

        if (h < 60) { r = c; g = x; b = 0; }
        else if (h < 120) { r = x; g = c; b = 0; }
        else if (h < 180) { r = 0; g = c; b = x; }
        else if (h < 240) { r = 0; g = x; b = c; }
        else if (h < 300) { r = x; g = 0; b = c; }
        else { r = c; g = 0; b = x; }

        return [
            Math.round((r + m) * 255),
            Math.round((g + m) * 255),
            Math.round((b + m) * 255)
        ];
    }

    rgbToHsv(r, g, b) {
        r /= 255; g /= 255; b /= 255;
        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        const d = max - min;
        let h = 0;
        const s = max === 0 ? 0 : d / max;
        const v = max;

        if (max !== min) {
            switch (max) {
                case r: h = (g - b) / d + (g < b ? 6 : 0); break;
                case g: h = (b - r) / d + 2; break;
                case b: h = (r - g) / d + 4; break;
            }
            h *= 60;
        }

        return [h, s, v];
    }
}
