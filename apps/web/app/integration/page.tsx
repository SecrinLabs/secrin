"use client";

import React, { useState } from "react";

import {
  IntegrationButtons,
  IntegrationModals,
  IntegrationModalType,
} from "@workspace/ui/components/integrations";

function Integration() {
  const [open, setOpen] = useState<IntegrationModalType>(null);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 dark:bg-neutral-950 py-10">
      <h1 className="text-3xl font-bold mb-6">App Integrations</h1>
      <IntegrationButtons setOpen={setOpen} />
      <IntegrationModals open={open} setOpen={setOpen} />
    </div>
  );
}

export default Integration;
