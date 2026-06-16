// API client for Monthly KPI Report

import { MonthlyKpiResponse, ApiError } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface FetchMonthlyKpiParams {
  domain_id: number;
  start_date: string; // YYYY-MM-DD
  end_date: string; // YYYY-MM-DD
}

/**
 * Fetch monthly KPI report from backend
 * GET /api/v1/monthly-kpi?domain_id=9&start_date=2026-05-01&end_date=2026-05-29
 */
export async function fetchMonthlyKpi(
  params: FetchMonthlyKpiParams
): Promise<MonthlyKpiResponse> {
  const queryParams = new URLSearchParams({
    domain_id: String(params.domain_id),
    start_date: params.start_date,
    end_date: params.end_date,
  });

  const url = `${API_BASE_URL}/api/v1/monthly-kpi?${queryParams.toString()}`;

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      credentials: 'include', // For CORS with cookies
    });

    if (!response.ok) {
      const error: ApiError = {
        status: response.status,
        message: `API error: ${response.statusText}`,
      };

      try {
        const errorBody = await response.json();
        error.detail = errorBody.detail || JSON.stringify(errorBody);
      } catch {
        // Ignore JSON parse error
      }

      throw error;
    }

    const data: MonthlyKpiResponse = await response.json();
    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    throw {
      status: 0,
      message: 'Network error or invalid response',
      detail: error instanceof Error ? error.message : String(error),
    } as ApiError;
  }
}

/**
 * Format active minutes as human-readable string
 * E.g., 269 -> "4h 29min"
 */
export function formatActiveMinutes(minutes: number): string {
  if (minutes === 0) return "0min";
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours === 0) return `${mins}min`;
  if (mins === 0) return `${hours}h`;
  return `${hours}h ${mins}min`;
}

/**
 * Format percentage string (already % included)
 */
export function formatPercentage(pct: string | number): string {
  if (typeof pct === 'string') return pct;
  return `${pct.toFixed(1)}%`;
}

/**
 * Determine triage status badge color
 */
export function getTriageColor(
  status: 'flagged' | 'inactive' | 'top' | 'active'
): 'red' | 'yellow' | 'gray' | 'blue' {
  switch (status) {
    case 'flagged':
      return 'yellow';
    case 'inactive':
      return 'gray';
    case 'top':
      return 'blue';
    case 'active':
      return 'gray';
    default:
      return 'gray';
  }
}