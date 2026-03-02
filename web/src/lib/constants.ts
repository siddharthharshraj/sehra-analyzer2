export const COMPONENTS = [
  "context",
  "policy",
  "service_delivery",
  "human_resources",
  "supply_chain",
  "barriers",
] as const;

export type ComponentName = (typeof COMPONENTS)[number];

export const COMPONENT_LABELS: Record<ComponentName, string> = {
  context: "Contextual/Demographic",
  policy: "Policy & Governance",
  service_delivery: "Service Delivery",
  human_resources: "Human Resources",
  supply_chain: "Supply Chain",
  barriers: "Barriers & Challenges",
};

export const COMPONENT_COLORS: Record<ComponentName, string> = {
  context: "#0D7377",
  policy: "#10857A",
  service_delivery: "#14967E",
  human_resources: "#18A781",
  supply_chain: "#1CB885",
  barriers: "#CC3333",
};

export const CLASSIFICATIONS = ["enabler", "barrier", "neutral"] as const;

export const THEMES = [
  "Infrastructure",
  "Funding",
  "Training",
  "Policy",
  "Community",
  "Technology",
  "Human Resources",
  "Supply Chain",
  "Governance",
  "Access",
  "Quality",
  "Other",
] as const;

export const STATUS_COLORS: Record<string, string> = {
  draft: "bg-amber-100 text-amber-800",
  reviewed: "bg-blue-100 text-blue-800",
  published: "bg-green-100 text-green-800",
};

export const TEAL = "#0D7377";
export const TEAL_DARK = "#095456";
export const RED = "#CC3333";
