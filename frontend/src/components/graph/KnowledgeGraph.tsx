'use client';

import dynamic from 'next/dynamic';
import { useEffect, useRef, useState } from 'react';
import type { GraphNode, GraphLink } from './KnowledgeGraphCanvas';

// react-force-graph-2d touches `window`, so it must never render on the server.
const Canvas = dynamic(() => import('./KnowledgeGraphCanvas'), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center text-sm text-gray-400">
      Loading graph…
    </div>
  ),
});

interface Props {
  nodes: GraphNode[];
  links: GraphLink[];
  onSelect?: (node: GraphNode | null) => void;
  focusId?: string | null;
  compact?: boolean;
  className?: string;
}

export default function KnowledgeGraph({
  nodes,
  links,
  onSelect,
  focusId,
  compact,
  className,
}: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 0, h: 0 });

  useEffect(() => {
    if (!ref.current) return;
    const el = ref.current;
    const update = () => setSize({ w: el.clientWidth, h: el.clientHeight });
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  return (
    <div ref={ref} className={className} style={{ width: '100%', height: '100%' }}>
      <Canvas
        width={size.w}
        height={size.h}
        nodes={nodes}
        links={links}
        onSelect={onSelect}
        focusId={focusId}
        compact={compact}
      />
    </div>
  );
}

export type { GraphNode, GraphLink };
