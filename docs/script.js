/**
 * Digital Grove Portfolio — Interactive JavaScript
 * Animations: Welcome sequence, streaming text, typing indicator, counter animations,
 * scroll reveal, trunk growth, icon interactions, cursor particles, theme/language toggle,
 * form handling, back to top
 */

// ========================================
// CONFIGURATION
// ========================================

const CONFIG = {
  streamingText: {
    speed: 40, // ms per character
    pauseAtEnd: 3000,
    loop: true
  },
  counter: {
    duration: 2500,
    easing: 'easeOutCubic'
  },
  themeTransition: {
    duration: 500
  },
  scrollAnimation: {
    threshold: 0.15,
    rootMargin: '0px 0px -80px 0px'
  },
  particles: {
    count: 30,
    size: { min: 2, max: 5 },
    speed: { min: 8, max: 20 }
  },
  cursorParticles: {
    maxParticles: 15,
    lifetime: 800
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
      element.textContent = Math.round(value).toLocaleString('ar-EG');
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

function getRandom(min, max) {
  return Math.random() * (max - min) + min;
}

function createElement(tag, className, attributes = {}) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  Object.entries(attributes).forEach(([key, value]) => el.setAttribute(key, value));
  return el;
}

// ========================================
// WELCOME ANIMATION MANAGER
// ========================================

const WelcomeManager = {
  init() {
    this.overlay = $('#welcomeOverlay');
    this.skipBtn = $('#welcomeSkip');
    this.welcomeSvg = $('.welcome-svg');
    this.trunkPath = $('#trunkPath');
    this.branchPaths = $$('.branch-draw');
    this.leaves = $$('.leaf');
    this.welcomeText = $('.welcome-text');
    this.welcomeSubtext = $('.welcome-subtext');
    this.skipRequested = false;

    // Check if user already saw welcome this session
    if (sessionStorage.getItem('welcomeShown')) {
      this.hide();
      return;
    }

    this.bindEvents();
    this.handleSkipTimeout();
  },

  bindEvents() {
    this.skipBtn?.addEventListener('click', () => this.skip());
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' || e.key === ' ') this.skip();
    });
    document.addEventListener('click', (e) => {
      if (!this.skipRequested && e.target !== this.skipBtn) {
        this.skip();
      }
    }, { once: true });
  },

  handleSkipTimeout() {
    // Auto-hide after welcome animation completes (~3.5s)
    setTimeout(() => {
      if (!this.skipRequested) this.hide();
    }, 3500);
  },

  skip() {
    this.skipRequested = true;
    this.hide();
  },

  hide() {
    this.overlay?.classList.add('hidden');
    sessionStorage.setItem('welcomeShown', 'true');
    
    // Trigger hero entrance after welcome
    setTimeout(() => {
      this.startHeroAnimations();
    }, 500);
  },

  startHeroAnimations() {
    // Start streaming text
    const heroDesc = $('#heroDescription');
    if (heroDesc && !heroDesc.classList.contains('visible')) {
      heroDesc.classList.add('visible');
      window.streamingText = new StreamingText(heroDesc);
    }

    // Animate counters
    new CounterAnimation().init();
  }
};

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
        this.overlay.classList.remove('active');
      }, CONFIG.themeTransition.duration / 2);
    } else {
      this.html.setAttribute('data-theme', theme);
      localStorage.setItem('theme', theme);
    }
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
      nav: { home: 'الرئيسية', about: 'نبذة عني', services: 'الخدمات', skills: 'المهارات', work: 'أعمالي', contact: 'تواصل' },
      hero: {
        badge: 'متاح للعمل • Available for work',
        greeting: 'مرحباً، أنا',
        name: 'سليم محمد',
        role: 'مهندس أتمتة ذكاء اصطناعي',
        description: 'أبني تدفقات عمل n8n، وكلاء AI، وبوتات تعمل 24/7 — أحوّل العمليات المتكررة إلى أنظمة ذكية توفّر عليك ساعات من العمل اليومي.',
        cta1: 'اطلب مشروعك الآن', cta2: 'شاهد أعمالي'
      },
      services: { title: 'خدماتي', subtitle: 'حلول أتمتة متكاملة تناسب احتياجاتك' },
      skills: { title: 'المهارات', subtitle: 'التقنيات التي أتقنها' },
      work: { title: 'أعمالي', subtitle: 'نماذج من الأعمال التي قمت بتنفيذها' },
      contact: { title: 'تواصل', subtitle: 'لديك مشروع؟ تواصل معي وسأرد عليك خلال 24 ساعة' },
      about: { title: 'من أنا؟', lead: 'أنا سليم محمد، مهندس أتمتة يعمل في مجال الأتمتة الذكية منذ أكثر من عامَين.' },
      workFilter: { all: 'الكل', n8n: 'n8n', 'ai-agent': 'AI Agent', bot: 'Bot', python: 'Python' }
    },
    en: {
      nav: { home: 'Home', about: 'About', services: 'Services', skills: 'Skills', work: 'Work', contact: 'Contact' },
      hero: {
        badge: 'Available for work',
        greeting: 'Hi, I am',
        name: 'Salim Muhammad',
        role: 'AI Automation Engineer',
        description: 'I build n8n workflows, AI agents, and 24/7 bots — transforming repetitive tasks into smart systems that save you hours every day.',
        cta1: 'Start Your Project', cta2: 'View My Work'
      },
      services: { title: 'Services', subtitle: 'Complete automation solutions for your needs' },
      skills: { title: 'Skills', subtitle: 'Technologies I master' },
      work: { title: 'Portfolio', subtitle: 'Selected projects I have built' },
      contact: { title: 'Contact', subtitle: 'Have a project? Reach out — I reply within 24 hours' },
      about: { title: 'About Me', lead: 'I am Salim Muhammad, an Automation Engineer working in AI automation for over 2 years.' },
      workFilter: { all: 'All', n8n: 'n8n', 'ai-agent': 'AI Agent', bot: 'Bot', python: 'Python' }
    }
  },

  init() {
    this.html = document.documentElement;
    this.toggle = $('#langToggle');
    this.icon = $('.lang-icon', this.toggle);
    this.currentLang = localStorage.getItem('salim-portfolio-lang') || 'en';
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
      '#skills': t.nav.skills,
      '#work': t.nav.work,
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
      '#skills': { title: t.skills.title, subtitle: t.skills.subtitle },
      '#work': { title: t.work.title, subtitle: t.work.subtitle },
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

    // Update hero
    if (t.hero) {
      const badge = $('.hero-badge .badge-text');
      if (badge) badge.textContent = ' ' + t.hero.badge;

      const greeting = $('.hero-greeting');
      if (greeting) greeting.textContent = t.hero.greeting;

      const name = $('.hero-name');
      if (name) name.textContent = t.hero.name;

      const role = $('.hero-role');
      if (role) role.textContent = t.hero.role;

      // Restart streaming text
      if (window.streamingText) {
        window.streamingText.updateText(t.hero.description);
      }

      const cta1 = $('.hero-cta .btn-primary span');
      const cta2 = $('.hero-cta .btn-secondary span');
      if (cta1) cta1.textContent = t.hero.cta1;
      if (cta2) cta2.textContent = t.hero.cta2;
    }

    // Update filter buttons
    $$('.filter-btn').forEach(btn => {
      const filter = btn.dataset.filter;
      if (t.workFilter[filter]) btn.textContent = t.workFilter[filter];
    });

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
    this.fullText = this.element.getAttribute('data-text') || this.element.textContent || 'أبني تدفقات عمل n8n، وكلاء AI، وبوتات تعمل 24/7 — أحوّل العمليات المتكررة إلى أنظمة ذكية توفّر عليك ساعات من العمل اليومي.';
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
// TRUNK GROWTH ANIMATION
// ========================================

class TrunkGrowth {
  init() {
    this.trunks = $$('.main-trunk path');
    this.nodes = $$('.main-trunk circle');
    
    this.observer = new IntersectionObserver(
      entries => this.handleIntersection(entries),
      { threshold: 0.3 }
    );
    
    this.trunks.forEach(trunk => this.observer.observe(trunk.parentElement));
    this.nodes.forEach(node => this.observer.observe(node.parentElement));
  }

  handleIntersection(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const trunk = entry.target.querySelector('path');
        const nodes = entry.target.querySelectorAll('circle');
        
        if (trunk) {
          trunk.style.animation = 'trunkGrow 1.5s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards';
        }
        
        nodes.forEach((node, index) => {
          node.style.animation = `nodeAppear 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards`;
          node.style.animationDelay = `${index * 0.15}s`;
        });
        
        this.observer.unobserve(entry.target);
      }
    });
  }
}

// ========================================
// PORTFOLIO/WORK FILTER
// ========================================

class PortfolioFilter {
  init() {
    this.buttons = $$('.filter-btn');
    this.items = $$('.portfolio-item, .work-item');
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
          item.style.transform = 'scale(1) translateX(0)';
        });
      } else {
        item.style.opacity = '0';
        item.style.transform = 'scale(0.95) translateX(-20px)';
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
    $$('.section-header, .service-card, .work-item, .skill-category, .contact-card, .feature-item, .about-image, .about-text, .hero-content, .about-content > *').forEach(el => {
      el.classList.add('fade-in');
      this.observer.observe(el);
    });

    // Observe stagger grids
    $$('.services-branches, .skills-branches, .work-branches, .hero-stats, .about-features, .skills-branches > *').forEach(el => {
      el.classList.add('stagger-in');
      this.observer.observe(el);
    });

    // Observe trunk elements
    $$('.trunk-center').forEach(el => {
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
// ICON INTERACTIONS
// ========================================

class IconInteractions {
  init() {
    // Service card icons
    $$('.service-card').forEach(card => {
      const icon = card.querySelector('.service-icon');
      if (!icon) return;

      card.addEventListener('mouseenter', () => this.animateIcon(icon, 'grow'));
      card.addEventListener('mouseleave', () => this.animateIcon(icon, 'reset'));
      card.addEventListener('touchstart', () => this.animateIcon(icon, 'grow'), { passive: true });
      card.addEventListener('touchend', () => this.animateIcon(icon, 'reset'), { passive: true });
    });

    // Skill tag leaf icons
    $$('.skill-tag').forEach(tag => {
      const leaf = tag.querySelector('.leaf-icon svg');
      if (!leaf) return;

      tag.addEventListener('mouseenter', () => {
        leaf.style.animation = 'leafPulse 0.4s ease-out';
      });
      tag.addEventListener('mouseleave', () => {
        leaf.style.animation = '';
      });
    });

    // Work item icons
    $$('.work-placeholder svg').forEach(svg => {
      const item = svg.closest('.work-item');
      if (!item) return;

      item.addEventListener('mouseenter', () => {
        svg.style.transform = 'scale(1.05)';
        svg.style.transition = 'transform 0.3s ease-out';
      });
      item.addEventListener('mouseleave', () => {
        svg.style.transform = 'scale(1)';
      });
    });

    // Contact icons
    $$('.contact-card').forEach(card => {
      const icon = card.querySelector('.contact-icon');
      if (!icon) return;

      card.addEventListener('mouseenter', () => this.animateIcon(icon, 'bounce'));
      card.addEventListener('mouseleave', () => this.animateIcon(icon, 'reset'));
    });

    // Feature icons
    $$('.feature-item').forEach(item => {
      const icon = item.querySelector('.feature-icon');
      if (!icon) return;

      item.addEventListener('mouseenter', () => this.animateIcon(icon, 'rotate'));
      item.addEventListener('mouseleave', () => this.animateIcon(icon, 'reset'));
    });

    // Floating badge
    const floatingBadge = $('.floating-badge');
    if (floatingBadge) {
      floatingBadge.addEventListener('mouseenter', () => {
        floatingBadge.style.animation = 'none';
        floatingBadge.style.transform = 'translateY(-12px) scale(1.02)';
      });
      floatingBadge.addEventListener('mouseleave', () => {
        floatingBadge.style.animation = 'badgeFloat 4s ease-in-out infinite';
      });
    }

    // Scroll indicator
    const scrollIndicator = $('.scroll-indicator');
    if (scrollIndicator) {
      scrollIndicator.addEventListener('click', () => {
        const aboutSection = $('#about');
        if (aboutSection) {
          aboutSection.scrollIntoView({ behavior: 'smooth' });
        }
      });
    }
  },

  animateIcon(icon, type) {
    switch (type) {
      case 'grow':
        icon.style.transform = 'scale(1.15) rotate(-5deg)';
        icon.style.transition = 'transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)';
        break;
      case 'bounce':
        icon.style.transform = 'scale(1.2)';
        icon.style.transition = 'transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)';
        break;
      case 'rotate':
        icon.style.transform = 'rotate(8deg) scale(1.1)';
        icon.style.transition = 'transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)';
        break;
      case 'reset':
        icon.style.transform = 'scale(1) rotate(0deg)';
        icon.style.transition = 'transform 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
        break;
    }
  }
}

// ========================================
// CURSOR PARTICLES
// ========================================

class CursorParticles {
  init() {
    this.container = $('#cursorParticles');
    if (!this.container) return;

    this.particles = [];
    this.mouseX = 0;
    this.mouseY = 0;
    this.lastSpawn = 0;

    // Create particles on mouse move
    document.addEventListener('mousemove', throttle((e) => {
      this.mouseX = e.clientX;
      this.mouseY = e.clientY;
      this.spawnParticle();
    }, 50));

    // Touch support
    document.addEventListener('touchmove', throttle((e) => {
      const touch = e.touches[0];
      if (touch) {
        this.mouseX = touch.clientX;
        this.mouseY = touch.clientY;
        this.spawnParticle();
      }
    }, 80), { passive: true });

    this.animate();
  },

  spawnParticle() {
    const now = Date.now();
    if (now - this.lastSpawn < 60) return;
    this.lastSpawn = now;

    const particle = document.createElement('div');
    particle.className = 'cursor-particle';
    const size = getRandom(2, 5);
    const color = Math.random() > 0.5 ? '#6B8F3C' : '#D8952B';
    const angle = getRandom(0, Math.PI * 2);
    const velocity = getRandom(20, 60);

    particle.style.cssText = `
      position: absolute;
      width: ${size}px;
      height: ${size}px;
      background: ${color};
      border-radius: 50%;
      left: ${this.mouseX}px;
      top: ${this.mouseY}px;
      pointer-events: none;
      opacity: 0.8;
    `;

    this.container.appendChild(particle);
    this.particles.push({ el: particle, angle, velocity, x: this.mouseX, y: this.mouseY, born: Date.now() });

    // Limit particles
    if (this.particles.length > CONFIG.cursorParticles.maxParticles) {
      const old = this.particles.shift();
      if (old.el.parentNode) old.el.remove();
    }
  },

  animate() {
    const now = Date.now();

    this.particles.forEach((p, index) => {
      const age = now - p.born;
      const progress = age / CONFIG.cursorParticles.lifetime;

      if (progress >= 1) {
        if (p.el.parentNode) p.el.remove();
        this.particles.splice(index, 1);
        return;
      }

      const moveX = Math.cos(p.angle) * p.velocity * (progress * 0.5);
      const moveY = Math.sin(p.angle) * p.velocity * (progress * 0.5) + age * 0.05;

      p.el.style.transform = `translate(${moveX}px, ${moveY}px)`;
      p.el.style.opacity = (1 - progress) * 0.8;
    });

    requestAnimationFrame(() => this.animate());
  }
}

// ========================================
// SOIL PARTICLES (Hero Background)
// ========================================

class SoilParticles {
  init() {
    this.container = $('#soilParticles');
    if (!this.container) return;

    this.particles = [];
    this.createParticles();
    this.animate();
  },

  createParticles() {
    for (let i = 0; i < CONFIG.particles.count; i++) {
      const particle = document.createElement('div');
      const size = getRandom(CONFIG.particles.size.min, CONFIG.particles.size.max);
      const color = Math.random() > 0.5 ? '#B8AE9A' : '#D8952B';
      const startX = getRandom(0, 100);
      const startY = getRandom(0, 100);
      const speed = getRandom(CONFIG.particles.speed.min, CONFIG.particles.speed.max);
      const direction = Math.random() > 0.5 ? 1 : -1;

      particle.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        background: ${color};
        border-radius: 50%;
        opacity: ${getRandom(0.1, 0.3)};
        left: ${startX}%;
        top: ${startY}%;
        pointer-events: none;
        transition: transform ${speed}s linear, opacity ${speed}s linear;
      `;

      this.container.appendChild(particle);
      this.particles.push({ el: particle, speed, direction, x: startX, y: startY });
    }
  },

  animate() {
    this.particles.forEach(p => {
      const moveX = (Math.random() - 0.5) * 8;
      const moveY = (Math.random() - 0.5) * 8;
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
// FLOATING PARTICLES (Welcome)
// ========================================

class FloatingParticles {
  init() {
    this.container = $('#floatingParticles');
    if (!this.container) return;

    this.particles = [];
    this.createParticles();
    this.animate();
  },

  createParticles() {
    for (let i = 0; i < 15; i++) {
      const particle = document.createElement('div');
      const size = getRandom(3, 8);
      const color = Math.random() > 0.5 ? '#6B8F3C' : '#D8952B';
      const startX = getRandom(10, 90);
      const startY = getRandom(10, 90);

      particle.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        background: ${color};
        border-radius: 50%;
        opacity: ${getRandom(0.3, 0.6)};
        left: ${startX}%;
        top: ${startY}%;
        pointer-events: none;
      `;

      this.container.appendChild(particle);
      this.particles.push({ el: particle, x: startX, y: startY, vx: getRandom(-0.5, 0.5), vy: getRandom(-0.5, 0.5) });
    }
  },

  animate() {
    this.particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;

      // Boundary bounce
      if (p.x <= 5 || p.x >= 95) p.vx *= -1;
      if (p.y <= 5 || p.y >= 95) p.vy *= -1;

      p.el.style.left = `${p.x}%`;
      p.el.style.top = `${p.y}%`;
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
      note.classList.add('success');
      note.style.color = '#6B8F3C';
      note.style.background = 'rgba(107, 143, 60, 0.15)';
      note.style.borderColor = '#6B8F3C';

      setTimeout(() => {
        note.textContent = orig;
        note.classList.remove('success');
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
// EXTERNAL LINK DEPARTURE ANIMATION
// ========================================

const ExternalLinkHandler = {
  init() {
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a[href^="http"], a[href^="mailto:"]');
      if (!link) return;

      const isInternal = link.href.includes(window.location.origin);
      if (isInternal) return;

      e.preventDefault();
      this.animateDeparture(link);
    });
  },

  animateDeparture(link) {
    const button = link.closest('.btn, .contact-link, .contact-links a, .footer-section a');
    
    if (button) {
      // Bloom animation
      button.style.transform = 'scale(1.1)';
      button.style.transition = 'transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)';
      
      // Create bloom particles
      this.createBloomParticles(button);
      
      setTimeout(() => {
        button.style.transform = 'scale(1)';
        window.open(link.href, link.target || '_blank');
      }, 350);
    } else {
      window.open(link.href, link.target || '_blank');
    }
  },

  createBloomParticles(element) {
    const rect = element.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    for (let i = 0; i < 6; i++) {
      const particle = document.createElement('div');
      const angle = (i / 6) * Math.PI * 2;
      const distance = 30;
      
      particle.style.cssText = `
        position: fixed;
        width: 6px;
        height: 6px;
        background: ${i % 2 === 0 ? '#6B8F3C' : '#D8952B'};
        border-radius: 50%;
        left: ${centerX}px;
        top: ${centerY}px;
        pointer-events: none;
        z-index: 9999;
      `;

      document.body.appendChild(particle);

      particle.animate([
        { transform: 'translate(0, 0) scale(1)', opacity: 1 },
        { transform: `translate(${Math.cos(i * Math.PI / 3) * 40}px, ${Math.sin(i * Math.PI / 3) * 40}px) scale(0)`, opacity: 0 }
      ], {
        duration: 500,
        easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)'
      }).onfinish = () => particle.remove();
    }
  }
};

// ========================================
// PROFILE PHOTO MANAGER
// ========================================

const ProfilePhotoManager = {
  init() {
    this.wrapper = $('#profilePhotoWrapper');
    this.placeholder = $('#profilePhotoPlaceholder');
    this.input = $('#profilePhotoInput');
    this.uploadBtn = $('#photoUploadBtn');
    this.photo = $('#profilePhoto');
    this.hint = this.placeholder?.querySelector('.photo-hint');
    
    if (!this.wrapper) return;
    
    this.loadSavedPhoto();
    this.bindEvents();
  },

  bindEvents() {
    // Click on upload button
    this.uploadBtn?.addEventListener('click', (e) => {
      e.stopPropagation();
      this.input?.click();
    });

    // Click on placeholder to upload
    this.placeholder?.addEventListener('click', () => {
      this.input?.click();
    });

    // File input change
    this.input?.addEventListener('change', (e) => this.handleFileSelect(e));

    // Drag and drop
    this.wrapper?.addEventListener('dragover', (e) => this.handleDragOver(e));
    this.wrapper?.addEventListener('dragleave', (e) => this.handleDragLeave(e));
    this.wrapper?.addEventListener('drop', (e) => this.handleDrop(e));

    // Remove photo on double click
    this.photo?.addEventListener('dblclick', () => this.removePhoto());
  },

  handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    this.wrapper.classList.add('drag-over');
  },

  handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    this.wrapper.classList.remove('drag-over');
  },

  handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    this.wrapper.classList.remove('drag-over');
    
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      this.processFile(file);
    }
  },

  handleFileSelect(e) {
    const file = e.target.files[0];
    if (file && file.type.startsWith('image/')) {
      this.processFile(file);
    }
    // Reset input value to allow selecting same file again
    e.target.value = '';
  },

  processFile(file) {
    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      this.showNotification('Photo too large. Maximum size is 5MB.', 'error');
      return;
    }

    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
    if (!allowedTypes.includes(file.type)) {
      this.showNotification('Invalid file type. Please use JPG, PNG, WebP, or GIF.', 'error');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const dataUrl = e.target.result;
      this.setPhoto(dataUrl);
      this.savePhoto(dataUrl);
      this.showNotification('Profile photo updated!', 'success');
    };
    reader.onerror = () => {
      this.showNotification('Failed to read file.', 'error');
    };
    reader.readAsDataURL(file);
  },

  setPhoto(dataUrl) {
    this.photo.src = dataUrl;
    this.photo.style.display = 'block';
    this.placeholder.style.display = 'none';
    this.wrapper.classList.add('has-photo');
    
    // Animate photo appearance
    this.photo.style.opacity = '0';
    this.photo.style.transform = 'scale(0.8)';
    requestAnimationFrame(() => {
      this.photo.style.transition = 'opacity 0.4s cubic-bezier(0.34, 1.56, 0.64, 1), transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)';
      this.photo.style.opacity = '1';
      this.photo.style.transform = 'scale(1)';
    });
  },

  removePhoto() {
    this.photo.src = '';
    this.photo.style.display = 'none';
    this.placeholder.style.display = 'flex';
    this.wrapper.classList.remove('has-photo');
    this.removeSavedPhoto();
    this.showNotification('Profile photo removed', 'info');
  },

  savePhoto(dataUrl) {
    try {
      localStorage.setItem('salim-profile-photo', dataUrl);
    } catch (e) {
      console.warn('Could not save photo to localStorage:', e);
    }
  },

  loadSavedPhoto() {
    try {
      const saved = localStorage.getItem('salim-profile-photo');
      if (saved) {
        this.setPhoto(saved);
      }
    } catch (e) {
      console.warn('Could not load photo from localStorage:', e);
    }
  },

  removeSavedPhoto() {
    try {
      localStorage.removeItem('salim-profile-photo');
    } catch (e) {
      console.warn('Could to remove photo from localStorage:', e);
    }
  },

  showNotification(message, type = 'info') {
    // Remove existing notification
    const existing = $('.photo-notification');
    if (existing) existing.remove();

    const notification = document.createElement('div');
    notification.className = `photo-notification photo-notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
      position: fixed;
      bottom: 100px;
      left: 50%;
      transform: translateX(-50%) translateY(100px);
      padding: 12px 24px;
      border-radius: 50px;
      font-size: 14px;
      font-weight: 500;
      z-index: 1000;
      opacity: 0;
      transform: translateX(-50%) translateY(100px);
      transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
      box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    `;

    const colors = {
      success: '#6B8F3C',
      error: '#B14C2E',
      info: '#6B8F3C',
      warning: '#D8952B'
    };
    notification.style.background = colors[type] || colors.info;
    notification.style.color = '#1B1712';

    document.body.appendChild(notification);

    requestAnimationFrame(() => {
      notification.style.opacity = '1';
      notification.style.transform = 'translateX(-50%) translateY(0)';
    });

    setTimeout(() => {
      notification.style.opacity = '0';
      notification.style.transform = 'translateX(-50%) translateY(100px)';
      setTimeout(() => notification.remove(), 400);
    }, 3000);
  }
};

// ========================================
// PARTICLE BURST SYSTEM (for CTA clicks, etc.)
// ========================================

class ParticleBurst {
  static create(x, y, color = '#D8952B', count = 12) {
    for (let i = 0; i < count; i++) {
      const particle = document.createElement('div');
      const angle = (i / 12) * Math.PI * 2;
      const distance = getRandom(30, 60);
      const size = getRandom(4, 10);
      
      particle.style.cssText = `
        position: fixed;
        width: ${size}px;
        height: ${size}px;
        background: ${color};
        border-radius: 50%;
        left: ${x}px;
        top: ${y}px;
        pointer-events: none;
        z-index: 9999;
        opacity: 1;
      `;

      document.body.appendChild(particle);

      const tx = Math.cos((i / 12) * Math.PI * 2) * getRandom(40, 80);
      const ty = Math.sin((i / 12) * Math.PI * 2) * getRandom(40, 80);

      particle.animate([
        { transform: `translate(0, 0) scale(1) rotate(0deg)`, opacity: 1 },
        { transform: `translate(${tx}px, ${ty}px) scale(0) rotate(${getRandom(-180, 180)}deg)`, opacity: 0 }
      ], {
        duration: getRandom(600, 1000),
        easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)'
      }).onfinish = () => particle.remove();
    }
  }

  static createOnElement(element, color = '#D8952B') {
    const rect = element.getBoundingClientRect();
    const x = rect.left + rect.width / 2;
    const y = rect.top + rect.height / 2;
    this.create(x, y, color);
  }
};

// ========================================
// MAGNETIC BUTTON EFFECT
// ========================================

class MagneticButtons {
  init() {
    this.buttons = $$('.btn, .service-card, .work-item, .skill-category, .contact-card, .feature-item, .filter-btn, .theme-toggle, .lang-toggle, .filter-btn');
    this.bindEvents();
  },

  bindEvents() {
    this.buttons.forEach(btn => {
      btn.addEventListener('mousemove', (e) => this.handleMouseMove(e, btn));
      btn.addEventListener('mouseleave', () => this.handleMouseLeave(btn));
      btn.addEventListener('mousedown', () => this.handleMouseDown(btn));
      btn.addEventListener('mouseup', () => this.handleMouseUp(btn));
      // Touch support
      btn.addEventListener('touchstart', () => this.handleMouseDown(btn), { passive: true });
      btn.addEventListener('touchend', () => this.handleMouseUp(btn), { passive: true });
    });
  },

  handleMouseMove(e, btn) {
    const rect = btn.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    const deltaX = (e.clientX - centerX) * 0.15;
    const deltaY = (e.clientY - centerY) * 0.15;
    
    btn.style.transform = `translate(${deltaX}px, ${deltaY}px) scale(1.02)`;
    btn.style.transition = 'transform 0.1s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
  },

  handleMouseLeave(btn) {
    btn.style.transform = 'translate(0, 0) scale(1)';
    btn.style.transition = 'transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)';
  },

  handleMouseDown(btn) {
    btn.style.transform = 'scale(0.96)';
    btn.style.transition = 'transform 0.1s cubic-bezier(0.34, 1.56, 0.64, 1)';
  },

  handleMouseUp(btn) {
    btn.style.transform = 'scale(1.02)';
    btn.style.transition = 'transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1)';
  }
};

// ========================================
// PARALLAX SCROLL EFFECTS
// ========================================

class ParallaxScroll {
  init() {
    this.elements = $$('[data-parallax]');
    this.bindEvents();
  },

  bindEvents() {
    window.addEventListener('scroll', throttle(() => this.updateParallax(), 16), { passive: true });
  },

  updateParallax() {
    const scrollY = window.pageYOffset;
    
    this.elements.forEach(el => {
      const speed = parseFloat(el.dataset.parallax) || 0.3;
      const rect = el.getBoundingClientRect();
      const viewportCenter = window.innerHeight / 2;
      const elementCenter = rect.top + rect.height / 2;
      const distance = (elementCenter - viewportCenter) * speed;
      
      el.style.transform = `translateY(${distance}px)`;
    });
  }
};

// ========================================
// TEXT REVEAL ANIMATIONS
// ========================================

class TextReveal {
  init() {
    this.elements = $$('[data-text-reveal], .hero-greeting, .hero-name, .hero-role, .section-title, .section-subtitle, .service-title, .service-description, .work-content h4, .work-content p, .skill-category-title, .about-lead, .about-text p');
    this.observer = new IntersectionObserver(
      entries => this.handleIntersection(entries),
      { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
    );
    
    this.elements.forEach((el, index) => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(30px)';
      el.style.transition = 'opacity 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94), transform 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
      el.style.transitionDelay = `${index * 50}ms`;
      this.observer.observe(el);
    });
  },

  handleIntersection(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
        this.observer.unobserve(entry.target);
      }
    });
  }
};

// ========================================
// ENHANCED SCROLL PROGRESS INDICATOR
// ========================================

class ScrollProgress {
  init() {
    this.bar = document.createElement('div');
    this.bar.className = 'scroll-progress-bar';
    this.bar.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 0%;
      height: 3px;
      background: linear-gradient(90deg, #6B8F3C, #D8952B);
      z-index: 9999;
      transition: width 0.1s linear;
      box-shadow: 0 2px 8px rgba(107, 143, 60, 0.4);
    `;
    document.body.appendChild(this.bar);
    
    window.addEventListener('scroll', throttle(() => this.update(), 16), { passive: true });
  },

  update() {
    const scrollTop = window.pageYOffset;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const progress = (scrollTop / docHeight) * 100;
    this.bar.style.width = `${Math.min(100, Math.max(0, progress))}%`;
  }
};

// ========================================
// THEME-AWARE PARTICLE SYSTEM
// ========================================

class ThemeAwareParticles {
  init() {
    this.particles = [];
    this.container = document.createElement('div');
    this.container.className = 'theme-particles';
    this.container.style.cssText = `
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 1;
      overflow: hidden;
    `;
    document.body.appendChild(this.container);
    
    this.createParticles();
    this.animate();
    
    // Recreate on theme change
    const observer = new MutationObserver(() => this.recreateParticles());
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  },

  createParticles() {
    const count = 25;
    for (let i = 0; i < count; i++) {
      this.createParticle();
    }
  },

  createParticle() {
    const particle = document.createElement('div');
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const colors = isDark ? ['#6B8F3C', '#D8952B', '#B8AE9A'] : ['#6B8F3C', '#D8952B', '#F1E9D8'];
    const color = colors[Math.floor(Math.random() * colors.length)];
    const size = getRandom(1, 4);
    const x = getRandom(0, 100);
    const y = getRandom(0, 100);
    const speedX = getRandom(-0.3, 0.3);
    const speedY = getRandom(-0.5, -0.1);
    const opacity = getRandom(0.1, 0.4);

    particle.style.cssText = `
      position: absolute;
      width: ${size}px;
      height: ${size}px;
      background: ${color};
      border-radius: 50%;
      left: ${x}%;
      top: ${y}%;
      opacity: ${opacity};
      pointer-events: none;
      will-change: transform, opacity;
    `;

    this.container.appendChild(particle);
    this.particles.push({ el: particle, x, y, speedX, speedY, opacity });
  },

  recreateParticles() {
    this.particles.forEach(p => p.el.remove());
    this.particles = [];
    this.createParticles();
  },

  animate() {
    this.particles.forEach(p => {
      p.x += p.speedX;
      p.y += p.speedY;

      // Wrap around
      if (p.y < -5) p.y = 105;
      if (p.y > 105) p.y = -5;
      if (p.x < -5) p.x = 105;
      if (p.x > 105) p.x = -5;

      p.el.style.left = `${p.x}%`;
      p.el.style.top = `${p.y}%`;
    });

    requestAnimationFrame(() => this.animate());
  }
};

// ========================================
// SCROLL-TRIGGERED TRUNK GROWTH
// ========================================

class ScrollTrunkGrowth {
  init() {
    this.trunks = $$('.main-trunk path');
    this.initObserver();
  },

  initObserver() {
    this.observer = new IntersectionObserver(
      entries => this.handleIntersection(entries),
      { threshold: 0.2, rootMargin: '0px 0px -100px 0px' }
    );

    $$('.trunk-center').forEach(el => this.observer.observe(el));
  },

  handleIntersection(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const trunk = entry.target.querySelector('.main-trunk path');
        const nodes = entry.target.querySelectorAll('.main-trunk circle');
        
        if (trunk && !trunk.classList.contains('grown')) {
          trunk.classList.add('grown');
          trunk.style.strokeDasharray = trunk.getTotalLength();
          trunk.style.strokeDashoffset = trunk.getTotalLength();
          trunk.style.animation = 'trunkGrow 2s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards';
        }
        
        nodes.forEach((node, index) => {
          if (!node.classList.contains('appeared')) {
            node.classList.add('appeared');
            node.style.animation = `nodeAppear 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards`;
            node.style.animationDelay = `${index * 0.1}s`;
          }
        });

        // Animate branches
        const branchCards = entry.target.parentElement?.querySelectorAll('.service-card, .skill-category, .work-item');
        branchCards?.forEach((card, index) => {
          card.style.animationDelay = `${index * 0.15}s`;
          card.classList.add('animate-in');
        });

        this.observer.unobserve(entry.target);
      }
    });
  }
};

// ========================================
// REDUCED MOTION HANDLER
// ========================================

const ReducedMotionHandler = {
  init() {
    this.mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    this.handleChange = this.handleChange.bind(this);
    this.mediaQuery.addEventListener('change', this.handleChange);
    this.handleChange(this.mediaQuery);
  },

  handleChange(e) {
    const reduced = e.matches;
    document.documentElement.classList.toggle('reduced-motion', reduced);
    
    if (reduced) {
      // Disable all animations
      const style = document.createElement('style');
      style.id = 'reduced-motion-styles';
      style.textContent = `
        .reduced-motion *,
        .reduced-motion *::before,
        .reduced-motion *::after {
          animation-duration: 0.01ms !important;
          animation-iteration-count: 1 !important;
          transition-duration: 0.01ms !important;
        }
      `;
      document.head.appendChild(style);
    } else {
      const style = $('#reduced-motion-styles');
      if (style) style.remove();
    }
  }
};

// ========================================
// INITIALIZATION
// ========================================

document.addEventListener('DOMContentLoaded', () => {
  // Core managers
  WelcomeManager.init();
  ThemeManager.init();
  LanguageManager.init();
  Navigation.init();
  ProfilePhotoManager.init();

  // Animations
  ScrollAnimations.init();
  new TrunkGrowth().init();
  new ScrollTrunkGrowth().init();
  new CounterAnimation().init();

  // Interactive features
  new PortfolioFilter().init();
  new SoilParticles().init();
  new FloatingParticles().init();
  new IconInteractions().init();
  new CursorParticles().init();
  new MagneticButtons().init();
  new ParallaxScroll().init();
  new TextReveal().init();
  new ScrollProgress().init();
  new ThemeAwareParticles().init();
  new ScrollTrunkGrowth().init();
  new ReducedMotionHandler().init();

  // Interactive features
  new PortfolioFilter().init();
  new SoilParticles().init();
  new FloatingParticles().init();
  new IconInteractions().init();
  new CursorParticles().init();
  ContactForm.init();
  BackToTop.init();
  ExternalLinkHandler.init();

  // Streaming text for hero description
  const heroDesc = $('#heroDescription');
  if (heroDesc) {
    heroDesc.setAttribute('data-text', heroDesc.textContent || 'I build n8n workflows, AI agents, and 24/7 bots — turning repetitive tasks into smart systems that save you hours every day.');
    // Streaming text will start after welcome animation
  }

  // Update year
  updateYear();

  // Console easter egg
  console.log('%c🌱 Welcome to Digital Grove', 'color: #6B8F3C; font-size: 24px; font-weight: bold; font-family: Fraunces, serif;');
  console.log('%cI am Salim Muhammad, AI Automation Engineer', 'color: #D8952B; font-size: 16px;');
  console.log('%cContact: salim.muhammad.work@gmail.com', 'color: #B8AE9A; font-size: 14px;');
  console.log('%cStack: n8n • Python • AI Agents • Telegram/WhatsApp Bots', 'color: #6B8F3C; font-size: 13px;');

  // Handle page visibility for theme transition
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
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
    TrunkGrowth,
    PortfolioFilter,
    Navigation,
    ScrollAnimations,
    SoilParticles,
    FloatingParticles,
    IconInteractions,
    CursorParticles,
    ContactForm,
    BackToTop,
    ExternalLinkHandler
  };
}