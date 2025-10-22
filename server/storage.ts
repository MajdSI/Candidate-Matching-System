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
    this.seedCandidates();
  }

  private seedCandidates() {
    const sampleCandidates: InsertCandidate[] = [
      {
        name: "Sarah Chen",
        title: "Senior Software Engineer",
        experience: "5 years",
        location: "San Francisco, CA",
        skills: ["JavaScript", "React", "Node.js", "Python", "AWS"],
        matchScore: 95,
        avatar: "SC",
        summary: "Full-stack developer with expertise in modern web technologies and cloud platforms.",
        email: "sarah.chen@email.com",
        phone: "+1 (555) 123-4567",
        education: [
          { degree: "M.S. Computer Science", school: "Stanford University", year: "2019" },
          { degree: "B.S. Software Engineering", school: "UC Berkeley", year: "2017" }
        ],
        workExperience: [
          {
            title: "Senior Software Engineer",
            company: "TechCorp Inc.",
            period: "2021 - Present",
            description: "Lead development of microservices architecture serving 10M+ users. Built scalable React applications and Node.js APIs."
          },
          {
            title: "Software Engineer",
            company: "StartupXYZ",
            period: "2019 - 2021",
            description: "Developed full-stack web applications using React, Node.js, and AWS. Improved application performance by 40%."
          }
        ],
        projects: [
          "E-commerce Platform - React/Node.js application with 50K+ active users",
          "Real-time Analytics Dashboard - Built with D3.js and WebSocket integration"
        ]
      },
      {
        name: "Marcus Johnson",
        title: "DevOps Engineer",
        experience: "4 years",
        location: "Austin, TX",
        skills: ["Docker", "Kubernetes", "AWS", "Python", "Jenkins"],
        matchScore: 88,
        avatar: "MJ",
        summary: "DevOps specialist focused on automation and scalable infrastructure solutions.",
        email: "marcus.johnson@email.com",
        phone: "+1 (555) 234-5678",
        education: [
          { degree: "B.S. Computer Science", school: "University of Texas", year: "2020" }
        ],
        workExperience: [
          {
            title: "DevOps Engineer",
            company: "CloudTech Solutions",
            period: "2020 - Present",
            description: "Managed Kubernetes clusters and CI/CD pipelines. Reduced deployment time by 60% through automation."
          }
        ],
        projects: [
          "Automated CI/CD Pipeline - Jenkins, Docker, and AWS integration",
          "Infrastructure as Code - Terraform and Ansible implementation"
        ]
      },
      {
        name: "Elena Rodriguez",
        title: "Frontend Developer",
        experience: "3 years",
        location: "Remote",
        skills: ["React", "TypeScript", "CSS", "Figma", "Jest"],
        matchScore: 82,
        avatar: "ER",
        summary: "Creative frontend developer with strong design sensibilities and testing expertise.",
        email: "elena.rodriguez@email.com",
        phone: "+1 (555) 345-6789",
        education: [
          { degree: "B.A. Digital Design", school: "Art Institute", year: "2021" }
        ],
        workExperience: [
          {
            title: "Frontend Developer",
            company: "Design Studio Pro",
            period: "2021 - Present",
            description: "Created responsive web applications with React and TypeScript. Collaborated with UX team on user interface design."
          }
        ],
        projects: [
          "Portfolio Website Builder - React-based drag-and-drop interface",
          "Mobile-First E-commerce Site - Responsive design with 98% mobile score"
        ]
      },
      {
        name: "David Kim",
        title: "Data Scientist",
        experience: "6 years",
        location: "Seattle, WA",
        skills: ["Python", "Machine Learning", "SQL", "TensorFlow", "R"],
        matchScore: 79,
        avatar: "DK",
        summary: "Data scientist specializing in machine learning and predictive analytics.",
        email: "david.kim@email.com",
        phone: "+1 (555) 456-7890",
        education: [
          { degree: "Ph.D. Data Science", school: "University of Washington", year: "2018" },
          { degree: "M.S. Statistics", school: "MIT", year: "2016" }
        ],
        workExperience: [
          {
            title: "Senior Data Scientist",
            company: "DataCorp Analytics",
            period: "2018 - Present",
            description: "Built machine learning models for predictive analytics. Improved model accuracy by 25% using advanced algorithms."
          }
        ],
        projects: [
          "Customer Churn Prediction Model - 92% accuracy using ensemble methods",
          "Real-time Recommendation Engine - TensorFlow-based collaborative filtering"
        ]
      },
      {
        name: "Amanda Foster",
        title: "Product Manager",
        experience: "7 years",
        location: "New York, NY",
        skills: ["Agile", "Scrum", "Analytics", "Strategy", "Leadership"],
        matchScore: 75,
        avatar: "AF",
        summary: "Experienced product manager with a track record of successful product launches.",
        email: "amanda.foster@email.com",
        phone: "+1 (555) 567-8901",
        education: [
          { degree: "MBA", school: "Harvard Business School", year: "2017" },
          { degree: "B.S. Engineering", school: "Columbia University", year: "2015" }
        ],
        workExperience: [
          {
            title: "Senior Product Manager",
            company: "InnovateTech",
            period: "2017 - Present",
            description: "Led product strategy for mobile applications with 5M+ downloads. Managed cross-functional teams of 15+ members."
          }
        ],
        projects: [
          "Mobile App Launch - Achieved 1M downloads in first 6 months",
          "Product Roadmap Strategy - Increased user retention by 35%"
        ]
      },
      {
        name: "James Wilson",
        title: "Backend Developer",
        experience: "4 years",
        location: "Chicago, IL",
        skills: ["Java", "Spring", "PostgreSQL", "Redis", "Microservices"],
        matchScore: 71,
        avatar: "JW",
        summary: "Backend developer experienced in building scalable enterprise applications.",
        email: "james.wilson@email.com",
        phone: "+1 (555) 678-9012",
        education: [
          { degree: "B.S. Computer Science", school: "University of Illinois", year: "2020" }
        ],
        workExperience: [
          {
            title: "Backend Developer",
            company: "Enterprise Solutions Inc.",
            period: "2020 - Present",
            description: "Developed RESTful APIs and microservices using Java Spring. Optimized database queries reducing response time by 50%."
          }
        ],
        projects: [
          "Microservices Architecture - Java Spring Boot with Redis caching",
          "API Gateway Implementation - Handled 100K+ requests per minute"
        ]
      }
    ];

    // Add sample candidates to storage
    sampleCandidates.forEach(candidate => {
      const id = randomUUID();
      this.candidates.set(id, { ...candidate, id });
    });
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
