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
