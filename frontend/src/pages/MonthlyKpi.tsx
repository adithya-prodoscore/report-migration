import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { MonthlyKpiReport } from '../components/MonthlyKpi/MonthlyKpiReport';
import { LoadingState } from '../components/shared/LoadingState';
import { MonthlyKpiResponse, ApiError } from '../types';
import { fetchMonthlyKpi } from '../api/client';

export const MonthlyKpiPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [data, setData] = useState<MonthlyKpiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  // Extract query parameters
  const domainId = parseInt(searchParams.get('domain_id') || '9', 10);
  const startDate = searchParams.get('start_date') || '2026-05-01';
  const endDate = searchParams.get('end_date') || '2026-05-29';

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchMonthlyKpi({
        domain_id: domainId,
        start_date: startDate,
        end_date: endDate,
      });
      setData(result);
    } catch (err) {
      setError(err as ApiError);
      console.error('Failed to fetch KPI report:', err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch on mount or when params change
  useEffect(() => {
    fetchData();
  }, [domainId, startDate, endDate]);

  if (loading) {
    return (
      <div className="bg-gray-50 min-h-screen flex items-center justify-center">
        <LoadingState />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-50 min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-600 mb-4">Error Loading Report</h2>
          <p className="text-gray-600 mb-6">{error.detail || error.message}</p>
          <button
            onClick={fetchData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-gray-50 min-h-screen flex items-center justify-center">
        <p className="text-gray-600">No data available</p>
      </div>
    );
  }

  return (
    <MonthlyKpiReport
      data={data}
      onRefresh={fetchData}
      isLoading={loading}
    />
  );
};

export default MonthlyKpiPage;