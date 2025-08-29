// Toggle de secciones Preventivo/Correctivo basado en 'order_type'.
// No requiere migraciones.

(function() {
  function applyVisibility() {
    var select = document.getElementById("id_order_type");
    if (!select) return;

    var val = select.value || "CORRECTIVE";
    var preventivos = document.querySelectorAll(".sigma-preventive-only");
    var correctivos = document.querySelectorAll(".sigma-corrective-only");

    if (val === "PREVENTIVE") {
      preventivos.forEach(function(el){ el.style.display = ""; });
      correctivos.forEach(function(el){ el.style.display = "none"; });
    } else {
      preventivos.forEach(function(el){ el.style.display = "none"; });
      correctivos.forEach(function(el){ el.style.display = ""; });
    }
  }

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function() {
    var sel = document.getElementById("id_order_type");
    if (sel) {
      sel.addEventListener("change", applyVisibility);
      applyVisibility();
    }
  });
})();
