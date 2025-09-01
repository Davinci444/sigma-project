(function($) {
  function toggleCorrective() {
    var sel = $('#id_order_type');
    var section = $('#corrective-section');
    if (!sel.length || !section.length) return;
    section.toggle(sel.val() === 'CORRECTIVE');
  }

  function initSelect($el) {
    var url = $el.data('url');
    $el.select2({
      ajax: {
        url: url,
        dataType: 'json',
        delay: 250,
        data: function(params) { return { search: params.term }; },
        processResults: function(data) {
          var results = data.results || data;
          return {
            results: results.map(function(obj) {
              var text = obj.plate || obj.full_name || obj.name;
              return { id: obj.id, text: text };
            })
          };
        }
      },
      width: 'style'
    });
    var icon = $el.next('.search-icon');
    if (icon.length) {
      icon.on('click', function() { $el.select2('open'); });
    }
  }

  function initAll(ctx) {
    $(ctx).find('select.select2-ajax').each(function() {
      initSelect($(this));
    });
  }

  $(function() {
    toggleCorrective();
    $('#id_order_type').on('change', toggleCorrective);

    initAll(document);

    $('#add-task-btn').on('click', function() {
      var totalForms = $('#id_tasks-TOTAL_FORMS');
      var tableBody = $('#tasks-table tbody');
      var tmpl = $('#task-empty-form').html();
      var idx = parseInt(totalForms.val(), 10);
      tableBody.append(tmpl.replace(/__prefix__/g, idx));
      totalForms.val(idx + 1);
      var newRow = tableBody.find('tr').last();
      initAll(newRow);
    });
  });
})(django.jQuery);
