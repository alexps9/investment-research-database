'use client'

import { useState } from 'react'
import type { InsightReport as InsightReportType } from '@/types/api'
import styles from './InsightReport.module.css'

interface InsightReportProps {
  report: InsightReportType
  onClose: () => void
}

export default function InsightReport({ report, onClose }: InsightReportProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({
    temporal: true,
    talent: false,
    bottleneck: false,
  })

  const toggle = (section: string) => {
    setExpanded(prev => ({ ...prev, [section]: !prev[section] }))
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.pathBadge}>{report.path}</span>
          <span className={styles.pathName}>{report.path_name}</span>
        </div>
        <button className={styles.closeBtn} onClick={onClose} aria-label="Close report">
          &times;
        </button>
      </div>

      <div className={styles.meta}>
        {report.paper_count} papers &middot; {report.temporal.stage}
      </div>

      {/* 时空定位 */}
      <div className={styles.section}>
        <button className={styles.sectionHeader} onClick={() => toggle('temporal')}>
          <span className={styles.sectionLabel}>时空定位</span>
          <span className={styles.chevron}>{expanded.temporal ? '−' : '+'}</span>
        </button>
        {expanded.temporal && (
          <div className={styles.sectionBody}>
            <p className={styles.desc}>{report.temporal.timeline_desc}</p>
            {report.temporal.key_milestones.length > 0 && (
              <ul className={styles.milestones}>
                {report.temporal.key_milestones.map((m, i) => (
                  <li key={i} className={styles.milestone}>
                    <span className={styles.milestoneYear}>{m.year}</span>
                    <span className={styles.milestoneTitle}>{m.paper_title}</span>
                    <span className={styles.milestoneContrib}>{m.contribution}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>

      {/* 人才图谱 */}
      <div className={styles.section}>
        <button className={styles.sectionHeader} onClick={() => toggle('talent')}>
          <span className={styles.sectionLabel}>人才图谱</span>
          <span className={styles.chevron}>{expanded.talent ? '−' : '+'}</span>
        </button>
        {expanded.talent && (
          <div className={styles.sectionBody}>
            <p className={styles.desc}>{report.talent.summary}</p>
            {report.talent.top_authors.length > 0 && (
              <div className={styles.authorList}>
                {report.talent.top_authors.map((a, i) => (
                  <div key={i} className={styles.authorItem}>
                    <span className={styles.authorName}>{a.name}</span>
                    <span className={styles.authorStats}>
                      {a.paper_count} papers &middot; {a.total_citations} citations
                    </span>
                  </div>
                ))}
              </div>
            )}
            {report.talent.institutions.length > 0 && (
              <div className={styles.instList}>
                {report.talent.institutions.map((inst, i) => (
                  <span key={i} className={styles.instTag} data-category={inst.category}>
                    {inst.name}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 瓶颈分析 */}
      <div className={styles.section}>
        <button className={styles.sectionHeader} onClick={() => toggle('bottleneck')}>
          <span className={styles.sectionLabel}>瓶颈分析</span>
          <span className={styles.chevron}>{expanded.bottleneck ? '−' : '+'}</span>
        </button>
        {expanded.bottleneck && (
          <div className={styles.sectionBody}>
            <p className={styles.desc}>{report.bottleneck.current_bottleneck}</p>
            {report.bottleneck.existing_solutions.length > 0 && (
              <>
                <div className={styles.subLabel}>已有方案</div>
                <ul className={styles.list}>
                  {report.bottleneck.existing_solutions.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </>
            )}
            {report.bottleneck.next_directions.length > 0 && (
              <>
                <div className={styles.subLabel}>可能方向</div>
                <ul className={styles.list}>
                  {report.bottleneck.next_directions.map((d, i) => (
                    <li key={i}>{d}</li>
                  ))}
                </ul>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}