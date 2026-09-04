
  const API = window.location.protocol.startsWith('http') ? '/api' : 'http://127.0.0.1:8000/api';
  let TOKEN = localStorage.getItem("recrutia_token") || null;
  let USERNAME = localStorage.getItem("recrutia_username") || "recruteur";
  let toutesCandidatures = [];
  let candidatureActive = null;
  let filtreActif = 'TOUS';

  // ── INIT ─────────────────────────────────────────────────────
  async function initialiserApp() {
    TOKEN = localStorage.getItem("recrutia_token") || null;
    USERNAME = localStorage.getItem("recrutia_username") || "recruteur";

    // Vérification silencieuse du token existant
    if (TOKEN) {
      try {
        const res = await fetch(`${API}/auth/me`, {
          headers: { "Authorization": `Bearer ${TOKEN}`, "Content-Type": "application/json" }
        });
        if (res.ok) {
          const data = await res.json();
          USERNAME = data.username;
        } else {
          TOKEN = null;
        }
      } catch (e) {
        console.warn("Vérification token échouée :", e);
        TOKEN = null;
      }
    }

    // Si pas de token, auto-login avec le compte démo
    if (!TOKEN) {
      try {
        const res = await fetch(`${API}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: "recruteur", password: "RecrutIA2026!" })
        });
        if (res.ok) {
          const data = await res.json();
          TOKEN = data.access_token;
          USERNAME = data.username || "recruteur";
          localStorage.setItem("recrutia_token", TOKEN);
          localStorage.setItem("recrutia_username", USERNAME);
        }
      } catch (e) {
        console.warn("Auto-login impossible :", e);
      }
    }

    // Toujours afficher le tableau de bord
    afficherApp();
  }

  window.addEventListener("DOMContentLoaded", () => {
    initialiserApp();
  });

  // Renouvelle le token auto (utilisé lors des erreurs 401)
  async function purgerEtObtenirToken() {
    localStorage.removeItem("recrutia_token");
    localStorage.removeItem("recrutia_username");
    TOKEN = null;
    try {
      const res = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: "recruteur", password: "RecrutIA2026!" })
      });
      if (res.ok) {
        const data = await res.json();
        TOKEN = data.access_token;
        USERNAME = data.username || "recruteur";
        localStorage.setItem("recrutia_token", TOKEN);
        localStorage.setItem("recrutia_username", USERNAME);
        return true;
      }
    } catch (e) {
      console.error("Échec purgerEtObtenirToken:", e);
    }
    return false;
  }

  function headers() {
    const h = { "Content-Type": "application/json" };
    if (TOKEN) h["Authorization"] = `Bearer ${TOKEN}`;
    return h;
  }

  // ── AUTH ──────────────────────────────────────────────────────
  function switchTab(tab) {
    const isLogin = tab === 'login';
    const tabLog = document.getElementById("tab-login");
    const tabReg = document.getElementById("tab-register");

    if (tabLog && tabReg) {
      if (isLogin) {
        tabLog.style.background = "#fff";
        tabLog.style.color = "var(--primary)";
        tabLog.style.boxShadow = "var(--shadow-sm)";

        tabReg.style.background = "transparent";
        tabReg.style.color = "var(--text-muted)";
        tabReg.style.boxShadow = "none";
      } else {
        tabReg.style.background = "#fff";
        tabReg.style.color = "var(--primary)";
        tabReg.style.boxShadow = "var(--shadow-sm)";

        tabLog.style.background = "transparent";
        tabLog.style.color = "var(--text-muted)";
        tabLog.style.boxShadow = "none";
      }
    }

    document.getElementById("form-login").style.display = isLogin ? "flex" : "none";
    document.getElementById("form-register").style.display = !isLogin ? "flex" : "none";
    document.getElementById("auth-error").style.display = "none";
  }

  function afficherErreurAuth(msg) {
    const el = document.getElementById("auth-error");
    el.innerText = msg;
    el.style.display = "block";
  }

  async function doLogin(e) {
    if (e) e.preventDefault();
    const userVal = (document.getElementById("login-user")?.value || "recruteur").trim();
    const passVal = (document.getElementById("login-pass")?.value || "RecrutIA2026!").trim();
    const btn = document.getElementById("btn-login");
    if (btn) { btn.innerHTML = '<span class="spinner"></span> Connexion en cours...'; btn.disabled = true; }

    try {
      const res = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: userVal, password: passVal })
      });
      if (res.ok) {
        const data = await res.json();
        TOKEN = data.access_token;
        USERNAME = data.username || userVal;
        localStorage.setItem("recrutia_token", TOKEN);
        localStorage.setItem("recrutia_username", USERNAME);
        if (window.location.search) history.replaceState({}, '', '/rh');
        afficherApp();
        if (btn) { btn.innerHTML = '<i class="fa-solid fa-right-to-bracket"></i> Se connecter'; btn.disabled = false; }
        return;
      } else {
        const err = await res.json().catch(() => ({}));
        afficherErreurAuth(err.detail || "Identifiants incorrects. Essayez : recruteur / RecrutIA2026!");
        if (btn) { btn.innerHTML = '<i class="fa-solid fa-right-to-bracket"></i> Se connecter'; btn.disabled = false; }
      }
    } catch {
      afficherErreurAuth("Impossible de contacter le serveur. Vérifiez que le backend est démarré sur le port 8000.");
      if (btn) { btn.innerHTML = '<i class="fa-solid fa-right-to-bracket"></i> Se connecter'; btn.disabled = false; }
    }
  }

  async function doRegister(e) {
    if (e) e.preventDefault();
    const btn = document.getElementById("btn-register");
    if (btn) {
      btn.innerHTML = '<span class="spinner"></span> Inscription...';
      btn.disabled = true;
    }
    try {
      const res = await fetch(`${API}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: document.getElementById("reg-user").value,
          password: document.getElementById("reg-pass").value
        })
      });
      const data = await res.json();
      if (res.ok) {
        toast("Compte créé avec succès ! Connectez-vous.", "success");
        switchTab('login');
        document.getElementById("login-user").value = document.getElementById("reg-user").value;
      } else {
        afficherErreurAuth(data.detail || "Erreur lors de la création du compte.");
      }
    } catch {
      afficherErreurAuth("Impossible de contacter le serveur.");
    }
    if (btn) {
      btn.innerHTML = '<i class="fa-solid fa-user-plus"></i> Créer mon compte';
      btn.disabled = false;
    }
  }

  function doLogout() {
    TOKEN = null; USERNAME = null;
    localStorage.removeItem("recrutia_token");
    localStorage.removeItem("recrutia_username");
    const authScreen = document.getElementById("auth-screen");
    const appScreen = document.getElementById("app-screen");
    if (authScreen) { authScreen.style.display = "flex"; authScreen.classList.remove("hidden"); }
    if (appScreen) { appScreen.style.display = "none"; appScreen.classList.remove("visible"); }
  }

  function afficherApp() {
    const authScreen = document.getElementById("auth-screen");
    const appScreen = document.getElementById("app-screen");
    if (authScreen) { authScreen.style.display = "none"; authScreen.classList.add("hidden"); }
    if (appScreen) { appScreen.style.display = "flex"; appScreen.classList.add("visible"); }
    const userLabel = document.getElementById("user-label");
    if (userLabel) userLabel.innerText = USERNAME || "recruteur";
    chargerOffres();
    chargerStats();
  }

  // ── STATS ─────────────────────────────────────────────────
  async function chargerStats() {
    try {
      const res = await fetch(`${API}/stats`, { headers: headers() });
      if (res.ok) {
        const s = await res.json();
        const el = document.getElementById("stat-entretiens");
        if (el) el.innerText = s.entretiens_planifies || 0;
        const elOff = document.getElementById("stat-offres");
        if (elOff) elOff.innerText = s.offres_actives || 0;
        const elCand = document.getElementById("stat-candidats");
        if (elCand) elCand.innerText = s.candidatures_total || 0;
      }
    } catch (e) {
      // Fallback : charger les entretiens directement
      fetch(`${API}/entretiens`, { headers: headers() })
        .then(r => r.ok ? r.json() : [])
        .then(data => { const el = document.getElementById("stat-entretiens"); if(el) el.innerText = data.length || 0; })
        .catch(() => {});
    }
  }

  // ── AUDIT ─────────────────────────────────────────────────────
  function ouvrirAudit() {
    document.getElementById("modal-audit").style.display = "flex";
    chargerAudit();
  }

  function fermerAudit() {
    document.getElementById("modal-audit").style.display = "none";
  }

  async function chargerAudit() {
    const container = document.getElementById("audit-list-container");
    container.innerHTML = '<div style="text-align:center; padding:20px; color:var(--text-muted);"><i class="fa-solid fa-spinner fa-spin"></i> Chargement du journal...</div>';
    try {
      const res = await fetch(`${API}/audit`, { headers: headers() });
      if (res.status === 401) { doLogout(); return; }
      if (res.ok) {
        const logs = await res.json();
        if (logs.length === 0) {
          container.innerHTML = '<div style="text-align:center; padding:20px; color:var(--text-muted);">Aucun événement dans le journal.</div>';
          return;
        }
        container.innerHTML = "";
        logs.forEach(log => {
          const date = new Date(log.timestamp).toLocaleString('fr-FR');
          container.innerHTML += `
            <div style="background:var(--bg-page); border:1px solid var(--border); border-radius:8px; padding:12px; font-size:12px;">
              <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <strong style="color:var(--text-primary);"><i class="fa-solid fa-user-circle"></i> ${log.utilisateur || 'Système'}</strong>
                <span style="color:var(--text-muted);">${date}</span>
              </div>
              <div style="color:var(--primary); font-weight:600; margin-bottom:4px;">${log.action}</div>
              <div style="color:var(--text-secondary); font-family:monospace; font-size:11px;">
                ${JSON.stringify(log.details)}
              </div>
            </div>
          `;
        });
      } else {
        container.innerHTML = '<div style="text-align:center; padding:20px; color:var(--accent-red);">Erreur lors du chargement de l\'audit.</div>';
      }
    } catch {
      container.innerHTML = '<div style="text-align:center; padding:20px; color:var(--accent-red);">Erreur réseau.</div>';
    }
  }

  // ── OFFRES ────────────────────────────────────────────────────
  async function chargerOffres() {
    try {
      const res = await fetch(`${API}/offres`, { headers: headers() });
      if (res.status === 401) {
        console.warn("Token expiré dans chargerOffres, régénération...");
        const ok = await purgerEtObtenirToken();
        if (ok) return chargerOffres();
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const offres = await res.json();
      document.getElementById("stat-offres").innerText = offres.length;

      // 1) Sélecteur pour le dépôt de CV (uniquement les offres réelles)
      const selUpload = document.getElementById("select-offre-upload");
      if (selUpload) {
        if (offres.length === 0) {
          selUpload.innerHTML = '<option value="">Aucune offre publiée — créez-en une à gauche</option>';
        } else {
          selUpload.innerHTML = '<option value="">-- Sélectionner l\'offre d\'emploi --</option>';
          offres.forEach(o => {
            selUpload.innerHTML += `<option value="${o.id}">${o.titre} (Exp. min: ${o.experience_min_annees} an/s)</option>`;
          });
        }
      }

      // 2) Sélecteur pour le filtrage des candidatures
      const selFilter = document.getElementById("select-offre-filter");
      if (selFilter) {
        selFilter.innerHTML = '<option value="ALL">📁 Toutes les candidatures</option>';
        offres.forEach(o => {
          selFilter.innerHTML += `<option value="${o.id}">${o.titre}</option>`;
        });
      }

      // 3) Grille des cartes d'offres sur le tableau de bord
      afficherGridOffresDashboard(offres);

      // 4) Charger les candidatures
      chargerCandidatures();
    } catch (err) {
      console.error("Erreur chargerOffres:", err);
      const grid = document.getElementById("offres-dashboard-grid");
      if (grid) grid.innerHTML = `
        <div style="grid-column:1/-1;text-align:center;padding:32px;background:#FEF2F2;border-radius:12px;color:#DC2626;">
          <i class="fa-solid fa-wifi fa-2x" style="margin-bottom:12px;display:block;"></i>
          <p style="font-weight:700;margin-bottom:8px;">Connexion au serveur backend...</p>
          <p style="font-size:13px;color:#9B1C1C;margin-bottom:16px;">Vérifiez que le serveur est démarré sur http://127.0.0.1:8000</p>
          <button onclick="chargerOffres()" style="padding:10px 24px;background:#059669;color:#fff;border:none;border-radius:8px;cursor:pointer;font-weight:600;">🔄 Réessayer</button>
        </div>`;
    }
  }

  function afficherGridOffresDashboard(offres) {
    const grid = document.getElementById("offres-dashboard-grid");
    if (!grid) return;
    if (!offres || offres.length === 0) {
      grid.innerHTML = `
        <div style="grid-column:1/-1; text-align:center; padding:32px; background:var(--bg-page); border:1px dashed var(--border); border-radius:12px; color:var(--text-muted);">
          <i class="fa-solid fa-folder-open fa-2x" style="margin-bottom:12px; color:var(--primary); opacity:0.6;"></i>
          <p style="font-weight:600;">Aucune offre d'emploi publiée pour le moment.</p>
          <p style="font-size:12px; margin-top:4px;">Utilisez le formulaire ci-dessus pour publier votre première offre RH.</p>
        </div>`;
      return;
    }
    grid.innerHTML = "";
    offres.forEach(o => {
      const comps = Array.isArray(o.competences_obligatoires) ? o.competences_obligatoires : (typeof o.competences_obligatoires === 'string' ? o.competences_obligatoires.split(',').map(s=>s.trim()).filter(Boolean) : []);
      const reqs = comps.map(c => `<span class="tag">${c}</span>`).join(" ");
      const card = document.createElement("div");
      card.style.cssText = "background:var(--bg-white); border:1px solid var(--border); border-radius:12px; padding:18px; display:flex; flex-direction:column; justify-content:space-between; gap:12px; box-shadow:var(--shadow-sm);";
      card.innerHTML = `
        <div>
          <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px; gap:8px;">
            <h3 style="font-size:15px; font-weight:700; color:var(--text-primary); margin:0;">${o.titre}</h3>
            <span style="background:#ECFDF5; color:#059669; font-size:10px; font-weight:700; padding:2px 8px; border-radius:99px; border:1px solid #A7F3D0; flex-shrink:0;">ACTIF</span>
          </div>
          <p style="font-size:12px; color:var(--text-secondary); line-height:1.5; margin-bottom:10px;">${o.description ? (o.description.length > 110 ? o.description.substring(0, 110) + '...' : o.description) : 'Description non disponible.'}</p>
          <div style="font-size:11px; color:var(--text-muted); margin-bottom:8px;">
            <i class="fa-solid fa-clock"></i> Expérience: <strong>${o.experience_min_annees} an(s) min.</strong>
          </div>
          <div style="display:flex; flex-wrap:wrap; gap:4px;">
            ${reqs || '<span style="font-size:11px; color:var(--text-muted);">Compétences non spécifiées</span>'}
          </div>
        </div>
        <div style="display:flex; gap:8px; border-top:1px solid var(--border); padding-top:12px; margin-top:4px;">
          <button onclick="editerOffreParId(${o.id})" style="flex:1; padding:6px 10px; font-size:12px; font-weight:600; background:#FEF3C7; color:#92400E; border:none; border-radius:6px; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:4px;">
            <i class="fa-solid fa-pen"></i> Modifier
          </button>
          <button onclick="supprimerOffreRH(${o.id})" style="padding:6px 12px; font-size:12px; font-weight:600; background:#FEE2E2; color:#991B1B; border:none; border-radius:6px; cursor:pointer;" title="Supprimer l'offre">
            <i class="fa-solid fa-trash"></i>
          </button>
          <button onclick="filtrerParOffreId(${o.id})" style="padding:6px 12px; font-size:12px; font-weight:600; background:var(--primary-light); color:var(--primary); border:none; border-radius:6px; cursor:pointer;" title="Voir les candidatures pour cette offre">
            <i class="fa-solid fa-users"></i> CVs
          </button>
        </div>`;
      grid.appendChild(card);
    });
  }

  function filtrerParOffreId(offreId) {
    const selFilter = document.getElementById("select-offre-filter");
    if (selFilter) selFilter.value = offreId;
    chargerCandidatures();
    const sectionCand = document.querySelector(".bottom-section");
    if (sectionCand) sectionCand.scrollIntoView({ behavior: 'smooth' });
    toast("Filtre appliqué pour cette offre !", "info");
  }

  // ── CALENDRIER DES ENTRETIENS ──────────────────────────────────

  function ouvrirCalendrier() {
    document.getElementById("modal-calendrier").style.display = "flex";
    chargerEntretiens();
  }

  function fermerCalendrier() {
    document.getElementById("modal-calendrier").style.display = "none";
  }

  async function chargerEntretiens() {
    const container = document.getElementById("calendrier-container");
    container.innerHTML = '<div style="text-align:center; padding:40px; color:var(--text-muted);"><i class="fa-solid fa-spinner fa-spin fa-2x"></i><p style="margin-top:12px;">Chargement du calendrier...</p></div>';
    try {
      const res = await fetch(`${API}/entretiens`, { headers: headers() });
      if (res.status === 401) { doLogout(); return; }
      const entretiens = await res.json();

      // Mise à jour compteur header
      document.getElementById("stat-entretiens").innerText = entretiens.length;

      // Stats
      const nbPresentiel = entretiens.filter(e => (e.format_entretien || "").toUpperCase() === "PRESENTIEL").length;
      const nbVisio      = entretiens.filter(e => (e.format_entretien || "").toUpperCase() === "VISIO").length;
      const offresUniques = new Set(entretiens.map(e => e.offre_id)).size;
      document.getElementById("cal-count-total").innerText = entretiens.length;
      document.getElementById("cal-count-presentiel").innerText = nbPresentiel;
      document.getElementById("cal-count-visio").innerText = nbVisio;
      document.getElementById("cal-count-offres").innerText = offresUniques;

      if (entretiens.length === 0) {
        container.innerHTML = `
          <div style="text-align:center; padding:60px 20px; color:var(--text-muted);">
            <i class="fa-regular fa-calendar-xmark" style="font-size:48px; opacity:0.4;"></i>
            <p style="margin-top:16px; font-size:15px; font-weight:600;">Aucun entretien planifié pour le moment.</p>
            <p style="font-size:13px; margin-top:4px;">Validez un candidat avec le bouton "Valider & Convoquer" pour créer un entretien.</p>
          </div>`;
        return;
      }

      afficherCalendrier(entretiens);
    } catch (err) {
      container.innerHTML = '<div style="text-align:center; padding:40px; color:var(--accent-red);"><i class="fa-solid fa-circle-exclamation fa-2x"></i><p style="margin-top:12px;">Erreur lors du chargement du calendrier.</p></div>';
    }
  }

  function afficherCalendrier(entretiens) {
    const container = document.getElementById("calendrier-container");

    // Grouper les entretiens par date (premier mot de la chaîne de date)
    const groupes = {};
    entretiens.forEach(e => {
      const dateKey = e.date_entretien || "Date non précisée";
      if (!groupes[dateKey]) groupes[dateKey] = [];
      groupes[dateKey].push(e);
    });

    let html = "";
    Object.entries(groupes).forEach(([dateLabel, liste]) => {
      html += `
        <div style="margin-bottom:24px;">
          <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
            <div style="width:10px; height:10px; border-radius:50%; background:var(--primary); flex-shrink:0;"></div>
            <div style="font-size:14px; font-weight:700; color:var(--primary); text-transform:uppercase; letter-spacing:0.5px;">
              <i class="fa-solid fa-calendar-day"></i> ${dateLabel}
            </div>
            <div style="flex:1; height:1px; background:var(--border);"></div>
            <span style="font-size:11px; color:var(--text-muted); background:var(--bg-page); padding:2px 8px; border-radius:20px; border:1px solid var(--border);">${liste.length} entretien${liste.length > 1 ? 's' : ''}</span>
          </div>
          <div style="display:flex; flex-direction:column; gap:10px; padding-left:20px; border-left:2px solid var(--primary-light);">
            ${liste.map(e => {
              const formatBadge = (e.format_entretien || "PRESENTIEL").toUpperCase() === "VISIO"
                ? '<span style="background:#EFF6FF; color:#1D4ED8; font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px; border:1px solid #BFDBFE;"><i class="fa-solid fa-video"></i> Visio</span>'
                : '<span style="background:#ECFDF5; color:#047857; font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px; border:1px solid #A7F3D0;"><i class="fa-solid fa-building"></i> Présentiel</span>';
              const scoreColor = e.score_ia >= 70 ? '#059669' : (e.score_ia >= 40 ? '#D97706' : '#DC2626');
              const initiale = (e.candidat_nom || "C").charAt(0).toUpperCase();
              return `
                <div style="background:#fff; border:1px solid var(--border); border-radius:12px; padding:16px; display:flex; align-items:center; gap:14px; box-shadow:0 1px 3px rgba(0,0,0,0.06); transition:box-shadow 0.2s;" onmouseover="this.style.boxShadow='0 4px 12px rgba(5,150,105,0.15)'" onmouseout="this.style.boxShadow='0 1px 3px rgba(0,0,0,0.06)'">
                  <div style="width:46px; height:46px; border-radius:50%; background:var(--primary); color:#fff; display:flex; align-items:center; justify-content:center; font-size:18px; font-weight:700; flex-shrink:0;">${initiale}</div>
                  <div style="flex:1; min-width:0;">
                    <div style="font-weight:700; font-size:15px; color:var(--text-primary);">${e.candidat_nom || "Candidat"}</div>
                    <div style="font-size:12px; color:var(--text-muted); margin-top:2px;"><i class="fa-solid fa-envelope"></i> ${e.candidat_email || "—"}</div>
                    <div style="font-size:12px; color:var(--text-secondary); margin-top:4px;"><i class="fa-solid fa-briefcase"></i> <strong>${e.offre_titre}</strong></div>
                  </div>
                  <div style="text-align:right; flex-shrink:0; display:flex; flex-direction:column; gap:6px; align-items:flex-end;">
                    ${formatBadge}
                    <div style="font-size:11px; color:var(--text-muted);"><i class="fa-solid fa-location-dot"></i> ${e.lieu_entretien || "—"}</div>
                    <div style="font-size:11px; color:${scoreColor}; font-weight:700;"><i class="fa-solid fa-star"></i> Score IA : ${Math.round(e.score_ia || 0)}/100</div>
                    <div style="font-size:10px; color:var(--text-muted);">RH : ${e.rh_utilisateur || "—"}</div>
                  </div>
                </div>`;
            }).join("")}
          </div>
        </div>`;
    });

    container.innerHTML = html;
  }

  let offreEnEditionId = null;

  function ouvrirModalOffres() {
    afficherModalOffres();
    document.getElementById("modal-offres").style.display = "flex";
  }

  function fermerModalOffres() {
    document.getElementById("modal-offres").style.display = "none";
  }

  async function afficherModalOffres() {
    const container = document.getElementById("offres-list-container");
    container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted);"><i class="fa-solid fa-spinner fa-spin"></i> Chargement...</div>';
    try {
      const res = await fetch(`${API}/offres`, { headers: headers() });
      if (!res.ok) throw new Error();
      const offres = await res.json();
      if (offres.length === 0) {
        container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted);">Aucune offre. Créez-en une dans le formulaire à gauche.</div>';
        return;
      }
      container.innerHTML = '';
      offres.forEach(o => {
        const comps = Array.isArray(o.competences_obligatoires) ? o.competences_obligatoires : (typeof o.competences_obligatoires === 'string' ? o.competences_obligatoires.split(',').map(s=>s.trim()).filter(Boolean) : []);
        const reqs = comps.map(c => `<span class="tag">${c}</span>`).join(' ');
        const statutBadge = o.statut === 'ACTIF' ? '<span style="background:#ECFDF5;color:#059669;font-size:10px;font-weight:700;padding:2px 8px;border-radius:99px;border:1px solid #A7F3D0;">ACTIF</span>' : '<span style="background:#FEF2F2;color:#DC2626;font-size:10px;font-weight:700;padding:2px 8px;border-radius:99px;">INACTIF</span>';
        const div = document.createElement('div');
        div.style.cssText = 'background:var(--bg-page);border:1px solid var(--border);border-radius:12px;padding:16px;display:flex;justify-content:space-between;align-items:flex-start;gap:12px;';
        div.innerHTML = `
          <div style="flex:1;min-width:0;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
              <span style="font-weight:700;font-size:14px;color:var(--text-primary);">${o.titre}</span>
              ${statutBadge}
            </div>
            <div style="font-size:11px;color:var(--text-muted);margin-bottom:6px;">Exp. min: <strong>${o.experience_min_annees} an(s)</strong> · #${o.id}</div>
            <div style="display:flex;flex-wrap:wrap;gap:4px;">${reqs || '<span style="font-size:11px;color:var(--text-muted);">Aucune compétence</span>'}</div>
          </div>
          <div style="display:flex;flex-direction:column;gap:6px;flex-shrink:0;">
            <button style="font-size:12px;padding:5px 10px;background:var(--primary);color:#fff;border:none;border-radius:6px;cursor:pointer;font-weight:600;" onclick="selectionnerOffreDepuisModal(${o.id})">Voir CVs</button>
            <button style="font-size:12px;padding:5px 10px;background:#FEF3C7;color:#92400E;border:none;border-radius:6px;cursor:pointer;font-weight:600;" onclick="editerOffreParId(${o.id})">✏️ Modifier</button>
            <button style="font-size:12px;padding:5px 10px;background:#FEE2E2;color:#991B1B;border:none;border-radius:6px;cursor:pointer;font-weight:600;" onclick="supprimerOffreRH(${o.id})">🗑️ Supprimer</button>
          </div>`;
        container.appendChild(div);
      });
    } catch {
      container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--accent-red);">Erreur chargement des offres.</div>';
    }
  }

  function selectionnerOffreDepuisModal(offreId) {
    filtrerParOffreId(offreId);
    fermerModalOffres();
  }

  async function editerOffreParId(offreId) {
    try {
      const res = await fetch(`${API}/offres/${offreId}`, { headers: headers() });
      if (!res.ok) { toast('Erreur chargement offre.', 'error'); return; }
      const offre = await res.json();
      offreEnEditionId = offre.id;
      document.getElementById('offre-titre').value = offre.titre || '';
      document.getElementById('offre-desc').value = offre.description || '';
      document.getElementById('offre-exp').value = offre.experience_min_annees || 0;
      const compsReq = Array.isArray(offre.competences_obligatoires) ? offre.competences_obligatoires : (typeof offre.competences_obligatoires === 'string' ? offre.competences_obligatoires.split(',').map(s=>s.trim()) : []);
      const compsOpt = Array.isArray(offre.competences_souhaitees) ? offre.competences_souhaitees : (typeof offre.competences_souhaitees === 'string' ? offre.competences_souhaitees.split(',').map(s=>s.trim()) : []);
      document.getElementById('offre-req').value = compsReq.join(', ');
      document.getElementById('offre-opt').value = compsOpt.join(', ');

      const btnSubmit = document.getElementById('btn-creer-offre');
      btnSubmit.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Sauvegarder les Modifications';
      btnSubmit.style.background = 'linear-gradient(135deg, #D97706, #92400E)';

      document.getElementById('btn-annuler-offre').style.display = 'block';
      document.getElementById('form-offre-title').textContent = `Modifier Offre #${offre.id}`;
      document.getElementById('form-offre-header').style.background = '#FFFBEB';

      fermerModalOffres();
      window.scrollTo({ top: 0, behavior: 'smooth' });
      toast(`Mode édition : ${offre.titre}`, 'info');
    } catch { toast('Erreur réseau.', 'error'); }
  }

  function annulerEditionOffre() {
    offreEnEditionId = null;
    document.getElementById('form-offre').reset();
    document.getElementById('offre-exp').value = '2';
    document.getElementById('btn-creer-offre').innerHTML = '<i class="fa-solid fa-paper-plane"></i> Publier l\'Offre RH';
    document.getElementById('btn-creer-offre').style.background = '';
    document.getElementById('btn-annuler-offre').style.display = 'none';
    document.getElementById('form-offre-title').textContent = 'Créer une Offre d\'Emploi RH';
    document.getElementById('form-offre-header').style.background = '';
  }

  async function supprimerOffreRH(offreId) {
    if (!confirm('Voulez-vous vraiment supprimer cette offre et toutes ses candidatures ?')) return;
    try {
      const res = await fetch(`${API}/offres/${offreId}`, { method: 'DELETE', headers: headers() });
      if (res.ok) {
        toast('Offre supprimée avec succès.', 'success');
        if (offreEnEditionId === offreId) annulerEditionOffre();
        chargerOffres();
        afficherModalOffres();
      } else {
        toast('Erreur lors de la suppression.', 'error');
      }
    } catch { toast('Erreur réseau.', 'error'); }
  }

  async function creerOffre(e) {
    e.preventDefault();
    const btn = document.getElementById('btn-creer-offre');
    btn.disabled = true;
    const isEdit = offreEnEditionId !== null;
    btn.innerHTML = isEdit ? '<i class="fa-solid fa-spinner fa-spin"></i> Sauvegarde...' : '<i class="fa-solid fa-spinner fa-spin"></i> Publication...';

    const payload = {
      titre: document.getElementById('offre-titre').value.trim(),
      description: document.getElementById('offre-desc').value.trim(),
      experience_min_annees: parseInt(document.getElementById('offre-exp').value) || 0,
      competences_obligatoires: document.getElementById('offre-req').value.split(',').map(s => s.trim()).filter(Boolean),
      competences_souhaitees: document.getElementById('offre-opt').value.split(',').map(s => s.trim()).filter(Boolean),
      formation_exigee: 'Non spécifiée',
    };

    try {
      const url = isEdit ? `${API}/offres/${offreEnEditionId}` : `${API}/offres`;
      const method = isEdit ? 'PUT' : 'POST';
      let res = await fetch(url, { method, headers: headers(), body: JSON.stringify(payload) });
      if (res.status === 401) {
        console.warn("Token expiré dans creerOffre, régénération...");
        const ok = await purgerEtObtenirToken();
        if (ok) {
          res = await fetch(url, { method, headers: headers(), body: JSON.stringify(payload) });
        }
      }
      if (res.ok) {
        toast(isEdit ? '✅ Offre modifiée ! Elle est visible dans l\'espace candidat.' : '✅ Offre publiée ! Visible sur le portail candidat.', 'success');
        annulerEditionOffre();
        chargerOffres();
      } else {
        const err = await res.json().catch(() => ({}));
        toast(err.detail || 'Erreur enregistrement.', 'error');
      }
    } catch { toast('Erreur réseau.', 'error'); }
    btn.disabled = false;
  }

  // ── CANDIDATURES ──────────────────────────────────────────────
  async function chargerCandidatures() {
    const selFilter = document.getElementById("select-offre-filter");
    const val = selFilter ? selFilter.value : "ALL";
    const endpoint = (!val || val === "ALL") ? `${API}/candidatures/toutes` : `${API}/offres/${val}/candidatures`;
    try {
      const res = await fetch(endpoint, { headers: headers() });
      if (res.status === 401) {
        console.warn("Token expiré dans chargerCandidatures, régénération...");
        const ok = await purgerEtObtenirToken();
        if (ok) return chargerCandidatures();
      }
      if (res.ok) {
        toutesCandidatures = await res.json();
        document.getElementById("stat-candidats").innerText = toutesCandidatures.length;
        filtrerListe();
      } else {
        toutesCandidatures = [];
        filtrerListe();
      }
    } catch (err) {
      console.error("Erreur chargerCandidatures:", err);
      toutesCandidatures = [];
      filtrerListe();
    }
  }

  function afficherCandidatures(liste) {
    const col = document.getElementById("master-col");
    const q = (document.getElementById("search-cand")?.value || "").trim();
    if (!liste || liste.length === 0) {
      if (q && filtreActif !== 'TOUS') {
        col.innerHTML = `
          <div class="list-empty" style="text-align:center; padding:32px 16px;">
            <i class="fa-solid fa-filter-circle-xmark" style="font-size:28px; color:var(--accent-amber); margin-bottom:8px;"></i>
            <p style="font-weight:700; color:var(--text-primary);">Aucun candidat pour "${q}" dans "${filtreActif === 'ATTENTE' ? 'En Attente RH' : filtreActif}"</p>
            <p style="font-size:12px; color:var(--text-muted); margin-top:6px;">Ce candidat a peut-être déjà été validé ou rejeté.<br>
            Cliquez sur <strong style="color:var(--primary); cursor:pointer; text-decoration:underline;" onclick="filtrer('TOUS', document.querySelector('.pill'))">"Tous"</strong> pour voir l'ensemble des candidats.</p>
          </div>`;
      } else if (q) {
        col.innerHTML = `<div class="list-empty"><i class="fa-solid fa-search"></i><p>Aucun candidat ne correspond à "${q}".</p></div>`;
      } else {
        col.innerHTML = `<div class="list-empty"><i class="fa-solid fa-folder-open"></i><p>Aucune candidature enregistrée pour cette catégorie.</p></div>`;
      }
      return;
    }
    col.innerHTML = "";
    liste.forEach(c => {
      const nom = c.candidat ? (c.candidat.nom || c.candidat.cv_fichier_nom || "Candidat") : "Candidat";
      const score = Math.round(c.score || 0);
      const sc = score >= 70 ? 'score-high' : (score >= 40 ? 'score-mid' : 'score-low');
      const scoreColor = score >= 70 ? 'var(--accent-green)' : (score >= 40 ? 'var(--accent-amber)' : 'var(--accent-red)');

      // ✅ Badge basé sur statut ET decision_rh
      const statut = c.statut || c.decision_rh || 'EN_ATTENTE';
      let badgeHtml = `<span class="badge badge-attente">EN ATTENTE</span>`;
      if (statut === 'ACCEPTE' || c.decision_rh === 'VALIDE') badgeHtml = `<span class="badge badge-valide">✓ ACCEPTÉ</span>`;
      if (statut === 'REFUSE' || c.decision_rh === 'REJETE' || c.statut_ia === 'rejete_auto_filtre') badgeHtml = `<span class="badge badge-rejete">✗ REJETÉ</span>`;
      if (c.decision_rh === 'CORRIGE') badgeHtml = `<span class="badge" style="background:#FEF3C7;color:#92400E;">✏ CORRIGÉ</span>`;

      const email = c.candidat && c.candidat.email ? c.candidat.email : '';

      const row = document.createElement("div");
      row.className = "cand-row" + (candidatureActive && candidatureActive.id === c.id ? " selected" : "");
      row.id = `row-${c.id}`;
      row.onclick = () => afficherDetail(c);
      row.innerHTML = `
        <div class="cand-avatar">${nom.charAt(0).toUpperCase()}</div>
        <div class="cand-info">
          <h3>${nom}</h3>
          <div class="cand-meta">
            <span><i class="fa-solid fa-file-pdf"></i> ${c.candidat ? c.candidat.cv_fichier_nom : ''}</span>
            ${email ? `<span><i class="fa-solid fa-envelope"></i> ${email}</span>` : ''}
            <span><i class="fa-solid fa-clock"></i> ${c.duree_traitement_sec?.toFixed(1)}s</span>
          </div>
        </div>
        <div class="cand-right">
          <div class="score-ring ${sc}" style="--score:${score}">
            <div class="score-ring-inner" style="color:${scoreColor}">${score}</div>
          </div>
          ${badgeHtml}
        </div>
      `;
      col.appendChild(row);
    });
  }

  function afficherDetail(c) {
    candidatureActive = c;
    // Surligner la ligne active
    document.querySelectorAll(".cand-row").forEach(r => r.classList.remove("selected"));
    const row = document.getElementById(`row-${c.id}`);
    if (row) row.classList.add("selected");

    const raw = c.raw_ingestion_json || {};
    const nom = c.candidat ? (c.candidat.nom || c.candidat.cv_fichier_nom || "Candidat") : "Candidat";
    const score = c.score || 0;
    const scoreColor = score >= 70 ? 'var(--accent-green)' : (score >= 40 ? 'var(--accent-amber)' : 'var(--accent-red)');
    const compTags = (raw.competences || []).map(s => `<span class="tag">${s}</span>`).join("");

    let decBtnCls = score >= 70
      ? "style='border-left: 4px solid var(--accent-green);'"
      : (score < 40 ? "style='border-left: 4px solid var(--accent-red);'" : "style='border-left: 4px solid var(--accent-amber);'");

    document.getElementById("detail-col").innerHTML = `
      <div class="detail-section" ${decBtnCls}>
        <h4><i class="fa-solid fa-user"></i> Dossier Candidat</h4>
        <div style="font-size:15px; font-weight:700; color:var(--text-primary); margin-bottom:4px;">${nom}</div>
        <div style="font-size:12px; color:var(--text-muted); margin-bottom:10px;">
          ${c.candidat && c.candidat.email ? `<i class="fa-solid fa-envelope"></i> ${c.candidat.email} &nbsp;` : ""}
          ${c.candidat && c.candidat.telephone ? `<i class="fa-solid fa-phone"></i> ${c.candidat.telephone}` : ""}
        </div>
        <button class="btn btn-primary" style="background:var(--primary); padding:7px 12px; font-size:12px; width:100%; justify-content:center;" onclick="telechargerPDF(${c.id})">
          <i class="fa-solid fa-file-pdf"></i> Télécharger Fiche RH (PDF)
        </button>
      </div>

      <div class="detail-section">
        <h4><i class="fa-solid fa-chart-bar"></i> Scores & Indicateurs</h4>
        <div class="kpi-row">
          <div class="kpi-box">
            <div class="kpi-val" style="color:${scoreColor};">${score}</div>
            <div class="kpi-lbl">Score IA /100</div>
          </div>
          <div class="kpi-box">
            <div class="kpi-val">${raw.experience_annees || 0}</div>
            <div class="kpi-lbl">Années Exp.</div>
          </div>
          <div class="kpi-box">
            <div class="kpi-val" style="font-size:13px;">${(raw.formation || 'N/A').split(' ')[0]}</div>
            <div class="kpi-lbl">Formation</div>
          </div>
        </div>
      </div>

      <div class="detail-section">
        <h4><i class="fa-solid fa-tags"></i> Compétences Détectées (${(raw.competences || []).length})</h4>
        <div class="tags">${compTags || '<span style="color:var(--text-muted);font-size:12px;">Aucune compétence détectée</span>'}</div>
      </div>

      <div class="detail-section">
        <h4><i class="fa-solid fa-robot"></i> Justification IA (Anti-Hallucination)</h4>
        <div class="justif-box">${c.justification_ia || 'Aucune justification disponible.'}</div>
      </div>

      <div class="detail-section">
        <h4><i class="fa-solid fa-gavel"></i> Décision Recruteur (Human-in-the-Loop)</h4>
        <div class="decision-btns">
          <button class="btn-dec btn-valide" onclick="ouvrirModalConvocation()"><i class="fa-solid fa-calendar-check"></i> Valider & Convoquer</button>
          <button class="btn-dec btn-corrige" onclick="prendreDecision('CORRIGE')"><i class="fa-solid fa-pen"></i> Corriger</button>
          <button class="btn-dec btn-rejete" onclick="prendreDecision('REJETE')"><i class="fa-solid fa-times"></i> Rejeter</button>
        </div>
        <input type="text" id="note-rh" class="note-input" placeholder="Ajouter une note RH (optionnel)...">
      </div>
    `;
  }

  function ouvrirModalConvocation() {
    if (!candidatureActive) return;
    const nom = candidatureActive.candidat ? (candidatureActive.candidat.nom || candidatureActive.candidat.cv_fichier_nom || "Candidat") : "Candidat";
    const email = candidatureActive.candidat ? (candidatureActive.candidat.email || "candidat@email.com") : "candidat@email.com";
    document.getElementById("conv-candidat-info").value = `${nom} (${email})`;
    
    // Date par défaut : Demain à 10h00
    const demain = new Date();
    demain.setDate(demain.getDate() + 1);
    demain.setHours(10, 0, 0, 0);
    const isoString = new Date(demain.getTime() - (demain.getTimezoneOffset() * 60000)).toISOString().slice(0, 16);
    document.getElementById("conv-datetime").value = isoString;

    document.getElementById("modal-convocation").style.display = "flex";
  }

  function fermerModalConvocation() {
    document.getElementById("modal-convocation").style.display = "none";
  }

  function changerFormatEntretien(val) {
    const inputLieu = document.getElementById("conv-lieu");
    if (val === 'VISIO') {
      inputLieu.value = "https://meet.google.com/artiweb-rh-interview";
    } else {
      inputLieu.value = "Bureaux ArtiWeb, Fès";
    }
  }

  async function envoyerConvocation(e) {
    e.preventDefault();
    if (!candidatureActive) return;

    const btn = document.getElementById("btn-send-conv");
    btn.innerHTML = '<span class="spinner"></span> Envoi de l\'email en cours...';
    btn.disabled = true;

    const dtRaw = document.getElementById("conv-datetime").value;
    const dtFormatted = dtRaw ? new Date(dtRaw).toLocaleString('fr-FR', { dateStyle: 'full', timeStyle: 'short' }) : dtRaw;

    const payload = {
      date_heure: dtFormatted,
      format_entretien: document.getElementById("conv-format").value,
      lieu_ou_lien: document.getElementById("conv-lieu").value,
      message_personnalise: document.getElementById("conv-msg").value
    };

    try {
      const res = await fetch(`${API}/candidatures/${candidatureActive.id}/convocation`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify(payload)
      });

      if (res.status === 401) { doLogout(); return; }
      if (res.ok) {
        const data = await res.json();
        toast(`✅ Convocation transmise par e-mail avec succès !`, "success");
        fermerModalConvocation();
        candidatureActive.decision_rh = "VALIDE";
        await chargerCandidatures();
        const updated = toutesCandidatures.find(c => c.id === candidatureActive.id);
        if (updated) afficherDetail(updated);
      } else {
        toast("Erreur lors de l'envoi de la convocation.", "error");
      }
    } catch {
      toast("Erreur réseau.", "error");
    }

    btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Envoyer Convocation Email';
    btn.disabled = false;
  }

  async function telechargerPDF(candId) {
    try {
      toast("📄 Génération du rapport PDF...", "info");
      const res = await fetch(`${API}/candidatures/${candId}/pdf`, { headers: headers() });
      if (res.status === 401) { doLogout(); return; }
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Rapport_RecrutIA_${candId}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        toast("✅ Rapport PDF téléchargé avec succès !", "success");
      } else {
        toast("Erreur lors de la génération du PDF.", "error");
      }
    } catch {
      toast("Erreur réseau.", "error");
    }
  }

  async function prendreDecision(decision) {
    if (!candidatureActive) return;
    const note = document.getElementById("note-rh")?.value || "";
    try {
      const res = await fetch(`${API}/candidatures/${candidatureActive.id}/decision`, {
        method: "PATCH",
        headers: headers(),
        body: JSON.stringify({ decision, note_rh: note, rh_utilisateur: USERNAME })
      });
      if (res.status === 401) { doLogout(); return; }
      if (res.ok) {
        const updated = await res.json();
        const icons = { VALIDE: "✅", CORRIGE: "✏️", REJETE: "❌" };
        const statutMsg = { VALIDE: "ACCEPTÉ", CORRIGE: "CORRIGÉ", REJETE: "REFUSÉ" };
        toast(`${icons[decision]} Candidature ${statutMsg[decision]} — Statut synchronisé !`, "success");
        // ✅ Mettre à jour l'objet local avec la réponse serveur
        const idx = toutesCandidatures.findIndex(c => c.id === candidatureActive.id);
        if (idx !== -1) toutesCandidatures[idx] = updated;
        candidatureActive = updated;
        await chargerCandidatures();
        const refreshed = toutesCandidatures.find(c => c.id === updated.id);
        if (refreshed) afficherDetail(refreshed);
      } else {
        const err = await res.json().catch(() => ({}));
        toast(err.detail || "Erreur lors de la décision.", "error");
      }
    } catch (e) { toast("Erreur réseau lors de la décision.", "error"); }
  }

  // ✅ Télécharger le CV original du candidat
  async function telechargerCV(candId) {
    try {
      toast("📥 Téléchargement du CV en cours...", "info");
      const res = await fetch(`${API}/candidatures/${candId}/cv`, { headers: headers() });
      if (res.status === 401) { doLogout(); return; }
      if (res.ok) {
        const blob = await res.blob();
        const contentDisposition = res.headers.get('Content-Disposition');
        let filename = `CV_candidat_${candId}.pdf`;
        if (contentDisposition) {
          const match = contentDisposition.match(/filename="?([^"\n]+)"?/);
          if (match) filename = match[1];
        }
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = filename;
        document.body.appendChild(a); a.click(); a.remove();
        window.URL.revokeObjectURL(url);
        toast("✅ CV téléchargé avec succès !", "success");
      } else if (res.status === 404) {
        toast("⚠️ CV non disponible (ancienne candidature sans fichier stocké).", "error");
      } else {
        toast("Erreur lors du téléchargement du CV.", "error");
      }
    } catch { toast("Erreur réseau.", "error"); }
  }

  // ── CV UPLOAD (RH) ─────────────────────────────────────────────
  function fileSelected(input) {
    document.getElementById("file-name").innerText = input.files[0] ? "📄 " + input.files[0].name : "";
  }

  async function soumettreCV() {
    const selUpload = document.getElementById("select-offre-upload");
    const offreId = selUpload ? selUpload.value : "";
    const fileInput = document.getElementById("cv-file");
    const nomCand = document.getElementById("cand-nom").value.trim();
    const emailCand = document.getElementById("cand-email").value.trim();

    if (!offreId) { toast("Veuillez choisir l'offre d'emploi visée.", "error"); return; }
    if (!nomCand) { toast("Veuillez saisir le nom du candidat.", "error"); return; }
    if (!emailCand || !emailCand.includes("@")) { toast("Veuillez saisir un email valide.", "error"); return; }
    if (!fileInput.files[0]) { toast("Veuillez choisir un fichier CV (.PDF ou .DOCX).", "error"); return; }

    const btn = document.getElementById("btn-submit-cv");
    btn.innerHTML = '<span class="spinner"></span> Traitement IA en cours...';
    btn.disabled = true;

    const fd = new FormData();
    fd.append("offre_id", offreId);
    fd.append("fichier_cv", fileInput.files[0]);
    fd.append("nom_candidat", nomCand);
    fd.append("email_candidat", emailCand);

    try {
      const authH = TOKEN ? { "Authorization": `Bearer ${TOKEN}` } : {};
      const res = await fetch(`${API}/candidatures`, {
        method: "POST",
        headers: authH,
        body: fd
      });
      if (res.status === 401) { doLogout(); return; }
      if (res.ok) {
        const cand = await res.json();
        toast(`✅ CV analysé — Score IA : ${cand.score}/100`, "success");
        document.getElementById("file-name").innerText = "";
        fileInput.value = "";
        document.getElementById("cand-nom").value = "";
        document.getElementById("cand-email").value = "";
        chargerCandidatures();
      } else {
        const err = await res.json();
        toast(err.detail || "Erreur lors de l'analyse du CV.", "error");
      }
    } catch { toast("Erreur réseau lors de l'envoi du CV.", "error"); }

    btn.innerHTML = '<i class="fa-solid fa-microchip"></i> Lancer l\'Ingestion & le Scoring IA';
    btn.disabled = false;
  }

  // ── FILTRES ───────────────────────────────────────────────────
  function filtrer(type, el) {
    filtreActif = type;
    document.querySelectorAll(".pill").forEach(p => p.classList.remove("active"));
    if (el) el.classList.add("active");
    filtrerListe();
  }

  function filtrerListe() {
    const q = (document.getElementById("search-cand")?.value || "").trim().toLowerCase();
    let liste = toutesCandidatures;

    if (filtreActif === 'EXCELLENT') {
      liste = liste.filter(c => (c.score || 0) >= 70);
    } else if (filtreActif === 'ATTENTE') {
      liste = liste.filter(c => c.decision_rh === 'EN_ATTENTE' || c.statut === 'EN_ATTENTE' || (!c.decision_rh && c.statut_ia !== 'rejete_auto_filtre'));
    } else if (filtreActif === 'REJETE') {
      liste = liste.filter(c => c.statut_ia === 'rejete_auto_filtre' || c.decision_rh === 'REJETE' || c.statut === 'REFUSE');
    }

    if (q) {
      liste = liste.filter(c => {
        const nom = c.candidat ? (c.candidat.nom || c.candidat.cv_fichier_nom || "").toLowerCase() : "";
        const email = c.candidat ? (c.candidat.email || "").toLowerCase() : "";
        const comps = (c.raw_ingestion_json?.competences || []).join(" ").toLowerCase();
        const offre = c.offre ? (c.offre.titre || "").toLowerCase() : "";
        return nom.includes(q) || email.includes(q) || comps.includes(q) || offre.includes(q);
      });
    }
    afficherCandidatures(liste);
  }

  // ── TOAST ─────────────────────────────────────────────────────
  function toast(msg, type = "") {
    const div = document.createElement("div");
    div.className = `toast-msg ${type}`;
    div.innerHTML = msg;
    document.getElementById("toast").appendChild(div);
    setTimeout(() => div.remove(), 3100);
  }

  // ── DRAG & DROP ───────────────────────────────────────────────
  const dz = document.getElementById("drop-zone");
  if (dz) {
    dz.addEventListener("dragover", e => { e.preventDefault(); dz.classList.add("dragover"); });
    dz.addEventListener("dragleave", () => dz.classList.remove("dragover"));
    dz.addEventListener("drop", e => {
      e.preventDefault();
      dz.classList.remove("dragover");
      const file = e.dataTransfer.files[0];
      if (file) {
        document.getElementById("cv-file").files = e.dataTransfer.files;
        document.getElementById("file-name").innerText = "📄 " + file.name;
      }
    });
  }
