'use client'

import { useState } from 'react'
import type { RoleMetric, EmployeeRecord } from '@/types/monthly-kpi-report'

interface WorkforceSectionProps {
  roles: RoleMetric[]
  roleDaily: Record<string, any>
  roleAvgs: Record<string, any>
  managerDaily: Record<string, any>
  managerAvgs: Record<string, any>
  departmentDaily: Record<string, any>
  departmentAvgs: Record<string, any>
  allEmployees: EmployeeRecord[]
  workMode: 'all' | 'remote' | 'in-office'
  searchQuery: string
  onSearchChange: (query: string) => void
}

export default function WorkforceSection({
  roles,
  allEmployees,
  workMode,
  searchQuery,
  onSearchChange,
}: WorkforceSectionProps) {
  const [groupBy, setGroupBy] = useState<'role' | 'manager' | 'department'>('role')

  const filteredEmployees = allEmployees.filter(emp => {
    const matchesSearch = emp.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         emp.role.toLowerCase().includes(searchQuery.toLowerCase())
    
    if (workMode === 'in-office') {
      return matchesSearch && emp.workplace === 'In-Office Only'
    } else if (workMode === 'remote') {
      return matchesSearch && emp.workplace === 'Remote Only'
    }
    return matchesSearch
  })

  return (
    <div className="space-y-8">
      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex gap-2">
          {[
            { id: 'role', label: 'By Role' },
            { id: 'manager', label: 'By Manager' },
            { id: 'department', label: 'By Department' },
          ].map(option => (
            <button
              key={option.id}
              onClick={() => setGroupBy(option.id as any)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                groupBy === option.id
                  ? 'bg-brand-blue-500 text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
        
        <input
          type="text"
          placeholder="Search employees..."
          value={searchQuery}
          onChange={e => onSearchChange(e.target.value)}
          className="px-4 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-blue-500"
        />
      </div>

      {/* Role Overviews */}
      <div className="kpi-card">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Group Overview</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {roles.slice(0, 6).map(role => (
            <div key={role.role} className="p-4 bg-slate-50 rounded-lg">
              <p className="font-semibold text-slate-900">{role.role}</p>
              <div className="grid grid-cols-2 gap-2 mt-3 text-sm">
                <div>
                  <p className="text-slate-600">Avg Score</p>
                  <p className="text-lg font-bold text-brand-blue-600">{role.avg}</p>
                </div>
                <div>
                  <p className="text-slate-600">Avg Time</p>
                  <p className="text-lg font-bold text-slate-900">{role.avgTimeLabel}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Employee List */}
      <div className="kpi-card">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Employees ({filteredEmployees.length})</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="border-b border-slate-200">
              <tr className="text-left text-xs font-medium text-slate-600 uppercase">
                <th className="pb-3 px-4">Name</th>
                <th className="pb-3 px-4">Role</th>
                <th className="pb-3 px-4">Manager</th>
                <th className="pb-3 px-4">Score</th>
                <th className="pb-3 px-4">Active Time</th>
                <th className="pb-3 px-4">Work Mode</th>
              </tr>
            </thead>
            <tbody>
              {filteredEmployees.map((emp, idx) => (
                <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-3 px-4 text-sm font-medium text-slate-900">{emp.name}</td>
                  <td className="py-3 px-4 text-sm text-slate-600">{emp.role}</td>
                  <td className="py-3 px-4 text-sm text-slate-600">{emp.manager}</td>
                  <td className="py-3 px-4 text-sm">
                    <span className="font-bold text-brand-blue-600">{emp.score}</span>
                  </td>
                  <td className="py-3 px-4 text-sm text-slate-600">{emp.activeTime}</td>
                  <td className="py-3 px-4 text-sm">
                    <span className="px-2 py-1 bg-slate-100 text-slate-700 rounded text-xs font-medium">
                      {emp.workplace}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
