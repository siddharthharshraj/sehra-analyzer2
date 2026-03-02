"use client";

import useSWR from "swr";
import { apiGet } from "@/lib/api-client";
import { FormatCards } from "@/components/export/format-cards";
import { ShareForm } from "@/components/export/share-form";
import { ShareLinksTable } from "@/components/export/share-links-table";
import type { ShareLink } from "@/lib/types";

interface ExportTabProps {
  sehraId: string;
  country: string;
}

export function ExportTab({ sehraId, country }: ExportTabProps) {
  const { data: shareLinks, mutate: mutateLinks } = useSWR<ShareLink[]>(
    `/shares/${sehraId}`,
    (url: string) => apiGet<ShareLink[]>(url),
  );

  return (
    <div className="space-y-6">
      <div>
        <h3 className="mb-3 font-medium">Download Report</h3>
        <FormatCards sehraId={sehraId} country={country} />
      </div>

      <div>
        <h3 className="mb-3 font-medium">Share Report</h3>
        <ShareForm sehraId={sehraId} onCreated={() => mutateLinks()} />
      </div>

      <ShareLinksTable
        links={shareLinks || []}
        onRefresh={() => mutateLinks()}
      />
    </div>
  );
}
