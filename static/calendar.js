
const uzMonths = ["Yanvar","Fevral","Mart","Aprel","May","Iyun","Iyul","Avgust","Sentabr","Oktabr","Noyabr","Dekabr"];
const uzWeek = ["Du","Se","Ch","Pa","Ju","Sh","Ya"];
let dpState = {};

function dpPad(n) {
  return String(n).padStart(2, "0");
}

function dpISO(d) {
  return d.getFullYear() + "-" + dpPad(d.getMonth() + 1) + "-" + dpPad(d.getDate());
}

function dpDisplay(d) {
  return dpPad(d.getDate()) + "." + dpPad(d.getMonth() + 1) + "." + d.getFullYear();
}

function closePickers() {
  document.querySelectorAll(".datepicker-popup").forEach(function (p) {
    p.classList.remove("open");
  });
}

function setCustomDate(key, d) {
  const text = document.getElementById(key + "Text");
  const value = document.getElementById(key + "Value");

  if (text) text.value = dpDisplay(d);
  if (value) value.value = dpISO(d);

  closePickers();
}

function movePickerMonth(key, delta) {
  if (!dpState[key]) dpState[key] = new Date();

  dpState[key] = new Date(
    dpState[key].getFullYear(),
    dpState[key].getMonth() + delta,
    1
  );

  renderPicker(key);
}

function renderPicker(key) {
  if (!dpState[key]) dpState[key] = new Date();

  const popup = document.getElementById(key + "Picker");
  if (!popup) return;

  const current = dpState[key];
  const year = current.getFullYear();
  const month = current.getMonth();

  const first = new Date(year, month, 1);
  const startOffset = (first.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const prevDays = new Date(year, month, 0).getDate();

  const selectedEl = document.getElementById(key + "Value");
  const selected = selectedEl ? selectedEl.value : "";
  const todayISO = dpISO(new Date());

  let html = "";
  html += '<div class="dp-head">';
  html += '<button type="button" class="dp-nav" data-dp-move="' + key + '" data-dp-delta="-1">‹</button>';
  html += '<div class="dp-title">' + uzMonths[month] + " " + year + "</div>";
  html += '<button type="button" class="dp-nav" data-dp-move="' + key + '" data-dp-delta="1">›</button>';
  html += "</div>";

  html += '<div class="dp-week">';
  html += uzWeek.map(function (w) { return "<span>" + w + "</span>"; }).join("");
  html += "</div>";

  html += '<div class="dp-grid">';

  for (let i = 0; i < 42; i++) {
    let dayNum;
    let d;
    let muted = false;

    if (i < startOffset) {
      dayNum = prevDays - startOffset + i + 1;
      d = new Date(year, month - 1, dayNum);
      muted = true;
    } else if (i >= startOffset + daysInMonth) {
      dayNum = i - startOffset - daysInMonth + 1;
      d = new Date(year, month + 1, dayNum);
      muted = true;
    } else {
      dayNum = i - startOffset + 1;
      d = new Date(year, month, dayNum);
    }

    const iso = dpISO(d);
    let cls = "";
    if (muted) cls += "muted ";
    if (todayISO === iso) cls += "today ";
    if (selected === iso) cls += "selected";

    html += '<button type="button" class="dp-day ' + cls + '" data-dp-select="' + key + '" data-year="' + d.getFullYear() + '" data-month="' + d.getMonth() + '" data-day="' + d.getDate() + '">' + dayNum + "</button>";
  }

  html += "</div>";
  popup.innerHTML = html;
}

function openCustomPicker(key) {
  closePickers();
  renderPicker(key);

  const popup = document.getElementById(key + "Picker");
  if (popup) popup.classList.add("open");
}

function setQuickRange(prefix, days) {
  const end = new Date();
  const start = new Date();

  start.setDate(end.getDate() - (days - 1));

  setCustomDate(prefix + "From", start);
  setCustomDate(prefix + "To", end);
}

function clearDateRange(prefix) {
  const ids = [
    prefix + "FromText",
    prefix + "FromValue",
    prefix + "ToText",
    prefix + "ToValue"
  ];

  ids.forEach(function (id) {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });

  closePickers();
}

document.addEventListener("click", function (e) {
  const trigger = e.target.closest("[data-datepicker-key]");
  if (trigger) {
    e.preventDefault();
    e.stopPropagation();
    openCustomPicker(trigger.getAttribute("data-datepicker-key"));
    return;
  }

  const mover = e.target.closest("[data-dp-move]");
  if (mover) {
    e.preventDefault();
    e.stopPropagation();
    movePickerMonth(
      mover.getAttribute("data-dp-move"),
      parseInt(mover.getAttribute("data-dp-delta"), 10)
    );
    return;
  }

  const selector = e.target.closest("[data-dp-select]");
  if (selector) {
    e.preventDefault();
    e.stopPropagation();

    setCustomDate(
      selector.getAttribute("data-dp-select"),
      new Date(
        parseInt(selector.getAttribute("data-year"), 10),
        parseInt(selector.getAttribute("data-month"), 10),
        parseInt(selector.getAttribute("data-day"), 10)
      )
    );
    return;
  }

  if (!e.target.closest(".custom-date-wrap")) {
    closePickers();
  }
});
