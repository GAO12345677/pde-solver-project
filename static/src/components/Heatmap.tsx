import Plot from 'react-plotly.js';

interface HeatmapProps {
  solution: number[];
  nx: number;
  ny: number;
  title?: string;
}

export default function Heatmap({ solution, nx, ny, title = '求解结果热力图' }: HeatmapProps) {
  const z = [];
  for (let i = 0; i < ny; i++) {
    z.push(solution.slice(i * nx, (i + 1) * nx));
  }

  const data = [
    {
      z,
      type: 'heatmap' as const,
      colorscale: 'Viridis',
    },
  ];

  const layout = {
    title: {
      text: title,
      font: { size: 16 },
    },
    xaxis: {
      title: 'X',
    },
    yaxis: {
      title: 'Y',
    },
    margin: {
      l: 60,
      r: 40,
      b: 60,
      t: 60,
    },
    autosize: true,
  };

  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
  };

  return (
    <div className="w-full">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <Plot
        data={data}
        layout={layout}
        config={config}
        style={{ width: '100%', height: '500px' }}
        useResizeHandler
      />
    </div>
  );
}
