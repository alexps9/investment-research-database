'use client';
import React, { createContext, useContext, useState, useEffect } from 'react';

export type Lang = 'zh' | 'en';

const STORAGE_KEY = 'hh_lang';

interface LangCtx {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string) => string;
}

const LangContext = createContext<LangCtx>({
  lang: 'zh',
  setLang: () => {},
  t: (k) => k,
});

// ── translations ───────────────────────────────────────────────────────────────
const TRANS: Record<Lang, Record<string, string>> = {
  zh: {
    // nav
    'nav.dashboard':  '仪表盘',
    'nav.sources':    '信号源',
    'nav.signals':    '信号',
    'nav.entities':   '实体',
    'nav.wiki':       '知识库',
    'nav.graph':      '知识图谱',
    'nav.ask':        '智能问答',
    // dashboard
    'dashboard.title':          '仪表盘',
    'dashboard.stats.sources':  '信号源',
    'dashboard.stats.signals':  '信号总数',
    'dashboard.stats.entities': '实体',
    'dashboard.stats.orgs':     '组织',
    'dashboard.recent_signals': '最新信号',
    'dashboard.recent_runs':    '最近任务',
    'dashboard.no_signals':     '暂无信号',
    'dashboard.no_runs':        '暂无任务记录',
    // sources
    'sources.title':        '信号源',
    'sources.search':       '搜索信号源…',
    'sources.col.name':     '名称',
    'sources.col.type':     '类型',
    'sources.col.tier':     '级别',
    'sources.col.org':      '组织',
    'sources.col.sector':   '领域',
    'sources.col.activity': '活跃度',
    'sources.col.twitter':  'Twitter',
    // signals
    'signals.title':        '信号',
    'signals.search':       '搜索信号…',
    'signals.col.title':    '标题',
    'signals.col.type':     '类型',
    'signals.col.source':   '来源',
    'signals.col.date':     '发布时间',
    'signals.col.status':   '状态',
    // entities
    'entities.title':       '实体',
    'entities.search':      '搜索实体…',
    'entities.col.name':    '名称',
    'entities.col.type':    '类型',
    'entities.col.aliases': '别名',
    // wiki
    'wiki.title':           '知识库',
    'wiki.search':          '搜索实体…',
    'wiki.back':            '返回列表',
    'wiki.col.description': '描述',
    'wiki.col.relations':   '关联实体',
    'wiki.col.signals':     '相关信号',
    // common
    'common.loading':       '加载中…',
    'common.error':         '加载失败',
    'common.empty':         '暂无数据',
    'common.view_all':      '查看全部',
    'common.back':          '返回',
    'common.unknown':       '未知',
    'common.active':        '活跃',
    'common.inactive':      '不活跃',
    // actions
    'action.edit':          '编辑',
    'action.delete':        '删除',
    'action.save':          '保存',
    'action.cancel':        '取消',
    'action.export':        '导出 CSV',
    'action.new':           '新建',
    'action.actions':       '操作',
    'action.saving':        '保存中…',
    'action.confirm_delete':'确定删除「{name}」吗？此操作不可撤销。',
    'action.edit_source':   '编辑信号源',
    'action.edit_signal':   '编辑信号',
    'action.save_failed':   '保存失败',
    'action.delete_failed': '删除失败',
    // ask / semantic search
    'ask.title':            '智能问答',
    'ask.subtitle':         '基于向量语义检索 + 大模型问答',
    'ask.mode.search':      '语义检索',
    'ask.mode.qa':          'AI 问答',
    'ask.placeholder.search':'输入想检索的内容，如「做多模态的华人研究者」',
    'ask.placeholder.qa':   '提一个问题，如「有哪些专注具身智能的机构？」',
    'ask.send':             '提交',
    'ask.thinking':         '思考中…',
    'ask.searching':        '检索中…',
    'ask.answer':           '回答',
    'ask.sources':          '参考来源',
    'ask.no_results':       '没有找到相关结果',
    'ask.disabled':         '语义功能未启用：请在后端配置 OPENAI_API_KEY / DEEPSEEK_API_KEY',
    'ask.reindex':          '重建索引',
    'ask.reindexing':       '建立索引中…',
    'ask.reindex_done':     '索引完成',
    'ask.reindex_hint':     '首次使用或数据更新后，需先重建向量索引',
    // activity levels
    'activity.very_active': '非常活跃',
    'activity.active':      '活跃',
    'activity.normal':      '一般',
    'activity.inactive':    '不活跃',
    'activity.unknown':     '未知',
    // tiers
    'tier.P0+': 'P0+',
    'tier.P1':  'P1',
    'tier.P2':  'P2',
    'tier.P3':  'P3',
    // sectors
    'sector.industry': '业界',
    'sector.academia': '学界',
    'sector.other':    '其他',
    'sector.media':    '媒体',
    // signal types
    'signal_type.paper':         '论文',
    'signal_type.tweet':         '推文',
    'signal_type.blog':          '博客',
    'signal_type.news':          '新闻',
    'signal_type.tech_report':   '技术报告',
    'signal_type.github_release':'GitHub发布',
    'signal_type.model_release': '模型发布',
    'signal_type.benchmark':     '基准测试',
    'signal_type.dataset':       '数据集',
    'signal_type.other':         '其他',
  },
  en: {
    // nav
    'nav.dashboard':  'Dashboard',
    'nav.sources':    'Sources',
    'nav.signals':    'Signals',
    'nav.entities':   'Entities',
    'nav.wiki':       'Wiki',
    'nav.graph':      'Graph',
    'nav.ask':        'Ask AI',
    // dashboard
    'dashboard.title':          'Dashboard',
    'dashboard.stats.sources':  'Sources',
    'dashboard.stats.signals':  'Signals',
    'dashboard.stats.entities': 'Entities',
    'dashboard.stats.orgs':     'Organisations',
    'dashboard.recent_signals': 'Latest Signals',
    'dashboard.recent_runs':    'Recent Runs',
    'dashboard.no_signals':     'No signals yet',
    'dashboard.no_runs':        'No run records',
    // sources
    'sources.title':        'Sources',
    'sources.search':       'Search sources…',
    'sources.col.name':     'Name',
    'sources.col.type':     'Type',
    'sources.col.tier':     'Tier',
    'sources.col.org':      'Organisation',
    'sources.col.sector':   'Sector',
    'sources.col.activity': 'Activity',
    'sources.col.twitter':  'Twitter',
    // signals
    'signals.title':        'Signals',
    'signals.search':       'Search signals…',
    'signals.col.title':    'Title',
    'signals.col.type':     'Type',
    'signals.col.source':   'Source',
    'signals.col.date':     'Published',
    'signals.col.status':   'Status',
    // entities
    'entities.title':       'Entities',
    'entities.search':      'Search entities…',
    'entities.col.name':    'Name',
    'entities.col.type':    'Type',
    'entities.col.aliases': 'Aliases',
    // wiki
    'wiki.title':           'Wiki',
    'wiki.search':          'Search entities…',
    'wiki.back':            'Back to list',
    'wiki.col.description': 'Description',
    'wiki.col.relations':   'Related entities',
    'wiki.col.signals':     'Related signals',
    // common
    'common.loading':       'Loading…',
    'common.error':         'Failed to load',
    'common.empty':         'No data',
    'common.view_all':      'View all',
    'common.back':          'Back',
    'common.unknown':       'Unknown',
    'common.active':        'Active',
    'common.inactive':      'Inactive',
    // actions
    'action.edit':          'Edit',
    'action.delete':        'Delete',
    'action.save':          'Save',
    'action.cancel':        'Cancel',
    'action.export':        'Export CSV',
    'action.new':           'New',
    'action.actions':       'Actions',
    'action.saving':        'Saving…',
    'action.confirm_delete':'Delete "{name}"? This cannot be undone.',
    'action.edit_source':   'Edit Source',
    'action.edit_signal':   'Edit Signal',
    'action.save_failed':   'Save failed',
    'action.delete_failed': 'Delete failed',
    // ask / semantic search
    'ask.title':            'Ask AI',
    'ask.subtitle':         'Vector semantic search + LLM Q&A',
    'ask.mode.search':      'Semantic Search',
    'ask.mode.qa':          'AI Q&A',
    'ask.placeholder.search':'Search, e.g. "Chinese researchers working on multimodal"',
    'ask.placeholder.qa':   'Ask a question, e.g. "Which labs focus on embodied AI?"',
    'ask.send':             'Submit',
    'ask.thinking':         'Thinking…',
    'ask.searching':        'Searching…',
    'ask.answer':           'Answer',
    'ask.sources':          'Sources',
    'ask.no_results':       'No relevant results found',
    'ask.disabled':         'Semantic features disabled: configure OPENAI_API_KEY / DEEPSEEK_API_KEY on the backend',
    'ask.reindex':          'Rebuild index',
    'ask.reindexing':       'Indexing…',
    'ask.reindex_done':     'Index complete',
    'ask.reindex_hint':     'Rebuild the vector index on first use or after data updates',
    // activity levels
    'activity.very_active': 'Very active',
    'activity.active':      'Active',
    'activity.normal':      'Normal',
    'activity.inactive':    'Inactive',
    'activity.unknown':     'Unknown',
    // tiers
    'tier.P0+': 'P0+',
    'tier.P1':  'P1',
    'tier.P2':  'P2',
    'tier.P3':  'P3',
    // sectors
    'sector.industry': 'Industry',
    'sector.academia': 'Academia',
    'sector.other':    'Other',
    'sector.media':    'Media',
    // signal types
    'signal_type.paper':         'Paper',
    'signal_type.tweet':         'Tweet',
    'signal_type.blog':          'Blog',
    'signal_type.news':          'News',
    'signal_type.tech_report':   'Tech Report',
    'signal_type.github_release':'GitHub Release',
    'signal_type.model_release': 'Model Release',
    'signal_type.benchmark':     'Benchmark',
    'signal_type.dataset':       'Dataset',
    'signal_type.other':         'Other',
  },
};

export function LangProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>('zh');

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as Lang | null;
    if (stored === 'zh' || stored === 'en') setLangState(stored);
  }, []);

  const setLang = (l: Lang) => {
    setLangState(l);
    localStorage.setItem(STORAGE_KEY, l);
  };

  const t = (key: string): string => TRANS[lang][key] ?? TRANS['en'][key] ?? key;

  return (
    <LangContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LangContext.Provider>
  );
}

export function useLang() {
  return useContext(LangContext);
}
