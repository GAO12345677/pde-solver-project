import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

interface SolutionChartProps {
  solution: number[];
  title?: string;
  color?: string;
}

export default function SolutionChart({ solution, title = '求解结果', color = '#8884d8' }: SolutionChartProps) {
  const data = solution.map((value, index) => ({
    x: index,
    y: value,
  }));

  return (
    <div className="w-full">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="x" label={{ value: '位置', position: 'insideBottom', offset: -5 }} />
          <YAxis label={{ value: '值', angle: -90, position: 'insideLeft' }} />
          <Tooltip formatter={(value: number) => value.toFixed(6)} labelFormatter={(label: number) => `位置: ${label}`} />
          <Legend />
          <Line type="monotone" dataKey="y" stroke={color} dot={false} name="解" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
