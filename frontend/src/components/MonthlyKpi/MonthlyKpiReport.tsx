import React from 'react';
import { MonthlyKpiResponse } from '../../types';
import { KpiHeader } from './KpiHeader';
import { KpiCards } from './KpiCards';
import { TriageSection } from './TriageSection';
import { RoleBaselines } from './RoleBaselines';
import { EmployeeTable } from './EmployeeTable';

interface MonthlyKpiReportProps {
  data: MonthlyKpiResponse;
  onRefresh?: () => void;
  isLoading?: boolean;
}

export const MonthlyKpiReport: React.FC<MonthlyKpiReportProps> = ({
  data,
  onRefresh = () => {},
  isLoading = false,
}) => {
  return (
    <div className="bg-gray-50 min-h-screen">
      <KpiHeader
        startDate={data.start_date}
        endDate={data.end_date}
        onRefresh={onRefresh}
        isLoading={isLoading}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* KPI Cards */}
        <KpiCards data={data} />

        {/* Triage Section */}
        <TriageSection data={data} />

        {/* Role Baselines */}
        <RoleBaselines data={data} />

        {/* Employee Table */}
        <EmployeeTable data={data} filterBy="all" />
      </div>
    </div>
  );
};