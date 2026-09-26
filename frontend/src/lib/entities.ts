import {
  BookOpen,
  Compass,
  Database,
  FlaskConical,
  Gauge,
  Lightbulb,
  type LucideIcon,
  TriangleAlert,
  User,
  Waypoints,
} from "lucide-react";

import type { EntityType, VerificationStatus } from "@/lib/api/types";

export interface EntityStyle {
  label: string;
  plural: string;
  color: string; // hex, for SVG / inline styles
  icon: LucideIcon;
}

export const ENTITY_STYLES: Record<EntityType, EntityStyle> = {
  Paper: { label: "Paper", plural: "Papers", color: "#0e0e10", icon: BookOpen },
  Method: { label: "Method", plural: "Methods", color: "#3d4fa8", icon: FlaskConical },
  Dataset: { label: "Dataset", plural: "Datasets", color: "#1f7a7a", icon: Database },
  Metric: { label: "Metric", plural: "Metrics", color: "#9c7a3c", icon: Gauge },
  Finding: { label: "Finding", plural: "Findings", color: "#2f7d5b", icon: Lightbulb },
  Limitation: { label: "Limitation", plural: "Limitations", color: "#b5542e", icon: TriangleAlert },
  FutureWork: { label: "Future work", plural: "Future work", color: "#7a4fa0", icon: Compass },
  ResearchGap: { label: "Research gap", plural: "Research gaps", color: "#6f6b64", icon: Waypoints },
  Author: { label: "Author", plural: "Authors", color: "#6f6b64", icon: User },
};

/** Types shown in the graph and twin (Author/ResearchGap are not produced yet). */
export const GRAPH_TYPES: EntityType[] = [
  "Paper",
  "Method",
  "Dataset",
  "Metric",
  "Finding",
  "Limitation",
  "FutureWork",
];

export const CLAIM_TYPES: EntityType[] = ["Finding", "Limitation", "FutureWork"];

export const VERIFICATION_STYLES: Record<
  VerificationStatus,
  { label: string; text: string; bg: string; dot: string; description: string }
> = {
  verified: {
    label: "Verified",
    text: "text-verified",
    bg: "bg-verified-soft",
    dot: "bg-verified",
    description: "Quote located in the paper and judged to support the claim",
  },
  flagged: {
    label: "Flagged",
    text: "text-flagged",
    bg: "bg-flagged-soft",
    dot: "bg-flagged",
    description: "Quote located, but only partially or not supporting the claim",
  },
  unverified: {
    label: "Unverified",
    text: "text-unverified",
    bg: "bg-unverified-soft",
    dot: "bg-unverified",
    description: "Quote located, semantic check not completed",
  },
};

export const RELATION_LABELS: Record<string, string> = {
  USES: "uses",
  EVALUATES: "evaluates on",
  REPORTS: "reports",
  CLAIMS: "claims",
  STATES: "states",
  COMPARES: "compares",
  IMPROVES: "improves",
  CONTRADICTS: "contradicts",
  SUGGESTS: "suggests",
  CITES: "cites",
  AUTHORED: "authored",
};

export function asVerificationStatus(value?: string | null): VerificationStatus | null {
  return value && value in VERIFICATION_STYLES ? (value as VerificationStatus) : null;
}
