/**
 * JavaScript Client utilities for Praktika-Tracker (MVP)
 * Author: Сәбитов Азамат (гр. АЖ-47)
 */

// --- Notification Toast Helper ---
function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toastEl = document.createElement("div");
  toastEl.className = `toast align-items-center text-white bg-${type === "error" ? "danger" : type} border-0 show shadow-lg mb-2`;
  toastEl.setAttribute("role", "alert");
  toastEl.setAttribute("aria-live", "assertive");
  toastEl.setAttribute("aria-atomic", "true");

  toastEl.innerHTML = `
    <div class="d-flex">
      <div class="toast-body fs-6">
        <i class="bi ${type === "error" ? "bi-exclamation-triangle-fill" : "bi-check-circle-fill"} me-2"></i>
        ${message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
  `;

  container.appendChild(toastEl);
  setTimeout(() => {
    toastEl.classList.remove("show");
    setTimeout(() => toastEl.remove(), 400);
  }, 4000);
}

// --- Client-side BIN Validation (KGD RK Algorithm) ---
function validateBinLocal(binStr) {
  if (!binStr || typeof binStr !== "string") return { valid: false, message: "БИН должен быть строкой" };
  const clean = binStr.trim();
  if (clean.length !== 12) return { valid: false, message: "Длина БИН должна быть ровно 12 цифр" };
  if (!/^\d{12}$/.test(clean)) return { valid: false, message: "БИН должен содержать только цифры" };

  const digits = clean.split("").map(Number);
  const w1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11];
  let s1 = digits.slice(0, 11).reduce((acc, d, i) => acc + d * w1[i], 0) % 11;
  let control = s1;

  if (s1 === 10) {
    const w2 = [3, 4, 5, 6, 7, 8, 9, 10, 11, 1, 2];
    let s2 = digits.slice(0, 11).reduce((acc, d, i) => acc + d * w2[i], 0) % 11;
    if (s2 < 10) {
      control = s2;
    } else {
      return { valid: false, message: "Контрольный разряд не формируется по правилам КГД РК" };
    }
  }

  if (control !== digits[11]) {
    return { valid: false, message: `Несовпадение контрольного разряда: ожидалось ${control}, указано ${digits[11]}` };
  }
  return { valid: true, message: "БИН корректен и подтвержден (КГД МФ РК)" };
}

// --- Client-side IIN Validation ---
function validateIinLocal(iinStr) {
  if (!iinStr || typeof iinStr !== "string") return { valid: false, message: "ИИН должен быть строкой" };
  const clean = iinStr.trim();
  if (clean.length !== 12) return { valid: false, message: "Длина ИИН должна быть ровно 12 цифр" };
  if (!/^\d{12}$/.test(clean)) return { valid: false, message: "ИИН должен содержать только цифры" };

  const digits = clean.split("").map(Number);
  const w1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11];
  let s1 = digits.slice(0, 11).reduce((acc, d, i) => acc + d * w1[i], 0) % 11;
  let control = s1;

  if (s1 === 10) {
    const w2 = [3, 4, 5, 6, 7, 8, 9, 10, 11, 1, 2];
    let s2 = digits.slice(0, 11).reduce((acc, d, i) => acc + d * w2[i], 0) % 11;
    if (s2 < 10) {
      control = s2;
    } else {
      return { valid: false, message: "Контрольный разряд не формируется по алгоритму" };
    }
  }

  if (control !== digits[11]) {
    return { valid: false, message: `Несовпадение контрольного разряда: ожидалось ${control}, указано ${digits[11]}` };
  }
  return { valid: true, message: "ИИН корректен" };
}

// --- Language Switcher (RU / KZ) ---
const translations = {
  ru: {
    nav_home: "Главная",
    nav_apply: "Подать заявку",
    nav_tracker: "Трекер статуса",
    nav_companies: "Базы практики",
    nav_coordinator: "Панель координатора",
    hero_title: "Автоматизация производственной практики ФИТ ЕНУ им. Л.Н. Гумилева (г. Астана)",
    hero_sub: "Единая платформа подачи заявлений, верификации предприятий по БИН, генерации типовых договоров и сводных приказов деканата.",
  },
  kz: {
    nav_home: "Басты бет",
    nav_apply: "Өтініш беру",
    nav_tracker: "Мәртебе трекері",
    nav_companies: "Тәжірибе базалары",
    nav_coordinator: "Үйлестіруші кабинеті",
    hero_title: "Л.Н. Гумилев атындағы ЕҰУ АТФ өндірістік практикасын автоматтандыру (Астана қ.)",
    hero_sub: "Өтініштерді қабылдау, БСН бойынша кәсіпорындарды тексеру, үлгілік шарттар мен декан бұйрықтарын автоматты түрде қалыптастыру порталы.",
  }
};

function setLanguage(lang) {
  localStorage.setItem("praktika_lang", lang);
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (translations[lang] && translations[lang][key]) {
      el.textContent = translations[lang][key];
    }
  });
  const btnKz = document.getElementById("lang-kz");
  const btnRu = document.getElementById("lang-ru");
  if (btnKz && btnRu) {
    if (lang === "kz") {
      btnKz.classList.add("active");
      btnRu.classList.remove("active");
    } else {
      btnRu.classList.add("active");
      btnKz.classList.remove("active");
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const savedLang = localStorage.getItem("praktika_lang") || "ru";
  setLanguage(savedLang);
});
