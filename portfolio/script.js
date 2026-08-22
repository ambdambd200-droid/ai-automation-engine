/**
 * Salim Muhammad Portfolio - Interactive JavaScript
 * Handles: Navigation, Theme Toggle, Language Switch, Form Submission, Animations
 * Design System: AI-Native UI (Space Grotesk + Archivo, Purple/Pink palette)
 */

// ========================================
// NAVIGATION
// ========================================
const navbar = document.getElementById('navbar');
const navToggle = document.getElementById('navToggle');
const navMenu = document.getElementById('navMenu');

if (navToggle && navMenu) {
  navToggle.addEventListener('click', () => {
    const isActive = navMenu.classList.toggle('active');
    navToggle.classList.toggle('active');
    navToggle.setAttribute('aria-expanded', isActive);
  });
}

// Close mobile menu when clicking a link
document.querySelectorAll('.nav-link').forEach(link => {
  link.addEventListener('click', () => {
    navMenu?.classList.remove('active');
    navToggle?.classList.remove('active');
    navToggle?.setAttribute('aria-expanded', 'false');
  });
});

// Navbar scroll effect
let lastScroll = 0;
window.addEventListener('scroll', () => {
  const currentScroll = window.pageYOffset;
  if (currentScroll > 50) {
    navbar?.classList.add('scrolled');
  } else {
    navbar?.classList.remove('scrolled');
  }
  lastScroll = currentScroll;
});

// ========================================
// ACTIVE LINK ON SCROLL
// ========================================
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('.nav-link');

function setActiveLink() {
  const scrollY = window.pageYOffset + 100;

  sections.forEach(section => {
    const sectionHeight = section.offsetHeight;
    const sectionTop = section.offsetTop;
    const sectionId = section.getAttribute('id');

    if (scrollY >= sectionTop && scrollY < sectionTop + sectionHeight) {
      navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${sectionId}`) {
          link.classList.add('active');
        }
      });
    }
  });
}

window.addEventListener('scroll', setActiveLink);

// ========================================
// THEME TOGGLE
// ========================================
const themeToggle = document.getElementById('themeToggle');
const html = document.documentElement;

const savedTheme = localStorage.getItem('theme') || 'light';
html.setAttribute('data-theme', savedTheme);
updateThemeIcon(savedTheme);

if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    const current = html.getAttribute('data-theme');
    const newTheme = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
  });
}

function updateThemeIcon(theme) {
  const icon = themeToggle?.querySelector('.theme-icon');
  if (icon) {
    icon.textContent = theme === 'dark' ? '☀️' : '🌙';
  }
}

// ========================================
// LANGUAGE TOGGLE (AR <-> EN)
// ========================================
const langToggle = document.getElementById('langToggle');
const LANG_STORAGE_KEY = 'salim-portfolio-lang';

const translations = {
  ar: {
    nav: { home: 'الرئيسية', about: 'نبذة عني', services: 'الخدمات', portfolio: 'أعمالي', skills: 'المهارات', contact: 'تواصل' },
    hero: {
      badge: 'متاح للعمل • Available for work',
      greeting: 'مرحباً، أنا',
      role: 'مهندس أتمتة ذكاء اصطناعي',
      description: 'أبني تدفقات عمل n8n، وكلاء AI، وبوتات تعمل 24/7 — أحوّل العمليات المتكررة إلى أنظمة ذكية توفّر عليك ساعات من العمل اليومي.',
      cta1: 'اطلب مشروعك الآن', cta2: 'شاهد أعمالي',
    },
    services: { title: 'خدماتي', subtitle: 'حلول أتمتة متكاملة تناسب احتياجاتك' },
    portfolio: { title: 'أعمالي', subtitle: 'نماذج من الأعمال التي قمت بتنفيذها' },
    skills: { title: 'المهارات', subtitle: 'التقنيات التي أتقنها' },
    contact: { title: 'تواصل', subtitle: 'لديك مشروع؟ تواصل معي وسأرد عليك خلال 24 ساعة' }
  },
  en: {
    nav: { home: 'Home', about: 'About', services: 'Services', portfolio: 'Work', skills: 'Skills', contact: 'Contact' },
    hero: {
      badge: 'Available for work',
      greeting: 'Hi, I am',
      role: 'AI Automation Engineer',
      description: 'I build n8n workflows, AI agents, and 24/7 bots — transforming repetitive tasks into smart systems that save you hours every day.',
      cta1: 'Start Your Project', cta2: 'View My Work',
    },
    services: { title: 'Services', subtitle: 'Complete automation solutions for your needs' },
    portfolio: { title: 'Portfolio', subtitle: 'Selected projects I have built' },
    skills: { title: 'Skills', subtitle: 'Technologies I master' },
    contact: { title: 'Contact', subtitle: 'Have a project? Reach out — I reply within 24 hours' }
  }
};

const savedLang = localStorage.getItem(LANG_STORAGE_KEY) || 'ar';
applyLanguage(savedLang);

if (langToggle) {
  langToggle.addEventListener('click', () => {
    const currentLang = html.getAttribute('lang') || 'ar';
    const newLang = currentLang === 'ar' ? 'en' : 'ar';
    applyLanguage(newLang);
    localStorage.setItem(LANG_STORAGE_KEY, newLang);
  });
}

function applyLanguage(lang) {
  html.setAttribute('lang', lang);
  html.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
  document.title = lang === 'ar'
    ? 'سليم محمد | مهندس أتمتة ذكاء اصطناعي'
    : 'Salim Muhammad | AI Automation Engineer';

  const icon = langToggle?.querySelector('.lang-icon');
  if (icon) icon.textContent = lang === 'ar' ? 'EN' : 'AR';

  const t = translations[lang];
  if (!t) return;

  // Nav links
  const navMap = { '#home': t.nav.home, '#about': t.nav.about, '#services': t.nav.services, '#portfolio': t.nav.portfolio, '#skills': t.nav.skills, '#contact': t.nav.contact };
  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (navMap[href]) link.textContent = navMap[href];
  });

  // Section headers
  const sectionHeaders = {
    '#about': { title: 'نبذة عني', subtitle: '' },
    '#services': { title: t.services.title, subtitle: t.services.subtitle },
    '#portfolio': { title: t.portfolio.title, subtitle: t.portfolio.subtitle },
    '#skills': { title: t.skills.title, subtitle: t.skills.subtitle },
    '#contact': { title: t.contact.title, subtitle: t.contact.subtitle }
  };

  Object.entries(sectionHeaders).forEach(([sel, txt]) => {
    const section = document.querySelector(sel);
    if (section) {
      const titleEl = section.querySelector('.section-title');
      const subEl = section.querySelector('.section-subtitle');
      if (titleEl) titleEl.textContent = txt.title;
      if (subEl && txt.subtitle) subEl.textContent = txt.subtitle;
    }
  });

  // Hero
  if (t.hero) {
    const heroBadge = document.querySelector('.hero-badge');
    if (heroBadge && t.hero.badge) heroBadge.lastChild.textContent = ' ' + t.hero.badge;
    const heroGreeting = document.querySelector('.hero-greeting');
    if (heroGreeting) heroGreeting.textContent = t.hero.greeting;
    const heroRole = document.querySelector('.hero-role');
    if (heroRole) heroRole.textContent = t.hero.role;
    const heroDesc = document.querySelector('.hero-description');
    if (heroDesc) heroDesc.textContent = t.hero.description;
    const heroCta1 = document.querySelector('.hero-cta .btn-primary span');
    if (heroCta1) heroCta1.textContent = t.hero.cta1;
    const heroCta2 = document.querySelector('.hero-cta .btn-secondary span');
    if (heroCta2) heroCta2.textContent = t.hero.cta2;
  }
}

// ========================================
// BACK TO TOP
// ========================================
const backToTop = document.getElementById('backToTop');

if (backToTop) {
  window.addEventListener('scroll', () => {
    if (window.pageYOffset > 500) {
      backToTop.classList.add('visible');
    } else {
      backToTop.classList.remove('visible');
    }
  });

  backToTop.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

// ========================================
// CONTACT FORM
// ========================================
const contactForm = document.getElementById('contactForm');

if (contactForm) {
  contactForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const submitBtn = contactForm.querySelector('button[type="submit"]');
    const originalText = submitBtn.querySelector('span').textContent;
    submitBtn.disabled = true;
    submitBtn.querySelector('span').textContent = langToggle?.textContent?.includes('EN') ? 'جاري الإرسال...' : 'Sending...';

    const formData = {
      name: document.getElementById('name').value,
      email: document.getElementById('email').value,
      service: document.getElementById('service').value,
      message: document.getElementById('message').value,
      timestamp: new Date().toISOString(),
    };

    try {
      const ENGINE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:5000'
        : 'https://ai-automation-engine.onrender.com';

      const response = await fetch(`${ENGINE_URL}/webhook/contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        showFormSuccess();
        contactForm.reset();
      } else {
        fallbackMailto(formData);
      }
    } catch (err) {
      fallbackMailto(formData);
    } finally {
      submitBtn.disabled = false;
      submitBtn.querySelector('span').textContent = originalText;
    }
  });
}

function fallbackMailto(data) {
  const subject = encodeURIComponent(`New inquiry from ${data.name}`);
  const body = encodeURIComponent(
    `Name: ${data.name}\n` +
    `Email: ${data.email}\n` +
    `Service: ${data.service || 'Not specified'}\n\n` +
    `Message:\n${data.message}`
  );
  window.location.href = `mailto:salim.muhammad.work@gmail.com?subject=${subject}&body=${body}`;
  showFormSuccess();
}

function showFormSuccess() {
  const note = document.querySelector('.form-note');
  if (note) {
    const orig = note.textContent;
    const isArabic = html.getAttribute('lang') === 'ar';
    note.textContent = isArabic ? '✅ تم إرسال رسالتك بنجاح! سأرد عليك خلال 24 ساعة.' : '✅ Message sent! I will reply within 24 hours.';
    note.style.color = '#10B981';
    setTimeout(() => {
      note.textContent = orig;
      note.style.color = '';
    }, 5000);
  }
}

// Form validation
document.querySelectorAll('.form-group input, .form-group textarea').forEach(input => {
  input.addEventListener('blur', () => {
    if (input.required && !input.value.trim()) {
      input.setAttribute('aria-invalid', 'true');
    } else {
      input.removeAttribute('aria-invalid');
    }
  });
  input.addEventListener('input', () => {
    if (input.hasAttribute('aria-invalid') && input.value.trim()) {
      input.removeAttribute('aria-invalid');
    }
  });
});

// ========================================
// INTERSECTION OBSERVER (Scroll Animations)
// ========================================
const observerOptions = {
  threshold: 0.1,
  rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, observerOptions);

// Add fade-in to sections and cards
document.querySelectorAll('.section-header, .service-card, .portfolio-item, .skill-category, .contact-card, .feature-item, .about-image, .about-text, .hero-content').forEach(el => {
  el.classList.add('fade-in');
  observer.observe(el);
});

// Stagger animation for grids
document.querySelectorAll('.services-grid, .portfolio-grid, .skills-grid, .hero-stats, .about-features').forEach(el => {
  el.classList.add('stagger-in');
  observer.observe(el);
});

// ========================================
// YEAR UPDATE
// ========================================
const yearEl = document.getElementById('year');
if (yearEl) yearEl.textContent = new Date().getFullYear();

// ========================================
// CONSOLE EASTER EGG
// ========================================
console.log('%c👋 Hello there!', 'color: #7C3AED; font-size: 24px; font-weight: bold;');
console.log('%cI am Salim Muhammad, AI Automation Engineer', 'color: #A78BFA; font-size: 16px;');
console.log('%cContact: salim.muhammad.work@gmail.com', 'color: #EC4899; font-size: 14px;');
console.log('%cStack: n8n • Python • AI Agents • Telegram/WhatsApp Bots', 'color: #6366F1; font-size: 13px;');