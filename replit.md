# HR Talent Matching Wizard

## Overview

This is an HR talent matching application that analyzes job descriptions and matches them with candidate profiles. The system provides a wizard-like interface where users can input job requirements and receive ranked candidate matches with detailed CV information. The application uses a modern web stack with React on the frontend and Express on the backend, styled with a professional design system inspired by modern SaaS tools.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Framework & Build System**
- React 18 with TypeScript for type-safe component development
- Vite as the build tool and development server, chosen for fast hot module replacement and optimized production builds
- Wouter for lightweight client-side routing instead of React Router to minimize bundle size

**UI Component System**
- Shadcn/ui components built on Radix UI primitives, providing accessible, unstyled components that can be customized
- Tailwind CSS for utility-first styling with a custom design system
- Design tokens defined in CSS variables for theme consistency (teal primary color #25C7BC, purple accent #9D67AA)
- Component variants using class-variance-authority for consistent styling patterns

**State Management**
- TanStack Query (React Query) for server state management, caching, and data synchronization
- Local component state with React hooks for UI state
- Custom query client configuration with infinite stale time to prevent unnecessary refetches

**Key Design Decisions**
- Three-screen wizard flow: input → loading → results, providing clear user journey
- Progressive loading animation with simulated analysis steps to enhance perceived performance
- Gradient backgrounds and card-based layouts for modern, professional appearance
- Responsive design with mobile breakpoints at 768px

### Backend Architecture

**Server Framework**
- Express.js for HTTP server and API routing
- TypeScript throughout for type safety across the stack
- Custom middleware for request logging and JSON response capturing

**API Design**
- RESTful endpoints under `/api` namespace
- GET `/api/candidates` - Retrieve all candidates sorted by match score
- GET `/api/candidates/:id` - Retrieve specific candidate details
- POST `/api/analyze` - Analyze job description and return matching candidates
- Zod schemas for request validation ensuring data integrity

**Data Layer**
- In-memory storage implementation (MemStorage class) for current deployment
- Drizzle ORM configured for PostgreSQL with schema definitions ready for database migration
- Schema includes candidates table with full CV information (education, work experience, skills, projects)
- Designed to easily swap MemStorage for database implementation without API changes

**Development Setup**
- Vite middleware integration for development with HMR
- Separate dev and production build processes
- esbuild for server-side bundling in production

### External Dependencies

**Database**
- Drizzle ORM configured for PostgreSQL via Neon serverless adapter
- Schema defined but currently using in-memory storage
- Migration system ready via drizzle-kit

**UI Libraries**
- Radix UI primitives for 20+ accessible components (Dialog, Accordion, Dropdown, etc.)
- Lucide React for consistent icon system
- date-fns for date manipulation
- embla-carousel-react for carousel functionality

**Development Tools**
- TypeScript compiler for type checking
- Vite plugins: runtime error overlay, cartographer (Replit integration), dev banner
- PostCSS with Tailwind and Autoprefixer for CSS processing

**Form Handling**
- React Hook Form for performant form state management
- Hookform resolvers for schema validation integration
- Zod for runtime type validation and schema definitions

**Key Architectural Patterns**
- Separation of concerns: shared schema definitions between client and server
- Path aliases (@/, @shared/, @assets/) for clean imports
- Type inference from database schema to ensure type safety
- Middleware pattern for cross-cutting concerns (logging, error handling)