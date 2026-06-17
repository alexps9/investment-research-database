'use client';

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';

export type Lang = 'zh' | 'en';

const TRANS: Record<Lang, Record<string, string>> = {
  zh: {
    'app.title': 'Research Studio',
    'app.tagline': '深度研究 · 技术路线 · 核心人物 · 产业追踪',
    'home.placeholder': '输入研究问题…',
    'home.search': '开始研究',
    'sidebar.new': '新会话',
    'sidebar.history': '历史会话',
    'sidebar.empty': '暂无历史会话',
    'status.running': '研究中…',
    'status.done': '已完成',
    'status.failed': '失败',
    'report.export_pdf': '导出 PDF',
    'report.trajectory': '技术路线演进',
    'report.people': '核心人物',
    'report.industry': '产业追踪',
    'report.back': '返回报告',
    'report.loading': '正在生成研究报告…',
    'trajectory.title': '技术路线演进',
    'people.title': '核心人物知识图谱',
    'industry.title': '产业追踪',
    'industry.signals': '技术信号',
    'industry.impact': '产业影响',
    'industry.talent': '关键人物',
    'industry.capital': '资本介入',
    'industry.funding': '相关融资',
    'industry.signals_live': '实时信号',
  },
  en: {
    'app.title': 'Research Studio',
    'app.tagline': 'Deep research · Trajectory · People · Industry',
    'home.placeholder': 'Ask a research question…',
    'home.search': 'Research',
    'sidebar.new': 'New session',
    'sidebar.history': 'History',
    'sidebar.empty': 'No sessions yet',
    'status.running': 'Running…',
    'status.done': 'Done',
    'status.failed': 'Failed',
    'report.export_pdf': 'Export PDF',
    'report.trajectory': 'Tech Trajectory',
    'report.people': 'Key People',
    'report.industry': 'Industry Tracking',
    'report.back': 'Back to report',
    'report.loading': 'Generating report…',
    'trajectory.title': 'Technology Trajectory',
    'people.title': 'Key People Subgraph',
    'industry.title': 'Industry Tracking',
    'industry.signals': 'Tech Signals',
    'industry.impact': 'Industry Impact',
    'industry.talent': 'Key Talent',
    'industry.capital': 'Capital',
    'industry.funding': 'Related Funding',
    'industry.signals_live': 'Live Signals',
  },
};

interface LangCtx {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string) => string;
}

const Ctx = createContext<LangCtx | null>(null);

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>('zh');
  useEffect(() => {
    const saved = localStorage.getItem('rs_lang') as Lang | null;
    if (saved === 'zh' || saved === 'en') setLang(saved);
  }, []);
  const set = (l: Lang) => {
    setLang(l);
    localStorage.setItem('rs_lang', l);
  };
  const t = (key: string) => TRANS[lang][key] ?? TRANS.en[key] ?? key;
  return <Ctx.Provider value={{ lang, setLang: set, t }}>{children}</Ctx.Provider>;
}

export function useLang() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useLang outside provider');
  return ctx;
}
