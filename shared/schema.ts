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

// Type definitions for CV details
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
export type Candidate = typeof candidates.$inferSelect;

// Job description analysis request
export const jobDescriptionSchema = z.object({
  description: z.string().min(10, "Job description must be at least 10 characters"),
});

export type JobDescription = z.infer<typeof jobDescriptionSchema>;
