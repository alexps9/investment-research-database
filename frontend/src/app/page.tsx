'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import { usePaperSearch } from '@/hooks/usePaperSearch'
import { useGraphFilter } from '@/hooks/useGraphFilter'
import { useInsightReport } from '@/hooks/useInsightReport'
import { fetchSeedNetwork } from '@/lib/api-client'
import SearchBar from '@/components/SearchBar'
import ForceGraph from '@/components/ForceGraph'
import FilterPanel from '@/components/FilterPanel'
import NodeDetail from '@/components/NodeDetail'
import InsightReportPanel from '@/components/InsightReport'
import Loading from '@/components/Loading'
import ErrorMessage from '@/components/ErrorMessage'
import type { Node, GraphResponse } from '@/types/api'
import styles from './page.module.css'

export default function Home() {
  const { query, isLoading, error, data, search, clear } = usePaperSearch()

  // Seed mode state (must be before useGraphFilter(seedData))
  const [mode, setMode] = useState<'search' | 'seed'>('search')
  const [seedData, setSeedData] = useState<GraphResponse | null>(null)
  const [seedLoading, setSeedLoading] = useState(false)
  const [seedError, setSeedError] = useState<string | null>(null)
  const { report, isLoading: reportLoading, error: reportError, activePath, loadReport, clearReport } = useInsightReport()

  const {
    filteredData,
    filters,
    yearBounds,
    maxCitations,
    setYearRange,
    setMinCitations,
    resetFilters,
    topNodes,
  } = useGraphFilter(data)

  // Seed mode filter (separate instance for seed data)
  const {
    filteredData: seedFilteredData,
    filters: seedFilters,
    yearBounds: seedYearBounds,
    maxCitations: seedMaxCitations,
    setYearRange: setSeedYearRange,
    setMinCitations: setSeedMinCitations,
    resetFilters: resetSeedFilters,
    topNodes: seedTopNodes,
  } = useGraphFilter(seedData)

  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [graphWidth, setGraphWidth] = useState(900)
  const [graphHeight, setGraphHeight] = useState(600)
  const [layoutMode, setLayoutMode] = useState<'timeline' | 'cluster'>('timeline')

  // Active data based on mode
  const activeData = mode === 'seed' ? seedData : data
  const activeFilteredData = mode === 'seed' ? seedFilteredData : filteredData
  const activeFilters = mode === 'seed' ? seedFilters : filters
  const activeYearBounds = mode === 'seed' ? seedYearBounds : yearBounds
  const activeMaxCitations = mode === 'seed' ? seedMaxCitations : maxCitations
  const activeSetYearRange = mode === 'seed' ? setSeedYearRange : setYearRange
  const activeSetMinCitations = mode === 'seed' ? setSeedMinCitations : setMinCitations
  const activeResetFilters = mode === 'seed' ? resetSeedFilters : resetFilters
  const activeTopNodes = mode === 'seed' ? seedTopNodes : topNodes
  const activeLoading = mode === 'seed' ? seedLoading : isLoading
  const activeError = mode === 'seed' ? seedError : error

  useEffect(() => {
    if (typeof window === 'undefined') return
    const update = () => {
      // Graph takes the right side: full width minus sidebar (280px)
      const sidebarWidth = 280
      setGraphWidth(Math.max(400, window.innerWidth - sidebarWidth - 32))
      setGraphHeight(Math.max(400, window.innerHeight - 48))
    }
    update()
    window.addEventListener('resize', update)
    return () => window.removeEventListener('resize', update)
  }, [])

  const handleSearch = useCallback((searchQuery: string) => {
    setSelectedNode(null)
    search(searchQuery, 100)
  }, [search])

  const handleRetry = useCallback(() => {
    if (query) search(query, 100)
  }, [query, search])

  const handleNodeClick = useCallback((node: Node) => {
    setSelectedNode(node)
  }, [])

  const enterSeedMode = useCallback(async () => {
    setMode('seed')
    setSelectedNode(null)
    clearReport()
    if (seedData) return // already loaded
    setSeedLoading(true)
    setSeedError(null)
    try {
      const result = await fetchSeedNetwork()
      setSeedData(result)
    } catch (err) {
      setSeedError(err instanceof Error ? err.message : 'Failed to load seed network')
    } finally {
      setSeedLoading(false)
    }
  }, [seedData, clearReport])

  const enterSearchMode = useCallback(() => {
    setMode('search')
    setSelectedNode(null)
    clearReport()
  }, [clearReport])

  // Map path letter to community index for legend click
  const COMMUNITY_TO_PATH: Record<number, string> = { 0: 'A', 1: 'B', 2: 'C', 3: 'D' }

  const handleLegendClick = useCallback((communityId: number) => {
    if (mode !== 'seed') return
    const path = COMMUNITY_TO_PATH[communityId]
    if (path) loadReport(path)
  }, [mode, loadReport])

  const topNodeIds = useMemo(() => {
    return new Set(activeTopNodes.map(n => n.id))
  }, [activeTopNodes])

  const communityStats = useMemo(() => {
    if (!activeFilteredData) return []
    const counts = new Map<number, number>()
    activeFilteredData.nodes.forEach(n => {
      const c = n.community ?? 0
      counts.set(c, (counts.get(c) ?? 0) + 1)
    })
    return Array.from(counts.entries())
      .sort((a, b) => b[1] - a[1]) // sort by count desc
  }, [activeFilteredData])

  const hasResults = activeFilteredData && activeFilteredData.metadata.total_nodes > 0
  const hasData = activeData && activeData.metadata.total_nodes > 0

  return (
    <div className={styles.layout}>
      {/* Left Sidebar */}
      <aside className={styles.sidebar}>
        <header className={styles.brand}>
          <h1 className={styles.brandTitle}>Paper<span className={styles.brandAccent}>Graph</span></h1>
          <p className={styles.brandSub}>技术路线图演化（引用网络）</p>
        </header>

        {/* Mode toggle */}
        <div className={styles.modeToggle}>
          <button
            className={`${styles.modeBtn}${mode === 'search' ? ` ${styles.modeBtnActive}` : ''}`}
            onClick={enterSearchMode}
          >
            搜索模式
          </button>
          <button
            className={`${styles.modeBtn}${mode === 'seed' ? ` ${styles.modeBtnActive}` : ''}`}
            onClick={enterSeedMode}
          >
            种子 Demo
          </button>
        </div>

        {mode === 'search' && (
          <SearchBar
            onSearch={handleSearch}
            isLoading={isLoading}
            placeholder="如 transformer, mamba..."
            ariaLabel="搜索学术论文"
          />
        )}

        {mode === 'seed' && !seedData && !seedLoading && !seedError && (
          <div className={styles.seedHint}>
            <p>加载 10 篇种子论文的技术路线图</p>
          </div>
        )}

        {activeError && (
          <ErrorMessage
            message={activeError}
            onRetry={mode === 'search' ? handleRetry : enterSeedMode}
            onDismiss={mode === 'search' ? clear : () => setSeedError(null)}
          />
        )}

        {hasData && (
          <FilterPanel
            yearRange={activeFilters.yearRange}
            yearBounds={activeYearBounds}
            minCitations={activeFilters.minCitations}
            maxCitations={activeMaxCitations}
            onYearChange={activeSetYearRange}
            onCitationsChange={activeSetMinCitations}
            onReset={activeResetFilters}
            totalNodes={activeData!.metadata.total_nodes}
            filteredNodes={activeFilteredData?.metadata.total_nodes ?? 0}
          />
        )}

        {selectedNode && (
          <NodeDetail
            node={selectedNode}
            onClose={() => setSelectedNode(null)}
          />
        )}

        {/* Community legend */}
        {hasResults && communityStats.length > 0 && (
          <div className={styles.legend}>
            <span className={styles.legendTitle}>
              {mode === 'seed' ? '技术路径（点击查看报告）' : '技术社区'}
            </span>
            <div className={styles.legendItems}>
              {communityStats.slice(0, 8).map(([communityId, count]) => (
                <div
                  key={communityId}
                  className={`${styles.legendItem}${mode === 'seed' ? ` ${styles.legendItemClickable}` : ''}${activePath === COMMUNITY_TO_PATH[communityId] ? ` ${styles.legendItemActive}` : ''}`}
                  onClick={() => handleLegendClick(communityId)}
                  role={mode === 'seed' ? 'button' : undefined}
                  tabIndex={mode === 'seed' ? 0 : undefined}
                >
                  <span
                    className={styles.legendDot}
                    style={{ backgroundColor: [
                      '#5B7FA5', '#8B6E5A', '#6A8F6A', '#9B7EAF', '#A08C5B', '#7A9E9E', '#B07878', '#6B8EAD'
                    ][communityId % 8] }}
                  />
                  <span className={styles.legendLabel}>
                    {activeData?.metadata.community_names?.[String(communityId)] ?? `社区 ${communityId + 1}`}
                  </span>
                  <span className={styles.legendCount}>{count} 篇</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Insight Report Panel (seed mode only) */}
        {reportLoading && (
          <div className={styles.reportLoading}>
            <Loading message="加载报告..." />
          </div>
        )}
        {reportError && (
          <ErrorMessage message={reportError} onDismiss={clearReport} />
        )}
        {report && (
          <InsightReportPanel report={report} onClose={clearReport} />
        )}
      </aside>

      {/* Main Canvas */}
      <main className={styles.canvas}>
        {activeLoading && (
          <div className={styles.centered}>
            <Loading message={mode === 'seed' ? '正在加载种子论文...' : '正在构建引用网络...'} />
          </div>
        )}

        {!activeLoading && !hasData && !activeError && (
          <div className={styles.centered}>
            <p className={styles.emptyTitle}>
              {mode === 'seed' ? '点击"种子 Demo"加载技术路线图' : '搜索一个主题，探索技术路线演化'}
            </p>
            {mode === 'search' && (
              <p className={styles.emptyHint}>试试 &quot;transformer&quot;、&quot;diffusion model&quot; 或 &quot;mamba&quot;</p>
            )}
          </div>
        )}

        {hasResults && (
          <>
            <div className={styles.layoutToggle}>
              <button
                className={`${styles.layoutToggleBtn}${layoutMode === 'timeline' ? ` ${styles.layoutToggleBtnActive}` : ''}`}
                onClick={() => setLayoutMode('timeline')}
              >
                时间轴
              </button>
              <button
                className={`${styles.layoutToggleBtn}${layoutMode === 'cluster' ? ` ${styles.layoutToggleBtnActive}` : ''}`}
                onClick={() => setLayoutMode('cluster')}
              >
                引用聚类
              </button>
            </div>
            <ForceGraph
              data={activeFilteredData!}
              width={graphWidth}
              height={graphHeight}
              onNodeClick={handleNodeClick}
              topNodeIds={topNodeIds}
              layoutMode={layoutMode}
            />
          </>
        )}

        {hasData && activeFilteredData && activeFilteredData.metadata.total_nodes === 0 && (
          <div className={styles.centered}>
            <p className={styles.emptyTitle}>没有论文匹配当前筛选条件</p>
            <button className={styles.resetBtn} onClick={activeResetFilters}>重置筛选</button>
          </div>
        )}

        {/* Graph legend overlay */}
        {hasResults && (
          <div className={styles.graphLegend}>
            <span className={styles.graphLegendTitle}>
              {activeFilters.yearRange[0]}–{activeFilters.yearRange[1]} 年发展概览
            </span>
            <span className={styles.graphLegendDivider}>·</span>
            <span>节点大小 = 引用量</span>
            <span className={styles.graphLegendDivider}>·</span>
            <span>颜色 = {mode === 'seed' ? '技术路径' : '技术社区'}</span>
            <span className={styles.graphLegendDivider}>·</span>
            <span>箭头 = 知识传承方向</span>
            <span className={styles.graphLegendDivider}>·</span>
            <span className={styles.graphLegendHighlight}>橙圈 = 引用量 Top 10</span>
          </div>
        )}

        {/* Stats bar */}
        {hasResults && (
          <div className={styles.statsBar}>
            <span>{activeFilteredData!.metadata.total_nodes} 篇论文</span>
            <span>·</span>
            <span>{activeFilteredData!.metadata.total_links} 条引用</span>
            {activeFilteredData!.metadata.communities > 0 && (
              <>
                <span>·</span>
                <span>{activeFilteredData!.metadata.communities} 个{mode === 'seed' ? '路径' : '社区'}</span>
              </>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
