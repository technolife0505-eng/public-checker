
(function(){
  function closeAll(except){
    document.querySelectorAll(".dup-source-menu").forEach(function(menu){
      if(menu !== except){
        menu.classList.remove("open");
        menu.style.display = "none";
      }
    });
  }

  window.mmToggleDuplicateSource = function(btn){
    var wrap = btn.closest(".dup-source");
    if(!wrap) return false;
    var menu = wrap.querySelector(".dup-source-menu");
    if(!menu) return false;

    var open = menu.classList.contains("open");
    closeAll(menu);

    if(open){
      menu.classList.remove("open");
      menu.style.display = "none";
    }else{
      menu.classList.add("open");
      menu.style.display = "block";
    }
    return false;
  };

  window.mmSelectDuplicateSource = function(option){
    var wrap = option.closest(".dup-source");
    if(!wrap) return false;
    var row = option.closest("tr");
    if(!row) return false;

    var source = option.getAttribute("data-source") || "";
    var time = option.getAttribute("data-time") || "";
    var url = option.getAttribute("data-url") || "#";

    var label = wrap.querySelector(".dup-source-label");
    if(label) label.textContent = source;

    var timeCell = row.querySelector(".dup-time-cell");
    if(timeCell) timeCell.textContent = time;

    var link = row.querySelector(".dup-link-cell a");
    if(link) link.href = url;

    closeAll(null);
    return false;
  };

  document.addEventListener("click", function(e){
    if(e.target.closest(".dup-source")) return;
    closeAll(null);
  }, true);

  document.addEventListener("keydown", function(e){
    if(e.key === "Escape") closeAll(null);
  }, true);
})();
