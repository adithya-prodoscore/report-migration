import React from 'react';

interface SectionProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}

export const Section: React.FC<SectionProps> = ({
  title,
  description,
  children,
  className = '',
}) => {
  return (
    <div className={`bg-gray-50 rounded-lg p-6 mb-6 ${className}`}>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">{title}</h2>
      {description && <p className="text-gray-600 mb-4">{description}</p>}
      {children}
    </div>
  );
};