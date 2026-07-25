(function () {
  if (!window.speechSynthesis) return;

  // —— Scroll indicator ——
  (function () {
    var markers = document.querySelectorAll(".da, .line");
    if (markers.length < 3) return;

    var wrap = document.createElement("div");
    wrap.className = "scr";
    markers.forEach(function () {
      var d = document.createElement("i");
      d.className = "scr-d";
      wrap.appendChild(d);
    });
    document.body.appendChild(wrap);

    var dots = wrap.querySelectorAll(".scr-d");

    function tick() {
      var cx = window.innerHeight / 2;
      for (var i = 0; i < markers.length; i++) {
        var r = markers[i].getBoundingClientRect();
        var active = r.top < cx && r.bottom > cx;
        dots[i].classList.toggle("on", active);
      }
    }
    window.addEventListener("scroll", tick, { passive: true });
    tick();
  })();

  var SPEAKER =
    '<svg viewBox="0 0 20 20" width="16" height="16" fill="currentColor"><path d="M9.5 2.5v15a.5.5 0 01-.5.5H6l-4-4H1a1 1 0 01-1-1V7a1 1 0 011-1h3l4-4a.5.5 0 01.5.5z"/><path d="M13 6.5a4 4 0 010 7" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/><path d="M15.5 4a7 7 0 010 12" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>';

  function speak(text, rate) {
    if (!text) return;
    window.speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance(text);
    u.lang = "da-DK";
    u.rate = rate || 0.9;
    var voices = speechSynthesis.getVoices();
    var dv = voices.find(function (v) {
      return v.lang.startsWith("da");
    });
    if (dv) u.voice = dv;
    speechSynthesis.speak(u);
  }

  function icon() {
    var s = document.createElement("span");
    s.className = "spk";
    s.innerHTML = SPEAKER;
    return s;
  }

  function slowLink(text) {
    var a = document.createElement("a");
    a.className = "spk-slow";
    a.textContent = "slow";
    a.href = "#";
    a.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      speak(text, 0.7);
    });
    return a;
  }

  function addButtons() {
    var els = document.querySelectorAll(".da, .line");
    for (var i = 0; i < els.length; i++) {
      var el = els[i];
      if (el.querySelector(".spk") || el.closest(".audio-block")) continue;
      var text = el.textContent.trim();
      if (!text) continue;

      var wrap = document.createElement("span");
      wrap.className = "spk-wrap";

      var i1 = icon();
      i1.addEventListener("click", function (t) {
        return function (e) {
          e.stopPropagation();
          speak(t, 1.0);
        };
      }(text));
      wrap.appendChild(i1);

      wrap.appendChild(slowLink(text));

      el.appendChild(wrap);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", addButtons);
  } else {
    addButtons();
  }
})();
