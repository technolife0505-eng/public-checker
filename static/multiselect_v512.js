
(function(){
  function norm(s){
    return (s || '').toString().toLowerCase()
      .replace(/ё/g,'е').replace(/ў/g,'у').replace(/қ/g,'к')
      .replace(/ғ/g,'г').replace(/ҳ/g,'х')
      .replace(/\s+/g,' ').trim();
  }

  function closeAll(except){
    document.querySelectorAll('.ms-menu').forEach(function(menu){
      if(menu !== except){
        menu.classList.remove('open');
        menu.style.display = 'none';
      }
    });
  }

  function applySearch(input){
    var menu = input.closest('.ms-menu');
    if(!menu) return;
    var q = norm(input.value);

    menu.querySelectorAll('.ms-option').forEach(function(row){
      var isAll = row.querySelector('[data-group-all]');
      var txt = norm(row.innerText || row.textContent || '');

      if(q === ''){
        row.style.display = 'flex';
      }else if(isAll){
        row.style.display = 'none';
      }else{
        row.style.display = txt.indexOf(q) !== -1 ? 'flex' : 'none';
      }
    });
  }

  window.mmToggleMS = function(btn){
    var wrap = btn.closest('.ms-wrap');
    if(!wrap) return false;

    var menu = wrap.querySelector('.ms-menu');
    if(!menu) return false;

    var opened = menu.classList.contains('open');
    closeAll(menu);

    if(opened){
      menu.classList.remove('open');
      menu.style.display = 'none';
    }else{
      menu.classList.add('open');
      menu.style.display = 'block';

      var input = menu.querySelector('.ms-search');
      if(input){
        input.value = '';
        applySearch(input);
        setTimeout(function(){ input.focus(); }, 50);
      }
    }
    return false;
  };

  function title(g){
    if(g === 'platforms') return 'Platformalar';
    if(g === 'sources') return 'Kanallar';
    if(g === 'keywords') return 'Kalit so‘zlar';
    return g;
  }

  function updateLabel(g){
    var allBox = document.querySelector('[data-group-all="'+g+'"]');
    var checked = Array.from(document.querySelectorAll('[data-group-item="'+g+'"]:checked'));
    var label = document.getElementById(g + 'Label');
    if(!label) return;

    if(allBox && allBox.checked){
      label.textContent = title(g) + ': Barchasi';
    }else if(checked.length === 0){
      if(allBox) allBox.checked = true;
      label.textContent = title(g) + ': Barchasi';
    }else{
      label.textContent = title(g) + ': ' + checked.length + ' ta tanlandi';
    }
  }

  function updateAllLabels(){
    ['platforms','sources','keywords'].forEach(updateLabel);
  }

  document.addEventListener('input', function(e){
    if(e.target && e.target.classList && e.target.classList.contains('ms-search')){
      applySearch(e.target);
    }
  }, true);

  document.addEventListener('keyup', function(e){
    if(e.target && e.target.classList && e.target.classList.contains('ms-search')){
      applySearch(e.target);
    }
  }, true);

  document.addEventListener('change', function(e){
    var all = e.target.closest('[data-group-all]');
    var item = e.target.closest('[data-group-item]');

    if(all){
      var g = all.getAttribute('data-group-all');
      if(all.checked){
        document.querySelectorAll('[data-group-item="'+g+'"]').forEach(function(x){
          x.checked = false;
        });
      }
    }

    if(item){
      var g2 = item.getAttribute('data-group-item');
      var allBox = document.querySelector('[data-group-all="'+g2+'"]');
      if(item.checked && allBox) allBox.checked = false;

      var any = Array.from(document.querySelectorAll('[data-group-item="'+g2+'']")).some(function(x){
        return x.checked;
      });

      if(!any && allBox) allBox.checked = true;
    }

    updateAllLabels();
  }, true);

  document.addEventListener('click', function(e){
    if(e.target.closest('.ms-btn')) return;
    if(e.target.closest('.ms-menu')) return;
    closeAll(null);
  }, true);

  document.addEventListener('keydown', function(e){
    if(e.key === 'Escape') closeAll(null);
  }, true);

  document.addEventListener('DOMContentLoaded', function(){
    updateAllLabels();

    document.querySelectorAll('.ms-search').forEach(function(input){
      input.removeAttribute('oninput');
      input.addEventListener('input', function(){ applySearch(input); });
      input.addEventListener('keyup', function(){ applySearch(input); });
    });
  });
})();
