import React, { useState } from 'react';
import { Section } from '../shared/Section';
import { Table } from '../shared/Table';
import { MonthlyKpiResponse, AvgsRecord } from '../../types';

interface RoleBaselineRow {
  role_name: string;
  avg_score: number;
  avg_active_minutes: number;
  avg_active_pct: string;
}

interface RoleBaselinesProps {
  data: MonthlyKpiResponse;
}

export const RoleBaselines: React.FC<RoleBaselinesProps> = ({ data }) => {
  const { ROLES } = data;
  
  const rows: RoleBaselineRow[] = Object.entries(ROLES).map(([roleName, avgs]) => ({
    role_name: roleName,
    avg_score: avgs.avg_score,
    avg_active_minutes: avgs.avg_active_minutes,
    avg_active_pct: avgs.avg_active_pct,
  }));

  const formatMinutes = (mins: number): string => {
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    if (h === 0) return `${m}min`;
    if (m === 0) return `${h}h`;
    return `${h}h ${m}min`;
  };

  const columns = [
    {
      key: 'role_name' as const,
      header: 'Role',
      className: 'font-semibold',
    },
    {
      key: 'avg_score' as const,
      header: 'Avg Score',
      className: 'text-center',
    },
    {
      key: 'avg_active_minutes' as const,
      header: 'Avg Active Time',
      render: (val: number) => formatMinutes(val),
      className: 'text-center',
    },
    {
      key: 'avg_active_pct' as const,
      header: 'Avg % Active',
      className: 'text-center',
    },
  ];

  return (
    <Section 
      title="Role Baselines" 
      description="Average performance metrics by role"
    >
      <Table columns={columns} rows={rows} striped />
    </Section>
  );
};