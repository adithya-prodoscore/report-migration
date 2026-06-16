import React from 'react';

type MetricColor = 'green' | 'yellow' | 'red' | 'blue' | 'gray';

interface MetricProps {
  label: string;
  value: string | number;
  unit?: string;
  color?: MetricColor;
  trend?: { direction: 'up' | 'down' | 'neutral'; value: string };
}

export const Metric: React.FC<MetricProps> = ({
  label,
  value,
  unit = '',
  color = 'gray',
  trend,
}) => {
  const colorClasses = {
    green: 'text-green-600',
    yellow: 'text-yellow-600',
    red: 'text-red-600',
    blue: 'text-blue-600',
    gray: 'text-gray-600',
  };

  return (
    <div className="text-center py-4">
      <p className="text-sm text-gray-500 font-medium">{label}</p>
      <p className={`text-3xl font-bold mt-2 ${colorClasses[color]}`}>
        {value}
        {unit && <span className="text-lg ml-2">{unit}</span>}
      </p>
      {trend && (
        <p className={`text-sm mt-2 ${trend.direction === 'up' ? 'text-green-600' : 'text-red-600'}`}>
          {trend.direction === 'up' ? '↑' : '↓'} {trend.value}
        </p>
      )}
    </div>
  );
};