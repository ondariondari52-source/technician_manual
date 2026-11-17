(function () {
  document.addEventListener("submit", function (event) {
    var message = event.target.getAttribute("data-confirm");
    if (message && !window.confirm(message)) {
      event.preventDefault();
    }
  });

  var box = document.getElementById("answer-box");
  if (!box) {
    return;
  }
  var body = box.querySelector(".answer-body");
  var guide = box.querySelector(".guide");
  var mode = box.getAttribute("data-mode");

  function paragraph(text, className) {
    var p = document.createElement("p");
    p.className = className || "";
    p.textContent = text;
    return p;
  }

  function reveal(nodes) {
    nodes.forEach(function (node, index) {
      node.classList.add("line");
      body.appendChild(node);
      window.setTimeout(function () { node.classList.add("on"); }, 120 + index * 320);
    });
  }

  function showGuide(data) {
    if (!data.figure || !guide) { return; }
    guide.innerHTML = "";
    var title = document.createElement("h3");
    title.textContent = data.figure_title;
    guide.appendChild(title);
    var holder = document.createElement("div");
    holder.innerHTML = data.figure;
    guide.appendChild(holder);
    if (data.ports && data.ports.length) {
      var list = document.createElement("ul");
      list.className = "legend";
      data.ports.forEach(function (label) {
        var item = document.createElement("li");
        item.textContent = label;
        list.appendChild(item);
      });
      guide.appendChild(list);
    }
    guide.appendChild(paragraph("Illustration only. Your model may look different.", "fine"));
    guide.classList.add("pop");
  }

  function show(data) {
    body.innerHTML = "";
    showGuide(data);
    var nodes = [];
    if (!data.answer) {
      var panel = document.createElement("div");
      panel.className = "refusal";
      var heading = document.createElement("b");
      heading.textContent = mode === "manual" ? "No supported answer" : "No AI answer";
      panel.appendChild(heading);
      panel.appendChild(paragraph(data.reason || "No answer was available."));
      if (mode === "manual") {
        panel.appendChild(paragraph("You can try the AI guidance option. It is not taken from the manual."));
      }
      reveal([panel]);
      return;
    }
    data.answer.split(/\n\s*\n|\n(?=\d+\.)/).forEach(function (part) {
      if (part.trim()) { nodes.push(paragraph(part.trim())); }
    });
    if (data.sources && data.sources.length) {
      var sources = document.createElement("p");
      sources.className = "sources";
      sources.appendChild(document.createTextNode("Sources: "));
      data.sources.forEach(function (number, index) {
        if (index) { sources.appendChild(document.createTextNode(", ")); }
        var link = document.createElement("a");
        link.href = "/section?n=" + number;
        link.textContent = "Section " + number;
        sources.appendChild(link);
      });
      nodes.push(sources);
    }
    reveal(nodes);
    if (data.flagged && data.flagged.length) {
      var flag = document.createElement("div");
      flag.className = "flag";
      flag.textContent = "Security check: " + data.flagged.length + " instruction-like sentence(s) in the manual text were ignored.";
      body.appendChild(flag);
    }
  }

  function fail() {
    body.innerHTML = "";
    body.appendChild(paragraph("The answer could not be loaded. Please try again.", "muted"));
  }

  fetch("/api/answer?mode=" + encodeURIComponent(mode) + "&q=" + encodeURIComponent(box.getAttribute("data-q")), { credentials: "same-origin" })
    .then(function (response) { return response.json(); })
    .then(show)
    .catch(fail);
})();
