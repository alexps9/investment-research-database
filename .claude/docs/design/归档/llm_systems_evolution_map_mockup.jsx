export default function LLMEvolutionMap() {
  const lanes = [
    {
      id: 1,
      title: 'Context Scaling',
      subtitle: '处理更长文本（4K → 1M+）',
      border: 'border-blue-500',
      paradigms: [
        {
          name: 'Post-Attention / SSM',
          color: 'bg-blue-500',
          line: 'border-blue-400',
          shape: 'circle',
          papers: [
            ['RetNet', '2023 Q2', '12%'],
            ['RWKV v6', '2023 Q2', '22%'],
            ['Mamba', '2023 Q4', '42%'],
            ['Mamba-2', '2024 Q2', '60%'],
            ['Mamba-3', '2024 Q4', '80%'],
          ],
        },
        {
          name: 'Sparse / Long Context',
          color: 'bg-teal-500',
          line: 'border-teal-400',
          shape: 'square',
          papers: [
            ['LongNet', '2023 Q1', '10%'],
            ['Ring Attention', '2023 Q3', '30%'],
            ['Infini-Attention', '2024 Q1', '48%'],
            ['YaRN', '2024 Q3', '68%'],
            ['LongRoPE', '2024 Q4', '80%'],
            ['Llama-3.1 128K', '2025 Q1', '92%'],
          ],
        },
        {
          name: 'Memory-Augmented',
          color: 'bg-violet-500',
          line: 'border-violet-400',
          shape: 'hex',
          papers: [
            ['RETRO', '2023 Q2', '18%'],
            ['HMT', '2023 Q4', '42%'],
            ['MemGPT', '2024 Q2', '64%'],
            ['RMT', '2024 Q4', '88%'],
          ],
        },
        {
          name: 'Kernel Optimization',
          color: 'bg-slate-500',
          line: 'border-slate-400',
          shape: 'square',
          papers: [
            ['FlashAttention', '2023 Q2', '20%'],
            ['FlashAttn-2', '2023 Q3', '42%'],
            ['FlashAttn-3', '2024 Q2', '64%'],
            ['FlashAttn-4', '2025 Q1', '90%'],
          ],
        },
      ],
    },
    {
      id: 2,
      title: 'Memory Wall',
      subtitle: '降低推理显存 / 带宽占用',
      border: 'border-emerald-500',
      paradigms: [
        {
          name: 'KV Compression',
          color: 'bg-fuchsia-500',
          line: 'border-fuchsia-400',
          shape: 'hex',
          papers: [
            ['MQA', '2023 Q1', '8%'],
            ['GQA', '2023 Q2', '22%'],
            ['MLA (DS-V2)', '2024 Q2', '60%'],
            ['MLA (DS-V3)', '2024 Q4', '78%'],
            ['TransMLA', '2025 Q1', '90%'],
          ],
        },
        {
          name: 'Paging / Offloading',
          color: 'bg-green-500',
          line: 'border-green-400',
          shape: 'square',
          papers: [
            ['PagedAttention', '2023 Q2', '18%'],
            ['vLLM v1', '2023 Q4', '42%'],
            ['vLLM v2', '2024 Q3', '70%'],
            ['PyramidKV', '2024 Q4', '84%'],
          ],
        },
      ],
    },
    {
      id: 3,
      title: 'Compute Allocation',
      subtitle: '有限算力下的最优分配',
      border: 'border-orange-500',
      paradigms: [
        {
          name: 'Conditional Compute',
          color: 'bg-red-500',
          line: 'border-red-400',
          shape: 'circle',
          papers: [
            ['GShard', '2023 Q1', '8%'],
            ['Switch Transformer', '2023 Q2', '22%'],
            ['Mixtral 8x7B', '2023 Q4', '42%'],
            ['DeepSeek-MoE', '2024 Q2', '60%'],
            ['DeepSeek-V3', '2024 Q4', '80%'],
            ['Qwen3 (MoE)', '2025 Q1', '92%'],
          ],
        },
        {
          name: 'Speculative / Draft',
          color: 'bg-blue-400',
          line: 'border-blue-300',
          shape: 'diamond',
          papers: [
            ['Speculative Decoding', '2023 Q2', '16%'],
            ['Medusa', '2023 Q4', '40%'],
            ['Lookahead Decoding', '2024 Q2', '58%'],
            ['EAGLE', '2024 Q3', '74%'],
          ],
        },
        {
          name: 'Reasoning Scaling',
          color: 'bg-orange-500',
          line: 'border-orange-400',
          shape: 'triangle',
          papers: [
            ['Chain-of-Thought', '2023 Q1', '10%'],
            ['o1-preview', '2024 Q4', '76%'],
            ['DeepSeek-R1', '2025 Q1', '88%'],
            ['Verifier / Rubric', '2025 Q2', '96%'],
          ],
        },
      ],
    },
  ];

  const renderShape = (shape, color) => {
    if (shape === 'square') {
      return <div className={`w-5 h-5 ${color} border-2 border-white shadow-md`} />;
    }
    if (shape === 'diamond') {
      return <div className={`w-5 h-5 rotate-45 ${color} border-2 border-white shadow-md`} />;
    }
    if (shape === 'triangle') {
      return <div className="w-0 h-0 border-l-[10px] border-r-[10px] border-b-[18px] border-l-transparent border-r-transparent border-b-orange-500 drop-shadow-md" />;
    }
    if (shape === 'hex') {
      return <div className={`w-5 h-5 ${color} shadow-md`} style={{ clipPath: 'polygon(25% 6%, 75% 6%, 100% 50%, 75% 94%, 25% 94%, 0% 50%)' }} />;
    }
    return <div className={`w-5 h-5 rounded-full ${color} border-2 border-white shadow-md`} />;
  };

  return (
    <div className="bg-white min-h-screen text-zinc-900 flex font-sans">
      <div className="flex-1 overflow-auto">
        <div className="sticky top-0 z-30 bg-white border-b border-zinc-200 px-8 py-5 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-black tracking-tight">LLM SYSTEMS EVOLUTION MAP</h1>
            <p className="mt-1 text-sm text-zinc-500">后 Transformer 时代技术演化地图（2023 → 2026）</p>
          </div>

          <div className="flex items-center gap-3 text-sm">
            <button className="px-4 py-2 rounded-xl bg-orange-500 text-white font-semibold">全局视图</button>
            <button className="px-4 py-2 rounded-xl border border-zinc-300 text-zinc-600">单一主题</button>
            <button className="px-4 py-2 rounded-xl border border-zinc-300 text-zinc-600">对比视图</button>
          </div>
        </div>

        <div className="px-8 py-6">
          <div className="grid grid-cols-[250px_1fr] border border-zinc-200 rounded-3xl overflow-hidden">
            <div className="bg-zinc-50 border-r border-zinc-200">
              <div className="h-24 border-b border-zinc-200 px-6 flex items-center text-xs uppercase tracking-[0.2em] text-zinc-500 font-bold">
                Bottleneck / Pressure Axis
              </div>

              {lanes.map((lane) => (
                <div key={lane.id} className={`border-l-4 ${lane.border} border-b border-zinc-200 px-6 py-10 min-h-[420px]`}>
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-white border border-zinc-300 flex items-center justify-center text-sm font-bold">
                      {lane.id}
                    </div>
                    <h2 className="text-2xl font-bold">{lane.title}</h2>
                  </div>

                  <p className="mt-4 text-sm text-zinc-500 leading-7">{lane.subtitle}</p>
                </div>
              ))}
            </div>

            <div className="relative overflow-hidden bg-white">
              <div className="grid grid-cols-4 h-24 border-b border-zinc-200 sticky top-0 z-20 bg-white">
                {['2023', '2024', '2025', '2026'].map((year) => (
                  <div key={year} className="border-r border-zinc-100 flex items-center justify-center text-2xl font-bold text-zinc-700">
                    {year}
                  </div>
                ))}
              </div>

              <div className="absolute top-0 bottom-0 left-[78%] border-l-2 border-dashed border-orange-400 z-10">
                <div className="absolute top-6 -left-4 text-xs font-bold text-orange-500">NOW</div>
              </div>

              <div className="absolute top-[68%] left-0 right-0 h-36 bg-gradient-to-r from-red-50 via-orange-100 to-red-50 opacity-60 pointer-events-none" />

              {lanes.map((lane, laneIndex) => (
                <div key={laneIndex} className="border-b border-zinc-200 min-h-[420px] relative">
                  {lane.paradigms.map((p, idx) => (
                    <div key={idx} className="relative h-24 border-b border-dashed border-zinc-100">
                      <div className="absolute left-5 top-4 flex items-center gap-2 text-sm font-semibold text-zinc-700 z-10">
                        <div className={`w-2.5 h-2.5 rounded-full ${p.color}`} />
                        {p.name}
                      </div>

                      <div className="absolute left-0 right-0 top-12 border-t border-dashed border-zinc-200" />

                      {p.papers.map((paper, i) => (
                        <div key={i} className="absolute top-8 -translate-x-1/2 group cursor-pointer" style={{ left: paper[2] }}>
                          <div className="transition-transform duration-200 group-hover:scale-125">
                            {renderShape(p.shape, p.color)}
                          </div>

                          <div className="mt-2 text-[11px] whitespace-nowrap text-center text-zinc-600">
                            <div>{paper[0]}</div>
                            <div className="text-zinc-400">{paper[1]}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <aside className="w-[420px] bg-zinc-50 border-l border-zinc-200 p-6 overflow-auto">
        <div className="flex items-center justify-between">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-xs font-semibold">
            Context Scaling
          </div>

          <button className="text-zinc-400 text-xl">×</button>
        </div>

        <h2 className="mt-5 text-4xl font-black tracking-tight">Mamba-2</h2>

        <div className="mt-3 flex items-center gap-4 text-sm text-zinc-500">
          <span>2024 Q2</span>
          <span>1,892 cites</span>
          <span>arXiv:2405.21060</span>
        </div>

        <div className="mt-8 space-y-8">
          <div>
            <div className="text-xs uppercase tracking-[0.2em] text-zinc-400 font-bold">解决的问题</div>
            <p className="mt-3 text-sm leading-7 text-zinc-700">
              如何在保持表达能力的同时实现 O(n) 复杂度的长序列建模。
            </p>
          </div>

          <div>
            <div className="text-xs uppercase tracking-[0.2em] text-zinc-400 font-bold">核心思想</div>
            <p className="mt-3 text-sm leading-7 text-zinc-700">
              选择性状态空间模型（Selective SSM）+ 硬件感知优化。
            </p>
          </div>

          <div>
            <div className="text-xs uppercase tracking-[0.2em] text-zinc-400 font-bold">Paradigm</div>
            <div className="mt-3 inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-sm font-medium">
              <div className="w-2 h-2 rounded-full bg-blue-500" />
              Post-Attention / SSM
            </div>
          </div>

          <div>
            <div className="text-xs uppercase tracking-[0.2em] text-zinc-400 font-bold">Layer</div>
            <div className="mt-3 flex items-center gap-3 text-sm text-zinc-700">
              <div className="w-4 h-4 rounded-full bg-blue-500" />
              arch / architecture-level change
            </div>
          </div>

          <div>
            <div className="text-xs uppercase tracking-[0.2em] text-zinc-400 font-bold">Competes With</div>
            <div className="mt-3 flex flex-wrap gap-2">
              {['Infini-Attention', 'RWKV', 'RetNet'].map((x) => (
                <div key={x} className="px-3 py-1 rounded-full border border-zinc-300 text-sm bg-white text-zinc-700">
                  {x}
                </div>
              ))}
            </div>
          </div>

          <div>
            <div className="text-xs uppercase tracking-[0.2em] text-zinc-400 font-bold">Philosophical Lineage</div>
            <div className="mt-3 flex flex-wrap gap-2">
              {['Hyena', 'xLSTM', 'RWKV'].map((x) => (
                <div key={x} className="px-3 py-1 rounded-full bg-zinc-200 text-sm text-zinc-700">
                  {x}
                </div>
              ))}
            </div>
          </div>

          <div>
            <div className="text-xs uppercase tracking-[0.2em] text-zinc-400 font-bold">核心洞察</div>
            <div className="mt-3 p-4 rounded-2xl bg-white border border-zinc-200 text-sm leading-7 text-zinc-700">
              Mamba-2 代表了一种“后 Attention”世界观：通过 selective state updates 替代全量 attention matrix，从根源上解决 sequence scaling 问题。
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}
