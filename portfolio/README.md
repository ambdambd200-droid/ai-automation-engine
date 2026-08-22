# Portfolio — Salim Muhammad

A modern, responsive portfolio website for Salim Muhammad, AI Automation Engineer.

## Features

- **Bilingual** (Arabic RTL + English LTR) with toggle
- **Dark/Light Mode** with system detection
- **Responsive Design** (mobile, tablet, desktop)
- **Modern UI** with glassmorphism + gradient effects
- **Fast** (vanilla HTML/CSS/JS, no framework dependencies)
- **Contact Form** wired to the AI engine webhook
- **SEO Optimized** (Open Graph, Twitter Cards, meta tags)

## Color Palette

Based on **Slate Professional** palette:
- Primary: `#2F4F4F` (Dark slate gray)
- Secondary: `#708090` (Slate gray)
- Accent: `#0EA5E9` (Sky blue)
- Background: `#F5F5F5` / `#FFFFFF` (light) / `#1A202C` (dark)

## Typography

- Arabic: **Cairo** (Google Fonts)
- English: **Inter** (Google Fonts)

## Files

```
portfolio/
├── index.html      # Main page with all sections
├── styles.css      # Complete styling with CSS variables
├── script.js       # Interactivity (nav, theme, language, form)
└── README.md       # This file
```

## Sections

1. **Hero** — Name, headline, CTA, stats
2. **About** — Bio, features grid
3. **Services** — 4 service cards with pricing
4. **Portfolio** — 4 featured projects with overlay
5. **Skills** — 6 categories with tags
6. **Contact** — Info cards + form
7. **Footer** — Links, services, contact

## Deployment

### Option 1: GitHub Pages
1. Push `portfolio/` to a GitHub repo
2. Settings → Pages → Source: `main` branch, `/portfolio` folder
3. Site live at `https://username.github.io/repo-name/`

### Option 2: Netlify
1. Drag & drop `portfolio/` folder to netlify.com/drop
2. Get instant URL

### Option 3: Vercel
1. Install Vercel CLI: `npm i -g vercel`
2. `cd portfolio && vercel --prod`

## Contact Form Integration

The form POSTs to the AI engine webhook:
```
POST {ENGINE_URL}/webhook/contact
```

Body:
```json
{
  "name": "...",
  "email": "...",
  "service": "n8n|ai-agent|bot|python|other",
  "message": "...",
  "timestamp": "ISO-8601"
}
```

If engine is unreachable, falls back to `mailto:` link.

## Customization

Edit the following in `index.html`:
- Name, headline, description (Hero section)
- Bio text (About section)
- Services + pricing
- Portfolio items
- Skills tags
- Contact info

All colors are CSS variables in `:root` — change once, applies everywhere.

## License

© 2026 Salim Muhammad. Personal portfolio.