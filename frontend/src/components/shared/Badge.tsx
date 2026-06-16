import React from 'react';

type BadgeStatus = 'flagged' | 'inactive' | 'top' | 'active' | 'warning' | 'critical';

interface BadgeProps {
  status: BadgeStatus;
  label?: string;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ status, label, className = '' }) => {
  const statusConfig = {
    flagged: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Flagged' },
    inactive: { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Inactive' },
    top: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Top Performer' },
    active: { bg: 'bg-green-100', text: 'text-green-800', label: 'Active' },
    warning: { bg: 'bg-amber-100', text: 'text-amber-800', label: 'Warning' },
    critical: { bg: 'bg-red-100', text: 'text-red-800', label: 'Critical' },
  };

  const config = statusConfig[status];
  const displayLabel = label || config.label;

  return (
    <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${config.bg} ${config.text} ${className}`}>
      {displayLabel}
    </span>
  );
};