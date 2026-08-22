(function () {
  const REPORT_ID = window.REPORT_ID;
  const ALL = window.CANDIDATES;

  let state = {
    tier: "all",
    stateFilter: "all",
    round1Only: false,
    round2Only: false,
    query: "",
    sortKey: "final_score",
    sortDir: -1,
  };

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  function matches(p, q) {
    if (!q) return true;
    const hay = (p.name + " " + p.email + " " + p.city + " " + p.employer + " " + p.mobile).toLowerCase();
    return hay.includes(q);
  }

  function starsHtml(uid, rating) {
    let out = `<span class="stars" data-uid="${esc(uid)}">`;
    for (let i = 1; i <= 5; i++) {
      out += `<span class="star ${i <= rating ? "filled" : ""}" data-value="${i}">★</span>`;
    }
    out += `</span>`;
    return out;
  }

  function render() {
    const q = state.query.trim().toLowerCase();
    let rows = ALL.filter((p) =>
      (state.tier === "all" || p.tier === state.tier) &&
      (state.stateFilter === "all" || p.state === state.stateFilter) &&
      (!state.round1Only || p.round1) &&
      (!state.round2Only || p.round2) &&
      matches(p, q)
    );
    rows.sort((a, b) => {
      const k = state.sortKey;
      let av = a[k], bv = b[k];
      if (typeof av === "string") { av = av.toLowerCase(); bv = bv.toLowerCase(); }
      if (av < bv) return -1 * state.sortDir;
      if (av > bv) return 1 * state.sortDir;
      return 0;
    });

    const tbody = document.getElementById("roster-body");
    const empty = document.getElementById("empty-state");
    if (rows.length === 0) {
      tbody.innerHTML = "";
      empty.style.display = "block";
      return;
    }
    empty.style.display = "none";

    tbody.innerHTML = rows.map((p) => {
      const tierClass = p.tier === "Intern" ? "intern" : (p.tier === "Experienced" ? "exp" : "other");
      const expLabel = p.tier === "Experienced" ? (p.exp_years + "y") : "—";
      const claude = p.claude_mentioned ? " ★" : "";
      return `<tr data-uid="${esc(p.uid)}">
        <td class="name">${esc(p.name)}</td>
        <td>${esc(p.mobile) || "—"}</td>
        <td class="muted">${esc(p.email) || "—"}</td>
        <td>${esc(p.city)}</td>
        <td class="muted">${esc(p.state)}</td>
        <td><span class="row-tier ${tierClass}">${esc(p.tier)}</span> <span class="muted">${esc(p.role)}</span></td>
        <td class="num">${expLabel}</td>
        <td class="num">${p.final_score}${claude}</td>
        <td class="num">${starsHtml(p.uid, p.rating)}</td>
        <td><input type="checkbox" class="round-checkbox" data-uid="${esc(p.uid)}" data-round="round1" ${p.round1 ? "checked" : ""}></td>
        <td><input type="checkbox" class="round-checkbox" data-uid="${esc(p.uid)}" data-round="round2" ${p.round2 ? "checked" : ""}></td>
        <td><a class="resume-link" href="${esc(p.resume)}" target="_blank" rel="noopener noreferrer">View ↗</a></td>
      </tr>`;
    }).join("");
  }

  function setSaveStatus(text, isError) {
    const el = document.getElementById("save-status");
    el.textContent = text;
    el.classList.toggle("error", !!isError);
    if (text) {
      clearTimeout(setSaveStatus._t);
      setSaveStatus._t = setTimeout(() => { el.textContent = ""; }, 2500);
    }
  }

  async function saveField(uid, payload) {
    setSaveStatus("Saving…");
    try {
      const res = await fetch(`/reports/${REPORT_ID}/candidates/${encodeURIComponent(uid)}/update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(await res.text());
      const updated = await res.json();
      const local = ALL.find((c) => c.uid === uid);
      if (local) Object.assign(local, updated);
      setSaveStatus("Saved");
    } catch (err) {
      console.error(err);
      setSaveStatus("Failed to save — try again", true);
    }
  }

  document.querySelectorAll(".filter-btn[data-tier]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".filter-btn[data-tier]").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.tier = btn.dataset.tier;
      render();
    });
  });

  document.getElementById("round1-toggle").addEventListener("click", (e) => {
    state.round1Only = !state.round1Only;
    e.target.classList.toggle("active", state.round1Only);
    render();
  });
  document.getElementById("round2-toggle").addEventListener("click", (e) => {
    state.round2Only = !state.round2Only;
    e.target.classList.toggle("active", state.round2Only);
    render();
  });

  document.getElementById("state-filter").addEventListener("change", (e) => {
    state.stateFilter = e.target.value;
    render();
  });

  document.getElementById("search").addEventListener("input", (e) => {
    state.query = e.target.value;
    render();
  });

  document.querySelectorAll("thead th[data-key]").forEach((th) => {
    th.addEventListener("click", () => {
      const key = th.dataset.key;
      if (state.sortKey === key) {
        state.sortDir *= -1;
      } else {
        state.sortKey = key;
        state.sortDir = key === "name" || key === "city" || key === "state" ? 1 : -1;
      }
      document.querySelectorAll("thead th").forEach((h) => h.classList.remove("sorted"));
      th.classList.add("sorted");
      render();
    });
  });

  document.getElementById("roster-body").addEventListener("click", (e) => {
    const star = e.target.closest(".star");
    if (star) {
      const uid = star.parentElement.dataset.uid;
      const rating = Number(star.dataset.value);
      const local = ALL.find((c) => c.uid === uid);
      if (local) local.rating = rating;
      render();
      saveField(uid, { rating });
      return;
    }
  });

  document.getElementById("roster-body").addEventListener("change", (e) => {
    const box = e.target.closest(".round-checkbox");
    if (box) {
      const uid = box.dataset.uid;
      const field = box.dataset.round;
      const local = ALL.find((c) => c.uid === uid);
      if (local) local[field] = box.checked;
      saveField(uid, { [field]: box.checked });
    }
  });

  render();
})();
