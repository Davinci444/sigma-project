(function() {
  function ready(fn) {
    if (document.readyState !== 'loading'){
      fn();
    } else {
      document.addEventListener('DOMContentLoaded', fn);
    }
  }

  function toggleFieldsets() {
    var orderTypeEl = document.getElementById('id_order_type');
    if (!orderTypeEl) return;

    var isCorrective = orderTypeEl.value === 'CORRECTIVE';

    // Fieldsets marcados con estas clases en admin.py
    var correctiveBlocks = document.querySelectorAll('.sigma-corrective-only');
    var preventiveBlocks = document.querySelectorAll('.sigma-preventive-only');

    correctiveBlocks.forEach(function(fs){
      fs.style.display = isCorrective ? '' : 'none';
    });
    preventiveBlocks.forEach(function(fs){
      fs.style.display = isCorrective ? 'none' : '';
    });

    // Deshabilitar inputs de la sección no visible para evitar que el usuario
    // cree datos “fantasma” en POST:
    function setDisabled(containerList, disabled) {
      containerList.forEach(function(fs){
        // Campos dentro del fieldset
        fs.querySelectorAll('input, select, textarea').forEach(function(el){
          el.disabled = disabled;
          if (disabled) {
            // Opcional: limpiar valores visibles
            if (el.tagName === 'SELECT') {
              if (el.multiple) {
                Array.from(el.options).forEach(function(opt){ opt.selected = false; });
              } else {
                el.selectedIndex = -1;
              }
            } else if (el.type === 'checkbox' || el.type === 'radio') {
              el.checked = false;
            } else {
              el.value = '';
            }
          }
        });
      });
    }

    if (isCorrective) {
      setDisabled(preventiveBlocks, true);
      setDisabled(correctiveBlocks, false);
    } else {
      setDisabled(correctiveBlocks, true);
      setDisabled(preventiveBlocks, false);
    }
  }

  ready(function(){
    // Ejecutar al cargar
    toggleFieldsets();

    // Reaccionar a cambios en el select de tipo
    var orderTypeEl = document.getElementById('id_order_type');
    if (orderTypeEl) {
      orderTypeEl.addEventListener('change', toggleFieldsets);
    }
  });
})();
