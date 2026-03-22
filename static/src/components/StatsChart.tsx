import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

interface StatsChartProps {
  stats?: {
    min: number;
    max: number;
    mean: number;
    std: number;
  } | null;
}

export default function StatsChart({ stats }: StatsChartProps) {
  if (!stats) {
    return <div className="text-sm text-gray-500">暂无统计数据</div>;
  }

  const data = [
    { name: '最小值', value: stats.min },
    { name: '最大值', value: stats.max },
    { name: '平均值', value: stats.mean },
    { name: '标准差', value: stats.std },
  ];

  return (
    <div className="w-full">
      <h3 className="text-lg font-semibold mb-4">统计信息</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis label={{ value: '数值', angle: -90, position: 'insideLeft' }} />
          <Tooltip formatter={(value: number) => value.toFixed(6)} />
          <Legend />
          <Bar dataKey="value" fill="#7c3aed" name="统计值" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
