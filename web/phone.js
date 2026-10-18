// Phone and tablet helpers for the browser build (also harmless on desktop).
//
// 1. Fit the canvas to the screen. pygbag sizes it once from the canvas's
//    pixel size at that moment, which is 1x1 until the game opens its
//    screen, so an installed app or a phone rotating mid-load could be left
//    squashed with bars. Instead a CSS rule fits it to the viewport at the
//    game's real aspect ratio, and updates by itself whenever the viewport
//    changes.
// 2. Go fullscreen and lock to landscape on the first tap. Browsers only
//    allow this straight after a touch. iPhone Safari has no fullscreen for
//    pages; there the game just plays in the page.
(function () {
  const root = document.documentElement;

  const style = document.createElement("style");
  style.textContent = `
    :root { --ar: 1.7778; }
    html, body { background: #1e1e1e !important; }
    #canvas {
      position: absolute !important; inset: 0 !important; margin: auto !important;
      width: min(100vw, calc(100vh * var(--ar))) !important;
      height: min(100vh, calc(100vw / var(--ar))) !important;
    }
    @supports (height: 100dvh) {
      #canvas {
        width: min(100dvw, calc(100dvh * var(--ar))) !important;
        height: min(100dvh, calc(100dvw / var(--ar))) !important;
      }
    }`;
  document.head.appendChild(style);

  function fit() {
    const c = document.getElementById("canvas");
    if (c && c.width > 1 && c.height > 1) root.style.setProperty("--ar", c.width / c.height);
  }
  function watch() {
    const c = document.getElementById("canvas");
    if (!c) return setTimeout(watch, 200);
    new MutationObserver(fit).observe(c, { attributes: true, attributeFilter: ["width", "height"] });
    fit();
  }
  watch();
  setInterval(fit, 1000);  // belt and braces

  const standalone = () =>
    matchMedia("(display-mode: fullscreen)").matches || matchMedia("(display-mode: standalone)").matches;

  async function go(e) {
    if (e.pointerType !== "touch" || document.fullscreenElement || standalone() || !root.requestFullscreen) return;
    try {
      await root.requestFullscreen({ navigationUI: "hide" });
    } catch (err) {
      return;
    }
    if (screen.orientation && screen.orientation.lock) {
      screen.orientation.lock("landscape").catch(() => {});
    }
  }
  window.addEventListener("pointerup", go, true);
})();
