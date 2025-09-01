// Filtra Subcategoría cuando cambia la Categoría en líneas de OT (admin inline)
(function() {
  function initRow(row) {
    const cat = row.querySelector('select[id$="-category"]');
    const sub = row.querySelector('select[id$="-subcategory"]');
    if (!cat || !sub) return;

    cat.addEventListener("change", function() {
      const catId = this.value;
      if (!catId) return;

      fetch(`/api/workorders/subcategories-by-category/?category=${catId}`, {
        credentials: "same-origin"
      })
      .then(r => r.json())
      .then(data => {
        const current = sub.value;
        while (sub.firstChild) sub.removeChild(sub.firstChild);
        const empty = document.createElement("option");
        empty.value = "";
        empty.textContent = "---------";
        sub.appendChild(empty);
        (data.items || []).forEach(item => {
          const opt = document.createElement("option");
          opt.value = item.id;
          opt.textContent = item.name;
          sub.appendChild(opt);
        });
        if ([...sub.options].some(o => o.value === current)) {
          sub.value = current;
        }
      })
      .catch(() => {});
    });
  }

  function initAll() {
    document.querySelectorAll("tr.dynamic-workordertask_set").forEach(initRow);
    // soportar "Add another" del admin
    document.body.addEventListener("click", function(e) {
      if (e.target && e.target.classList.contains("add-row")) {
        setTimeout(() => {
          document.querySelectorAll("tr.dynamic-workordertask_set").forEach(initRow);
        }, 60);
      }
    });
  }

  if (document.readyState !== "loading") initAll();
  else document.addEventListener("DOMContentLoaded", initAll);
})();
