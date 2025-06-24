import express, { Request, Response } from "express";

const app = express();
const PORT = 3000;

app.use(express.json());

// Routes
app.get("/", (req: Request, res: Response) => {
  res.send("Hello from TypeScript API!");
});

app.get("/api/users", (req: Request, res: Response) => {
  res.json([
    { id: 1, name: "Alice" },
    { id: 2, name: "Bob" },
  ]);
});

app.post("/api/users", (req: Request, res: Response) => {
  const user = req.body;
  res.status(201).json({ message: "User created", user });
});

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
