import React from "react";

function page() {
  return (
    <div className="flex flex-1 flex-col gap-6 p-6 max-w-5xl mx-auto">
      <div className="space-y-4">
        <h1 className="text-3xl font-bold tracking-tight">Knowledge Source</h1>
        <p className="text-muted-foreground text-lg">
          Connect your repositories to access and manage your sources in one
          place.
        </p>
      </div>
    </div>
  );
}

export default page;
