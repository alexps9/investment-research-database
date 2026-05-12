declare module '*.json' {
  const value: {
    lanes: Array<{
      id: string;
      title: string;
      subtitle: string;
      color: string;
    }>;
    rows: Array<{
      id: string;
      lane: string;
      title: string;
      subtitle: string;
    }>;
    papers: Array<{
      id: string;
      title: string;
      year: number;
      quarter: number;
      paradigm: string;
      layer: string;
      lane: string;
      row: string;
      path: string;
      size: string;
      builds_on: string[];
    }>;
    iterations: Array<{
      id: string;
      title: string;
      subtitle: string;
      path: string;
      row: string;
      papers: string[];
      mutations: Record<string, {
        summary: string;
        detail: string;
        bottleneck?: string;
        result?: string;
      }>;
    }>;
  };
  export default value;
}
