import Link from 'next/link'
import { REPORTS } from './reports/registry'

export default function HomePage() {
  return (
    <main className="max-w-6xl mx-auto px-4 py-12 sm:px-6 lg:px-8 w-full flex-1 flex flex-col justify-start">
      {/* Header Section */}
      <div className="mb-10 border-b border-slate-200 pb-6">
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-950 sm:text-4xl">
          Prodoscore Reports
        </h1>
        <p className="mt-2 text-base text-slate-500">
          Select an available dashboard below to analyze metrics and performance data.
        </p>
      </div>

      {/* Reports Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {REPORTS.map((report) => (
          <Link 
            key={report.slug} 
            href={`/reports/${report.slug}`}
            className="block p-6 bg-white rounded-xl border border-slate-200 shadow-xs hover:shadow-md hover:border-indigo-500 transition-all duration-200 group"
          >
            <div className="flex flex-col h-full justify-between">
              <div>
                <h2 className="text-lg font-bold text-slate-900 group-hover:text-indigo-600 transition-colors duration-200">
                  {report.title}
                </h2>
                <p className="mt-2 text-sm text-slate-500 line-clamp-3 leading-relaxed">
                  {report.description}
                </p>
              </div>
              
              {/* Action Indicator */}
              <div className="mt-5 flex items-center text-xs font-semibold text-indigo-600 group-hover:text-indigo-700">
                Open Dashboard
                <svg 
                  className="ml-1 w-4 h-4 transform group-hover:translate-x-1 transition-transform duration-200" 
                  fill="none" 
                  viewBox="0 0 24 24" 
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Empty State Layout */}
      {REPORTS.length === 0 && (
        <div className="text-center py-16 px-4 border-2 border-dashed border-slate-200 rounded-xl bg-white max-w-sm mx-auto w-full mt-12">
          <svg 
            className="mx-auto h-10 w-10 text-slate-400" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 13h6m-3-3v6m-9 1V4a2 2 0 012-2h6l2 2h6a2 2 0 012 2v12a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
          </svg>
          <h3 className="mt-4 text-sm font-semibold text-slate-900">No reports ready</h3>
          <p className="mt-1 text-sm text-slate-400">
            Once migrations create new reports, they will show up automatically.
          </p>
        </div>
      )}
    </main>
  )
}