# Animation Presets — Approved & Reusable

Animations that were approved by the user and can be reused or adapted for similar layouts.

---

## Preset: Slide-In Fade Blur (Left/Right)

**Approved on:** 2026-05-20
**Project:** atovio-colour-picker
**Layout type:** 2x2 grid with products overlapping colored rectangles
**Best for:** Product showcases, comparison layouts, multi-item displays

### Products — slide from sides with fade + blur + bezier ease
```js
const slideDur = 0.9;

// Left-side products — slide from left
tl.from('#product-left-1', {
  x: -120, y: 20, opacity: 0, filter: 'blur(12px)',
  duration: slideDur, ease: 'power3.out'
}, 0.1);

tl.from('#product-left-2', {
  x: -120, y: 20, opacity: 0, filter: 'blur(12px)',
  duration: slideDur, ease: 'power3.out'
}, 0.3);

// Right-side products — slide from right
tl.from('#product-right-1', {
  x: 120, y: -20, opacity: 0, filter: 'blur(12px)',
  duration: slideDur, ease: 'power3.out'
}, 0.2);

tl.from('#product-right-2', {
  x: 120, y: 20, opacity: 0, filter: 'blur(12px)',
  duration: slideDur, ease: 'power3.out'
}, 0.4);
```

### Labels — slide from sides with fade + blur, staggered after products
```js
// Left-side labels
tl.from('#label-left-1', {
  x: -80, opacity: 0, filter: 'blur(8px)',
  duration: 0.7, ease: 'power3.out'
}, 0.4);

tl.from('#label-left-2', {
  x: -80, opacity: 0, filter: 'blur(8px)',
  duration: 0.7, ease: 'power3.out'
}, 0.6);

// Right-side labels
tl.from('#label-right-1', {
  x: 80, opacity: 0, filter: 'blur(8px)',
  duration: 0.7, ease: 'power3.out'
}, 0.5);

tl.from('#label-right-2', {
  x: 80, opacity: 0, filter: 'blur(8px)',
  duration: 0.7, ease: 'power3.out'
}, 0.7);
```

**Settings:** 5s total, ~1.5s animation + 3.5s hold

---

## Preset: Counter Animation (Number Count-Up)

**Approved on:** 2026-05-20
**Project:** atovio-wearable-purifier
**Layout type:** Stats/numbers display
**Best for:** Feature highlights, data/stat callouts, product specs

### Counting from 0 to target number
```js
const counter1 = { val: 0 };
tl.to(counter1, {
  val: 15,
  duration: 1.5,
  ease: 'power1.out',
  onUpdate: () => {
    document.querySelector('#counter-1').textContent = Math.round(counter1.val) + ' MINS';
  }
}, 0);

const counter2 = { val: 0 };
tl.to(counter2, {
  val: 1.5,
  duration: 1.5,
  ease: 'power1.out',
  onUpdate: () => {
    document.querySelector('#counter-2').textContent = counter2.val.toFixed(1) + ' HOURS';
  }
}, 0);
```

**Font:** Bebas Neue, 145px, letter-spacing -0.01em, base64 embedded
**Settings:** 5s total, 1.5s count animation + hold

---

## Preset: Static Scene with Delayed Highlight Pop (Pointer-only)

**Approved on:** 2026-05-20
**Project:** atovio-overprepared-parent
**Layout type:** Multi-product layout with callout pointer labels and CTA button
**Best for:** Clean, company-standard static presentation with delayed accent pops to draw eyes to key product details and the call-to-action button without cluttering the main content.

### Pointer Labels — delayed scale-up from center/sides with overshoot ease
```js
// Delayed start at 1.0s to allow static presentation first
tl.fromTo("#label-age", 
  { opacity: 0, scale: 0, transformOrigin: "left center" }, 
  { opacity: 1, scale: 1, duration: 0.6, ease: "back.out(1.5)" }, 
  1.0
);
tl.fromTo("#label-ozone", 
  { opacity: 0, scale: 0, transformOrigin: "left center" }, 
  { opacity: 1, scale: 1, duration: 0.6, ease: "back.out(1.5)" }, 
  1.2
);
tl.fromTo("#label-wearable", 
  { opacity: 0, scale: 0, transformOrigin: "right center" }, 
  { opacity: 1, scale: 1, duration: 0.6, ease: "back.out(1.5)" }, 
  1.4
);
```

### CTA Button — delayed scale pop slide at the end
```js
tl.fromTo("#cta-button", 
  { opacity: 0, scale: 0.8, y: 15, transformOrigin: "center center" }, 
  { opacity: 1, scale: 1, y: 0, duration: 0.8, ease: "back.out(1.8)" }, 
  1.6
);
```

**Settings:** 5s total, 1.0s static hold -> 1.4s staggered highlights entry -> 2.6s final hold. Keep logo, text, products, and grid completely static.

---

## Preset: Counter-Rotating Orbit (Tagline + Products)

**Approved on:** 2026-05-20
**Project:** atovio-lowest-price-ever
**Layout type:** Radial composition — products arranged around a center, with curved tagline text ringing the central content
**Best for:** Circular/radial ad layouts where products are arranged on a ring around centered messaging. Adds continuous "wheel" motion while keeping headline/price/badge anchored.

### Curved tagline text — clockwise spin
```js
tl.to("#circular-text", {
  rotation: 720,          // 2 rotations across composition for visible motion at slow speed
  duration: 40,
  ease: "none",
  transformOrigin: "center center"
}, 0);
```

### Product orbit container — anti-clockwise spin, half the speed
```js
// Wrap all products in a 1080x1080 absolute-positioned div (#purifier-orbit)
// so a single transform rotates them as a group around the canvas center.
tl.to("#purifier-orbit", {
  rotation: -360,         // 1 rotation, opposite direction
  duration: 40,
  ease: "none",
  transformOrigin: "center center"
}, 0);
```

**Settings:** 40s total (= LCM of both rotation periods). Composition duration must equal the LCM of the two rotation periods so both elements return to start orientation at the loop boundary — otherwise the GIF jumps on repeat. Counter-rotation reinforces depth and adds visual richness without distracting from the central message. All other elements (headline, price pill, badge, logo) stay static.

**Structural note:** Anniversary badge `z-index` must be higher than the price pill if they visually overlap — otherwise the badge is hidden behind the pill.

---

## How to Use Presets

1. During Phase 4, check if any preset matches the current design layout
2. **Suggest the matching preset to the user** as one of the animation options
3. User can accept as-is, modify, or request something completely custom
4. After user approves a NEW animation style, **add it here as a new preset**

## Adding New Presets

After any animation is approved by the user:
1. Add a new section with: name, date, project, layout type, best-for description
2. Include the exact GSAP code that was approved
3. Note the settings (duration, easing, timing)
4. This grows into a library the user can pick from in future projects
