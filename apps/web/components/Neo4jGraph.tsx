"use client";

import { useEffect, useState, useCallback } from "react";
import dynamic from "next/dynamic";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertCircle, Loader2 } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

// Dynamically import ForceGraph3D with SSR disabled
const ForceGraph3D = dynamic(() => import("react-force-graph-3d"), {
  ssr: false,
});

interface Neo4jGraphProps {
  neo4jUrl?: string;
  username?: string;
  password?: string;
  database?: string;
  limit?: number;
  onDisconnect?: () => void;
}

// ForceGraph node type - matches the library's expected structure
interface GraphNode {
  id?: string | number;
  label?: string;
  caption?: string;
  size?: number;
  x?: number;
  y?: number;
  z?: number;
  vx?: number;
  vy?: number;
  vz?: number;
  fx?: number;
  fy?: number;
  fz?: number;
  [key: string]: unknown;
}

interface GraphLink {
  source: string | number | GraphNode;
  target: string | number | GraphNode;
  weight?: number;
  type?: string;
}

interface Neo4jRecord {
  get(key: string): {
    id: { toNumber: () => number };
    label?: string;
    caption?: string;
    size?: number;
    [key: string]: unknown;
  };
}

const colorPalette: Record<string, string> = {
  Commit: "#ff6b6b",
  Repository: "#4ecdc4",
  Person: "#45b7d1",
  File: "#f9ca24",
  default: "#95a5a6",
};

export default function Neo4jGraph({
  neo4jUrl = "neo4j://127.0.0.1:7687",
  username = "neo4j",
  password = "10514912",
  database = "demo",
  limit = 5000,
  onDisconnect,
}: Neo4jGraphProps) {
  const [graphData, setGraphData] = useState<{
    nodes: GraphNode[];
    links: GraphLink[];
  }>({
    nodes: [],
    links: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const loadGraphData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Dynamic import of neo4j-driver for client-side only
      const neo4j = (await import("neo4j-driver")).default;

      // FIX: Check if the URL implies a secure connection (Cloud/Aura)
      const isSecure =
         neo4jUrl.startsWith('neo4j+s://') ||
         neo4jUrl.startsWith('neo4j+ssc://') ||
         neo4jUrl.startsWith('bolt+s://') ||
         neo4jUrl.startsWith('bolt+ssc://');
      
      const driver = neo4j.driver(
        neo4jUrl,
        neo4j.auth.basic(username, password),
        // If it's a secure URL, don't pass any config (let the URL handle it).
        // If it's local, explicitly turn off encryption.
        isSecure ? {} : { encrypted: "ENCRYPTION_OFF" }
      );
      
      const session = driver.session({ database });

      const start = Date.now();
      const result = await session.run(
        "MATCH (n)-[r]->(m) RETURN { id: id(n), label:head(labels(n)), caption:n.name, size:n.pagerank } as source, { id: id(m), label:head(labels(m)), caption:m.name, size:m.pagerank } as target, {weight:log(r.weight), type:type(r)} as rel LIMIT $limit",
        { limit: neo4j.int(limit) }
      );

      const nodes: Record<number, GraphNode> = {};
      const links: GraphLink[] = result.records.map((r: Neo4jRecord) => {
        const source = r.get("source");
        const sourceId = source.id.toNumber();
        const sourceNode: GraphNode = {
          id: sourceId,
          label: source.label || "Unknown",
          caption: source.caption,
          size: source.size,
        };
        nodes[sourceId] = sourceNode;

        const target = r.get("target");
        const targetId = target.id.toNumber();
        const targetNode: GraphNode = {
          id: targetId,
          label: target.label || "Unknown",
          caption: target.caption,
          size: target.size,
        };
        nodes[targetId] = targetNode;

        const rel = r.get("rel");
        return {
          source: sourceId,
          target: targetId,
          weight: rel.weight as number | undefined,
          type: (rel.type as string) || "RELATED",
        };
      });

      await session.close();
      await driver.close();

      console.log(`${links.length} links loaded in ${Date.now() - start} ms`);

      setGraphData({ nodes: Object.values(nodes), links });
      setLoading(false);
    } catch (err) {
      console.error("Error loading graph data:", err);
      const errorMessage =
        err instanceof Error ? err.message : "Failed to load graph data";
      setError(errorMessage);
      setLoading(false);
    }
  }, [neo4jUrl, username, password, database, limit]);

  useEffect(() => {
    loadGraphData();
  }, [loadGraphData]);

  const handleNodeHover = (node: GraphNode | null) => {
    setHoveredNode(node);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    setTooltipPos({ x: e.clientX, y: e.clientY });
  };

  const getConnectionCount = (nodeId: string | number | undefined) => {
    if (!nodeId) return 0;
    return graphData.links.filter(
      (l) => l.source === nodeId || l.target === nodeId
    ).length;
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-background gap-4">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-foreground text-lg">Loading graph data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-background p-4">
        <Alert variant="destructive" className="max-w-md">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Connection Error</AlertTitle>
          <AlertDescription className="mt-2">{error}</AlertDescription>
        </Alert>
        {onDisconnect && (
          <Button onClick={onDisconnect} className="mt-6">
            Go Back to Form
          </Button>
        )}
      </div>
    );
  }

  return (
    <div
      className="relative w-full h-screen bg-background"
      onMouseMove={handleMouseMove}
    >
      <ForceGraph3D
        graphData={graphData}
        nodeVal={(node) => (node as GraphNode).size || 1}
        nodeColor={(node) =>
          colorPalette[(node as GraphNode).label || "default"] ||
          colorPalette["default"]
        }
        linkAutoColorBy="type"
        linkWidth={(link) => (link as GraphLink).weight || 1}
        linkOpacity={0.1}
        nodeOpacity={0.9}
        onNodeHover={handleNodeHover}
        onNodeClick={(node) => console.log("Node clicked:", node)}
        enableNodeDrag={true}
        enableNavigationControls={true}
      />

      {hoveredNode && (
        <Card
          className="fixed pointer-events-none z-50 max-w-xs"
          style={{
            left: `${tooltipPos.x + 15}px`,
            top: `${tooltipPos.y + 15}px`,
          }}
        >
          <CardContent className="pt-6">
            <div className="font-bold text-primary mb-3">
              {hoveredNode.label || "Node"}
            </div>
            <div className="text-sm space-y-2">
              <div>
                <span className="font-semibold text-foreground">ID:</span>
                <span className="text-muted-foreground ml-2">
                  {hoveredNode.id}
                </span>
              </div>
              {hoveredNode.caption && (
                <div>
                  <span className="font-semibold text-foreground">Name:</span>
                  <span className="text-muted-foreground ml-2">
                    {hoveredNode.caption}
                  </span>
                </div>
              )}
              {hoveredNode.size && (
                <div>
                  <span className="font-semibold text-foreground">Size:</span>
                  <span className="text-muted-foreground ml-2">
                    {typeof hoveredNode.size === "number"
                      ? hoveredNode.size.toFixed(3)
                      : hoveredNode.size}
                  </span>
                </div>
              )}
              <div>
                <span className="font-semibold text-foreground">
                  Connections:
                </span>
                <span className="text-muted-foreground ml-2">
                  {getConnectionCount(hoveredNode.id)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
