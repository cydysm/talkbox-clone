(function () {
  "use strict";

  var navList = document.querySelector("#header #nav ul");
  var navToggle = navList ? navList.querySelector("li.icon a") : null;

  if (navList && navToggle) {
    navToggle.addEventListener("click", function (event) {
      event.preventDefault();
      navList.classList.toggle("responsive");
    });
  }
})();

/* ---------------------------------------------------------------
   消息提示：10 秒倒计时后自动消失；悬停暂停倒计时。
   --------------------------------------------------------------- */
(function () {
  "use strict";

  var DURATION_SECONDS = 10;

  function countdown(message) {
    if (message.querySelector(".message-countdown")) { return; }
    var remaining = DURATION_SECONDS;
    var badge = document.createElement("span");
    badge.className = "message-countdown";
    badge.textContent = remaining;
    message.appendChild(badge);

    var paused = false;
    message.addEventListener("mouseenter", function () { paused = true; });
    message.addEventListener("mouseleave", function () { paused = false; });

    var timer = window.setInterval(function () {
      if (paused) { return; }
      remaining -= 1;
      if (remaining <= 0) {
        window.clearInterval(timer);
        var container = message.closest(".messages");
        message.remove();
        if (container && !container.querySelector(".message")) {
          container.remove();
        }
        return;
      }
      badge.textContent = remaining;
    }, 1000);
  }

  function init() {
    Array.prototype.forEach.call(document.querySelectorAll(".message"), countdown);
  }

  if (document.readyState !== "loading") { init(); }
  else { document.addEventListener("DOMContentLoaded", init); }
})();

