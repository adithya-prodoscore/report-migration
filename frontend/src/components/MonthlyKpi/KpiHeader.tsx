import React from 'react';

interface KpiHeaderProps {
  startDate: string;
  endDate: string;
  onRefresh: () => void;
  isLoading?: boolean;
}

export const KpiHeader: React.FC<KpiHeaderProps> = ({
  startDate,
  endDate,
  onRefresh,
  isLoading = false,
}) => {
  const formatDateRange = (start: string, end: string): string => {
    const s = new Date(start);
    const e = new Date(end);
    const monthStart = s.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    const monthEnd = e.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    return `${monthStart} - ${monthEnd}`;
  };

  return (
    <div className="bg-white border-b border-gray-200 px-6 py-6 mb-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Monthly KPI Report</h1>
          <p className="text-gray-600 mt-2">{formatDateRange(startDate, endDate)}</p>
        </div>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {isLoading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>
    </div>
  );
};