
import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { Sentiment } from '../types';

interface SentimentChartProps {
  data: { name: string; value: number }[];
}

const COLORS: Record<string, string> = {
  [Sentiment.Positive]: '#10B981', // Emerald 500
  [Sentiment.Negative]: '#EF4444', // Red 500
  [Sentiment.Neutral]: '#6B7280',  // Gray 500
};

export const SentimentChart: React.FC<SentimentChartProps> = ({ data }) => {
  return (
    <div style={{ width: '100%', height: 300 }}>
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
            nameKey="name"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[entry.name]} />
            ))}
          </Pie>
          <Tooltip 
             contentStyle={{ 
                backgroundColor: 'rgba(31, 41, 55, 0.8)', // gray-800 with opacity
                borderColor: '#4B5563', // gray-600
                borderRadius: '0.5rem',
                color: '#F9FAFB', // gray-50
            }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
