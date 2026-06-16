import React from 'react';

interface CardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'elevated' | 'bordered';
}

export const Card: React.FC<CardProps> = ({
  title,
  children,
  className = '',
  variant = 'default',
}) => {
  const baseStyles = 'p-4 rounded-lg';
  const variantStyles = {
    default: 'bg-white border border-gray-200',
    elevated: 'bg-white shadow-md',
    bordered: 'bg-gray-50 border-2 border-gray-300',
  };

  return (
    <div className={`${baseStyles} ${variantStyles[variant]} ${className}`}>
      {title && <h3 className="text-lg font-semibold mb-4 text-gray-800">{title}</h3>}
      {children}
    </div>
  );
};