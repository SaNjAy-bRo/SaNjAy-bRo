#!/usr/bin/env node
// Builds the live "GitHub pulse" card (dark + light) from the GitHub GraphQL API.
// Runs in .github/workflows/profile.yml with the workflow's own GITHUB_TOKEN.
// No dependencies: Node 20+ (global fetch).
//
//   GITHUB_TOKEN=... GH_LOGIN=SaNjAy-bRo GH_ORG=clevercroworg OUT_DIR=dist node scripts/generate-stats.mjs
//   MOCK=1 OUT_DIR=dist node scripts/generate-stats.mjs   # offline preview with fake data

import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const LOGIN = process.env.GH_LOGIN || "SaNjAy-bRo";
const ORG = process.env.GH_ORG || "";
const OUT = process.env.OUT_DIR || "dist";
const TOKEN = process.env.GITHUB_TOKEN;

const SANS = "'Inter','Segoe UI',-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif";
const MONO = "'JetBrains Mono','Fira Code','SFMono-Regular',Consolas,'DejaVu Sans Mono',Menlo,monospace";

const THEMES = {
  dark: { bg0: "#0c0b1d", bg1: "#07070f", text: "#f5f7ff", muted: "#9aa4c7", faint: "#2a2848",
          cyan: "#22d3ee", violet: "#a78bfa", pink: "#f472b6", green: "#34d399", amber: "#fbbf24", tile: "#ffffff", tileOp: 0.04 },
  light: { bg0: "#ffffff", bg1: "#f5f3ff", text: "#0f172a", muted: "#475569", faint: "#e4e1f5",
           cyan: "#0891b2", violet: "#7c3aed", pink: "#db2777", green: "#059669", amber: "#d97706", tile: "#7c3aed", tileOp: 0.05 },
};

const LANG_FRAGMENT = `nodes { isFork languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } } }`;

async function gql(query, variables) {
  const res = await fetch("https://api.github.com/graphql", {
    method: "POST",
    headers: { Authorization: `bearer ${TOKEN}`, "Content-Type": "application/json", "User-Agent": "profile-stats" },
    body: JSON.stringify({ query, variables }),
  });
  const json = await res.json();
  if (!res.ok || json.errors) throw new Error(`GraphQL error: ${res.status} ${JSON.stringify(json.errors || json)}`);
  return json.data;
}

async function load() {
  const userQ = `query($login: String!) {
    user(login: $login) {
      contributionsCollection {
        contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
      }
      repositories(ownerAffiliations: OWNER, privacy: PUBLIC, first: 100) { totalCount ${LANG_FRAGMENT} }
    }
  }`;
  const data = await gql(userQ, { login: LOGIN });
  const user = data.user;
  let orgRepos = null;
  if (ORG) {
    try {
      const orgQ = `query($org: String!) { organization(login: $org) { repositories(privacy: PUBLIC, first: 100) { totalCount ${LANG_FRAGMENT} } } }`;
      orgRepos = (await gql(orgQ, { org: ORG })).organization?.repositories ?? null;
    } catch (e) {
      console.warn(`Skipping org stats: ${e.message}`);
    }
  }
  return { user, orgRepos };
}

function mock() {
  const weeks = [];
  const start = new Date();
  start.setUTCDate(start.getUTCDate() - 364);
  let seed = 11;
  const rnd = () => ((seed = (seed * 9301 + 49297) % 233280) / 233280);
  for (let w = 0; w < 53; w++) {
    const days = [];
    for (let d = 0; d < 7; d++) {
      const dt = new Date(start.getTime() + (w * 7 + d) * 864e5);
      days.push({ date: dt.toISOString().slice(0, 10), contributionCount: rnd() < 0.15 ? 0 : Math.floor(rnd() * 22) });
    }
    weeks.push({ contributionDays: days });
  }
  const total = weeks.flatMap((w) => w.contributionDays).reduce((a, d) => a + d.contributionCount, 0);
  const langs = (pairs) => ({ nodes: [{ isFork: false, languages: { edges: pairs.map(([name, color, size]) => ({ size, node: { name, color } })) } }] });
  return {
    user: { contributionsCollection: { contributionCalendar: { totalContributions: total, weeks } },
            repositories: { totalCount: 2, ...langs([["Kotlin", "#A97BFF", 400000]]) } },
    orgRepos: { totalCount: 44, ...langs([["TypeScript", "#3178c6", 3200000], ["JavaScript", "#f1e05a", 1200000], ["CSS", "#663399", 600000], ["HTML", "#e34c26", 380000], ["Python", "#3572A5", 160000]]) },
  };
}

function summarise({ user, orgRepos }) {
  const cal = user.contributionsCollection.contributionCalendar;
  const days = cal.weeks.flatMap((w) => w.contributionDays).filter((d) => d.date <= new Date().toISOString().slice(0, 10));

  // Streaks (a day with no contributions *today* doesn't break the current streak yet).
  let current = 0;
  let i = days.length - 1;
  if (i >= 0 && days[i].contributionCount === 0) i--;
  for (; i >= 0 && days[i].contributionCount > 0; i--) current++;
  let longest = 0, run = 0;
  for (const d of days) { run = d.contributionCount > 0 ? run + 1 : 0; longest = Math.max(longest, run); }
  const activeDays = days.filter((d) => d.contributionCount > 0).length;

  const weekly = cal.weeks.map((w) => w.contributionDays.reduce((a, d) => a + d.contributionCount, 0)).slice(-52);

  const langMap = new Map();
  for (const repos of [user.repositories, orgRepos]) {
    for (const r of repos?.nodes ?? []) {
      if (r.isFork) continue;
      for (const e of r.languages.edges) {
        const cur = langMap.get(e.node.name) || { size: 0, color: e.node.color || "#8b93a7" };
        cur.size += e.size;
        langMap.set(e.node.name, cur);
      }
    }
  }
  const totalSize = [...langMap.values()].reduce((a, l) => a + l.size, 0) || 1;
  const langs = [...langMap.entries()].sort((a, b) => b[1].size - a[1].size).slice(0, 6)
    .map(([name, l]) => ({ name, color: l.color, pct: (l.size / totalSize) * 100 }));

  return {
    total: cal.totalContributions, current, longest, activeDays, weekly, langs,
    repos: (user.repositories?.totalCount ?? 0) + (orgRepos?.totalCount ?? 0),
  };
}

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const fmt = (n) => n.toLocaleString("en-IN");

function card(s, theme) {
  const c = THEMES[theme];
  const W = 1200, H = 470;
  const tiles = [
    { label: "CONTRIBUTIONS", value: fmt(s.total), sub: "in the last 12 months", col: c.cyan },
    { label: "CURRENT STREAK", value: `${s.current} day${s.current === 1 ? "" : "s"}`, sub: "and counting", col: c.green },
    { label: "LONGEST STREAK", value: `${s.longest} days`, sub: "in the last 12 months", col: c.violet },
    { label: "PUBLIC REPOS", value: fmt(s.repos), sub: ORG ? `mine + @${ORG}` : "on GitHub", col: c.pink },
  ];
  const tw = 265, gap = 18, tx0 = 34;
  const tileSvg = tiles.map((t, i) => {
    const x = tx0 + i * (tw + gap);
    return `<g class="up" style="animation-delay:${(i * 0.12).toFixed(2)}s">
      <rect x="${x}" y="30" width="${tw}" height="118" rx="18" fill="${c.tile}" fill-opacity="${c.tileOp}" stroke="${t.col}" stroke-opacity="0.35"/>
      <rect x="${x}" y="30" width="4" height="118" rx="2" fill="${t.col}"/>
      <text x="${x + 24}" y="62" class="mono" font-size="12" font-weight="700" letter-spacing="2" fill="${c.muted}">${t.label}</text>
      <text x="${x + 22}" y="108" class="sans" font-size="38" font-weight="800" fill="${t.col}">${esc(t.value)}</text>
      <text x="${x + 24}" y="132" class="sans" font-size="13" fill="${c.muted}">${esc(t.sub)}</text>
    </g>`;
  }).join("");

  // Weekly activity bars
  const bx = 34, by = 196, bw = W - 68, bh = 120;
  const max = Math.max(1, ...s.weekly);
  const step = bw / s.weekly.length;
  const bars = s.weekly.map((v, i) => {
    const h = Math.max(3, (v / max) * bh);
    const x = bx + i * step + 2;
    return `<rect class="bar" style="animation-delay:${(i * 0.018).toFixed(3)}s" x="${x.toFixed(1)}" y="${(by + bh - h).toFixed(1)}" width="${(step - 4).toFixed(1)}" height="${h.toFixed(1)}" rx="3" fill="url(#barG)"/>`;
  }).join("");

  // Languages
  const ly = 382;
  let lx = bx;
  const segs = s.langs.map((l, i) => {
    const w = (l.pct / 100) * bw;
    const seg = `<rect x="${lx.toFixed(1)}" y="${ly}" width="${Math.max(w - 3, 2).toFixed(1)}" height="12" rx="6" fill="${l.color}"/>`;
    lx += w;
    return seg;
  }).join("");
  const legend = s.langs.map((l, i) => {
    const x = bx + i * (bw / Math.max(s.langs.length, 1));
    return `<circle cx="${(x + 6).toFixed(1)}" cy="${ly + 42}" r="6" fill="${l.color}"/>
      <text x="${(x + 18).toFixed(1)}" y="${ly + 47}" class="sans" font-size="14" font-weight="600" fill="${c.text}">${esc(l.name)}</text>
      <text x="${(x + 18 + l.name.length * 9.6 + 10).toFixed(1)}" y="${ly + 47}" class="mono" font-size="13" fill="${c.muted}">${l.pct.toFixed(1)}%</text>`;
  }).join("");

  const updated = new Date().toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "Asia/Kolkata" });

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="GitHub stats: ${fmt(s.total)} contributions in the last year, ${s.current}-day current streak, ${s.longest}-day longest streak, ${s.repos} public repositories">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${c.bg0}"/><stop offset="1" stop-color="${c.bg1}"/></linearGradient>
    <linearGradient id="barG" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="${c.violet}"/><stop offset="1" stop-color="${c.cyan}"/></linearGradient>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="${c.cyan}"/><stop offset="0.5" stop-color="${c.violet}"/><stop offset="1" stop-color="${c.pink}"/></linearGradient>
    <clipPath id="cl"><rect x="1" y="1" width="${W - 2}" height="${H - 2}" rx="24"/></clipPath>
  </defs>
  <style>
    .sans { font-family: ${SANS}; }
    .mono { font-family: ${MONO}; }
    .up { animation: up .9s cubic-bezier(.2,.8,.2,1) both; }
    @keyframes up { from { transform: translateY(12px); opacity: 0; } to { transform: none; opacity: 1; } }
    .bar { transform-box: fill-box; transform-origin: bottom; animation: grow 1.2s cubic-bezier(.2,.8,.2,1) both; }
    @keyframes grow { from { transform: scaleY(0); } to { transform: scaleY(1); } }
    .lang { animation: reveal 1.6s cubic-bezier(.2,.8,.2,1) .4s both; }
    @keyframes reveal { from { clip-path: inset(0 100% 0 0); } to { clip-path: inset(0 0 0 0); } }
  </style>
  <g clip-path="url(#cl)"><rect width="${W}" height="${H}" fill="url(#bg)"/></g>
  <rect x="1" y="1" width="${W - 2}" height="${H - 2}" rx="24" fill="none" stroke="url(#edge)" stroke-opacity="0.45"/>
  ${tileSvg}
  <text x="${bx}" y="182" class="mono" font-size="12" font-weight="700" letter-spacing="2" fill="${c.muted}">WEEKLY ACTIVITY · LAST 52 WEEKS</text>
  <text x="${W - 34}" y="182" text-anchor="end" class="mono" font-size="12" fill="${c.muted}">${s.activeDays} active days</text>
  <line x1="${bx}" x2="${bx + bw}" y1="${by + bh + 0.5}" y2="${by + bh + 0.5}" stroke="${c.faint}"/>
  ${bars}
  <text x="${bx}" y="${ly - 14}" class="mono" font-size="12" font-weight="700" letter-spacing="2" fill="${c.muted}">TOP LANGUAGES · PUBLIC REPOS</text>
  <text x="${W - 34}" y="${ly - 14}" text-anchor="end" class="mono" font-size="12" fill="${c.muted}">updated ${updated}</text>
  <rect x="${bx}" y="${ly}" width="${bw}" height="12" rx="6" fill="${c.faint}"/>
  <g class="lang">${segs}</g>
  ${legend}
</svg>
`;
}

const raw = process.env.MOCK ? mock() : await load();
const stats = summarise(raw);
mkdirSync(OUT, { recursive: true });
for (const theme of Object.keys(THEMES)) {
  const file = join(OUT, `pulse-${theme}.svg`);
  writeFileSync(file, card(stats, theme));
  console.log(`wrote ${file}`);
}
console.log(JSON.stringify({ ...stats, weekly: `${stats.weekly.length} weeks` }));
