import { type Candidate, type InsertCandidate } from "@shared/schema";
import { randomUUID } from "crypto";

export interface IStorage {
  // Candidate operations
  getCandidates(): Promise<Candidate[]>;
  getCandidate(id: string): Promise<Candidate | undefined>;
  createCandidate(candidate: InsertCandidate): Promise<Candidate>;
}

export class MemStorage implements IStorage {
  private candidates: Map<string, Candidate>;

  constructor() {
    this.candidates = new Map();
    // No dummy data - backend developer will load real candidates
  }

  async getCandidates(): Promise<Candidate[]> {
    return Array.from(this.candidates.values()).sort((a, b) => b.matchScore - a.matchScore);
  }

  async getCandidate(id: string): Promise<Candidate | undefined> {
    return this.candidates.get(id);
  }

  async createCandidate(insertCandidate: InsertCandidate): Promise<Candidate> {
    const id = randomUUID();
    const candidate: Candidate = { ...insertCandidate, id };
    this.candidates.set(id, candidate);
    return candidate;
  }
}

export const storage = new MemStorage();
