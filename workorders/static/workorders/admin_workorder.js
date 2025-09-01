(function($){
  // On change of category, fetch subcategories and update select
  function bindCategorySubcategory(container){
    container = container || document;
    // Main WorkOrder fields
    var $cat = $(container).find('#id_category');
    var $sub = $(container).find('#id_subcategory, #id_sub_category, #id_subcategoria');

    if($cat.length && $sub.length){
      var loadSubs = function(categoryId, $target){
        if(!categoryId){ $target.empty(); return; }
        $.get('/admin/workorders/workorder/subcategories/', {category: categoryId}, function(items){
          var current = $target.val();
          $target.empty();
          $target.append($('<option>', {value: '', text: '---------'}));
          items.forEach(function(it){
            $target.append($('<option>', {value: it.id, text: it.text}));
          });
          if(current){ $target.val(current).trigger('change'); }
        });
      };
      $cat.on('change', function(){
        loadSubs($(this).val(), $sub);
      });

      // initial load if category is prefilled but subcategory not present
      if($cat.val() && !$sub.val()){
        loadSubs($cat.val(), $sub);
      }
    }

    // Inline formsets (WorkOrderTask etc.)
    $(container).find('.dynamic-workordertask, .dynamic_workordertask, tr.form-row').each(function(){
      var $row = $(this);
      var $icat = $row.find('select[id$="-category"], select[id$="-categoria"]');
      var $isub = $row.find('select[id$="-subcategory"], select[id$="-sub_category"], select[id$="-subcategoria"]');
      if($icat.length && $isub.length){
        var reloadInline = function(){
          $.get('/admin/workorders/workorder/subcategories/', {category: $icat.val()}, function(items){
            var selected = $isub.val();
            $isub.empty();
            $isub.append($('<option>', {value: '', text: '---------'}));
            items.forEach(function(it){ $isub.append($('<option>', {value: it.id, text: it.text})); });
            if(selected){ $isub.val(selected); }
          });
        };
        $icat.off('change.adminwo').on('change.adminwo', reloadInline);
        if($icat.val() && !$isub.val()){ reloadInline(); }
      }
    });
  }

  function init(){
    bindCategorySubcategory(document);
    // Observe for added inline rows
    var target = document.querySelector('#content');
    if(!target) return;
    var obs = new MutationObserver(function(muts){
      muts.forEach(function(m){
        m.addedNodes && m.addedNodes.forEach(function(n){
          if(n.nodeType === 1){
            bindCategorySubcategory(n);
          }
        });
      });
    });
    obs.observe(target, { childList: true, subtree: true });
  }

  $(document).ready(init);
})(django.jQuery);
