import type { Express } from "express";
import express from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { jobDescriptionSchema } from "@shared/schema";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export async function registerRoutes(app: Express): Promise<Server> {
  // Explicitly return 404 for favicon requests
  app.get('/favicon.ico', (req, res) => {
    res.status(404).end();
  });
  app.get('/favicon.png', (req, res) => {
    res.status(404).end();
  });

  // Serve static CV files
  app.use('/cvs', express.static(path.join(__dirname, 'public/cvs')));
  
  // Get all candidates sorted by match score
  app.get("/api/candidates", async (_req, res) => {
    try {
      const candidates = await storage.getCandidates();
      res.json(candidates);
    } catch (error) {
      console.error("Error fetching candidates:", error);
      res.status(500).json({ error: "Failed to fetch candidates" });
    }
  });

  // Get a specific candidate by ID
  app.get("/api/candidates/:id", async (req, res) => {
    try {
      const candidate = await storage.getCandidate(req.params.id);
      if (!candidate) {
        return res.status(404).json({ error: "Candidate not found" });
      }
      res.json(candidate);
    } catch (error) {
      console.error("Error fetching candidate:", error);
      res.status(500).json({ error: "Failed to fetch candidate" });
    }
  });

  // Analyze job description and return matching candidates
  app.post("/api/analyze", async (req, res) => {
    try {
      const result = jobDescriptionSchema.safeParse(req.body);
      
      if (!result.success) {
        return res.status(400).json({ 
          error: "Invalid job description",
          details: result.error.errors 
        });
      }

      // For now, just return all candidates
      // In a real application, this would analyze the job description
      // and calculate match scores based on skills, experience, etc.
      const candidates = await storage.getCandidates();
      
      res.json({ 
        candidates,
        message: "Analysis complete" 
      });
    } catch (error) {
      console.error("Error analyzing job description:", error);
      res.status(500).json({ error: "Failed to analyze job description" });
    }
  });

  const httpServer = createServer(app);

  return httpServer;
}
