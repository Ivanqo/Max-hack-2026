# Admin Frontend

React + TypeScript admin panel for managing the platform.

## Features

- Dashboard with analytics overview
- Knowledge base management (CRUD)
- Opportunities management (CRUD)
- Career roles management (CRUD)
- Analytics and reporting
- Protected routes with authentication
- Responsive design

## Setup

```bash
npm install
npm run dev
```

The admin panel will run on `http://localhost:5174` with API proxy to `http://localhost:3000`.

## Tech Stack

- React 18
- TypeScript
- Vite
- React Router
- Axios
- Tailwind CSS
- Lucide Icons

## Project Structure

```
src/
├── api/           # API client configuration
├── components/    # Reusable components
├── contexts/      # React contexts (Auth)
├── pages/         # Page components
├── types/         # TypeScript type definitions
└── utils/         # Utility functions
```

## Authentication

Admin users must have `role: 'admin'` to access the panel. The auth token is stored in localStorage.
