import React from 'react';

export const LoadingState: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="animate-spin h-12 w-12 rounded-full border-4 border-gray-300 border-t-blue-600 mb-4"></div>
      <p className="text-gray-600 font-medium">Loading KPI data...</p>
    </div>
  );
};