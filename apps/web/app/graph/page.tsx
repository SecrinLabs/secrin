"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import Neo4jGraph from "@/components/Neo4jGraph";

interface Neo4jCredentials {
  neo4jUrl: string;
  username: string;
  password: string;
  database: string;
}

export default function GraphPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [credentials, setCredentials] = useState<Neo4jCredentials>({
    neo4jUrl: "neo4j://127.0.0.1:7687",
    username: "neo4j",
    password: "",
    database: "secrin",
  });
  const [formData, setFormData] = useState({
    neo4jUrl: "neo4j://127.0.0.1:7687",
    username: "neo4j",
    password: "",
    database: "secrin",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setCredentials(formData);
    setIsAuthenticated(true);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleDisconnect = () => {
    setIsAuthenticated(false);
    setFormData({
      ...formData,
      password: "",
    });
  };

  if (isAuthenticated) {
    return (
      <main className="w-full h-screen relative">
        <Button
          onClick={handleDisconnect}
          variant="destructive"
          className="absolute top-4 right-4 z-50"
        >
          Disconnect
        </Button>
        <Neo4jGraph
          neo4jUrl={credentials.neo4jUrl}
          username={credentials.username}
          password={credentials.password}
          database={credentials.database}
          limit={5000}
          onDisconnect={handleDisconnect}
        />
      </main>
    );
  }

  return (
    <main className="w-full h-screen flex items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl">Neo4j Graph Viewer</CardTitle>
          <CardDescription>
            Enter your Neo4j credentials to visualize the graph
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="neo4jUrl">Neo4j URL</Label>
              <Input
                type="text"
                id="neo4jUrl"
                name="neo4jUrl"
                value={formData.neo4jUrl}
                onChange={handleChange}
                placeholder="neo4j://127.0.0.1:7687"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleChange}
                placeholder="neo4j"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="••••••••"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="database">Database</Label>
              <Input
                type="text"
                id="database"
                name="database"
                value={formData.database}
                onChange={handleChange}
                placeholder="demo"
                required
              />
            </div>

            <Button type="submit" className="w-full">
              Connect & View Graph
            </Button>
          </form>

          <p className="text-sm text-muted-foreground text-center mt-6">
            Make sure your Neo4j instance is running and accessible
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
