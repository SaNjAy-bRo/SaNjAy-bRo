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
const MONO = "'JetBrains Mono','SFMono-Regular',Consolas,'Liberation Mono','DejaVu Sans Mono',Menlo,monospace";

const THEMES = {
  dark: { card: "#12161e", line: "#232a36", line2: "#2e3644", ink: "#ece6da", ink2: "#c9c3b6", muted: "#8b93a3", faint: "#566072",
          accent: "#f5a524", green: "#6ee7a8", langs: ["#f5a524", "#e8e2d6", "#9aa3b2", "#c4734f", "#7fa7a0", "#5f6b7e"] },
  light: { card: "#fffdf9", line: "#e5dfd2", line2: "#d9d1c1", ink: "#1b1915", ink2: "#3b3730", muted: "#6f6a60", faint: "#a59f93",
           accent: "#e0791b", green: "#2f9e66", langs: ["#e0791b", "#1b1915", "#6f6a60", "#b4532d", "#4f8278", "#a9a294"] },
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
  const weekStarts = cal.weeks.map((w) => w.contributionDays[0]?.date).slice(-52);

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
    total: cal.totalContributions, current, longest, activeDays, weekly, weekStarts, langs,
    repos: (user.repositories?.totalCount ?? 0) + (orgRepos?.totalCount ?? 0),
  };
}

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const fmt = (n) => n.toLocaleString("en-IN");

function card(s, theme) {
  const c = THEMES[theme];
  const W = 1200, H = 500, P = 36;
  const stats = [
    { label: "CONTRIBUTIONS", value: fmt(s.total), sub: "last 12 months" },
    { label: "CURRENT STREAK", value: `${s.current}`, unit: s.current === 1 ? "day" : "days", sub: "and counting", live: true },
    { label: "LONGEST STREAK", value: `${s.longest}`, unit: "days", sub: "last 12 months" },
    { label: "PUBLIC REPOS", value: fmt(s.repos), sub: ORG ? `mine + @${ORG}` : "on GitHub" },
  ];
  const colw = (W - 2 * P) / 4;
  const statSvg = stats.map((t, i) => {
    const x = P + i * colw + (i ? 28 : 0);
    const valW = t.value.length * 30;
    return `<g class="up" style="animation-delay:${(i * 0.1).toFixed(2)}s">
      ${i ? `<line x1="${P + i * colw}" x2="${P + i * colw}" y1="${P}" y2="${P + 118}" stroke="${c.line}"/>` : ""}
      <text x="${x}" y="${P + 14}" class="mono" font-size="12" letter-spacing="2" fill="${c.muted}"><tspan fill="${c.accent}" font-weight="700">${String(i + 1).padStart(2, "0")}</tspan>  ${t.label}</text>
      <text x="${x - 2}" y="${P + 78}" class="sans" font-size="54" font-weight="800" letter-spacing="-2" fill="${c.ink}">${esc(t.value)}${t.unit ? `<tspan class="sans" font-size="20" font-weight="600" letter-spacing="0" fill="${c.muted}" dx="8">${t.unit}</tspan>` : ""}</text>
      ${t.live ? `<circle class="ping" cx="${x + 4}" cy="${P + 104}" r="3.5" fill="${c.green}"/><circle cx="${x + 4}" cy="${P + 104}" r="3.5" fill="${c.green}"/>` : ""}
      <text x="${x + (t.live ? 16 : 0)}" y="${P + 108}" class="mono" font-size="12" letter-spacing="1.4" fill="${c.faint}">${esc(t.sub.toUpperCase())}</text>
    </g>`;
  }).join("");

  // Weekly activity
  const bx = P, by = 214, bw = W - 2 * P, bh = 120;
  const max = Math.max(1, ...s.weekly);
  const step = bw / s.weekly.length;
  const bars = s.weekly.map((v, i) => {
    const h = Math.max(2, (v / max) * bh);
    const x = bx + i * step + 3;
    const hot = v === max;
    return `<rect class="bar" style="animation-delay:${(i * 0.015).toFixed(3)}s" x="${x.toFixed(1)}" y="${(by + bh - h).toFixed(1)}" width="${(step - 6).toFixed(1)}" height="${h.toFixed(1)}" fill="${hot ? c.accent : c.ink}" fill-opacity="${hot ? 1 : (0.18 + 0.6 * (v / max)).toFixed(2)}"/>`;
  }).join("");
  // month ticks
  const months = [];
  const days = s.weekStarts;
  let last = "";
  days.forEach((d, i) => {
    const m = new Date(d + "T00:00:00Z").toLocaleString("en-US", { month: "short", timeZone: "UTC" }).toUpperCase();
    if (m !== last) {
      if (last) months.push(`<text x="${(bx + i * step + 3).toFixed(1)}" y="${by + bh + 22}" class="mono" font-size="10.5" letter-spacing="1.2" fill="${c.faint}">${m}</text>`);
      last = m;
    }
  });

  // Languages
  const ly = 412;
  let lx = bx;
  const segs = s.langs.map((l, i) => {
    const w = (l.pct / 100) * bw;
    const seg = `<rect x="${lx.toFixed(1)}" y="${ly}" width="${Math.max(w - 3, 2).toFixed(1)}" height="10" fill="${c.langs[i % c.langs.length]}"/>`;
    lx += w;
    return seg;
  }).join("");
  const legend = s.langs.map((l, i) => {
    const x = bx + i * (bw / Math.max(s.langs.length, 1));
    return `<rect x="${x.toFixed(1)}" y="${ly + 30}" width="10" height="10" fill="${c.langs[i % c.langs.length]}"/>
      <text x="${(x + 18).toFixed(1)}" y="${ly + 40}" class="sans" font-size="15" font-weight="600" fill="${c.ink}">${esc(l.name)}</text>
      <text x="${(x + 18 + l.name.length * 9 + 10).toFixed(1)}" y="${ly + 40}" class="mono" font-size="12.5" fill="${c.muted}">${l.pct.toFixed(1)}%</text>`;
  }).join("");

  const updated = new Date().toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "Asia/Kolkata" }).toUpperCase();

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="GitHub stats: ${fmt(s.total)} contributions in the last year, ${s.current}-day current streak, ${s.longest}-day longest streak, ${s.repos} public repositories">
  <style>
    .sans { font-family: ${SANS}; }
    .mono { font-family: ${MONO}; }
    .up { animation: up .9s cubic-bezier(.2,.8,.2,1) both; }
    @keyframes up { from { transform: translateY(10px); opacity: 0; } to { transform: none; opacity: 1; } }
    .bar { transform-box: fill-box; transform-origin: bottom; animation: grow 1.1s cubic-bezier(.2,.8,.2,1) both; }
    @keyframes grow { from { transform: scaleY(0); } to { transform: scaleY(1); } }
    .lang { animation: reveal 1.6s cubic-bezier(.2,.8,.2,1) .3s both; }
    @keyframes reveal { from { clip-path: inset(0 100% 0 0); } to { clip-path: inset(0 0 0 0); } }
    .ping { transform-box: fill-box; transform-origin: center; animation: ping 2s ease-out infinite; }
    @keyframes ping { from { transform: scale(1); opacity: .6; } to { transform: scale(2.8); opacity: 0; } }
  </style>
  <rect x="0.5" y="0.5" width="${W - 1}" height="${H - 1}" rx="16" fill="${c.card}" stroke="${c.line}"/>
  ${statSvg}
  <line x1="${P}" x2="${W - P}" y1="172" y2="172" stroke="${c.line}"/>
  <text x="${bx}" y="200" class="mono" font-size="12" letter-spacing="2" fill="${c.muted}">WEEKLY ACTIVITY · LAST 52 WEEKS</text>
  <text x="${W - P}" y="200" text-anchor="end" class="mono" font-size="12" letter-spacing="1.4" fill="${c.muted}">${s.activeDays} ACTIVE DAYS</text>
  ${bars}
  <line x1="${bx}" x2="${bx + bw}" y1="${by + bh + 0.5}" y2="${by + bh + 0.5}" stroke="${c.line2}"/>
  ${months.join("")}
  <text x="${bx}" y="${ly - 16}" class="mono" font-size="12" letter-spacing="2" fill="${c.muted}">TOP LANGUAGES · PUBLIC REPOS</text>
  <text x="${W - P}" y="${ly - 16}" text-anchor="end" class="mono" font-size="11" letter-spacing="1.4" fill="${c.faint}">UPDATED ${updated}</text>
  <rect x="${bx}" y="${ly}" width="${bw}" height="10" fill="${c.line}"/>
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
