'use client'

import type { EmployeeRecord, GroupAvgs, ToolMeta } from '@/types/monthly-kpi-report'

interface DataSectionProps {
  allEmployees: EmployeeRecord[]
  companyAvgs: GroupAvgs
  roleAvgs: Record<string, GroupAvgs>
  managerAvgs: Record<string, GroupAvgs>
  departmentAvgs: Record<string, GroupAvgs>
  toolMeta: Record<string, ToolMeta>
}

export default function DataSection({
  allEmployees,
  companyAvgs,
  roleAvgs,
  departmentAvgs,
}: DataSectionProps) {
  return (
    <div className="space-y-8">
      {/* Data Table */}
      <div className="kpi-card">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-slate-900">Employee Metrics</h3>
          <button className="px-4 py-2 bg-brand-blue-500 text-white rounded-lg text-sm font-medium hover:bg-brand-blue-600 transition-colors">
            Export CSV
          </button>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-200 bg-slate-50">
              <tr className="text-left text-xs font-semibold text-slate-600 uppercase">
                <th className="py-3 px-4">Employee</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4">Score</th>
                <th className="py-3 px-4">Mon-Fri</th>
                <th className="py-3 px-4">Active Time</th>
                <th className="py-3 px-4">% Active</th>
              </tr>
            </thead>
            <tbody>
              {allEmployees.map((emp, idx) => (
                <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-3 px-4 font-medium text-slate-900">{emp.name}</td>
                  <td className="py-3 px-4 text-slate-600">{emp.role}</td>
                  <td className="py-3 px-4">
                    <span className="font-bold text-brand-blue-600">{emp.score}</span>
                  </td>
                  <td className="py-3 px-4 text-slate-600 text-xs">
                    {emp.mon} / {emp.tue} / {emp.wed} / {emp.thu} / {emp.fri}
                  </td>
                  <td className="py-3 px-4 text-slate-600">{emp.activeTime}</td>
                  <td className="py-3 px-4 text-slate-600">{emp.pctActive}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Aggregates */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Roles */}
        {Object.entries(roleAvgs).length > 0 && (
          <div className="kpi-card">
            <h4 className="font-semibold text-slate-900 mb-4">Role Averages</h4>
            <div className="space-y-3">
              {Object.entries(roleAvgs).slice(0, 5).map(([role, avg]) => (
                <div key={role} className="flex justify-between items-center p-2 bg-slate-50 rounded">
                  <span className="text-sm text-slate-600">{role}</span>
                  <span className="font-semibold text-brand-blue-600">{avg.score}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Departments */}
        {Object.entries(departmentAvgs).length > 0 && (
          <div className="kpi-card">
            <h4 className="font-semibold text-slate-900 mb-4">Department Averages</h4>
            <div className="space-y-3">
              {Object.entries(departmentAvgs).slice(0, 5).map(([dept, avg]) => (
                <div key={dept} className="flex justify-between items-center p-2 bg-slate-50 rounded">
                  <span className="text-sm text-slate-600">{dept}</span>
                  <span className="font-semibold text-brand-blue-600">{avg.score}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Company Avgs Summary */}
      <div className="kpi-card">
        <h4 className="font-semibold text-slate-900 mb-4">Company Averages</h4>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          {[
            { label: 'Score', value: companyAvgs.score },
            { label: 'Active Time', value: companyAvgs.activeTime },
            { label: '% Active', value: companyAvgs.pctActive },
            { label: 'First Activity', value: companyAvgs.firstActivity },
          ].map(item => (
            <div key={item.label} className="p-3 bg-slate-50 rounded-lg">
              <p className="text-xs text-slate-600 font-medium">{item.label}</p>
              <p className="text-base font-bold text-slate-900 mt-1">{item.value}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
