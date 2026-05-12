import type { GraphNode } from '@/types/citation-graph'
import styles from './CitationGraph.module.css'

interface PositionedNode extends GraphNode {
  _x: number
  _y: number
  _r: number
}

interface Props {
  nodes: PositionedNode[]
  selectedId: string | null
}

// Only tier-1 nodes get a static caption. Tier-2 show on hover via native title attr.
// Selected node always gets a caption regardless of tier.
export function NodeLabels({ nodes, selectedId }: Props) {
  return (
    <>
      {nodes
        .filter((n) => n.tier === 1 || n.id === selectedId)
        .map((n) => {
          const label = shortTitle(n)
          return (
            <div
              key={`label-${n.id}`}
              className={`${styles.nodeLabel}${n.tier === 2 ? ` ${styles.nodeLabelSoft}` : ''}`}
              style={{ left: n._x, top: n._y + n._r + 4 }}
            >
              {label}
            </div>
          )
        })}
    </>
  )
}

// Extract a short display name. Prefers canonical architecture name when available.
function shortTitle(n: GraphNode): string {
  const map: Record<string, string> = {
    'linear-transformer': 'Linear-T',
    performer: 'Performer',
    hippo: 'HiPPO',
    s4: 'S4',
    h3: 'H3',
    hyena: 'Hyena',
    'rwkv-v4': 'RWKV v4',
    'rwkv-v7': 'RWKV-7',
    retnet: 'RetNet',
    mamba: 'Mamba',
    'mamba-2': 'Mamba-2',
    gla: 'GLA',
    griffin: 'Griffin',
    jamba: 'Jamba',
    xlstm: 'xLSTM',
    deltanet: 'DeltaNet',
    longformer: 'Longformer',
    'big-bird': 'BigBird',
    'streaming-llm': 'StreamingLLM',
    longnet: 'LongNet',
    'ring-attention': 'Ring-Attn',
    'infini-attention': 'Infini-Attn',
    rope: 'RoPE',
    alibi: 'ALiBi',
    retro: 'RETRO',
    yarn: 'YaRN',
    longrope: 'LongRoPE',
    hmt: 'HMT',
    mqa: 'MQA',
    gqa: 'GQA',
    'deepseek-v2': 'DS-V2 (MLA)',
    'deepseek-v3': 'DS-V3',
    transmla: 'TransMLA',
    'flash-attn': 'FlashAttn',
    'flash-attn-2': 'FlashAttn-2',
    'flash-attn-3': 'FlashAttn-3',
    'flash-attn-4': 'FlashAttn-4',
    'paged-attention': 'PagedAttn',
    sglang: 'SGLang',
    'speculative-decoding': 'Speculative',
    medusa: 'Medusa',
    'lookahead-decoding': 'Lookahead',
    eagle: 'EAGLE',
    'eagle-2': 'EAGLE-2',
    gshard: 'GShard',
    'switch-transformer': 'Switch-T',
    glam: 'GLaM',
    megablocks: 'MegaBlocks',
    'st-moe': 'ST-MoE',
    'expert-choice': 'Expert-Choice',
    'deepseek-moe': 'DS-MoE',
    openmoe: 'OpenMoE',
    'mixtral-8x7b': 'Mixtral 8x7B',
    'qwen-moe': 'Qwen-MoE',
    'grok-1': 'Grok-1',
    dbrx: 'DBRX',
  }
  return map[n.id] ?? n.title.split(':')[0].slice(0, 16)
}
