# HR Talent Matching Wizard - Design Guidelines

## Design Approach
**Hybrid Utility-First System**: This HR application balances professional functionality with visual appeal. The design draws inspiration from modern SaaS tools (Linear, Notion) while maintaining HR-specific requirements for clarity and data presentation.

## Core Design Elements

### A. Color Palette

**Brand Colors:**
- Primary Teal: `185 71% 48%` - Main interactive elements, progress indicators, loading states
- Purple Accent: `283 37% 53%` - Secondary highlights, gradient terminal
- Neutral Gray: `220 10% 82%` - Gradient start, subtle backgrounds

**Background:**
- Main gradient: `linear-gradient(135deg, #D0D0D0 0%, #25C7BC 50%, #9D67AA 100%)`
- Card backgrounds: Pure white (`#FFFFFF`)
- Hover states: Gray-100 for buttons, Gray-50 for cards

**Functional Colors:**
- Success (High Match): Teal variations
- Text Primary: Gray-800 (`#1F2937`)
- Text Secondary: Gray-600 (`#4B5563`)
- Text Muted: Gray-500 (`#6B7280`)
- Borders: Gray-200 (`#E5E7EB`)

### B. Typography

**Font Family:**
- System font stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`

**Hierarchy:**
- H1 (Main Title): `text-4xl font-bold` - Gray-800
- H2 (Section Headers): `text-2xl font-bold` - Gray-800
- H3 (Loading/Status): `text-xl font-semibold` - Gray-700
- Body: `text-base` - Gray-600
- Labels: `text-lg font-semibold` - Gray-700
- Small Text: `text-sm` - Gray-500

### C. Layout System

**Spacing Primitives:**
Use Tailwind units of **2, 4, 6, 8** for consistent rhythm (e.g., `p-8`, `mb-6`, `space-x-4`)

**Container Strategy:**
- Main content: `max-w-6xl mx-auto`
- Form elements: `max-w-2xl mx-auto`
- Full viewport: `min-h-full` with `p-6` outer padding

**Grid Layouts:**
- Candidate cards: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6`

### D. Component Library

**1. Cards**
- Background: White
- Border radius: `rounded-xl` (12px)
- Shadow: `shadow-lg` at rest
- Hover shadow: Enhanced depth with `0 20px 25px -5px rgba(0,0,0,0.1)`
- Padding: `p-8` for sections, `p-6` for cards
- Transition: `transition-all duration-300`

**2. Buttons**
- Primary: Teal background, white text, `rounded-lg`, `px-6 py-3`
- Secondary: Gray-100 background, Gray-700 text, `px-4 py-2`
- Hover: Scale and background color transitions
- Disabled: 50% opacity with `cursor-not-allowed`

**3. Form Elements**
- Text areas: `border-2 border-gray-200 rounded-lg`
- Focus state: `border-blue-500 ring-2 ring-blue-200`
- Padding: `p-4`
- Transition: `transition-all duration-200`

**4. Candidate Match Cards**
- Avatar circle: `w-16 h-16 rounded-full` with gradient backgrounds
- Match score: Large, bold percentage in top-right
- Skill tags: `rounded-full px-3 py-1` with teal/purple backgrounds, white text
- Hover effect: `translateY(-4px)` with enhanced shadow

**5. Loading States**
- Spinner: Circular with teal border, transparent top
- Progress bar: Height `h-2`, gradient fill matching brand colors
- Loading dots: Three dots with staggered animation
- Background: White card with centered content

**6. Skill Tags**
- Border radius: `rounded-full`
- Padding: `px-3 py-1`
- Font size: `text-sm`
- Hover: `scale(1.05)` transform
- Colors: Alternate teal and purple backgrounds

**7. Results Dashboard**
- Grid layout with consistent gaps
- Sort indicator in header
- "New Search" reset button (top-right)
- Match scores prominently displayed (large, bold)

### E. Animations

**Micro-interactions:**
- Card hover: `translateY(-4px)` with 0.3s ease
- Skill tag hover: `scale(1.05)` with 0.2s ease
- Button transitions: 0.2s color/background changes

**Loading Animations:**
- Pulse: 2s infinite for status indicators
- Slide-up: 0.6s ease-out for result reveals
- Progress bar: Smooth width transitions (0.3s)
- Spinner: Continuous rotation
- Loading dots: 1.5s staggered opacity (0s, 0.3s, 0.6s delays)

**No heavy animations** - Keep interactions subtle and professional

## Layout Specifications

**Three-Phase Interface:**

1. **Input Phase**: Centered card with textarea, prominent CTA button
2. **Loading Phase**: Centered spinner, progress bar, status messages
3. **Results Phase**: Grid of candidate cards with filtering/sorting options

**Vertical Rhythm:**
- Header: `mb-8`
- Sections: `mb-8` separation
- Card internals: `mb-4` to `mb-6` for elements

**Responsive Breakpoints:**
- Mobile (base): Single column, reduced padding (`p-4`)
- Tablet (md): Two-column grid for candidates
- Desktop (lg): Three-column grid, full spacing

## Interaction Patterns

**Primary Flow:**
1. User pastes job description → Large textarea with clear placeholder
2. Click "Find Matches" → Instant loading state transition
3. Progress updates → Animated bar with contextual messages
4. Results appear → Slide-up animation, sorted by match score
5. Click candidate → Expand to show full CV details
6. "New Search" → Reset to input phase

**Data Presentation:**
- Match scores: 0-100 scale with color coding (75+ excellent)
- Skills: Tag clouds with visual separation
- Experience: Clear timeline format
- Contact info: Accessible but not primary focus

## Images

**No images required** - This is a data-driven utility interface. Avatar placeholders use initials with gradient backgrounds (matching brand colors). Focus remains on information clarity and efficient scanning.