# Spy Cat Agency - Backend

This is the backend for the Spy Cat Agency management system. It provides a RESTful API to manage spy cats, their missions, and assigned targets.

## Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/your-username/spy-cat-backend.git
cd spy-cat-backend
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the root directory and define your database URL:

```
DB_USER=postgres
DB_PASSWORD=federico
DB_HOST=localhost
DB_PORT=5432
DB_NAME=developsToday
```

### 4. Run the application

```bash
fastapi dev main.py
```

The API will be available at http://localhost:8000

### 5. API Documentation

Once the server is running, you can explore the API at:

- **Swagger:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Postman Collection

You can find the Postman collection for testing all endpoints [here](https://developstodaytest-9107.postman.co/workspace/DevelopsTodayTest-Workspace~548b06be-db7f-48cc-8672-93c800e16cc1/collection/32813474-14b244b7-2b97-4346-9bec-e4455ac7b3a1?action=share&creator=32813474).

## Available Endpoints

### Spy Cats

- `POST /cats` - Create a new spy cat
- `GET /cats` - List all spy cats
- `GET /cats/{id}` - Get a single cat
- `PUT /cats/{id}` - Update cat's salary
- `DELETE /cats/{id}` - Remove a spy cat

### Missions

- `POST /missions` - Create a mission with targets
- `GET /missions` - List all missions
- `GET /missions/{id}` - Get mission details
- `PUT /missions/{mission_id}/assign` - Assign a cat to a mission
- `DELETE /missions/{id}` - Delete a mission (if not assigned)

### Targets

- `PUT /missions/{mission_id}/targets/{target_id}/notes` - Update notes (only if not complete)
- `PUT /missions/{mission_id}/targets/{target_id}/complete` - Mark target as complete

## Notes

- All breed validations are made using TheCatAPI.
- Once all targets are marked as complete, the mission is automatically completed.

## Contact

For questions or support, please contact: fededeniard@gmail.com
