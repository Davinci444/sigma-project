// workorders/static/workorders/admin_workorder.js
(function () {
  function toggleByType() {
    var select = document.getElementById("id_order_type");
    if (!select) return;
    var ot = select.value || "CORRECTIVE";

    var corrective = document.querySelectorAll(".sigma-corrective-only");
    var preventive = document.querySelectorAll(".sigma-preventive-only");

    corrective.forEach(function (el) {
      el.style.display = (ot === "CORRECTIVE") ? "" : "none";
    });
    preventive.forEach(function (el) {
      el.style.display = (ot === "PREVENTIVE") ? "" : "none";
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var sel = document.getElementById("id_order_type");
    if (sel) {
      sel.addEventListener("change", toggleByType);
      toggleByType();
    }
  });
})();
