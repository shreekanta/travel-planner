# Frontend CLAUDE Guidance

This document provides specific guidance for the frontend development within the TravelPlanner project.

## Standards and Best Practices
@import url("../CLAUDE.md") # Example: import shared root guidance
@import url("./frontend_standards.md") # Example: import frontend-specific standards

## Frontend Commands

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
npm run build        # tsc + vite build
```

Point the UI at a non-default backend:
```bash
VITE_API=http://localhost:8000 npm run dev
```

## Frontend Specifics
*   ... (add frontend-specific instructions here)
