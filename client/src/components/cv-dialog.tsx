import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Mail, Phone, MapPin, GraduationCap, Briefcase, Code2 } from "lucide-react";
import type { Candidate } from "@shared/schema";

interface CVDialogProps {
  candidate: Candidate | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function CVDialog({ candidate, open, onOpenChange }: CVDialogProps) {
  if (!candidate) return null;

  const matchColor = 
    candidate.matchScore >= 90 ? "text-brand-teal" : 
    candidate.matchScore >= 80 ? "text-brand-purple" : 
    "text-muted-foreground";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" data-testid="dialog-cv">
        <DialogHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-4">
              <div 
                className="w-16 h-16 rounded-full flex items-center justify-center text-white font-bold text-xl bg-gradient-to-br from-brand-teal to-brand-purple"
              >
                {candidate.avatar}
              </div>
              <div>
                <DialogTitle className="text-2xl font-bold" data-testid="text-cv-name">
                  {candidate.name}
                </DialogTitle>
                <p className="text-lg text-muted-foreground">{candidate.title}</p>
              </div>
            </div>
            <div className="text-right">
              <div className={`text-3xl font-bold ${matchColor}`}>
                {candidate.matchScore}%
              </div>
              <div className="text-sm text-muted-foreground">Match Score</div>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-6 mt-6">
          {/* Contact Information */}
          <section>
            <h3 className="text-lg font-semibold mb-3 flex items-center">
              <Mail className="w-5 h-5 mr-2 text-primary" />
              Contact Information
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex items-center">
                <Mail className="w-4 h-4 mr-2 text-muted-foreground" />
                <a href={`mailto:${candidate.email}`} className="text-primary hover:underline" data-testid="text-cv-email">
                  {candidate.email}
                </a>
              </div>
              <div className="flex items-center">
                <Phone className="w-4 h-4 mr-2 text-muted-foreground" />
                <span data-testid="text-cv-phone">{candidate.phone}</span>
              </div>
              <div className="flex items-center">
                <MapPin className="w-4 h-4 mr-2 text-muted-foreground" />
                <span>{candidate.location}</span>
              </div>
            </div>
          </section>

          <Separator />

          {/* Summary */}
          <section>
            <h3 className="text-lg font-semibold mb-3">Professional Summary</h3>
            <p className="text-sm text-muted-foreground">{candidate.summary}</p>
          </section>

          <Separator />

          {/* Skills */}
          <section>
            <h3 className="text-lg font-semibold mb-3 flex items-center">
              <Code2 className="w-5 h-5 mr-2 text-primary" />
              Skills
            </h3>
            <div className="flex flex-wrap gap-2">
              {candidate.skills.map((skill, index) => (
                <Badge
                  key={index}
                  variant="secondary"
                  className="px-3 py-1 bg-primary/10 text-primary border-0"
                >
                  {skill}
                </Badge>
              ))}
            </div>
          </section>

          <Separator />

          {/* Education */}
          <section>
            <h3 className="text-lg font-semibold mb-3 flex items-center">
              <GraduationCap className="w-5 h-5 mr-2 text-primary" />
              Education
            </h3>
            <div className="space-y-3">
              {candidate.education.map((edu, index) => (
                <div key={index} className="border-l-2 border-primary pl-4">
                  <h4 className="font-semibold">{edu.degree}</h4>
                  <p className="text-sm text-muted-foreground">{edu.school}</p>
                  <p className="text-xs text-muted-foreground">{edu.year}</p>
                </div>
              ))}
            </div>
          </section>

          <Separator />

          {/* Work Experience */}
          <section>
            <h3 className="text-lg font-semibold mb-3 flex items-center">
              <Briefcase className="w-5 h-5 mr-2 text-primary" />
              Work Experience
            </h3>
            <div className="space-y-4">
              {candidate.workExperience.map((exp, index) => (
                <div key={index} className="border-l-2 border-primary pl-4">
                  <h4 className="font-semibold">{exp.title}</h4>
                  <p className="text-sm font-medium text-muted-foreground">{exp.company}</p>
                  <p className="text-xs text-muted-foreground mb-2">{exp.period}</p>
                  <p className="text-sm">{exp.description}</p>
                </div>
              ))}
            </div>
          </section>

          <Separator />

          {/* Projects */}
          <section>
            <h3 className="text-lg font-semibold mb-3">Notable Projects</h3>
            <ul className="space-y-2">
              {candidate.projects.map((project, index) => (
                <li key={index} className="text-sm flex items-start">
                  <span className="mr-2 text-primary">•</span>
                  <span>{project}</span>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </DialogContent>
    </Dialog>
  );
}
