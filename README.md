# rockscraper-backend

RockScraper is an AI and [UpRock's](https://uprock.com/) DePIN powered Scraper. This repository holds the backend of RockScraper.

### Setup

1. Update the environment variables in `.env.dev`, `.env.test`, or `.env.prod` as needed

### Environment Variables

The following environment variables are required for the database connection:

```
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=rockscraper_db
```

### Docker

To run the application with Docker:

```bash
npm run dockerUp
```

This will start the application with PostgreSQL and Redis.
