'use client'

import type { Node } from '@/types/api'
import styles from './NodeDetail.module.css'

export interface NodeDetailProps {
  node: Node | null
  onClose: () => void
}

export default function NodeDetail({ node, onClose }: NodeDetailProps) {
  if (!node) return null

  const openAlexUrl = `https://openalex.org/works/${node.id}`

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <span className={styles.label}>论文详情</span>
        <button className={styles.closeBtn} onClick={onClose} aria-label="Close detail panel">
          ×
        </button>
      </div>

      <h3 className={styles.title}>{node.title}</h3>

      <div className={styles.meta}>
        <div className={styles.metaItem}>
          <span className={styles.metaLabel}>年份</span>
          <span className={styles.metaValue}>{node.publication_year}</span>
        </div>
        <div className={styles.metaItem}>
          <span className={styles.metaLabel}>引用数</span>
          <span className={styles.metaValue}>{node.cited_by_count.toLocaleString()}</span>
        </div>
        {node.community !== undefined && (
          <div className={styles.metaItem}>
            <span className={styles.metaLabel}>社区</span>
            <span className={styles.metaValue}>#{node.community}</span>
          </div>
        )}
      </div>

      <a
        href={openAlexUrl}
        target="_blank"
        rel="noopener noreferrer"
        className={styles.link}
      >
        在 OpenAlex 查看 →
      </a>
    </div>
  )
}
