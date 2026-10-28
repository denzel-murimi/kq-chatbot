Database Migrations
Apply migrations in numerical order using the Supabase SQL Editor.

Example:

Open Supabase
Open SQL Editor
Paste the contents of the migration file
Run it
Apply the next migration
Security Model
This project uses two layers of protection for database tables:

Table grants
Row Level Security (RLS)
The FastAPI backend connects directly to PostgreSQL using the postgres role.

Because the postgres role has BYPASSRLS, RLS policies do not protect the backend connection itself.

Passenger access control is enforced in the backend using PNR and last-name verification.

RLS and revoked grants provide defense in depth by preventing unauthorized access through Supabase's auto-generated REST API.