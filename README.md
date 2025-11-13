# Vacation Management API

A Flask-based RESTful API for managing employees, authentication, and vacation tracking.  
The system supports admin and regular user roles, JWT authentication, and includes endpoints for managing users, vacation totals, and vacation usage.

---

## Features

- User authentication using **JWT**
- Role-based access control (**Admin / Regular user**)
- Employee management (create, edit, delete)
- Vacation tracking:
  - Total vacation days per year
  - Used vacation days per period
  - CSV bulk upload for vacation records
- Validation for overlapping vacation dates and remaining vacation balance
- Organized modular structure using **Flask Blueprints**
- Database management via **SQLAlchemy**

---

## Tech Stack

|      Category    |       Technology        |
|------------------|-------------------------|
| Framework        | Flask                   |
| ORM              | SQLAlchemy              |
| Auth             | Flask-JWT-Extended      |
| DB               | PostgreSQL (Dockerized) |
| DB for pytests   | SQLite                  |
| Testing          | Pytest (Dockerized)     |
| CSV Parsing      | Python CSV module       |
| Containerization | Docker & Docker Compose |


---

## Setup Instructions

### 1 Clone the repository

```bash
git clone https://github.com/velicki/vacation_tracker.git
cd vacation_tracker
```

### 2 Configure environment variables

**Create a .env file in the project root:**

```bash
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=vacation_tracker
POSTGRES_PORT=5432

# Flask / SQLAlchemy
DATABASE_URL=postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:${POSTGRES_PORT}/${POSTGRES_DB}

# pgAdmin
PGADMIN_DEFAULT_EMAIL=admin@example.com
PGADMIN_DEFAULT_PASSWORD=admin
PGADMIN_PORT=5050

# Flask app
FLASK_APP=main.py
FLASK_ENV=development
FLASK_RUN_PORT=5000

# JWT
JWT_SECRET_KEY=super_secret_word_change_me
```

### 3 Run the Docker

This project uses **Docker Compose** to orchestrate multiple services:
- **Flask API** (main application)
- **PostgreSQL** (database)
- **pgAdmin** (database management interface)
- **Pytest container** (for running tests in isolation)

Each service is defined in the `docker-compose.yml` file, which also includes automatic **health checks**.  
The Flask app will not start until PostgreSQL is confirmed to be healthy (checked via `pg_isready`).

---

#### Start the containers

To build and start all services:

```bash
docker-compose up --build
```

Once started, you can access:

|  Service  |          URL          |                   Description                  |
|-----------|-----------------------|------------------------------------------------|
| Flask API | http://localhost:5000 | Main REST API                                  |
| pgAdmin   | http://localhost:5050 | PostgreSQL GUI (use the credentials from .env) |

### Stop the containers

To stop all running containers (without deleting the data):

```bash
docker-compose down
```

To stop and remove all containers, networks, and volumes (⚠️ this will erase all PostgreSQL data):

```bash
docker-compose down -v
```

### Health checks

- The PostgreSQL container includes an automatic health check using pg_isready.

- The Flask container uses depends_on with condition: service_healthy, ensuring that the API starts only after the database is fully ready.

These checks run automatically — you don’t need to manually verify service status.

### 4 Run Pytests

Automated testing is fully containerized using **Pytest** and runs independently of the production database.  
Tests are executed automatically each time the Docker environment is started.

---

#### How it works

- A dedicated **pytest container** is defined in `docker-compose.yml`.
- It runs a total of **50 unit and integration tests**.
- Tests use an **SQLite database** (in-memory) to ensure full isolation from the production **PostgreSQL** instance.
- After all tests finish, the pytest container **stops automatically**.
- Test execution is repeated **three times** for better visual clarity in Docker logs.

The commands executed inside the container are:

```bash
pytest -q /app/tests
pytest
pytest -v
```

### Viewing test results

When you run **docker-compose up**, test results will appear directly in the terminal output.
You’ll see multiple summary sections indicating test pass/fail status and duration for each run.

Example output:

```bash
============================= test session starts =============================
collected 50 items

tests/test_auth.py ..........
tests/test_users.py .........
tests/test_vacations.py .....
...
======================= 50 passed in 4.32s (3 reruns) =========================
```

### 5 How to Use the Application

After the containers are running, you can start using the **API** via tools such as **Postman**, **cURL**, or **httpie**.
The following steps describe how to initialize the system, log in, and use authorized endpoints

### Step 1: Initialize the Admin User

Before you can use the system, you must create the first admin account.
This is done through the **/auth/initialize** endpoint.

```bash
POST http://localhost:5000/auth/initialize

```

Request Example:

```json
{
    "email": "admin@example.com",
    "password": "AdminPass123!"
}
```

Response Example:

```json
{
  "message": "Initial admin created successfully"
}

```

This step can only be performed once.
If the admin already exists, the endpoint will return an error.

### Step 2: Log In to Obtain a JWT Token

After initialization, use the admin’s credentials to log in and get your access token.

```bash
POST http://localhost:5000/auth/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "AdminPass123!"
}

```

Response Example:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6..."
}
```

### Step 3: Use the JWT Token for Authorized Requests

All protected endpoints require a valid JWT token in the request header:

```bash
Authorization: Bearer <your_access_token>
```

For example, to get all users:

```bash
GET http://localhost:5000/auth/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6...
```

### Step 4: Create and Manage Employees

As an admin, you can add or remove employees via the **/auth/register** endpoints.
Each new employee can then log in and view their own vacation data.

Example – Create a new user:

```bash
POST http://localhost:5000/auth/register
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "email": "employee1@example.com",
  "password": "test123"
}
```

### Step 5: View and Manage Vacations

Employees and admins can view vacation totals and used days.
Admins can also update vacation totals or upload CSV files with vacation records.

Examples:

Get overview for a user:

```bash
GET http://localhost:5000/vacations/2
Authorization: Bearer <user_token>
```

Admin updates total vacation days:

```bash
PATCH http://localhost:5000/vacations/totals
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "user_id": 2,
  "year": 2025,
  "added_days": 3
}
```

### Step 6: pgAdmin

You can access **pgAdmin** at:

```bash
http://localhost:5050
```

Login using the credentials from your **.env** file.

### 6 Endpoints and How to Use Them

This section provides an overview of all available API endpoints, grouped by functionality.
Each subsection includes the endpoint’s purpose, required permissions, request examples, and typical responses.

### 6.1 Authentication Endpoints

POST /auth/initialize

Description:
Initializes the system by creating the first admin user.
This endpoint can only be used once, when the database is empty.

Request Example:

```bash
POST http://localhost:5000/auth/initialize
Content-Type: application/json

{
    "email": "admin@example.com",
    "password": "AdminPass123!"
}
```

Successful Response:

```json
{
    "message": "Initial admin created successfully"
}
```

Error Response (if admin already exists):

```json
{
    "error": "Setup already completed. Admin exists."
}
```

### 6.2 POST /auth/login

Description:

Authenticates a user using their email and password.
If the credentials are valid, returns a JWT access token that must be included in the **Authorization** header for all protected endpoints.

Request Example:

```bash
POST http://localhost:5000/auth/login
Content-Type: application/json

{
    "email": "admin@example.com",
    "password": "AdminPass123!"
}
```

Successful Response:

```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR..."
}
```

Usage Note:

Include the token in subsequent requests as follows:

```bash
Authorization: Bearer <your_access_token>
```

### 6.3 POST /auth/logout

Description:

Logs out the currently authenticated user by blacklisting their JWT token, preventing further use of that token.

Authentication:

Requires a valid JWT access token in the request header.

Request Example:

```bash
POST http://localhost:5000/auth/logout
Authorization: Bearer <your_access_token>
```
Successful Response:

```json
{
    "msg": "Successfully logged out"
}
```

Usage Note:

After logout, the token is added to the blacklist and cannot be used again for any authenticated request.

### 6.4 POST /auth/register

Description:

Creates a new user account.
Only admins can create new users.
If the **is_admin** field is not provided, it defaults to **false**.

Authentication:

Requires a valid JWT access token from an admin user.

Request Example:

```bash
POST http://localhost:5000/auth/register
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```

Request Body:

```json
{
    "email": "admin1@example.com",
    "password": "AdminPass123!",
    "is_admin": false
}

```

Successful Response:

```json
{
    "id": 2,
    "email": "admin1@example.com",
    "is_admin": false
}
```

Notes:

- If **is_admin** is not included, the new user will be created as a regular (non-admin) user.

- Only users with **is_admin = true** can access this endpoint.

- Passwords are securely hashed before being stored in the database.

### 6.5 GET /users/me

Description:

Returns the profile information of the currently logged-in user.
Useful for verifying the authenticated user’s details after login.

Authentication:

Requires a valid JWT access token.

Request Example:

```bash
GET http://localhost:5000/users/me
Authorization: Bearer <access_token>
```

Successful Response:

```json
{
    "id": 1,
    "email": "admin@example.com",
    "is_admin": true
}
```

Notes:

- This endpoint always returns the data of the user who owns the provided JWT.

- No parameters are required in the request.

### 6.6 GET /users/<user_id>

Description:

Fetches details for a specific user based on their unique user ID.
Only administrators can use this endpoint to view other users.

Authentication:

- Requires a valid JWT access token
- Admin-only access

Request Example:

```bash
GET http://localhost:5000/users/1
Authorization: Bearer <access_token>
```

Successful Response:

```json
{
    "id": 1,
    "email": "admin@example.com",
    "is_admin": true
}
```

Notes:

- The **<user_id>** parameter must be a valid integer ID of an existing user.

- If the user does not exist, the response will return a 404 error with:

```json
{"error": "User not found"}
```

### 6.7 GET /users/

Description:

Retrieves a complete list of all registered users in the system.
Only administrators can access this endpoint.

Authentication:

- Requires a valid JWT access token
- Admin-only access

Request Example:

```bash
GET http://localhost:5000/users/
Authorization: Bearer <access_token>
```

Successful Response:

```json
[
    {
        "id": 1,
        "email": "admin@example.com",
        "is_admin": true
    },
    {
        "id": 2,
        "email": "admin1@example.com",
        "is_admin": false
    }
]
```

Notes:

- Regular users are not authorized to access this endpoint.

- If a non-admin token is used, the API will return a 403 error:

```json
{
    "error": "Admin only"
}
```

### 6.8 PUT /users/<user_id>

Description:

Updates user account information.
Both admins and regular users can access this endpoint, but with different permissions.

Authentication:

- Requires a valid JWT access token

Admin Permissions:

- Can update any user’s password or admin status

- Cannot remove their own admin status (**is_admin: false** on themselves is forbidden)

Request Example (Admin updating another user):

```bash
PUT http://localhost:5000/users/2
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```
```json
{
    "is_admin": false,
    "password": "UserPass123!"
}
```

Regular User Permissions:

- Can only update their own password

- Cannot change **is_admin** field

- Cannot modify other users’ data

Request Example (Regular user updating own password):

```bash
PUT http://localhost:5000/users/2
Authorization: Bearer <user_access_token>
Content-Type: application/json
```
```json
{
    "password": "MyNewPassword123!"
}
```

Successful Response:

```json
{
    "id": 2,
    "email": "admin1@example.com",
    "is_admin": false
}
```

Error Example:

- Admin tries to remove own admin status:

```bas
{"error": "Cannot remove your own admin status"}
```

### 6.9 DELETE /users/<user_id>

Description:

Deletes a user account from the system.
Only admins can perform this action.

Authentication:

- Requires a valid Admin JWT access token

Request Example:

```bash
DELETE http://localhost:5000/users/2
Authorization: Bearer <admin_access_token>
```

Successful Response:

```json
{
    "message": "User admin1@example.com deleted successfully"
}
```

### 6.10 POST /vacations/totals

Description:

Creates a new total vacation record for a specific user and year.
Only admins are allowed to perform this action.

Authentication:

- Requires a valid Admin JWT access token

Request Example:

```bash
POST http://localhost:5000/vacations/totals
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```

Request Body:

```json
{
    "user_id": 1,
    "year": 2019,
    "total_days": 30
}
```

Successful Response:

```json
{
    "employee_id": 1,
    "message": "Vacation total created",
    "total_days": 30,
    "year": 2019
}
```

### 6.11 PATCH /vacations/totals

Description:

Updates an existing vacation total by adding extra vacation days for a specific user and year.
Only admins can perform this action.

Authentication:

- Requires a valid Admin JWT access token

Request Example:

```bas
PATCH http://localhost:5000/vacations/totals
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```

Request Body:

```json
{
    "user_id": 1,
    "year": 2019,
    "added_days": 5
}
```

Successful Response:

```json
{
    "employee_id": 1,
    "message": "Vacation total updated",
    "total_days": 35,
    "total_days_left": 35,
    "year": 2019
}
```

### 6.12 GET /vacations/<user_id>

Description:

Retrieves a vacation overview for a specific user, listing all years with:

- total vacation days,

- used days,

- remaining days.

Authentication:

- Requires a valid JWT access token

- Admin: Can view any user's vacation overview

- Regular user: Can view only their own profile

Request Example:

```bash
GET http://localhost:5000/vacations/1
Authorization: Bearer <jwt_access_token>
```

Successful Response Example:

```json
[
    {
        "year": 2019,
        "total_days": 35,
        "used_days": 0,
        "days_left": 35
    },
    {
        "year": 2020,
        "total_days": 30,
        "used_days": 0,
        "days_left": 30
    },
    {
        "year": 2021,
        "total_days": 25,
        "used_days": 0,
        "days_left": 25
    }
]
```

### 6.13 POST /vacations/vacation-used

Description:

Adds a vacation usage record for a user.

- Only admin users can add vacation usage.

- The system automatically calculates workdays between **start_date** and **end_date**, excluding weekends.

- Prevents overlapping vacation periods in workdays.

Authentication:

- Requires a valid Admin JWT access token

Request Example:

```bash
POST http://localhost:5000/vacations/vacation-used
Authorization: Bearer <admin_jwt_access_token>
Content-Type: application/json
```

Request Body

```json
{
    "user_id": 1,
    "start_date": "2019-04-01",
    "end_date": "2019-04-22"
}
```

- Note: CSV file upload is also supported for bulk entries, but JSON mode is shown here.

Successful Response Example:

```json
{
    "message": "Vacation entry added",
    "days_used": 16,
    "days_left_now": 19
}
```

- In this example, the total range between **start_date** and **end_date** was 22 days, but weekends are automatically excluded, so 16 days of vacation are counted and 19 days remain.

### 6.14 GET /vacations/<user_id>/<year>

Description:

Returns the vacation usage details for a specific year for a user.

- Admins can view any user.

- Regular users can only view their own data.

- Lists total vacation days, used days, remaining days, and detailed vacation entries for that year.

Authentication:
- Requires a valid JWT access token

Request Example:

```bash
GET http://localhost:5000/vacations/1/2019
Authorization: Bearer <jwt_access_token>
```

Request Parameters:

| Parameter | Type | Description                                    |
| --------- | ---- | ---------------------------------------------- |
| user_id   | int  | ID of the user whose vacation is being queried |
| year      | int  | Year for which vacation details are requested  |

Successful Response Example:

```json
{
    "year": 2019,
    "total_days": 35,
    "used_days": 26,
    "days_left": 9,
    "vacations": [
        {
            "id": 1,
            "start_date": "2019-04-01",
            "end_date": "2019-04-22",
            "days_used": 16
        },
        {
            "id": 2,
            "start_date": "2019-05-10",
            "end_date": "2019-05-23",
            "days_used": 10
        }
    ]
}
```

### 6.15 GET /vacations/<user_id>/used?from=YYYY-MM-DD&to=YYYY-MM-DD

Description:

Returns the number of vacation days used by a user within a specified period.

- Admins can view any user.

- Regular users can only view their own data.

- The calculation excludes weekends (Saturdays and Sundays).

Authentication:

- Requires a valid JWT access token

Request Example:

```bash
GET http://localhost:5000/vacations/1/used?from=2019-03-01&to=2019-04-09
Authorization: Bearer <jwt_access_token>
```

Request Parameters:

| Parameter | Type   | Description                                          |
| --------- | ------ | ---------------------------------------------------- |
| user_id   | int    | ID of the user whose vacation usage is being queried |
| from      | string | Start date in `YYYY-MM-DD` format                    |
| to        | string | End date in `YYYY-MM-DD` format                      |

Successful Response Example:

```json
{
    "user_id": 1,
    "from": "2019-03-01",
    "to": "2019-04-09",
    "days_used": 7
}
```

### 6.16 Bulk CSV Uploads

Certain endpoints allow admin users to perform bulk operations via CSV uploads.
All CSV endpoints require an admin JWT token.

How to upload a CSV file in Postman:

1. Go to the Body → form-data tab.

2. Set the Key = **file**.

3. Set the Type = **File**.

4. Select the desired CSV file.



1. Add new users – **POST /auth/register**

Description: Bulk create users.

Format of CSV file:

```bash
Employee Email,Employee Password
user1@rbt.rs,Abc!@#$
user2@rbt.rs,Abc!@#$
user3@rbt.rs,Abc!@#$,true
user4@rbt.rs,Abc!@#$,false
```

- The **is_admin** field is optional (defaults to **false**).

Response Example:

```json
{
    "created": 99,
    "duplicates_skipped": 0,
    "message": "Bulk import completed"
}
```

2. Add vacation totals per year – **POST /vacations/totals**

Description: Bulk upload total vacation days for employees.
CSV format: First row should contain the year, second row headers like **Employee,Total vacation days**.

Format of CSV file:

```bash
Vacation year,2019
Employee,Total vacation days
user1@rbt.rs,30
user2@rbt.rs,25
user3@rbt.rs,28
```

Response Example:

```json
{
    "created": 56,
    "skipped_existing": [],
    "skipped_not_found": [],
    "year": 2019
}
```

3. Add used vacation days – **POST /vacations/vacation-used**

Description: Bulk upload vacation usage records for employees.

- Automatically calculates workdays (excludes weekends).

- Skips entries if the employee does not exist, does not have vacation total for the year, overlaps with existing vacations, or lacks enough remaining days.

Format of CSV file:

```bash
Employee,Vacation start date,Vacation end date
user1@rbt.rs,"Friday, August 30, 2019","Wednesday, September 11, 2019"
user1@rbt.rs,"Thursday, October 24, 2019","Thursday, October 24, 2019"
user1@rbt.rs,"Friday, November 22, 2019","Friday, November 22, 2019"
user1@rbt.rs,"Monday, March 9, 2020","Monday, March 9, 2020"
user1@rbt.rs,"Monday, May 25, 2020","Thursday, May 28, 2020"
```

Response Example:

```json
{
    "created": 42,
    "skipped_not_found": ["user1@example.com"],
    "skipped_no_total_for_year": ["user2@example.com"],
    "skipped_overlap": ["user3@example.com"],
    "skipped_not_enough_days": ["user4@example.com"]
}
```


### Roles and Permissions:

|     **Role**     | -> |                    Permissions                    |
|------------------|----|---------------------------------------------------|
| **Admin**        | -> | Can manage users, assign vacations, view all data |
| **Regular User** | -> | Can view their own vacation info                  |

