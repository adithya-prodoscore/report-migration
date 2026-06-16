import React from 'react';

interface EmptyStateProps {
  title: string;
  message: string;
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ title, message, icon }) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      {icon && <div className="text-4xl mb-4">{icon}</div>}
      <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      <p className="text-gray-600 mt-2">{message}</p>
    </div>
  );
};