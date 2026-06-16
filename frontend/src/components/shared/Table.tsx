import React from 'react';

interface Column<T> {
  key: keyof T | string;
  header: string;
  render?: (value: T[keyof T], row: T) => React.ReactNode;
  className?: string;
  sortable?: boolean;
}

interface TableProps<T> {
  columns: Column<T>[];
  rows: T[];
  keyExtractor?: (row: T, index: number) => string;
  onRowClick?: (row: T) => void;
  striped?: boolean;
  hoverable?: boolean;
  rowClassName?: (row: T) => string;
}

export function Table<T extends Record<string, unknown>>({
  columns,
  rows,
  keyExtractor = (_, i) => String(i),
  onRowClick,
  striped = true,
  hoverable = true,
  rowClassName = () => '',
}: TableProps<T>): React.ReactElement {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm text-left">
        <thead className="bg-gray-100 border-b border-gray-300">
          <tr>
            {columns.map((col) => (
              <th
                key={String(col.key)}
                className={`px-4 py-3 font-semibold text-gray-700 ${col.className || ''}`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr
              key={keyExtractor(row, idx)}
              onClick={() => onRowClick?.(row)}
              className={`border-b border-gray-200 ${
                striped && idx % 2 === 1 ? 'bg-gray-50' : 'bg-white'
              } ${hoverable && onRowClick ? 'hover:bg-blue-50 cursor-pointer' : ''} ${rowClassName(row)}`}
            >
              {columns.map((col) => (
                <td key={String(col.key)} className={`px-4 py-3 ${col.className || ''}`}>
                  {col.render ? col.render(row[col.key as keyof T], row) : String(row[col.key as keyof T])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}