"use client";

import { useState, useEffect } from "react";
import { Button } from "@workspace/ui/components/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@workspace/ui/components/dialog";
import { Input } from "@workspace/ui/components/input";
import { Label } from "@workspace/ui/components/label";
import { endpoints } from "@workspace/ui/lib/config";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@workspace/ui/components/select";
import { Alert, AlertDescription } from "@workspace/ui/components/alert";
import { FileText, AlertCircle } from "lucide-react";
import { SitemapConfig } from "@workspace/ui/types/Integration.js";

export function DocumentationIntegrationModal({
  open,
  onClose,
  config,
}: {
  open: boolean;
  onClose: () => void;
  config: SitemapConfig;
}) {
  const [sitemapUrl, setSitemapUrl] = useState("");
  const [docType, setDocType] = useState("Docusaurus");
  const [error, setError] = useState("");

  // Initialize form with config data when modal opens
  useEffect(() => {
    if (open && config) {
      setSitemapUrl(config.sitemapUrl || "");
      setDocType(config.docType || "Docusaurus");
      setError("");
    }
  }, [open, config]);

  const isValid = /^https?:\/\/.+/.test(sitemapUrl);

  async function handleSave() {
    if (!isValid) {
      setError("Please enter a valid URL.");
      return;
    }
    setError("");
    try {
      const response = await fetch(endpoints.integrationUpdate, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: "sitemap", // or the relevant integration name
          is_connected: true, // or the actual state
          config: {
            sitemapUrl,
            docType,
          },
        }),
      });
      if (!response.ok) {
        const data = await response.json();
        setError(data.detail || "Failed to update integration.");
        return;
      }
      onClose();
    } catch (err) {
      setError("Network error.");
    }
    onClose();
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900">
              <FileText className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <DialogTitle>Configure Documentation Source</DialogTitle>
              <DialogDescription className="mt-1">
                DevSecrin can extract context from your external documentation
                by crawling your sitemap. Provide the publicly available sitemap
                URL.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="sitemap-url">Sitemap URL</Label>
            <Input
              id="sitemap-url"
              type="url"
              value={sitemapUrl}
              onChange={(e) => setSitemapUrl(e.target.value)}
              placeholder="https://docs.example.com/sitemap.xml"
              className={
                error ? "border-red-500 focus-visible:ring-red-500" : ""
              }
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="doc-type">Documentation Type</Label>
            <Select value={docType} onValueChange={setDocType}>
              <SelectTrigger>
                <SelectValue placeholder="Select documentation type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Docusaurus">Docusaurus</SelectItem>
                <SelectItem value="Gitbook">Gitbook</SelectItem>
                <SelectItem value="Custom">Custom</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )} */}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={!isValid}>
            Save Configuration
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
