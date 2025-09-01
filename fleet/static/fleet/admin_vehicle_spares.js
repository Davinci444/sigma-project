// Encadenado Categoría -> Ítem en el inline de repuestos del vehículo
(function($){
  function wireInline($context){
    $context = $context || $(document);
    $context.find('tr.form-row, .dynamic-vehiclespare').each(function(){
      var $row = $(this);
      var $cat = $row.find('select[id$="category"], select[name$="category"]');
      var $item = $row.find('select[id$="spare_item"], select[name$="spare_item"]');
      if(!$cat.length || !$item.length) return;

      function reload(){
        var val = $cat.val();
        if(!val){ return; }
        $.get(window.location.pathname + "spare-items/", {category: val}, function(items){
          var cur = $item.val();
          $item.empty();
          $item.append($('<option>', {value: "", text: "---------"}));
          items.forEach(function(it){
            $item.append($('<option>', {value: it.id, text: it.text})); 
          });
          if(cur){ $item.val(cur); }
        });
      }
      $cat.off("change.vs").on("change.vs", reload);
      if($cat.val() && !$item.val()){ reload(); }
    });
  }

  $(document).ready(function(){
    wireInline($(document));
    var target = document.querySelector('#content');
    if(!target) return;
    var obs = new MutationObserver(function(muts){
      muts.forEach(function(m){
        (m.addedNodes||[]).forEach(function(n){
          if(n.nodeType === 1){
            wireInline($(n));
          }
        });
      });
    });
    obs.observe(target, {childList:true, subtree:true});
  });
})(django.jQuery);
