import React, { useState, useMemo } from 'react';
import { Section } from '../shared/Section';
import { Table } from '../shared/Table';
import { Badge } from '../shared/Badge';
import { EmptyState } from '../shared/EmptyState';
import { MonthlyKpiResponse, EmployeeRecord } from '../../types';

interface EmployeeTableProps {
  data: MonthlyKpiResponse;
  filterBy?: 'all' | 'flagged' | 'inactive' | 'top';
}

type FilterType = 'all' | 'flagged' | 'inactive' | 'top';

export const EmployeeTable: React.FC<EmployeeTableProps> = ({
  data,
  filterBy = 'all',
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<string>('name');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  const { ALL_EMPLOYEES, NEEDS_ATTENTION, INACTIVE, TOP_PERFORMERS } = data;

  // Determine employee status
  const getEmployeeStatus = (emp: EmployeeRecord): FilterType | null => {
    const inactive_ids = new Set(INACTIVE.map(e => e.employee_id));
    const flagged_ids = new Set(NEEDS_ATTENTION.map(e => e.employee_id));
    const top_ids = new Set(TOP_PERFORMERS.map(e => e.employee_id));

    if (inactive_ids.has(emp.employee_id)) return 'inactive';
    if (flagged_ids.has(emp.employee_id)) return 'flagged';
    if (top_ids.has(emp.employee_id)) return 'top';
    return 'all';
  };

  const getStatusBadge = (status: FilterType | null) => {
    if (status === 'flagged') return <Badge status="flagged" />;
    if (status === 'inactive') return <Badge status="inactive" />;
    if (status === 'top') return <Badge status="top" />;
    return <span className="text-xs text-gray-500">Active</span>;
  };

  // Filter and search
  const filteredRows = useMemo(() => {
    let result = ALL_EMPLOYEES;

    // Apply status filter
    if (filterBy !== 'all') {
      result = result.filter(emp => getEmployeeStatus(emp) === filterBy);
    }

    // Apply search
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        emp =>
          emp.name.toLowerCase().includes(q) ||
          emp.role.toLowerCase().includes(q) ||
          emp.department.toLowerCase().includes(q)
      );
    }

    // Apply sort
    result.sort((a, b) => {
      let aVal: any = a[sortBy as keyof EmployeeRecord];
      let bVal: any = b[sortBy as keyof EmployeeRecord];

      // Handle numeric strings
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        if (aVal.includes('%') || aVal.includes('h')) {
          // Time/percentage comparison
          return sortDir === 'asc'
            ? aVal.localeCompare(bVal)
            : bVal.localeCompare(aVal);
        }
      }

      if (aVal < bVal) return sortDir === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });

    return result;
  }, [ALL_EMPLOYEES, filterBy, searchQuery, sortBy, sortDir]);

  const columns = [
    {
      key: 'name' as const,
      header: 'Name',
      className: 'font-semibold',
    },
    {
      key: 'role' as const,
      header: 'Role',
    },
    {
      key: 'department' as const,
      header: 'Department',
    },
    {
      key: 'overall_score' as const,
      header: 'Score',
      className: 'text-center',
    },
    {
      key: 'overall_active_pct' as const,
      header: 'Active %',
      className: 'text-center',
    },
    {
      key: 'in_office_pct' as const,
      header: 'In-Office',
      className: 'text-center',
    },
    {
      key: 'remote_pct' as const,
      header: 'Remote',
      className: 'text-center',
    },
  ];

  if (ALL_EMPLOYEES.length === 0) {
    return <EmptyState title="No employees" message="No employee data available" icon="👥" />;
  }

  return (
    <Section 
      title="Employee Roster" 
      description={`Showing ${filteredRows.length} of ${ALL_EMPLOYEES.length} employees`}
    >
      <div className="mb-4 space-y-3">
        <input
          type="text"
          placeholder="Search by name, role, or department..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
        />
      </div>

      <div className="overflow-x-auto">
        <Table
          columns={columns}
          rows={filteredRows}
          keyExtractor={(row) => row.employee_id}
          striped
          hoverable
          rowClassName={(row) => {
            const status = getEmployeeStatus(row);
            if (status === 'inactive') return 'bg-red-50';
            if (status === 'flagged') return 'bg-yellow-50';
            if (status === 'top') return 'bg-blue-50';
            return '';
          }}
        />
      </div>
    </Section>
  );
};