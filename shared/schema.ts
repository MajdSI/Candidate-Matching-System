import { sql } from "drizzle-orm";
import { pgTable, text, varchar, integer, jsonb } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// Candidate table with full CV information
export const candidates = pgTable("candidates", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  name: text("name").notNull(),
  title: text("title").notNull(),
  experience: text("experience").notNull(),
  location: text("location").notNull(),
  skills: text("skills").array().notNull(),
  matchScore: integer("match_score").notNull().default(0),
  avatar: text("avatar").notNull(),
  summary: text("summary").notNull(),
  email: text("email").notNull(),
  phone: text("phone").notNull(),
  education: jsonb("education").notNull().$type<Education[]>(),
  workExperience: jsonb("work_experience").notNull().$type<WorkExperience[]>(),
  projects: text("projects").array().notNull(),
});

// Type definitions
export type Education = {
  degree: string;
  school: string;
  year: string;
};

export type WorkExperience = {
  title: string;
  company: string;
  period: string;
  description: string;
};

export const insertCandidateSchema = createInsertSchema(candidates).omit({
  id: true,
});

export type InsertCandidate = z.infer<typeof insertCandidateSchema>;

// Base candidate row type
export type Candidate = typeof candidates.$inferSelect;

// ---------- Backend API Types ----------
export interface MatchRes {
  rank: number;
  final_score: number;
  ce_score: number;
  hybrid_score_0_100: number;
  cv_uid: number;
  cv_id?: number | null;
  cv_text: string;
  cv_summary?: string | null;
  clean_cv_full?: string | null;
  explanation?: {
    reasons?: string[];
    matches?: string[];
    raw?: string;
    error?: string;
  } | null;
}

// ----------- Request DTOs -----------
export interface MatchReq {
  jd_text: string;
  jd_col: string;
  cv_col: string;
  resolve_jd_to_col: string;
  topk?: number;
  candidate_topk?: number;
  rrf_k?: number;
  threshold?: number | null;
  cosine_floor?: number;
  alpha?: number;
  batch_size?: number;
  cv_text_pref?: string;
  async_explain?: boolean;
}

export interface ExplainReq {
  jd_text: string;
  candidates: Array<{
    cv_uid: number;
    cv_text: string;
    rank: number;
    [key: string]: any;
  }>;
  llm_model?: string;
  max_reasons?: number;
  per_cv_char_budget?: number;
}


// ---------- UI-friendly type ----------
export interface CandidateWithExplanation extends Candidate {
  cv_id?: number | null;  // added
  explanation?: {
    reasons?: string[];
    matches?: string[];
    raw?: string;
    error?: string;
  } | null;               // added
}


export type UICandidate = Candidate & {
  cv_id?: number | null;
  cv_uid?: number;
  matchScore: number;  // convenient alias for final_score * 100
  explanation?: MatchRes["explanation"] | null;
};