(function () {
  "use strict";

  var article = document.querySelector("article.post");
  var content = document.querySelector("article.post .content");
  var menu = document.getElementById("menu");
  var nav = document.querySelector("#header-post-bar #nav");
  var menuIcons = Array.prototype.slice.call(
    document.querySelectorAll("#menu-icon, #menu-icon-tablet")
  );
  var tabletMenuIcon = document.getElementById("menu-icon-tablet");
  var tabletTopIcon = document.getElementById("top-icon-tablet");

  function escapeHtml(value) {
    return value.replace(/[&<>"']/g, function (character) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[character];
    });
  }

  function buildTableOfContents() {
    var destinations = [document.getElementById("toc"), document.getElementById("toc-footer")].filter(Boolean);
    var headings = content ? Array.prototype.slice.call(content.querySelectorAll("h2, h3")) : [];
    if (!headings.length) {
      destinations.forEach(function (destination) { destination.remove(); });
      var toggle = document.getElementById("toc-footer-toggle");
      if (toggle) { toggle.remove(); }
      return;
    }

    var usedIds = Object.create(null);
    var items = headings.map(function (heading, index) {
      var base = heading.id || ("section-" + (index + 1));
      var id = base;
      var suffix = 2;
      while (usedIds[id]) {
        id = base + "-" + suffix;
        suffix += 1;
      }
      usedIds[id] = true;
      heading.id = id;
      return {
        id: id,
        text: heading.textContent.trim(),
        level: Number(heading.tagName.substring(1), 10)
      };
    });

    var html = '<ol class="toc">' + items.map(function (item) {
      return '<li class="toc-item toc-level-' + item.level + '">' +
        '<a class="toc-link" href="#' + escapeHtml(item.id) + '">' +
        '<span class="toc-text">' + escapeHtml(item.text) + "</span></a></li>";
    }).join("") + "</ol>";

    destinations.forEach(function (destination) { destination.innerHTML = html; });
  }

  function isDisplayed(element) {
    return !!(element && element.offsetParent !== null);
  }

  function setMenuOpen(open) {
    if (!menu) { return; }
    menu.style.visibility = open ? "visible" : "hidden";
    if (nav) { nav.style.display = open ? "" : "none"; }
    menuIcons.forEach(function (icon) {
      icon.setAttribute("aria-expanded", open ? "true" : "false");
      icon.classList.toggle("active", open);
    });
  }

  function bindToggle(triggerId, targetId) {
    var trigger = document.getElementById(triggerId);
    var target = document.getElementById(targetId);
    if (!trigger || !target) { return; }
    trigger.addEventListener("click", function (event) {
      event.preventDefault();
      target.style.display = target.style.display === "none" ? "block" : "none";
    });
  }

  function initialize() {
    buildTableOfContents();

    if (menu) {
      setMenuOpen(window.innerWidth >= 1440);
    }

    menuIcons.forEach(function (icon) {
      icon.addEventListener("click", function (event) {
        event.preventDefault();
        setMenuOpen(menu.style.visibility !== "visible");
      });
    });

    bindToggle("menu-footer", "nav-footer");
    bindToggle("toc-footer-toggle", "toc-footer");
    bindToggle("share-footer-toggle", "share-footer");

    var fallbackCopyLink = function () {
      var input = document.createElement("textarea");
      input.value = window.location.href;
      input.setAttribute("readonly", "");
      input.style.position = "fixed";
      input.style.opacity = "0";
      document.body.appendChild(input);
      input.select();
      try { document.execCommand("copy"); } catch (error) {}
      document.body.removeChild(input);
    };
    Array.prototype.forEach.call(
      document.querySelectorAll("#share a.share-copy, #share-footer a.share-copy"),
      function (link) {
        link.addEventListener("click", function (event) {
          event.preventDefault();
          var message = link.getAttribute("data-share-message") || "链接已复制到剪贴板。";
          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(window.location.href).then(
              function () { window.alert(message); },
              function () { fallbackCopyLink(); window.alert(message); }
            );
          } else {
            fallbackCopyLink();
            window.alert(message);
          }
        });
      }
    );

    var shareToggle = document.querySelector("#actions .share-toggle");
    var sharePanel = document.getElementById("share");
    if (shareToggle && sharePanel) {
      shareToggle.addEventListener("click", function (event) {
        event.preventDefault();
        sharePanel.style.display = sharePanel.style.display === "none" ? "block" : "none";
      });
    }

    [["#actions .nav-prev", "i-prev"],
     ["#actions .nav-next", "i-next"],
     ["#actions a.back-to-top", "i-top"],
     ["#actions .share-toggle", "i-share"]].forEach(function (pair) {
      var trigger = document.querySelector(pair[0]);
      var info = document.getElementById(pair[1]);
      if (!trigger || !info) { return; }
      trigger.addEventListener("mouseenter", function () { info.style.display = ""; });
      trigger.addEventListener("mouseleave", function () { info.style.display = "none"; });
    });

    Array.prototype.forEach.call(document.querySelectorAll(".back-to-top, #top-icon-tablet"), function (link) {
      link.addEventListener("click", function (event) {
        event.preventDefault();
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    });

    Array.prototype.forEach.call(document.querySelectorAll("#toc a, #toc-footer a"), function (link) {
      link.addEventListener("click", function () {
        var footerToc = document.getElementById("toc-footer");
        if (footerToc) { footerToc.style.display = "none"; }
      });
    });

    var lastScrollTop = 0;
    var footerPost = document.getElementById("footer-post");

    window.addEventListener("scroll", function () {
      var distance = window.scrollY;

      if (footerPost) {
        footerPost.style.display = distance > lastScrollTop && distance > 80 ? "none" : "";
      }

      ["nav-footer", "toc-footer", "share-footer"].forEach(function (id) {
        var panel = document.getElementById(id);
        if (panel) { panel.style.display = "none"; }
      });

      if (tabletTopIcon) { tabletTopIcon.style.display = distance > 100 ? "" : "none"; }
      if (tabletMenuIcon && !isDisplayed(document.getElementById("menu-icon"))) {
        tabletMenuIcon.style.display = distance > 100 ? "none" : "";
      }

      lastScrollTop = distance <= 0 ? 0 : distance;
    }, { passive: true });
  }

  if (article) {
    if (document.readyState !== "loading") { initialize(); }
    else { document.addEventListener("DOMContentLoaded", initialize); }
  }
})();
