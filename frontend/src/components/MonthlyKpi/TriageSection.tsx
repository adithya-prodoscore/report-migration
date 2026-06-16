import React, { useState } from 'react';
import { Card } from '../shared/Card';
import { Section } from '../shared/Section';
import { Badge } from '../shared/Badge';
import { EmptyState } from '../shared/EmptyState';
import { MonthlyKpiResponse, TriageEmployee } from '../../types';

interface TriageSectionProps {
  data: MonthlyKpiResponse;
}

const TriageList: React.FC<{ items: TriageEmployee[]; limit?: number }> = ({ items, limit = 3 }) => {
  const displayed = items.slice(0, limit);
  
  if (items.length === 0) {
    return <EmptyState title="None" message="No employees in this category" icon="✓" />;
  }

  return (
    <div className="space-y-3">
      {displayed.map((emp) => (
        <div key={emp.employee_id} className="flex justify-between items-center p-3 bg-gray-50 rounded">
          <div>
            <p className="font-medium text-gray-900">{emp.name}</p>
            <p className="text-sm text-gray-600">{emp.role}</p>
          </div>
          <div className="text-right">
            <p className="font-semibold text-gray-900">{emp.score}</p>
            <p className="text-sm text-gray-600">{emp.active_minutes}min</p>
          </div>
        </div>
      ))}
      {items.length > limit && (
        <p className="text-sm text-blue-600 font-medium py-2">
          +{items.length - limit} more
        </p>
      )}
    </div>
  );
};

export const TriageSection: React.FC<TriageSectionProps> = ({ data }) => {
  const { NEEDS_ATTENTION, INACTIVE, TOP_PERFORMERS } = data;

  return (
    <Section title="Employee Triage" description="Quick view of employee performance categories">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Needs Attention */}
        <Card title="Needs Attention" variant="bordered">
          <Badge status="flagged" className="mb-4 block" />
          <TriageList items={NEEDS_ATTENTION} />
        </Card>

        {/* Inactive */}
        <Card title="Inactive" variant="bordered">
          <Badge status="inactive" className="mb-4 block" />
          <TriageList items={INACTIVE} />
        </Card>

        {/* Top Performers */}
        <Card title="Top Performers" variant="bordered">
          <Badge status="top" className="mb-4 block" />
          <TriageList items={TOP_PERFORMERS} />
        </Card>
      </div>
    </Section>
  );
};