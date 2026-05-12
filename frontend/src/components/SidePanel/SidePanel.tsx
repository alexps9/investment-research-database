'use client'

import type { GraphNode, TechAssessment } from '@/types/citation-graph'
import { LANES } from '@/lib/citation-graph/constants'
import styles from './SidePanel.module.css'

interface Props {
  node: GraphNode | null
  assessment: TechAssessment | null // null for tier-2 or unfetched
  onClose: () => void
}

export default function SidePanel({ node, assessment, onClose }: Props) {
  if (!node) {
    return (
      <aside className={styles.panel}>
        <div className={styles.empty}>
          <div className={styles.emptyKicker}>Citation Graph / Side Panel</div>
          <div className={styles.emptyTitle}>点击画布中的节点查看详情</div>
          <p>Tier-1 论文显示完整的 7 模块评估。Tier-2 论文显示精简元数据。</p>
          <p style={{ marginTop: 16, color: '#bbb' }}>
            选中后，相关引用边会在画布中高亮。
          </p>
        </div>
      </aside>
    )
  }

  return (
    <aside className={styles.panel}>
      <div className={styles.body}>
        <Head node={node} onClose={onClose} />
        {node.tier === 1 && assessment ? (
          <FullAssessment a={assessment} />
        ) : (
          <Tier2Notice node={node} />
        )}
      </div>
    </aside>
  )
}

function Head({ node, onClose }: { node: GraphNode; onClose: () => void }) {
  const lane = LANES[node.lane]
  const sub = lane.subLanes[node.sub_lane]
  return (
    <div className={styles.head}>
      <button type="button" className={styles.headClose} onClick={onClose} aria-label="close">
        ×
      </button>
      <div className={styles.headTags}>
        <span
          className={styles.headLaneTag}
          style={{
            color: lane.color,
            backgroundColor: lane.fill,
            borderColor: lane.color,
          }}
        >
          L{node.lane}-{node.sub_lane} · {sub.title}
        </span>
        {node.alpha === 'high' && <span className={styles.headParadigmTag}>α HIGH</span>}
      </div>
      <h2 className={styles.headTitle}>{node.title}</h2>
      <div className={styles.headMeta}>
        <span>
          {node.year} Q{node.quarter}
        </span>
        <span>·</span>
        <span className={styles.headCites}>
          {node.cited_by_count.toLocaleString()} cites
        </span>
        <span>·</span>
        {node.arxiv_id ? (
          <a
            href={`https://arxiv.org/abs/${node.arxiv_id}`}
            target="_blank"
            rel="noreferrer"
          >
            arXiv:{node.arxiv_id}
          </a>
        ) : node.source_url ? (
          <a href={node.source_url} target="_blank" rel="noreferrer">
            source
          </a>
        ) : null}
      </div>
    </div>
  )
}

function FullAssessment({ a }: { a: TechAssessment }) {
  return (
    <>
      <Module index="02" title="Positioning">
        <div className={styles.kv}>
          <div className={styles.kvKey}>Role</div>
          <div className={styles.kvVal}>{a.positioning.role}</div>
        </div>
        <div className={styles.kv}>
          <div className={styles.kvKey}>Benchmark</div>
          <div className={styles.kvValMuted}>{a.positioning.benchmark}</div>
        </div>
        <div className={styles.kv}>
          <div className={styles.kvKey}>Core diff</div>
          <div className={styles.kvValHighlight}>{a.positioning.coreDiff}</div>
        </div>
      </Module>

      <Module index="03" title="Evolution">
        <div className={styles.chain}>
          <div className={styles.chainRow}>
            <div className={styles.chainLabel}>Predecessors</div>
            <div className={styles.chainValue}>
              {a.evolution.predecessors.map((p, i) => (
                <span key={i}>
                  {i > 0 && <span className={styles.chainArrow}>+</span>}
                  {p}
                </span>
              ))}
            </div>
          </div>
          <div className={styles.chainRow}>
            <div className={styles.chainLabel}>Current</div>
            <div className={styles.chainValue}>
              <span className={styles.chainArrow}>→</span>
              {a.evolution.current}
            </div>
          </div>
          <div className={styles.chainRow}>
            <div className={styles.chainLabel}>Successors</div>
            <div className={styles.chainValue}>
              {a.evolution.successors.length > 0
                ? a.evolution.successors.map((s, i) => (
                    <span key={i}>
                      {i > 0 && <span className={styles.chainArrow}>|</span>}
                      {s}
                    </span>
                  ))
                : <span style={{ color: '#bbb' }}>— 尚未观察到后继</span>}
            </div>
          </div>
        </div>
      </Module>

      <Module index="04" title="Stage">
        <div className={styles.kv}>
          <div className={styles.kvKey}>Phase</div>
          <div className={styles.kvValHighlight}>{a.stageDetail.phase}</div>
        </div>
        <div className={styles.kv}>
          <div className={styles.kvKey}>Period</div>
          <div className={styles.kvValMuted}>{a.stageDetail.period}</div>
        </div>
        {a.growth && (
          <div className={styles.kv}>
            <div className={styles.kvKey}>Growth</div>
            <div className={styles.kvValHighlight} style={{ color: '#ff4400' }}>
              {a.growth}
            </div>
          </div>
        )}
        <div style={{ marginTop: 12 }}>
          <ul className={styles.list}>
            {a.stageDetail.signals.map((s, i) => (
              <li key={i} className={styles.listItem}>
                <span className={styles.listMarker}>
                  {String(i + 1).padStart(2, '0')}
                </span>
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </div>
      </Module>

      <Module index="05" title="Players">
        <div className={styles.players}>
          {a.players.coreResearchers.map((r, i) => (
            <div key={i} className={styles.playerRow}>
              <span className={styles.playerName}>{r.name}</span>
              <span className={styles.playerAff}>{r.affiliation}</span>
            </div>
          ))}
        </div>
        {a.players.activeTeams.length > 0 && (
          <div className={styles.teams}>
            {a.players.activeTeams.map((t, i) => (
              <span key={i} className={styles.team}>
                {t}
              </span>
            ))}
          </div>
        )}
      </Module>

      <Module index="06" title="Bottlenecks">
        <ul className={styles.list}>
          {a.bottlenecks.current.map((b, i) => (
            <li key={`c-${i}`} className={styles.listItem}>
              <span className={styles.listMarker}>now</span>
              <span>{b}</span>
            </li>
          ))}
          {a.bottlenecks.unsolved.map((b, i) => (
            <li key={`u-${i}`} className={styles.listItem}>
              <span className={styles.listMarker} style={{ color: '#ff4400' }}>
                open
              </span>
              <span>{b}</span>
            </li>
          ))}
        </ul>
      </Module>

      <Module index="07" title="Conclusion">
        <div className={styles.conclusion}>{a.conclusion}</div>
      </Module>
    </>
  )
}

function Tier2Notice({ node }: { node: GraphNode }) {
  return (
    <>
      <div className={styles.simpleNotice}>
        Tier-2 · 衍生论文 — 此处仅展示基础元数据
      </div>
      <Module index="02" title="Tags">
        <div className={styles.teams}>
          {node.tags.map((t, i) => (
            <span key={i} className={styles.team}>
              {t}
            </span>
          ))}
        </div>
      </Module>
      {node.note && (
        <Module index="03" title="Note">
          <div className={styles.conclusion}>{node.note}</div>
        </Module>
      )}
      {node.authors.length > 0 && (
        <Module index="04" title="Authors">
          <div className={styles.players}>
            {node.authors.map((a, i) => (
              <div key={i} className={styles.playerRow}>
                <span className={styles.playerName}>{a}</span>
              </div>
            ))}
          </div>
        </Module>
      )}
    </>
  )
}

function Module({
  index,
  title,
  children,
}: {
  index: string
  title: string
  children: React.ReactNode
}) {
  return (
    <div className={styles.module}>
      <div className={styles.moduleHeader}>
        <div className={styles.moduleTitle}>{title}</div>
        <div className={styles.moduleIndex}>{index}</div>
      </div>
      {children}
    </div>
  )
}
