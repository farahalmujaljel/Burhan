import { Suspense } from "react";

import { KnowledgeGraphView } from "@/components/graph/KnowledgeGraphView";

export const metadata = { title: "Knowledge Graph" };

export default function GraphPage() {
  // useSearchParams (for ?focus=) must sit under a Suspense boundary.
  return (
    <Suspense>
      <KnowledgeGraphView />
    </Suspense>
  );
}
