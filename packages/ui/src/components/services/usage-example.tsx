// Example usage of ServiceStatusWidget in your web app
// Add this to your layout or main component

import { ServiceStatusWidget } from "@workspace/ui/components/services/ServiceStatusWidget";
import { ReactNode } from "react";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      {/* Your main content */}
      <main>{children}</main>

      {/* Service Status Widget - Fixed position button */}
      <ServiceStatusWidget />
    </div>
  );
}

// Alternative: Use it in a specific page
export function ServicesPage() {
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">Services Dashboard</h1>

      {/* Your other content */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Your dashboard cards */}
      </div>

      {/* Service Status Widget */}
      <ServiceStatusWidget />
    </div>
  );
}

// Custom positioning example
export function CustomServiceWidget() {
  return (
    <div className="relative">
      {/* Your content */}

      {/* Custom positioned service widget */}
      <ServiceStatusWidget className="bottom-4 right-4" />
    </div>
  );
}
