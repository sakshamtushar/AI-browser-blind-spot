// hva.js: site-side interaction telemetry for the Phase 3 person-vs-agent runs.
// Records what the *website* can see about how a page was used, and POSTs one
// JSON summary to /telemetry when the visitor submits the form, follows a link,
// or leaves the page. Lab canary pages only; collects no personal data.
(function () {
  var t0 = performance.now();
  var s = {
    page: location.pathname,
    loadedAt: new Date().toISOString(),
    webdriver: !!navigator.webdriver,
    visibility: document.visibilityState,
    keys: 0, keysUntrusted: 0, keyGapsMs: [],
    inputs: {},            // inputType -> count (insertText, insertFromPaste, insertReplacementText, ...)
    pastes: 0,
    pointerMoves: 0, pointerMovesUntrusted: 0,
    clicks: [],            // {tag, trusted, x, y, movesBefore, msSinceLoad}
    focusOrder: [],
    scrolls: 0,
    fieldLengths: {},      // filled at send: name -> value length (never the value)
    firstInteractionMs: null,
    sentReason: null, msOnPage: null
  };
  var lastKey = null, sent = false;
  function first() { if (s.firstInteractionMs === null) s.firstInteractionMs = Math.round(performance.now() - t0); }

  document.addEventListener('keydown', function (e) {
    first(); s.keys++; if (!e.isTrusted) s.keysUntrusted++;
    var now = performance.now(); if (lastKey !== null && s.keyGapsMs.length < 400) s.keyGapsMs.push(Math.round(now - lastKey)); lastKey = now;
  }, true);
  document.addEventListener('input', function (e) {
    first(); var k = (e.inputType || 'none') + (e.isTrusted ? '' : ':untrusted'); s.inputs[k] = (s.inputs[k] || 0) + 1;
  }, true);
  document.addEventListener('paste', function () { first(); s.pastes++; }, true);
  document.addEventListener('pointermove', function (e) { s.pointerMoves++; if (!e.isTrusted) s.pointerMovesUntrusted++; }, { capture: true, passive: true });
  document.addEventListener('scroll', function () { s.scrolls++; }, { capture: true, passive: true });
  document.addEventListener('focusin', function (e) { first(); if (s.focusOrder.length < 50) s.focusOrder.push((e.target.name || e.target.tagName || '?') + (e.isTrusted ? '' : ':untrusted')); }, true);
  document.addEventListener('click', function (e) {
    first();
    if (s.clicks.length < 50) s.clicks.push({ tag: e.target.tagName, trusted: e.isTrusted, x: e.clientX, y: e.clientY, movesBefore: s.pointerMoves, msSinceLoad: Math.round(performance.now() - t0) });
  }, true);

  function send(reason) {
    if (sent) return; sent = true;
    s.sentReason = reason; s.msOnPage = Math.round(performance.now() - t0);
    // Field lengths only: a value longer than the keys typed, with no paste, was set by script.
    Array.prototype.forEach.call(document.querySelectorAll('input,textarea'), function (el) { if (el.name) s.fieldLengths[el.name] = el.value.length; });
    var canary = document.querySelector('input[name=name]');
    if (canary && /^C0C0N-CANARY-/.test(canary.value)) s.canary = canary.value;  // canary strings only
    var body = JSON.stringify(s);
    if (!(navigator.sendBeacon && navigator.sendBeacon('/telemetry', new Blob([body], { type: 'application/json' })))) {
      try { var x = new XMLHttpRequest(); x.open('POST', '/telemetry', false); x.setRequestHeader('Content-Type', 'application/json'); x.send(body); } catch (err) {}
    }
  }
  document.addEventListener('submit', function () { send('submit'); }, true);
  document.addEventListener('click', function (e) { var a = e.target.closest && e.target.closest('a[href]'); if (a) send('link'); }, true);
  window.addEventListener('pagehide', function () { send('pagehide'); });
})();
