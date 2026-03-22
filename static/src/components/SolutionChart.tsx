import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

interface SolutionChartProps {
  solution: number[];
  title?: string;
  color?: string;
}

export default function SolutionChart({ solution, title = 'Solution', color = '#2563eb' }: SolutionChartProps) {
  const data = solution.map((value, index) => ({
    x: index,
    y: value,
  }));

  return (
    <div className="w-full">
      <h3 className="mb-4 text-lg font-semibold">{title}</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="x" label={{ value: 'Grid index', position: 'insideBottom', offset: -5 }} />
          <YAxis label={{ value: 'Value', angle: -90, position: 'insideLeft' }} />
          <Tooltip formatter={(value: number) => value.toFixed(6)} labelFormatter={(label: number) => `Index: ${label}`} />
          <Legend />
          <Line type="monotone" dataKey="y" stroke={color} dot={false} name="Numerical solution" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
