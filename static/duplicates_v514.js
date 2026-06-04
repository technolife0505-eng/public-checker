
(function(){
  function closeAll(){
    document.querySelectorAll(".dup-source-menu").forEach(function(menu){
      menu.classList.remove("open");
      menu.style.display = "none";
    });
  }

  function placeMenu(btn, menu){
    var rect = btn.getBoundingClientRect();
    menu.style.position = "fixed";
    menu.style.left = rect.left + "px";
    menu.style.top = (rect.bottom + 6) + "px";
    menu.style.width = Math.max(230, rect.width + 70) + "px";
    menu.style.zIndex = "2147483647";
  }

  window.mmToggleDuplicateSource = function(btn){
    var wrap = btn.closest(".dup-source");
    if(!wrap) return false;
    var menu = wrap.querySelector(".dup-source-menu");
    if(!menu) return false;

    var willOpen = !menu.classList.contains("open");
    closeAll();

    if(willOpen){
      placeMenu(btn, menu);
      menu.classList.add("open");
      menu.style.display = "block";
    }
    return false;
  };

  window.mmSelectDuplicateSource = function(option){
    var menu = option.closest(".dup-source-menu");
    var row = option.closest("tr");
    if(!row && menu){
      var wrap = menu.closest(".dup-source");
      if(wrap) row = wrap.closest("tr");
    }
    if(!row) return false;

    var source = option.getAttribute("data-source") || "";
    var time = option.getAttribute("data-time") || "";
    var url = option.getAttribute("data-url") || "#";

    var label = row.querySelector(".dup-source-label");
    if(label) label.textContent = source;

    var timeCell = row.querySelector(".dup-time-cell");
    if(timeCell) timeCell.textContent = time;

    var link = row.querySelector(".dup-link-cell a");
    if(link) link.href = url;

    closeAll();
    return false;
  };

  document.addEventListener("click", function(e){
    var srcBtn = e.target.closest(".dup-source-btn");
    if(srcBtn){
      e.preventDefault();
      e.stopPropagation();
      window.mmToggleDuplicateSource(srcBtn);
      return;
    }

    var opt = e.target.closest(".dup-source-option");
    if(opt){
      e.preventDefault();
      e.stopPropagation();
      window.mmSelectDuplicateSource(opt);
      return;
    }

    if(!e.target.closest(".dup-source-menu")) closeAll();
  }, true);

  document.addEventListener("scroll", closeAll, true);
  window.addEventListener("resize", closeAll);
  document.addEventListener("keydown", function(e){
    if(e.key === "Escape") closeAll();
  }, true);
})();
