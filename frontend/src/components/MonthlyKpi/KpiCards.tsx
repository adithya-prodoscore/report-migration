import React from 'react';
import { Card } from '../shared/Card';
import { Metric } from '../shared/Metric';
import { MonthlyKpiResponse } from '../../types';

interface KpiCardsProps {
  data: MonthlyKpiResponse;
}

export const KpiCards: React.FC<KpiCardsProps> = ({ data }) => {
  const { COMPANY, NEEDS_ATTENTION, INACTIVE } = data;
  
  const flaggedCount = NEEDS_ATTENTION.length;
  const inactiveCount = INACTIVE.length;
  const totalFlaggedPct = COMPANY.total_employees > 0 
    ? ((flaggedCount + inactiveCount) / COMPANY.total_employees * 100).toFixed(1)
    : '0.0';

  const formatMinutes = (mins: number): string => {
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    if (h === 0) return `${m}min`;
    if (m === 0) return `${h}h`;
    return `${h}h ${m}min`;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      <Card variant="elevated">
        <Metric
          label="Total Employees"
          value={COMPANY.total_employees}
          color="blue"
        />
      </Card>
      
      <Card variant="elevated">
        <Metric
          label="Average Score"
          value={COMPANY.avg_score}
          color="blue"
        />
      </Card>
      
      <Card variant="elevated">
        <Metric
          label="Avg Active Time"
          value={formatMinutes(COMPANY.avg_active_minutes)}
          color="green"
        />
      </Card>
      
      <Card variant="elevated">
        <Metric
          label="% Flagged / Inactive"
          value={totalFlaggedPct}
          unit="%"
          color={parseFloat(totalFlaggedPct) > 20 ? 'red' : 'yellow'}
        />
      </Card>
    </div>
  );
};