import Plot from 'react-plotly.js';

interface HeatmapProps {
  solution: number[];
  nx: number;
  ny: number;
  title?: string;
}

export default function Heatmap({ solution, nx, ny, title = 'Heatmap' }: HeatmapProps) {
  const z = [];
  for (let i = 0; i < ny; i += 1) {
    z.push(solution.slice(i * nx, (i + 1) * nx));
  }

  return (
    <div className="w-full">
      <h3 className="mb-4 text-lg font-semibold">{title}</h3>
      <Plot
        data={[
          {
            z,
            type: 'heatmap',
            colorscale: 'Viridis',
          },
        ]}
        layout={{
          title,
          xaxis: { title: 'x' },
          yaxis: { title: 'y' },
          margin: { l: 60, r: 20, b: 50, t: 60 },
          autosize: true,
        }}
        config={{
          responsive: true,
          displayModeBar: true,
          displaylogo: false,
        }}
        style={{ width: '100%', height: '500px' }}
        useResizeHandler
      />
    </div>
  );
}
