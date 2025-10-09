import InviteForm from "@/components/invite/InviteForm";
import React, { Suspense } from "react";

function page() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <InviteForm />
    </Suspense>
  );
}

export default page;
