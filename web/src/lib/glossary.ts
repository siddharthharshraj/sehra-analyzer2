export const GLOSSARY: Record<string, string> = {
  enabler: "A factor that helps or supports eye health services in a district. More enablers = better readiness.",
  barrier: "A factor that blocks or hinders eye health services. Fewer barriers = better readiness.",
  "enabler rate": "The percentage of findings that are enablers (positive factors) out of all findings. Higher is better.",
  component: "One of the 6 key areas assessed in SEHRA: Context, Policy, Service Delivery, Human Resources, Supply Chain, and Barriers.",
  "qualitative entry": "A specific observation or remark extracted from the assessment, classified by AI as an enabler or barrier.",
  confidence: "How certain the AI is about its classification (0-100%). Higher confidence means the AI is more sure.",
  theme: "The topic category of an entry, such as Infrastructure, Funding, Training, etc.",
  classification: "Whether an entry is an enabler (positive) or barrier (negative) factor.",
  "batch approve": "Accept all AI classifications above a confidence threshold at once, instead of reviewing one by one.",
  draft: "Initial status of an assessment. Entries can still be edited and reviewed.",
  reviewed: "Assessment where all entries have been checked. Ready for publishing.",
  published: "Final status. Assessment is locked and available for export and sharing.",
  codebook: "The master list of all SEHRA questions organized by component. Used as the template for assessments.",
  sehra: "School Eye Health Rapid Assessment - a standardized tool for evaluating eye health services at district level.",
};

export const COMPONENT_DESCRIPTIONS: Record<string, string> = {
  context: "Background information about the district including demographics, geography, and existing health infrastructure.",
  policy: "Government policies, guidelines, and governance structures related to eye health services.",
  service_delivery: "How eye health services are actually provided, including screening programs and referral pathways.",
  human_resources: "Staffing levels, training, and capacity of eye health workers in the district.",
  supply_chain: "Availability and distribution of equipment, medicines, and supplies for eye health.",
  barriers: "Obstacles and challenges that prevent effective eye health service delivery.",
};
