/* CanaryTrip dashboard — Three.js file-system particle field + live feed. */
(function () {
  "use strict";

  /* ================= boot sequence ================= */
  const bootLines = [
    "> canarytrip v0.1.0 — behavioral ransomware tripwire",
    "> loading detection engine ............ OK",
    "> deploying canary files .............. OK",
    "> arming filesystem watchers .......... OK",
    "> opening 3D visualization ............ OK",
    "> STATUS: monitoring — all quiet",
  ];
  const bootEl = document.getElementById("boot");
  const bootLog = document.getElementById("boot-log");
  let bi = 0;
  const bootTimer = setInterval(() => {
    if (bi < bootLines.length) {
      bootLog.textContent += bootLines[bi++] + "\n";
    } else {
      clearInterval(bootTimer);
      setTimeout(() => bootEl.classList.add("done"), 450);
    }
  }, 260);

  /* ================= 2D starfield ================= */
  const starCv = document.getElementById("stars");
  const sctx = starCv.getContext("2d");
  let stars = [];
  function sizeStars() {
    starCv.width = innerWidth; starCv.height = innerHeight;
    stars = Array.from({ length: 160 }, () => ({
      x: Math.random() * starCv.width,
      y: Math.random() * starCv.height,
      r: Math.random() * 1.4 + 0.3,
      s: Math.random() * 0.25 + 0.05,
      tw: Math.random() * Math.PI * 2,
    }));
  }
  sizeStars();
  addEventListener("resize", sizeStars);
  (function drawStars() {
    sctx.clearRect(0, 0, starCv.width, starCv.height);
    for (const st of stars) {
      st.y -= st.s; if (st.y < 0) st.y = starCv.height;
      st.tw += 0.03;
      const a = 0.25 + 0.35 * Math.abs(Math.sin(st.tw));
      sctx.beginPath();
      sctx.arc(st.x, st.y, st.r, 0, Math.PI * 2);
      sctx.fillStyle = `rgba(0,229,255,${a.toFixed(3)})`;
      sctx.fill();
    }
    requestAnimationFrame(drawStars);
  })();

  /* ================= Three.js scene ================= */
  const canvas = document.getElementById("scene");
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x05070f, 0.028);
  const camera = new THREE.PerspectiveCamera(55, 1, 0.1, 200);
  camera.position.set(0, 9, 26);
  camera.lookAt(0, 0, 0);

  scene.add(new THREE.AmbientLight(0x8899ff, 0.7));
  const key = new THREE.DirectionalLight(0x00e5ff, 1.1);
  key.position.set(8, 14, 10);
  scene.add(key);

  const field = new THREE.Group();   // rotating file-system disc
  scene.add(field);

  const CYAN = new THREE.Color(0x00e5ff);
  const DIM = new THREE.Color(0x2a4a6e);
  const RED = new THREE.Color(0xff3355);

  const nodes = new Map();  // path -> {mesh, base, flash}
  const nodeGeo = new THREE.SphereGeometry(0.32, 12, 12);

  // expanding shockwave rings (pooled)
  const rings = [];
  const ringGeo = new THREE.RingGeometry(0.9, 1.0, 48);
  for (let i = 0; i < 14; i++) {
    const m = new THREE.Mesh(
      ringGeo,
      new THREE.MeshBasicMaterial({ color: 0xff3355, transparent: true, opacity: 0, side: THREE.DoubleSide })
    );
    m.rotation.x = -Math.PI / 2;
    m.visible = false;
    scene.add(m);
    rings.push({ mesh: m, t: 1 });
  }
  function shockwave(x, z) {
    const r = rings.find((r) => r.t >= 1) || rings[0];
    r.t = 0;
    r.mesh.position.set(x, 0.1, z);
    r.mesh.visible = true;
  }

  function layout(i, n) {
    // golden-angle spiral disc
    const golden = Math.PI * (3 - Math.sqrt(5));
    const r = 3.2 + 10.5 * Math.sqrt(i / n);
    const a = i * golden;
    return { x: r * Math.cos(a), z: r * Math.sin(a), y: (Math.sin(i * 12.9898) * 0.5) * 1.6 };
  }

  function addNode(path, isCanary, idx, total) {
    const { x, y, z } = layout(idx, total);
    const mat = new THREE.MeshStandardMaterial({
      color: isCanary ? CYAN.clone() : DIM.clone(),
      emissive: isCanary ? CYAN.clone().multiplyScalar(0.9) : DIM.clone().multiplyScalar(0.25),
      roughness: 0.35, metalness: 0.6,
    });
    const mesh = new THREE.Mesh(nodeGeo, mat);
    const s = isCanary ? 1.7 : 1.0;
    mesh.scale.setScalar(s);
    mesh.position.set(x, y, z);
    field.add(mesh);
    nodes.set(path, { mesh, base: mat.color.clone(), flash: 0, isCanary, x, z });
  }

  function tamperNode(path) {
    const n = nodes.get(path);
    if (!n) return;
    n.flash = 1;
    shockwave(n.x, n.z);
  }

  function resetNodes() {
    for (const n of nodes.values()) {
      n.flash = 0;
      n.mesh.material.color.copy(n.isCanary ? CYAN : DIM);
      n.mesh.material.emissive.copy(
        (n.isCanary ? CYAN : DIM).clone().multiplyScalar(n.isCanary ? 0.9 : 0.25)
      );
    }
  }

  const clock3 = new THREE.Clock();
  let shake = 0;
  (function animate() {
    requestAnimationFrame(animate);
    const dt = Math.min(clock3.getDelta(), 0.05);
    const t = clock3.elapsedTime;

    field.rotation.y += dt * 0.06;

    for (const n of nodes.values()) {
      if (n.flash > 0) {
        n.flash = Math.max(0, n.flash - dt * 0.9);
        const k = 0.5 + 0.5 * Math.sin(t * 18);
        n.mesh.material.color.copy(RED).lerp(n.base, n.flash * 0.4);
        n.mesh.material.emissive.setRGB(0.9 * k + 0.2, 0.05, 0.12);
        n.mesh.scale.setScalar((n.isCanary ? 1.7 : 1.0) * (1 + 0.35 * k * (1 - n.flash)));
      } else if (n.isCanary) {
        const p = 0.75 + 0.25 * Math.sin(t * 2.4);
        n.mesh.material.emissive.copy(CYAN).multiplyScalar(0.9 * p);
      }
    }
    for (const r of rings) {
      if (r.t < 1) {
        r.t = Math.min(1, r.t + dt * 0.9);
        const s = 0.6 + r.t * 7;
        r.mesh.scale.set(s, s, s);
        r.mesh.material.opacity = 0.85 * (1 - r.t);
        if (r.t >= 1) r.mesh.visible = false;
      }
    }
    if (shake > 0) {
      shake = Math.max(0, shake - dt * 2.2);
      camera.position.x = (Math.random() - 0.5) * shake * 1.4;
      camera.position.y = 9 + (Math.random() - 0.5) * shake;
    } else {
      camera.position.x *= 0.95;
      camera.position.y += (9 + Math.sin(t * 0.4) * 0.7 - camera.position.y) * 0.03;
    }
    camera.lookAt(0, 0, 0);
    renderer.render(scene, camera);
  })();

  function resize3d() {
    const r = canvas.parentElement.getBoundingClientRect();
    renderer.setSize(r.width, r.height, false);
    camera.aspect = r.width / Math.max(1, r.height);
    camera.updateProjectionMatrix();
  }
  addEventListener("resize", resize3d);

  /* ================= UI wiring ================= */
  const banner = document.getElementById("status-banner");
  const timeline = document.getElementById("timeline");
  const gaugesEl = document.getElementById("gauges");
  const gaugeMap = new Map();

  function fmtTime(ts) {
    return new Date(ts * 1000).toLocaleTimeString([], { hour12: false });
  }

  function logLine(kind, msg, ts) {
    const div = document.createElement("div");
    div.className = "tl-item " + kind;
    div.innerHTML = `<div class="t">${fmtTime(ts || Date.now() / 1000)}</div><div class="msg"></div>`;
    div.querySelector(".msg").textContent = msg;
    timeline.prepend(div);
    while (timeline.children.length > 60) timeline.lastChild.remove();
  }

  function setStatus(state) {
    if (state === "UNDER ATTACK") {
      banner.textContent = "● UNDER ATTACK";
      banner.className = "attack";
      shake = 1;
    } else {
      banner.textContent = "● SAFE";
      banner.className = "safe";
    }
  }

  function upsertGauge(path, entropy, tampered) {
    let g = gaugeMap.get(path);
    if (!g) {
      const div = document.createElement("div");
      div.className = "gauge";
      div.innerHTML = `<div class="g-head"><span class="g-name"></span><span class="g-val"></span></div>
                       <div class="g-bar"><div class="g-fill"></div></div>`;
      div.querySelector(".g-name").textContent = path.split("/").pop();
      div.querySelector(".g-name").title = path;
      gaugesEl.appendChild(div);
      g = { el: div, fill: div.querySelector(".g-fill"), val: div.querySelector(".g-val") };
      gaugeMap.set(path, g);
    }
    g.val.textContent = entropy.toFixed(2) + " bits";
    g.fill.style.width = Math.min(100, (entropy / 8) * 100) + "%";
    g.el.classList.toggle("hot", tampered || entropy >= 7.0);
  }

  async function refreshStats() {
    try {
      const [s, f] = await Promise.all([
        fetch("/api/status").then((r) => r.json()),
        fetch("/api/files").then((r) => r.json()),
      ]);
      document.getElementById("st-files").textContent = s.files_watched;
      document.getElementById("st-canaries").textContent = s.canaries;
      document.getElementById("st-alerts").textContent = s.alerts_total;
      const mean = f.reduce((a, x) => a + x.entropy, 0) / Math.max(1, f.length);
      document.getElementById("st-entropy").textContent = mean.toFixed(2);
      setStatus(s.state);
    } catch (e) { /* backend warming up */ }
  }

  function buildField(fileList) {
    // clear & rebuild
    for (const n of nodes.values()) field.remove(n.mesh);
    nodes.clear();
    fileList.forEach((f, i) => addNode(f.path, f.is_canary, i, fileList.length));
    // gauges for canaries only
    gaugesEl.innerHTML = ""; gaugeMap.clear();
    fileList.filter((f) => f.is_canary).forEach((f) => upsertGauge(f.path, f.entropy, f.tampered));
    resize3d();
  }

  function onFileEvent(ev) {
    if (ev.tampered) tamperNode(ev.path);
    const g = gaugeMap.get(ev.path);
    if (g) upsertGauge(ev.path, ev.entropy, ev.tampered);
    if (ev.tampered) {
      logLine("warn", `MODIFIED ${ev.path} — entropy ${ev.entropy.toFixed(2)}${ev.is_canary ? " [CANARY]" : ""}`, ev.ts);
    }
    refreshStats();
  }

  function onAlert(a) {
    setStatus("UNDER ATTACK");
    shake = 1;
    logLine("alert", `TRIPWIRE ${a.level}: severity ${a.severity} — ${a.files_affected} files, ${a.canary_hits} canaries hit`, a.ts);
    refreshStats();
  }

  /* ================= websocket ================= */
  let ws;
  function connect() {
    ws = new WebSocket(`ws://${location.host}/ws/events`);
    ws.onmessage = (m) => {
      const d = JSON.parse(m.data);
      if (d.type === "snapshot") { buildField(d.files); d.alerts.forEach((a) => onAlert(a)); }
      else if (d.type === "file_event") onFileEvent(d);
      else if (d.type === "alert") onAlert(d);
      else if (d.type === "status") { setStatus(d.state); if (d.state === "SAFE") resetNodes(); }
      else if (d.type === "files_reset") resetNodes();
    };
    ws.onclose = () => setTimeout(connect, 2000);
    ws.onerror = () => ws.close();
  }

  document.getElementById("simulate").addEventListener("click", async () => {
    logLine("info", "staging simulated encryption burst…");
    await fetch("/api/simulate", { method: "POST" });
  });

  /* clock */
  setInterval(() => {
    document.getElementById("clock").textContent =
      new Date().toLocaleTimeString([], { hour12: false });
  }, 1000);

  connect();
  refreshStats();
  setInterval(refreshStats, 8000);
  logLine("info", "dashboard online — monitoring for encryption bursts");
})();
