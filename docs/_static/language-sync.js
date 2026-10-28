/* Language of the code tabs: MATLAB or Python.
 *
 * sphinx-design links the tabs that have the same sync key on one page and
 * remembers the choice for the next page, but in sessionStorage, which a new
 * browser tab or a later visit does not see. This script stores the choice in
 * localStorage and applies it to every tab set of the page when the page loads
 * and when the reader changes the language. Tab sets that have no sync key, such
 * as the install tabs ("Python (pip)", "MATLAB (Add-Ons)"), follow the language
 * too: the first tab whose label names the language is selected. A tab set
 * that already shows a tab of the language is left as it is, and a tab set that
 * has no tab of the language is not touched.
 */
(function () {
  "use strict";

  var KEY = "docs-language";

  function languageOf(label) {
    var text = label.getAttribute("data-sync-id") || label.textContent;
    if (/python/i.test(text)) return "python";
    if (/matlab/i.test(text)) return "matlab";
    return null;
  }

  function read() {
    try {
      return window.localStorage.getItem(KEY);
    } catch (error) {
      return null;
    }
  }

  function write(language) {
    try {
      window.localStorage.setItem(KEY, language);
    } catch (error) {
      /* storage is blocked: the language still applies to the open page */
    }
  }

  function labelsOf(tabSet) {
    return Array.prototype.filter.call(tabSet.children, function (element) {
      return element.classList.contains("sd-tab-label");
    });
  }

  function apply(language, keep) {
    document.querySelectorAll(".sd-tab-set").forEach(function (tabSet) {
      if (tabSet === keep) return;
      var labels = labelsOf(tabSet);
      var matches = labels.filter(function (label) {
        return languageOf(label) === language;
      });
      if (!matches.length) return;
      var shown = labels.filter(function (label) {
        return label.previousElementSibling && label.previousElementSibling.checked;
      })[0];
      if (shown && languageOf(shown) === language) return;
      matches[0].previousElementSibling.checked = true;
    });
  }

  document.addEventListener("click", function (event) {
    var label = event.target.closest && event.target.closest(".sd-tab-label");
    if (!label) return;
    var language = languageOf(label);
    if (!language) return;
    write(language);
    apply(language, label.closest(".sd-tab-set"));
  });

  /* The language was changed in another tab of the site. */
  window.addEventListener("storage", function (event) {
    if (event.key === KEY && event.newValue) apply(event.newValue);
  });

  /* After the listeners of sphinx-design, which restores its own choice from
   * sessionStorage, so that the stored language wins. */
  document.addEventListener("DOMContentLoaded", function () {
    window.setTimeout(function () {
      var language = read();
      if (language) apply(language);
    }, 0);
  });
})();
