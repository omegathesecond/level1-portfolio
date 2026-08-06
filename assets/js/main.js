/* ============================================================
   BONZINILABS LTD — site scripts
   Mobile navigation, EN/FR translation, contact form (mailto).
   No dependencies, no tracking, no backend.
   ============================================================ */

(function () {
  "use strict";

  var CONTACT_EMAIL = "contact@bonzinilabs.com";

  /* ---------- Current year in the footer ---------- */
  var yearEl = document.getElementById("year");
  if (yearEl) {
    yearEl.textContent = String(new Date().getFullYear());
  }

  /* ---------- Mobile navigation ---------- */
  var nav = document.getElementById("nav");
  var navToggle = document.getElementById("navToggle");

  function closeNav() {
    if (!nav || !navToggle) return;
    nav.classList.remove("is-open");
    navToggle.setAttribute("aria-expanded", "false");
  }

  if (nav && navToggle) {
    navToggle.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });

    nav.addEventListener("click", function (e) {
      if (e.target.tagName === "A") closeNav();
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeNav();
    });
  }

  /* ---------- Translations (English is the source in the HTML) ---------- */
  var FR = {
    "skip": "Aller au contenu",

    "nav.services": "Services",
    "nav.process": "Notre méthode",
    "nav.about": "À propos",
    "nav.contact": "Contact",
    "cta.contact": "Nous contacter",
    "cta.services": "Voir nos services",

    "hero.eyebrow": "Société britannique spécialisée en IA",
    "hero.title1": "Mettez l'IA au travail",
    "hero.title2": "dans votre entreprise.",
    "hero.sub":
      "BONZINILABS conçoit des agents IA sur mesure, des chatbots intelligents et des systèmes d'automatisation qui répondent à vos clients, prennent en charge les tâches répétitives et relient les outils que vous utilisez déjà.",
    "hero.badge1": "Agents IA sur mesure",
    "hero.badge2": "API WhatsApp Business",
    "hero.badge3": "Automatisation des processus",
    "hero.badge4": "Exclusivement B2B",

    "services.label": "Services",
    "services.title": "Ce que nous construisons pour nos clients",
    "services.intro":
      "Nous livrons des projets logiciels au forfait ou au mois. Chaque mission commence par un cadrage détaillé et se termine par un système que votre équipe maîtrise et exploite.",

    "svc1.title": "Agents IA sur mesure",
    "svc1.body":
      "Des assistants autonomes entraînés sur vos données, votre ton et vos règles. Ils qualifient vos prospects, rédigent des réponses, résument vos documents et agissent dans vos outils — avec un contrôle humain là où c'est nécessaire.",
    "svc1.li1": "Base de connaissances et questions-réponses sur documents",
    "svc1.li2": "Accès aux outils et API pour des actions réelles",
    "svc1.li3": "Garde-fous, journalisation et transfert à un humain",

    "svc2.title": "Chatbots intelligents",
    "svc2.body":
      "Des assistants orientés client pour votre site web, votre boîte de support ou vos messageries. Ils répondent dans la langue de vos clients, 24h/24, et transmettent proprement à votre équipe lorsqu'un humain est nécessaire.",
    "svc2.li1": "Widget de site web et support multicanal",
    "svc2.li2": "Réponses multilingues issues de vos propres contenus",
    "svc2.li3": "Intégration CRM et service client",

    "svc3.title": "Automatisation WhatsApp Business API",
    "svc3.body":
      "Intégrations officielles de la plateforme WhatsApp Business : conversations automatisées, suivi de commandes, rappels de rendez-vous, notifications et relances de paiement — sur le canal que vos clients utilisent déjà.",
    "svc3.li1": "Configuration Cloud API et modèles de messages",
    "svc3.li2": "Scénarios automatisés avec réponses IA",
    "svc3.li3": "Boîte de réception partagée et statistiques",

    "svc4.title": "Automatisation des processus métier",
    "svc4.body":
      "Nous supprimons les étapes manuelles entre vos systèmes : saisie de données, devis, facturation, reporting, onboarding. Intégrations sur mesure entre votre CRM, vos tableurs, vos e-mails, vos paiements et vos outils internes.",
    "svc4.li1": "Conception et développement des flux automatisés",
    "svc4.li2": "Intégrations d'API et flux de données",
    "svc4.li3": "Supervision, maintenance et support",

    "process.label": "Notre méthode",
    "process.title": "Du premier échange au système en production",
    "step1.title": "Cadrage",
    "step1.body":
      "Nous analysons le processus à automatiser, les outils concernés et le résultat attendu. Vous recevez un périmètre écrit, un prix fixe et un calendrier.",
    "step2.title": "Développement",
    "step2.body":
      "Nous développons et testons la solution par cycles courts, avec une démonstration fonctionnelle à chaque étape. Aucune boîte noire.",
    "step3.title": "Mise en ligne et support",
    "step3.body":
      "Nous déployons, formons votre équipe et supervisons le système. Le support et les améliorations continues sont disponibles en abonnement mensuel.",

    "about.label": "À propos",
    "about.title": "Une société technologique britannique dédiée à l'IA appliquée",
    "about.p1":
      "BONZINILABS LTD est une société de développement logiciel enregistrée en Angleterre et au Pays de Galles, basée à Londres. Nous concevons et développons des outils et des solutions d'automatisation basés sur l'intelligence artificielle pour d'autres entreprises.",
    "about.p2":
      "Nos clients sont des PME qui veulent servir leurs clients plus vite sans augmenter leurs effectifs : agences, marques e-commerce, prestataires de services et acteurs locaux. Nous travaillons à distance avec des clients en Europe et en Afrique, en anglais comme en français.",
    "about.p3":
      "Notre approche est délibérément pragmatique. Nous ne vendons pas de présentations stratégiques : nous livrons des logiciels qui fonctionnent, intégrés aux systèmes que vous utilisez déjà, et nous en restons responsables après la mise en ligne.",
    "about.facts": "Informations légales",
    "about.legal": "Dénomination sociale",
    "about.reg": "Immatriculation",
    "about.regval": "Enregistrée en Angleterre et au Pays de Galles",
    "about.office": "Siège social",
    "about.model": "Modèle économique",
    "about.modelval":
      "Développement logiciel et services d'automatisation B2B, facturés au projet ou au mois",
    "about.email": "E-mail",

    "contact.label": "Contact",
    "contact.title": "Dites-nous ce que vous souhaitez automatiser",
    "contact.intro":
      "Envoyez-nous une courte description de votre projet : nous répondons sous deux jours ouvrés.",
    "contact.emailTitle": "E-mail",
    "contact.addrTitle": "Siège social",
    "contact.hoursTitle": "Horaires",
    "contact.hours": "Du lundi au vendredi, 9h00 – 18h00 (heure du Royaume-Uni)",

    "form.name": "Votre nom",
    "form.email": "Adresse e-mail",
    "form.company": "Entreprise (facultatif)",
    "form.message": "Comment pouvons-nous vous aider ?",
    "form.submit": "Envoyer le message",
    "form.note":
      "Ce formulaire ouvre votre application e-mail avec le message pré-rempli. Vous pouvez aussi écrire directement à contact@bonzinilabs.com.",
    "form.error":
      "Merci d'indiquer votre nom, une adresse e-mail valide et un message.",

    "footer.tag": "L'IA au service des entreprises",
    "footer.reg": "Enregistrée en Angleterre et au Pays de Galles",
    "footer.top": "Retour en haut"
  };

  var translatable = Array.prototype.slice.call(
    document.querySelectorAll("[data-i18n]")
  );

  // Keep the original English strings so switching back is lossless.
  var EN = {};
  translatable.forEach(function (el) {
    EN[el.getAttribute("data-i18n")] = el.textContent;
  });

  var META = {
    en: {
      title:
        "BONZINILABS LTD — AI Automation & Custom AI Agents for Business",
      description:
        "BONZINILABS LTD is a UK software company building AI automation for business: custom AI agents, intelligent chatbots, WhatsApp Business API integrations and business process automation."
    },
    fr: {
      title:
        "BONZINILABS LTD — Automatisation IA et agents IA sur mesure pour entreprises",
      description:
        "BONZINILABS LTD est une société britannique de développement logiciel spécialisée en automatisation par l'IA : agents IA sur mesure, chatbots intelligents, intégrations de l'API WhatsApp Business et automatisation des processus métier."
    }
  };

  function applyLanguage(lang) {
    var dict = lang === "fr" ? FR : EN;

    translatable.forEach(function (el) {
      var key = el.getAttribute("data-i18n");
      var value = lang === "fr" ? dict[key] : EN[key];
      if (typeof value === "string") el.textContent = value;
    });

    document.documentElement.lang = lang;
    document.title = META[lang].title;

    var desc = document.querySelector('meta[name="description"]');
    if (desc) desc.setAttribute("content", META[lang].description);

    document.querySelectorAll(".lang-switch button").forEach(function (btn) {
      var active = btn.getAttribute("data-lang") === lang;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-pressed", active ? "true" : "false");
    });

    try {
      localStorage.setItem("bzl-lang", lang);
    } catch (e) {
      /* storage unavailable — language simply resets on reload */
    }
  }

  document.querySelectorAll(".lang-switch button").forEach(function (btn) {
    btn.addEventListener("click", function () {
      applyLanguage(btn.getAttribute("data-lang"));
    });
  });

  // Restore the saved choice, otherwise follow the browser language.
  var saved = null;
  try {
    saved = localStorage.getItem("bzl-lang");
  } catch (e) {
    saved = null;
  }
  var initial =
    saved ||
    ((navigator.language || "en").toLowerCase().indexOf("fr") === 0 ? "fr" : "en");
  if (initial === "fr") applyLanguage("fr");

  /* ---------- Contact form → pre-filled email ---------- */
  var form = document.getElementById("contactForm");
  var formError = document.getElementById("formError");

  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();

      // form.elements avoids the HTMLFormElement.name / .method name clash
      var f = form.elements;
      var name = f.namedItem("name").value.trim();
      var email = f.namedItem("email").value.trim();
      var company = f.namedItem("company").value.trim();
      var message = f.namedItem("message").value.trim();
      var validEmail = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email);

      if (!name || !validEmail || !message) {
        if (formError) formError.hidden = false;
        return;
      }
      if (formError) formError.hidden = true;

      var isFr = document.documentElement.lang === "fr";
      var subject = (isFr ? "Demande de projet — " : "Project enquiry — ") + name +
        (company ? " (" + company + ")" : "");
      var body =
        (isFr ? "Nom" : "Name") + ": " + name + "\n" +
        (isFr ? "E-mail" : "Email") + ": " + email + "\n" +
        (isFr ? "Entreprise" : "Company") + ": " + (company || "—") + "\n\n" +
        message + "\n";

      window.location.href =
        "mailto:" + CONTACT_EMAIL +
        "?subject=" + encodeURIComponent(subject) +
        "&body=" + encodeURIComponent(body);
    });
  }
})();
