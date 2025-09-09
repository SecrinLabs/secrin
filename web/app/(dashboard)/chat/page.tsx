import { DevSecrinChat } from "@/components/chat";
import React from "react";

function page() {
  return (
    <div className="flex justify-center items-center">
      {/* <ChatInput /> */}
      <DevSecrinChat
        className="flex justify-center items-center py-6
        md:min-h-[calc(100vh-64px)]
        fixed bottom-0 left-0 right-0 px-4 pb-4 bg-background
        md:static md:px-0 md:pb-0 md:bg-transparent"
      />
    </div>
  );
}

export default page;
