// Mostrar/Ocultar "Correctivo" robusto (por value y por texto visible)
function isCorrectiveOption(sel){
  if(!sel) return false;
  const val = (sel.value || "").toUpperCase();
  if(val.includes("CORRECTIVE")) return true;
  const opt = sel.options[sel.selectedIndex];
  const text = (opt && opt.text ? opt.text : "").toLowerCase();
  return text.includes("correctiv");
}
function toggleCorrective(){
  const sel = document.getElementById("id_order_type");
  const block = document.getElementById("corrective-section");
  if(!sel || !block) return;
  block.style.display = isCorrectiveOption(sel) ? "block" : "none";
}
document.addEventListener("change", function(e){
  if(e.target && e.target.id === "id_order_type") toggleCorrective();
});
document.addEventListener("DOMContentLoaded", function(){
  toggleCorrective();
  const addBtn = document.getElementById("add-task-btn");
  const totalForms = document.getElementById("id_tasks-TOTAL_FORMS");
  const tableBody = document.querySelector("#tasks-table tbody");
  const tmpl = document.getElementById("task-empty-form");
  if(addBtn && totalForms && tableBody && tmpl){
    addBtn.addEventListener("click", function(){
      const idx = parseInt(totalForms.value, 10);
      const newRowHtml = tmpl.innerHTML.replace(/__prefix__/g, idx);
      tableBody.insertAdjacentHTML('beforeend', newRowHtml);
      totalForms.value = idx + 1;
    });
  }
});
