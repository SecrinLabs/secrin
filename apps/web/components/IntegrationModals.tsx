"use clinet";

import React, { useState } from "react";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description: string;
  children: React.ReactNode;
  onSubmit: () => void;
  submitLabel: string;
  disabled?: boolean;
}

export function IntegrationModal({
  open,
  onClose,
  title,
  description,
  children,
  onSubmit,
  submitLabel,
  disabled,
}: ModalProps) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60">
      <div className="bg-white dark:bg-neutral-900 rounded-lg shadow-lg w-full max-w-md p-6 relative">
        <button
          className="absolute top-3 right-3 text-gray-400 hover:text-gray-600"
          onClick={onClose}
          aria-label="Close"
        >
          ×
        </button>
        <h2 className="text-xl font-bold mb-2">{title}</h2>
        <p className="text-gray-600 dark:text-gray-300 mb-4">{description}</p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onSubmit();
          }}
        >
          {children}
          <div className="flex justify-end gap-2 mt-6">
            <button
              type="button"
              className="px-4 py-2 rounded bg-gray-200 dark:bg-neutral-800 text-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-neutral-700"
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
              disabled={disabled}
            >
              {submitLabel}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// --- GitHub Modal ---
export function GitHubIntegrationModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [username, setUsername] = useState("");
  const [token, setToken] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [error, setError] = useState("");
  const isValid =
    username &&
    token.length >= 10 &&
    /^https:\/\/github.com\/.+\/.+/.test(repoUrl);

  function handleConnect() {
    if (!isValid) {
      setError("Please fill all fields correctly.");
      return;
    }
    setError("");
    // TODO: Save credentials
    onClose();
  }

  return (
    <IntegrationModal
      open={open}
      onClose={onClose}
      title="Connect GitHub Repository"
      description={
        "To fetch commit history and code context, DevSecrin needs access to your GitHub account. Generate a Personal Access Token with repo and read:user permissions."
      }
      onSubmit={handleConnect}
      submitLabel="Connect"
      disabled={!isValid}
    >
      <div className="mb-3">
        <label className="block text-sm font-medium mb-1">
          GitHub Username
        </label>
        <input
          type="text"
          className="w-full border rounded px-3 py-2"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="octocat"
        />
      </div>
      <div className="mb-3">
        <label className="block text-sm font-medium mb-1">
          Personal Access Token
        </label>
        <input
          type="password"
          className="w-full border rounded px-3 py-2"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          placeholder="••••••••••"
        />
      </div>
      <div className="mb-3">
        <label className="block text-sm font-medium mb-1">Repository URL</label>
        <input
          type="url"
          className="w-full border rounded px-3 py-2"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          placeholder="https://github.com/user/repo"
        />
      </div>
      {error && <div className="text-red-500 text-sm mb-2">{error}</div>}
    </IntegrationModal>
  );
}

// --- Documentation Modal ---
export function DocumentationIntegrationModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [sitemapUrl, setSitemapUrl] = useState("");
  const [docType, setDocType] = useState("Docusaurus");
  const [error, setError] = useState("");
  const isValid = /^https?:\/\/.+/.test(sitemapUrl);

  function handleSave() {
    if (!isValid) {
      setError("Please enter a valid URL.");
      return;
    }
    setError("");
    // TODO: Save documentation config
    onClose();
  }

  return (
    <IntegrationModal
      open={open}
      onClose={onClose}
      title="Configure Documentation Source"
      description={
        "DevSecrin can extract context from your external documentation by crawling your sitemap. Provide the publicly available sitemap URL."
      }
      onSubmit={handleSave}
      submitLabel="Save"
      disabled={!isValid}
    >
      <div className="mb-3">
        <label className="block text-sm font-medium mb-1">Sitemap URL</label>
        <input
          type="url"
          className="w-full border rounded px-3 py-2"
          value={sitemapUrl}
          onChange={(e) => setSitemapUrl(e.target.value)}
          placeholder="https://docs.example.com/sitemap.xml"
        />
      </div>
      <div className="mb-3">
        <label className="block text-sm font-medium mb-1">
          Documentation Type
        </label>
        <select
          className="w-full border rounded px-3 py-2"
          value={docType}
          onChange={(e) => setDocType(e.target.value)}
        >
          <option value="Docusaurus">Docusaurus</option>
          <option value="Gitbook">Gitbook</option>
          <option value="Custom">Custom</option>
        </select>
      </div>
      {error && <div className="text-red-500 text-sm mb-2">{error}</div>}
    </IntegrationModal>
  );
}

// --- Local Repo Modal ---
export function LocalRepoIntegrationModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [localPath, setLocalPath] = useState("");
  const [projectName, setProjectName] = useState("");
  const [error, setError] = useState("");
  const isValid = localPath.length > 0 && projectName.length > 0;

  function handleSave() {
    if (!isValid) {
      setError("Please fill all fields.");
      return;
    }
    setError("");
    // TODO: Save local repo config
    onClose();
  }

  return (
    <IntegrationModal
      open={open}
      onClose={onClose}
      title="Add Local Code Repository"
      description={
        "Point DevSecrin to a local codebase directory. This will enable offline analysis and context extraction."
      }
      onSubmit={handleSave}
      submitLabel="Scan & Save"
      disabled={!isValid}
    >
      <div className="mb-3">
        <label className="block text-sm font-medium mb-1">Local Path</label>
        <input
          type="text"
          className="w-full border rounded px-3 py-2"
          value={localPath}
          onChange={(e) => setLocalPath(e.target.value)}
          placeholder="/Users/yourname/project"
        />
      </div>
      <div className="mb-3">
        <label className="block text-sm font-medium mb-1">Project Name</label>
        <input
          type="text"
          className="w-full border rounded px-3 py-2"
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          placeholder="My Project"
        />
      </div>
      {error && <div className="text-red-500 text-sm mb-2">{error}</div>}
    </IntegrationModal>
  );
}
