/**
 * Salim Muhammad Portfolio - Interactive JavaScript
 * AI-Native UI Design System
 * Features: Streaming text, typing indicators, project filtering, counter animations,
 * theme/language toggle, scroll animations, form handling
 */

// ========================================
// CONFIGURATION
// ========================================
const CONFIG = {
  streamingText: {
    speed: 30, // ms per character
    pauseAtEnd: 2000,
    loop: true
  },
  counter: {
    duration: 2000,
    easing: 'easeOutCubic'
  },
  themeTransition: {
    duration: 400
  },
  scrollAnimation: {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  },
  particles: {
    count: 20,
    size: { min: 2, max: 6 },
    speed: { min: 10, max: 30 }
  }
};

// ========================================
// UTILITY FUNCTIONS
// ========================================

const $ = (selector, context = document) => context.querySelector(selector);
const $$ = (selector, context = document) => [...context.querySelectorAll(selector)];

const easeOutCubic = t => 1 - Math.pow(1 - t, 3);
const easeOutQuart = t => 1 - Math.pow(1 - t, 4);

function animateValue(element, start, end, duration, easing = easeOutCubic) {
  const startTime = performance.now();
  const isInt = Number.isInteger(end);

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = easing(progress);
    const value = start + (end - start) * eased;

    if (isInt) {
      element.textContent = Math.round(value).toLocaleString();
    } else {
      element.textContent = value.toFixed(1);
    }

    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }

  requestAnimationFrame(update);
}

function debounce(fn, delay) {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}

function throttle(fn, limit) {
  let inThrottle;
  return (...args) => {
    if (!inThrottle) {
      fn(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

// ========================================
// THEME MANAGEMENT
// ========================================

const ThemeManager = {
  init() {
    this.html = document.documentElement;
    this.toggle = $('#themeToggle');
    this.sunIcon = $('.sun-icon', this.toggle);
    this.moonIcon = $('.moon-icon', this.toggle);
    this.overlay = $('.theme-transition-overlay');

    const savedTheme = localStorage.getItem('theme') ||
      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');

    this.setTheme(savedTheme, false);
    this.bindEvents();
  },

  setTheme(theme, animate = true) {
    if (animate && this.overlay) {
      this.overlay.classList.add('active');
      setTimeout(() => {
        this.html.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        this.updateIcons(theme);
        this.overlay.classList.remove('active');
      }, CONFIG.themeTransition.duration / 2);
    } else {
      this.html.setAttribute('data-theme', theme);
      localStorage.setItem('theme', theme);
      this.updateIcons(theme);
    }
  },

  updateIcons(theme) {
    // Icons are handled via CSS [data-theme] selectors
  },

  toggle() {
    const current = this.html.getAttribute('data-theme');
    this.setTheme(current === 'dark' ? 'light' : 'dark');
  },

  bindEvents() {
    this.toggle?.addEventListener('click', () => this.toggle());
  }
};

// ========================================
// LANGUAGE MANAGEMENT
// ========================================

const LanguageManager = {
  translations: {
    ar: {
      nav: { home: 'الرئيسية', about: 'نبذة عني', services: 'الخدمات', portfolio: 'أعمالي', skills: 'المهارات', contact: 'تواصل' },
      hero: {
        badge: 'متاح للعمل • Available for work',
        greeting: 'مرحباً، أنا',
        name: 'سليم محمد',
        role: 'مهندس أتمتة ذكاء اصطناعي',
        description: 'أبني تدفقات عمل n8n، وكلاء AI، وبوتات تعمل 24/7 — أحوّل العمليات المتكررة إلى أنظمة ذكية توفّر عليك ساعات من العمل اليومي.',
        cta1: 'اطلب مشروعك الآن', cta2: 'شاهد أعمالي'
      },
      services: { title: 'خدماتي', subtitle: 'حلول أتمتة متكاملة تناسب احتياجاتك' },
      portfolio: { title: 'أعمالي', subtitle: 'نماذج من الأعمال التي قمت بتنفيذها' },
      skills: { title: 'المهارات', subtitle: 'التقنيات التي أتقنها' },
      contact: { title: 'تواصل', subtitle: 'لديك مشروع؟ تواصل معي وسأرد عليك خلال 24 ساعة' },
      about: { title: 'من أنا؟', lead: 'أنا سليم محمد، مهندس أتمتة يعمل في مجال الأتمتة الذكية منذ أكثر من عامَين.' },
      filter: { all: 'الكل', n8n: 'n8n', 'ai-agent': 'AI Agent', bot: 'Bot', python: 'Python' }
    },
    en: {
      nav: { home: 'Home', about: 'About', services: 'Services', portfolio: 'Work', skills: 'Skills', contact: 'Contact' },
      hero: {
        badge: 'Available for work',
        greeting: 'Hi, I am',
        name: 'Salim Muhammad',
        role: 'AI Automation Engineer',
        description: 'I build n8n workflows, AI agents, and 24/7 bots — transforming repetitive tasks into smart systems that save you hours every day.',
        cta1: 'Start Your Project', cta2: 'View My Work'
      },
      services: { title: 'Services', subtitle: 'Complete automation solutions for your needs' },
      portfolio: { title: 'Portfolio', subtitle: 'Selected projects I have built' },
      skills: { title: 'Skills', subtitle: 'Technologies I master' },
      contact: { title: 'Contact', subtitle: 'Have a project? Reach out — I reply within 24 hours' },
      about: { title: 'About Me', lead: 'I am Salim Muhammad, an Automation Engineer working in AI automation for over 2 years.' },
      filter: { all: 'All', n8n: 'n8n', 'ai-agent': 'AI Agent', bot: 'Bot', python: 'Python' }
    }
  },

  init() {
    this.html = document.documentElement;
    this.toggle = $('#langToggle');
    this.icon = $('.lang-icon', this.toggle);
    this.savedLang = localStorage.getItem('salim-portfolio-lang') || 'ar';
    this.currentLang = this.savedLang;
    this.applyLanguage(this.currentLang, false);
    this.bindEvents();
  },

  applyLanguage(lang, animate = true) {
    this.currentLang = lang;
    this.html.setAttribute('lang', lang);
    this.html.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
    localStorage.setItem('salim-portfolio-lang', lang);

    if (this.icon) {
      this.icon.textContent = lang === 'ar' ? 'EN' : 'AR';
    }

    const t = this.translations[lang];
    if (!t) return;

    // Update nav links
    const navMap = {
      '#home': t.nav.home,
      '#about': t.nav.about,
      '#services': t.nav.services,
      '#portfolio': t.nav.portfolio,
      '#skills': t.nav.skills,
      '#contact': t.nav.contact
    };

    $$('.nav-link').forEach(link => {
      const href = link.getAttribute('href');
      if (navMap[href]) link.textContent = navMap[href];
    });

    // Update section headers
    const sections = {
      '#about': { title: t.about.title, subtitle: '' },
      '#services': { title: t.services.title, subtitle: t.services.subtitle },
      '#portfolio': { title: t.portfolio.title, subtitle: t.portfolio.subtitle },
      '#skills': { title: t.skills.title, subtitle: t.skills.subtitle },
      '#contact': { title: t.contact.title, subtitle: t.contact.subtitle }
    };

    Object.entries(sections).forEach(([sel, txt]) => {
      const section = $(sel);
      if (section) {
        const titleEl = section.querySelector('.section-title');
        const subEl = section.querySelector('.section-subtitle');
        if (titleEl) titleEl.textContent = txt.title;
        if (subEl && txt.subtitle) subEl.textContent = txt.subtitle;
      }
    });

    // Update filter buttons
    $$('.filter-btn').forEach(btn => {
      const filter = btn.dataset.filter;
      if (t.filter[filter]) btn.textContent = t.filter[filter];
    });

    // Update hero
    if (t.hero) {
      const badge = $('.hero-badge .badge-text');
      if (badge) badge.textContent = ' ' + t.hero.badge;

      const greeting = $('.hero-greeting');
      if (greeting) greeting.setAttribute('data-text', t.hero.greeting);

      const name = $('.hero-name');
      if (name) name.setAttribute('data-text', t.hero.name);

      const role = $('.hero-role');
      if (role) role.setAttribute('data-text', t.hero.role);

      // Restart streaming text
      if (window.streamingText) {
        window.streamingText.updateText(t.hero.description);
      }

      const cta1 = $('.hero-cta .btn-primary span');
      const cta2 = $('.hero-cta .btn-secondary span');
      if (cta1) cta1.textContent = t.hero.cta1;
      if (cta2) cta2.textContent = t.hero.cta2;
    }

    // Update document title
    document.title = lang === 'ar'
      ? 'سليم محمد | مهندس أتمتة ذكاء اصطناعي'
      : 'Salim Muhammad | AI Automation Engineer';
  },

  toggle() {
    this.applyLanguage(this.currentLang === 'ar' ? 'en' : 'ar');
  },

  bindEvents() {
    this.toggle?.addEventListener('click', () => this.toggle());
  }
};

// ========================================
// STREAMING TEXT ANIMATION
// ========================================

class StreamingText {
  constructor(element, options = {}) {
    this.element = element;
    this.options = { ...CONFIG.streamingText, ...options };
    this.fullText = '';
    this.currentIndex = 0;
    this.isDeleting = false;
    this.typingTimeout = null;
    this.typingIndicator = $('#typingIndicator');
    this.init();
  }

  init() {
    this.fullText = this.element.getAttribute('data-text') || this.element.textContent;
    this.element.textContent = '';
    this.start();
  }

  updateText(newText) {
    this.fullText = newText;
    this.currentIndex = 0;
    this.isDeleting = false;
    this.element.textContent = '';
    if (this.typingTimeout) clearTimeout(this.typingTimeout);
    this.start();
  }

  start() {
    this.type();
  }

  type() {
    if (this.isDeleting) {
      this.currentIndex--;
      this.element.textContent = this.fullText.substring(0, this.currentIndex);
    } else {
      this.currentIndex++;
      this.element.textContent = this.fullText.substring(0, this.currentIndex);
    }

    // Show/hide typing indicator
    if (this.typingIndicator) {
      this.typingIndicator.style.opacity = this.isDeleting ? '0' : '1';
    }

    let speed = this.options.speed;
    const isEnd = this.currentIndex === this.fullText.length;
    const isStart = this.currentIndex === 0;

    if (isEnd && !this.isDeleting) {
      if (this.options.loop) {
        speed = this.options.pauseAtEnd;
        this.isDeleting = true;
      } else {
        if (this.typingIndicator) this.typingIndicator.style.opacity = '0';
        return;
      }
    } else if (isStart && this.isDeleting) {
      this.isDeleting = false;
    }

    this.typingTimeout = setTimeout(() => this.type(), speed);
  }

  destroy() {
    if (this.typingTimeout) clearTimeout(this.typingTimeout);
  }
}

// ========================================
// COUNTER ANIMATION
// ========================================

class CounterAnimation {
  init() {
    this.counters = $$('.stat-number[data-target]');
    this.observer = new IntersectionObserver(
      entries => this.handleIntersection(entries),
      { threshold: 0.5 }
    );
    this.counters.forEach(counter => this.observer.observe(counter));
  }

  handleIntersection(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting && !entry.target.classList.contains('counted')) {
        entry.target.classList.add('counted');
        const target = parseInt(entry.target.dataset.target, 10);
        animateValue(entry.target, 0, target, CONFIG.counter.duration, CONFIG.counter.easing);
      }
    });
  }
}

// ========================================
// PORTFOLIO FILTER
// ========================================

class PortfolioFilter {
  init() {
    this.buttons = $$('.filter-btn');
    this.items = $$('.portfolio-item');
    this.bindEvents();
  }

  bindEvents() {
    this.buttons.forEach(btn => {
      btn.addEventListener('click', () => this.filter(btn.dataset.filter, btn));
    });
  }

  filter(category, activeBtn) {
    // Update active button
    this.buttons.forEach(b => {
      b.classList.remove('active');
      b.setAttribute('aria-selected', 'false');
    });
    activeBtn.classList.add('active');
    activeBtn.setAttribute('aria-selected', 'true');

    // Filter items with animation
    this.items.forEach((item, index) => {
      const categories = item.dataset.category.split(' ');
      const matches = category === 'all' || categories.includes(category);

      if (matches) {
        item.classList.remove('hidden');
        item.style.transitionDelay = `${index * 50}ms`;
        requestAnimationFrame(() => {
          item.style.opacity = '1';
          item.style.transform = 'scale(1)';
        });
      } else {
        item.style.opacity = '0';
        item.style.transform = 'scale(0.95)';
        setTimeout(() => {
          if (!item.classList.contains('hidden')) {
            item.classList.add('hidden');
          }
        }, 300);
      }
    });
  }
}

// ========================================
// NAVIGATION
// ========================================

const Navigation = {
  init() {
    this.navbar = $('#navbar');
    this.navToggle = $('#navToggle');
    this.navMenu = $('#navMenu');
    this.navLinks = $$('.nav-link');
    this.sections = $$('section[id]');
    this.lastScroll = 0;

    this.bindEvents();
    this.handleScroll();
  },

  bindEvents() {
    // Mobile menu toggle
    this.navToggle?.addEventListener('click', () => this.toggleMobileMenu());

    // Close menu on link click
    this.navLinks.forEach(link => {
      link.addEventListener('click', () => this.closeMobileMenu());
    });

    // Scroll events
    window.addEventListener('scroll', throttle(() => this.handleScroll(), 16), { passive: true });
  },

  toggleMobileMenu() {
    const isActive = this.navMenu.classList.toggle('active');
    this.navToggle.classList.toggle('active');
    this.navToggle.setAttribute('aria-expanded', isActive);
    document.body.style.overflow = isActive ? 'hidden' : '';
  },

  closeMobileMenu() {
    this.navMenu.classList.remove('active');
    this.navToggle.classList.remove('active');
    this.navToggle.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  },

  handleScroll() {
    const currentScroll = window.pageYOffset;

    // Navbar scroll effect
    if (currentScroll > 50) {
      this.navbar.classList.add('scrolled');
    } else {
      this.navbar.classList.remove('scrolled');
    }

    // Active link on scroll
    const scrollY = currentScroll + 100;
    this.sections.forEach(section => {
      const sectionHeight = section.offsetHeight;
      const sectionTop = section.offsetTop;
      const sectionId = section.getAttribute('id');

      if (scrollY >= sectionTop && scrollY < sectionTop + sectionHeight) {
        this.navLinks.forEach(link => {
          link.classList.remove('active');
          if (link.getAttribute('href') === `#${sectionId}`) {
            link.classList.add('active');
          }
        });
      }
    });

    this.lastScroll = currentScroll;
  }
};

// ========================================
// SCROLL ANIMATIONS
// ========================================

const ScrollAnimations = {
  init() {
    this.observer = new IntersectionObserver(
      entries => this.handleIntersection(entries),
      CONFIG.scrollAnimation
    );

    // Observe fade-in elements
    $$('.section-header, .service-card, .portfolio-item, .skill-category, .contact-card, .feature-item, .about-image, .about-text, .hero-content').forEach(el => {
      el.classList.add('fade-in');
      this.observer.observe(el);
    });

    // Observe stagger grids
    $$('.services-grid, .portfolio-grid, .skills-grid, .hero-stats, .about-features').forEach(el => {
      el.classList.add('stagger-in');
      this.observer.observe(el);
    });
  },

  handleIntersection(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        this.observer.unobserve(entry.target);
      }
    });
  }
};

// ========================================
// FLOATING PARTICLES
// ========================================

class FloatingParticles {
  init() {
    this.container = $('#floatingParticles');
    if (!this.container) return;

    this.particles = [];
    this.createParticles();
    this.animate();
  }

  createParticles() {
    for (let i = 0; i < CONFIG.particles.count; i++) {
      const particle = document.createElement('div');
      const size = Math.random() * (CONFIG.particles.size.max - CONFIG.particles.size.min) + CONFIG.particles.size.min;
      const color = Math.random() > 0.5 ? '#7C3AED' : '#EC4899';
      const startX = Math.random() * 100;
      const startY = Math.random() * 100;
      const speed = Math.random() * (CONFIG.particles.speed.max - CONFIG.particles.speed.min) + CONFIG.particles.speed.min;
      const direction = Math.random() > 0.5 ? 1 : -1;

      particle.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        background: ${color};
        border-radius: 50%;
        opacity: ${Math.random() * 0.3 + 0.1};
        left: ${startX}%;
        top: ${startY}%;
        pointer-events: none;
        transition: transform ${speed}s linear, opacity ${speed}s linear;
      `;

      this.container.appendChild(particle);
      this.particles.push({ el: particle, speed, direction, x: startX, y: startY });
    }
  }

  animate() {
    this.particles.forEach(p => {
      const moveX = (Math.random() - 0.5) * 10;
      const moveY = (Math.random() - 0.5) * 10;
      const newX = Math.max(0, Math.min(100, p.x + moveX * p.direction));
      const newY = Math.max(0, Math.min(100, p.y + moveY * p.direction));

      p.el.style.transform = `translate(${newX - p.x}%, ${newY - p.y}%)`;
      p.x = newX;
      p.y = newY;
    });

    requestAnimationFrame(() => this.animate());
  }
}

// ========================================
// CONTACT FORM
// ========================================

const ContactForm = {
  init() {
    this.form = $('#contactForm');
    this.submitBtn = this.form?.querySelector('button[type="submit"]');
    this.bindEvents();
  },

  bindEvents() {
    this.form?.addEventListener('submit', e => this.handleSubmit(e));

    // Real-time validation
    $$('.form-group input, .form-group textarea, .form-group select').forEach(input => {
      input.addEventListener('blur', () => this.validateField(input));
      input.addEventListener('input', () => {
        if (input.hasAttribute('aria-invalid') && input.value.trim()) {
          input.removeAttribute('aria-invalid');
        }
      });
    });
  },

  validateField(field) {
    if (field.required && !field.value.trim()) {
      field.setAttribute('aria-invalid', 'true');
      return false;
    }
    if (field.type === 'email' && field.value.trim()) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(field.value)) {
        field.setAttribute('aria-invalid', 'true');
        return false;
      }
    }
    field.removeAttribute('aria-invalid');
    return true;
  },

  async handleSubmit(e) {
    e.preventDefault();

    // Validate all fields
    let isValid = true;
    $$('.form-group input, .form-group textarea', this.form).forEach(field => {
      if (!this.validateField(field)) isValid = false;
    });

    if (!isValid) return;

    const originalText = this.submitBtn.querySelector('span').textContent;
    const isArabic = document.documentElement.getAttribute('lang') === 'ar';

    this.submitBtn.disabled = true;
    this.submitBtn.querySelector('span').textContent = isArabic ? 'جاري الإرسال...' : 'Sending...';

    const formData = {
      name: $('#name').value,
      email: $('#email').value,
      service: $('#service').value,
      message: $('#message').value,
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
        this.showSuccess();
        this.form.reset();
      } else {
        this.fallbackMailto(formData);
      }
    } catch (err) {
      this.fallbackMailto(formData);
    } finally {
      this.submitBtn.disabled = false;
      this.submitBtn.querySelector('span').textContent = originalText;
    }
  },

  fallbackMailto(data) {
    const subject = encodeURIComponent(`New inquiry from ${data.name}`);
    const body = encodeURIComponent(
      `Name: ${data.name}\n` +
      `Email: ${data.email}\n` +
      `Service: ${data.service || 'Not specified'}\n\n` +
      `Message:\n${data.message}`
    );
    window.location.href = `mailto:salim.muhammad.work@gmail.com?subject=${subject}&body=${body}`;
    this.showSuccess();
  },

  showSuccess() {
    const note = $('.form-note');
    if (note) {
      const orig = note.textContent;
      const isArabic = document.documentElement.getAttribute('lang') === 'ar';
      note.textContent = isArabic ? '✅ تم إرسال رسالتك بنجاح! سأرد عليك خلال 24 ساعة.' : '✅ Message sent! I will reply within 24 hours.';
      note.style.color = '#10B981';
      note.style.background = 'rgba(16, 185, 129, 0.1)';
      note.style.borderColor = '#10B981';

      setTimeout(() => {
        note.textContent = orig;
        note.style.color = '';
        note.style.background = '';
        note.style.borderColor = '';
      }, 5000);
    }
  }
};

// ========================================
// BACK TO TOP
// ========================================

const BackToTop = {
  init() {
    this.btn = $('#backToTop');
    if (!this.btn) return;

    window.addEventListener('scroll', throttle(() => {
      if (window.pageYOffset > 500) {
        this.btn.classList.add('visible');
      } else {
        this.btn.classList.remove('visible');
      }
    }, 100));

    this.btn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }
};

// ========================================
// YEAR UPDATE
// ========================================

function updateYear() {
  const yearEl = $('#year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();
}

// ========================================
// INITIALIZATION
// ========================================

document.addEventListener('DOMContentLoaded', () => {
  // Core managers
  ThemeManager.init();
  LanguageManager.init();
  Navigation.init();

  // Animations
  ScrollAnimations.init();
  new CounterAnimation().init();

  // Interactive features
  new PortfolioFilter().init();
  new FloatingParticles().init();
  ContactForm.init();
  BackToTop.init();

  // Streaming text for hero description
  const heroDesc = $('#heroDescription');
  if (heroDesc) {
    heroDesc.setAttribute('data-text', heroDesc.textContent || 'أبني تدفقات عمل n8n، وكلاء AI، وبوتات تعمل 24/7 — أحوّل العمليات المتكررة إلى أنظمة ذكية توفّر عليك ساعات من العمل اليومي.');
    window.streamingText = new StreamingText(heroDesc);
  }

  // Update year
  updateYear();

  // Console easter egg
  console.log('%c👋 Hello there!', 'color: #7C3AED; font-size: 24px; font-weight: bold;');
  console.log('%cI am Salim Muhammad, AI Automation Engineer', 'color: #A78BFA; font-size: 16px;');
  console.log('%cContact: salim.muhammad.work@gmail.com', 'color: #EC4899; font-size: 14px;');
  console.log('%cStack: n8n • Python • AI Agents • Telegram/WhatsApp Bots', 'color: #6366F1; font-size: 13px;');

  // Handle page visibility for theme transition
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      // Ensure theme is consistent
      const savedTheme = localStorage.getItem('theme');
      if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
      }
    }
  });
});

// ========================================
// EXPORTS (for testing)
// ========================================
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    ThemeManager,
    LanguageManager,
    StreamingText,
    CounterAnimation,
    PortfolioFilter,
    Navigation,
    ScrollAnimations,
    FloatingParticles,
    ContactForm,
    BackToTop
  };
}