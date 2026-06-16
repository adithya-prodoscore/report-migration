// Tool/Product Registry
// Metadata for all tools tracked in KPI reports

export interface ToolMetadata {
  name: string;
  type: 'collab' | 'call' | 'focus' | 'other';
  icon: string;
  color: string;
  category: string;
}

export const TOOL_REGISTRY: Record<string, ToolMetadata> = {
  gmail: {
    name: 'Gmail',
    type: 'collab',
    icon: '📧',
    color: '#EA4335',
    category: 'Email',
  },
  slack: {
    name: 'Slack',
    type: 'collab',
    icon: '💬',
    color: '#36C5F0',
    category: 'Chat',
  },
  google_meet: {
    name: 'Google Meet',
    type: 'call',
    icon: '📹',
    color: '#00BF63',
    category: 'Meetings',
  },
  microsoft_teams: {
    name: 'Microsoft Teams',
    type: 'call',
    icon: '👥',
    color: '#6264A7',
    category: 'Meetings',
  },
  zoom: {
    name: 'Zoom',
    type: 'call',
    icon: '🎥',
    color: '#0B5CFF',
    category: 'Meetings',
  },
  notion: {
    name: 'Notion',
    type: 'focus',
    icon: '📝',
    color: '#000000',
    category: 'Productivity',
  },
  jira: {
    name: 'Jira',
    type: 'focus',
    icon: '🎯',
    color: '#0052CC',
    category: 'Project Management',
  },
  asana: {
    name: 'Asana',
    type: 'focus',
    icon: '✅',
    color: '#F06A4D',
    category: 'Project Management',
  },
  github: {
    name: 'GitHub',
    type: 'focus',
    icon: '🐙',
    color: '#181717',
    category: 'Development',
  },
  gitlab: {
    name: 'GitLab',
    type: 'focus',
    icon: '🦊',
    color: '#FC6D26',
    category: 'Development',
  },
  figma: {
    name: 'Figma',
    type: 'focus',
    icon: '🎨',
    color: '#F24E1E',
    category: 'Design',
  },
  tableau: {
    name: 'Tableau',
    type: 'focus',
    icon: '📊',
    color: '#2E75B6',
    category: 'Analytics',
  },
  salesforce: {
    name: 'Salesforce',
    type: 'focus',
    icon: '🤝',
    color: '#00A1E0',
    category: 'CRM',
  },
};

/**
 * Get tool metadata by slug or name
 */
export function getTool(
  slugOrName: string,
  defaultTool?: ToolMetadata
): ToolMetadata | undefined {
  const tool = TOOL_REGISTRY[slugOrName.toLowerCase()];
  if (tool) return tool;

  // Fallback search by name
  return Object.values(TOOL_REGISTRY).find(
    t => t.name.toLowerCase() === slugOrName.toLowerCase()
  ) || defaultTool;
}

/**
 * Get icon and color for a tool
 */
export function getToolIcon(slug: string): string {
  const tool = getTool(slug);
  return tool?.icon || '🔧';
}

export function getToolColor(slug: string): string {
  const tool = getTool(slug);
  return tool?.color || '#999999';
}

/**
 * List all tools by category
 */
export function getToolsByCategory(category: string): ToolMetadata[] {
  return Object.values(TOOL_REGISTRY).filter(t => t.category === category);
}

/**
 * Get all unique categories
 */
export function getCategories(): string[] {
  return [...new Set(Object.values(TOOL_REGISTRY).map(t => t.category))];
}