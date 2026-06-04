
(function(){
  function closeAll(except){
    document.querySelectorAll(".ms-menu").forEach(function(menu){
      if(menu !== except){
        menu.classList.remove("open");
        menu.style.display = "none";
      }
    });
  }

  window.mmToggleMS = function(btn){
    var wrap = btn.closest(".ms-wrap");
    if(!wrap) return false;
    var menu = wrap.querySelector(".ms-menu");
    if(!menu) return false;

    var isOpen = menu.classList.contains("open");
    closeAll(menu);

    if(isOpen){
      menu.classList.remove("open");
      menu.style.display = "none";
    }else{
      menu.classList.add("open");
      menu.style.display = "block";
      var search = menu.querySelector(".ms-search");
      if(search){
        search.value = "";
        filterMSOptions(search);
        setTimeout(function(){ search.focus(); }, 30);
      }
    }
    return false;
  };

  window.filterMSOptions = function(input){
    var q = (input.value || "").toLowerCase().trim();
    var menu = input.closest(".ms-menu");
    if(!menu) return;
    menu.querySelectorAll(".ms-option").forEach(function(row){
      var text = (row.textContent || "").toLowerCase();
      row.style.display = text.indexOf(q) >= 0 ? "flex" : "none";
    });
  };

  function title(g){
    if(g==="platforms") return "Platformalar";
    if(g==="sources") return "Kanallar";
    if(g==="keywords") return "Kalit so‘zlar";
    return g;
  }

  function updateLabel(g){
    var allBox = document.querySelector('[data-group-all="'+g+'"]');
    var checked = Array.from(document.querySelectorAll('[data-group-item="'+g+'"]:checked'));
    var label = document.getElementById(g+"Label");
    if(!label) return;

    if(allBox && allBox.checked){
      label.textContent = title(g) + ": Barchasi";
    }else if(checked.length === 0){
      if(allBox) allBox.checked = true;
      label.textContent = title(g) + ": Barchasi";
    }else{
      label.textContent = title(g) + ": " + checked.length + " ta tanlandi";
    }
  }

  function updateAll(){ ["platforms","sources","keywords"].forEach(updateLabel); }

  document.addEventListener("change", function(e){
    var all = e.target.closest("[data-group-all]");
    var item = e.target.closest("[data-group-item]");

    if(all){
      var g = all.getAttribute("data-group-all");
      if(all.checked){
        document.querySelectorAll('[data-group-item="'+g+'"]').forEach(function(x){ x.checked = false; });
      }
    }

    if(item){
      var g2 = item.getAttribute("data-group-item");
      var allBox = document.querySelector('[data-group-all="'+g2+'"]');
      if(item.checked && allBox) allBox.checked = false;

      var any = Array.from(document.querySelectorAll('[data-group-item="'+g2+'"]')).some(function(x){ return x.checked; });
      if(!any && allBox) allBox.checked = true;
    }

    updateAll();
  });

  document.addEventListener("click", function(e){
    if(e.target.closest(".ms-btn")) return;
    if(e.target.closest(".ms-menu")) return;
    closeAll(null);
  });

  document.addEventListener("keydown", function(e){
    if(e.key === "Escape") closeAll(null);
  });

  document.addEventListener("DOMContentLoaded", updateAll);
})();
