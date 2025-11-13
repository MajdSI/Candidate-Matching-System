import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import type { Candidate, MatchRes } from "@shared/schema"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Generate Arabic name in English letters based on cv_id
 * Includes both male and female names, ensures unique last names
 */
function generateCandidateName(cvId: number): string {
  const arabicMaleNames = [
    "Saad", "Khalid", "Mohammed", "Ahmed", "Omar", "Yusuf", "Ibrahim", 
    "Hassan", "Ali", "Faisal", "Sultan", "Nasser", "Majed", "Turki", "Bandar",
    "Abdullah", "Fahad", "Saud", "Khalil", "Zaid", "Hamza", "Tariq", "Bader",
    "Mansour", "Raed", "Waleed", "Fares", "Yazeed", "Khaled", "Saeed", "Nawaf",
    "Mutaz", "Sami", "Hani", "Rami", "Fadi", "Tamer", "Yasser", "Bassam",
    "Tarek", "Wael", "Ziyad", "Hatem", "Majid", "Nader", "Osama", "Karim"
  ];
  const arabicFemaleNames = [
    "Fatima", "Sara", "Noura", "Layla", "Amira", "Mariam", "Aisha", 
    "Hala", "Rania", "Lina", "Dina", "Yasmin", "Reem", "Hanan", "Nada",
    "Salma", "Rana", "Maya", "Leila", "Zeinab", "Hiba", "Rim", "Shaima",
    "Maha", "Noor", "Rahaf", "Lama", "Rawan", "Dana", "Tala", "Raghad",
    "Layan", "Jana", "Tara", "Yara", "Haya", "Nour", "Sana", "Hind",
    "Amina", "Lubna", "Noora", "Farah", "Sanaa", "Huda", "Mona", "Nadia"
  ];
  // Unique Arabic last names - matches CSV generation
  const arabicLastNames = [
    "Alsaud", "Alotaibi", "Alharbi", "Alahmed", "Almutairi", "Alzahrani", 
    "Alshammari", "Alqarni", "Almalki", "Alghamdi", "Almousa", "Alrashid", 
    "Almazroa", "Alsharif", "Almuhanna", "Almawash", "Alshahrani", "Alqahtani", 
    "Aldosari", "Alhazmi", "Alfahad", "Almubarak", "Alkhaldi", "Almansoori",
    "Alhumaid", "Alsuwaidi", "Almazrouei", "Alshamsi", "Alnuaimi", "Aldhaheri",
    "Alblushi", "Alhosani", "Almazmi", "Alshahwi", "Alhinai", "Alraisi",
    "Alshukaili", "Almuhaimid", "Alhamdan", "Alshahri", "Almutawa", "Alshammasi",
    "Alkhatib", "Alshehri", "Alshahwan", "Almajed", "Alharbi", "Aldosari",
    "Alhazmi", "Alfahad", "Almubarak", "Alkhaldi", "Almansoori", "Alhumaid",
    "Alsuwaidi", "Alshamsi", "Alnuaimi", "Aldhaheri", "Alblushi", "Alhosani",
    "Alshahwan", "Almuhaimid", "Alhamdan", "Alshahri", "Almutawa", "Alshammasi",
    "Alkhatib", "Alshehri", "Almajed", "Alharbi", "Aldosari", "Alhazmi",
    "Alfahad", "Almubarak", "Alkhaldi", "Almansoori", "Alhumaid", "Alsuwaidi",
    "Alshamsi", "Alnuaimi", "Aldhaheri", "Alblushi", "Alhosani", "Almazmi"
  ];
  
  // Remove duplicates while preserving order (matches CSV logic)
  const uniqueLastNames = Array.from(new Set(arabicLastNames));
  
  // Alternate between male and female names (matches CSV: cv_id % 2 === 0 is female)
  const isFemale = cvId % 2 === 0;
  const firstNames = isFemale ? arabicFemaleNames : arabicMaleNames;
  
  // Use same algorithm as CSV: (cv_id * 3) % len(first_names) and (cv_id * 5) % len(last_names)
  const firstIdx = (cvId * 3) % firstNames.length;
  const lastIdx = (cvId * 5) % uniqueLastNames.length;
  
  return `${firstNames[firstIdx]} ${uniqueLastNames[lastIdx]}`;
}

/**
 * Transform backend MatchRes response to Candidate format
 * Extracts name, title, education degree, and skills from cv_summary
 */
export function transformMatchResToCandidate(matchRes: MatchRes): Candidate {
  // Convert final_score (0-1) to matchScore (0-100)
  const matchScore = Math.round(matchRes.final_score * 100);
  
  // Generate candidate name based on cv_id (using cv_id if available, else cv_uid)
  const cvId = matchRes.cv_id ?? matchRes.cv_uid;
  const name = generateCandidateName(cvId);
  
  // Parse cv_summary JSON to extract structured data
  let title = "Professional";
  let educationDegree = "Not specified";
  let skills: string[] = [];
  let fullSummary = ""; // For debugging
  
  if (matchRes.cv_summary) {
    fullSummary = matchRes.cv_summary; // Store full summary for debugging
    try {
      // Try to parse cv_summary as JSON
      // Sometimes the JSON might be truncated or malformed, so try to fix it
      let summaryStr = matchRes.cv_summary.trim();
      
      // Try to fix common JSON issues (unterminated strings, etc.)
      // If it doesn't end with }, try to find a valid JSON structure
      if (!summaryStr.endsWith('}')) {
        // Try to find the last complete JSON object
        const lastBrace = summaryStr.lastIndexOf('}');
        if (lastBrace > 0) {
          summaryStr = summaryStr.substring(0, lastBrace + 1);
        }
      }
      
      const summaryData = JSON.parse(summaryStr);
      
      // Extract title - try multiple possible fields and structures
      // 1. Try titles array (most common)
      if (summaryData.titles && Array.isArray(summaryData.titles) && summaryData.titles.length > 0) {
        // Get the first non-empty title
        const firstTitle = summaryData.titles.find((t: string) => t && t.trim().length > 0);
        if (firstTitle) {
          title = String(firstTitle).trim();
        }
      }
      // 2. Try direct title field (singular)
      else if (summaryData.title && typeof summaryData.title === 'string' && summaryData.title.trim().length > 0) {
        title = String(summaryData.title).trim();
      }
      // 3. Try title as an array with first element
      else if (summaryData.title && Array.isArray(summaryData.title) && summaryData.title.length > 0) {
        const firstTitle = summaryData.title.find((t: string) => t && t.trim().length > 0);
        if (firstTitle) {
          title = String(firstTitle).trim();
        }
      }
      
      // Extract education degree (Bachelor, Masters, PhD)
      if (summaryData.education && Array.isArray(summaryData.education) && summaryData.education.length > 0) {
        const firstEducation = summaryData.education[0];
        if (typeof firstEducation === 'object' && firstEducation.degree) {
          const degreeStr = String(firstEducation.degree).toLowerCase();
          if (degreeStr.includes('phd') || degreeStr.includes('doctorate')) {
            educationDegree = "PhD";
          } else if (degreeStr.includes('master')) {
            educationDegree = "Masters";
          } else if (degreeStr.includes('bachelor') || degreeStr.includes('bachelor')) {
            educationDegree = "Bachelor";
          } else {
            educationDegree = firstEducation.degree;
          }
        } else if (typeof firstEducation === 'string') {
          const degreeStr = firstEducation.toLowerCase();
          if (degreeStr.includes('phd') || degreeStr.includes('doctorate')) {
            educationDegree = "PhD";
          } else if (degreeStr.includes('master')) {
            educationDegree = "Masters";
          } else if (degreeStr.includes('bachelor')) {
            educationDegree = "Bachelor";
          } else {
            educationDegree = firstEducation;
          }
        }
      }
      
      // Extract max 3 tools from skills.tools
      if (summaryData.skills && typeof summaryData.skills === 'object') {
        if (summaryData.skills.tools && Array.isArray(summaryData.skills.tools)) {
          skills = summaryData.skills.tools
            .slice(0, 3)
            .map((tool: any) => String(tool).trim())
            .filter((tool: string) => tool.length > 0);
        }
      }
    } catch (e) {
      // If parsing fails, cv_summary might not be valid JSON
      // Try to extract title from raw string using regex
      console.warn(`Failed to parse cv_summary for cv_uid ${matchRes.cv_uid}:`, e);
      console.log(`Full cv_summary for debugging:`, fullSummary);
      
      // Try multiple regex patterns to extract title from raw string
      // Pattern 1: "titles": ["Title"]
      let titleMatch = fullSummary.match(/"titles"\s*:\s*\[\s*"([^"]+)"/);
      if (titleMatch && titleMatch[1]) {
        title = titleMatch[1].trim();
      } else {
        // Pattern 2: "title": "Title"
        titleMatch = fullSummary.match(/"title"\s*:\s*"([^"]+)"/);
        if (titleMatch && titleMatch[1]) {
          title = titleMatch[1].trim();
        } else {
          // Pattern 3: 'titles': ['Title'] (single quotes)
          titleMatch = fullSummary.match(/'titles'\s*:\s*\[\s*'([^']+)'/);
          if (titleMatch && titleMatch[1]) {
            title = titleMatch[1].trim();
          } else {
            // Pattern 4: 'title': 'Title' (single quotes)
            titleMatch = fullSummary.match(/'title'\s*:\s*'([^']+)'/);
            if (titleMatch && titleMatch[1]) {
              title = titleMatch[1].trim();
            }
          }
        }
      }
      
      // If still no title found, log for debugging
      if (title === "Professional") {
        console.warn(`Could not extract title from cv_summary for cv_uid ${matchRes.cv_uid}. Using default "Professional".`);
        console.log(`cv_summary preview:`, fullSummary.substring(0, 200));
      }
    }
  } else {
    // cv_summary is missing or null
    console.warn(`cv_summary is missing for cv_uid ${matchRes.cv_uid}. Using default title "Professional".`);
  }
  
  // If no skills found, use empty array (will be hidden in UI)
  if (skills.length === 0) {
    skills = [];
  }
  
  // Generate avatar initials from name
  const nameParts = name.split(" ");
  const avatar = nameParts.length >= 2 
    ? (nameParts[0][0] + nameParts[1][0]).toUpperCase()
    : nameParts[0].substring(0, 2).toUpperCase();

  return {
    id: matchRes.cv_uid.toString(),
    name,
    title,
    experience: "Experience available in CV", // Keep for schema but won't be displayed
    location: educationDegree, // Use education degree instead of location
    skills: skills.slice(0, 3), // Max 3 skills
    matchScore,
    avatar,
    summary: fullSummary, // Keep for backward compatibility but won't be displayed
    email: `candidate${matchRes.cv_uid}@example.com`,
    phone: "Phone available in CV",
    education: [],
    workExperience: [],
    projects: [],
    explanation: matchRes.explanation || null, // Pass through explanation from backend
    cv_id: matchRes.cv_id ?? matchRes.cv_uid, // Store cv_id for PDF download
  } as Candidate & { explanation?: MatchRes['explanation']; cv_id?: number };
}
