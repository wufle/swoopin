// Phones and tablets: go fullscreen and lock to landscape on the first tap.
// Browsers only allow this straight after a touch, so it hooks the first
// one (usually the tap that starts the game) and again after the player
// leaves fullscreen. iPhone Safari has no fullscreen for pages; there the
// game just plays in the page (or add it to the home screen).
(function () {
  const el = document.documentElement;
  const standalone = () =>
    matchMedia("(display-mode: fullscreen)").matches || matchMedia("(display-mode: standalone)").matches;

  async function go(e) {
    if (e.pointerType !== "touch" || document.fullscreenElement || standalone() || !el.requestFullscreen) return;
    try {
      await el.requestFullscreen({ navigationUI: "hide" });
    } catch (err) {
      return;
    }
    if (screen.orientation && screen.orientation.lock) {
      screen.orientation.lock("landscape").catch(() => {});
    }
  }

  window.addEventListener("pointerup", go, true);
  // let the page re-fit the canvas once the size has settled
  document.addEventListener("fullscreenchange", () => {
    setTimeout(() => window.dispatchEvent(new Event("resize")), 150);
  });
})();
