# Trekking Management Application

A role-based web application for coordinating trekking activities, built for the
App Dev I course project. Admins manage treks and staff, Trek Staff run their
assigned treks, and Trekkers browse and book open treks.

## Tech Stack

- **Backend:** Flask (application factory + Blueprints)
- **Frontend:** Jinja2 templates, HTML, CSS, Bootstrap 5 (CSS only — no JavaScript
  is used anywhere in the app, including for the core requirements; Bootstrap is
  vendored locally in `app/static/css/` so the demo works fully offline)
- **Database:** SQLite, created and seeded **programmatically** via
  Flask-SQLAlchemy (`db.create_all()`), never via a manual tool like DB Browser
- **Auth / sessions:** Flask-Login
- **Forms & CSRF protection:** Flask-WTF / WTForms

## Project Structure

```
Trekking-Management-Application/
├── app/
│   ├── __init__.py          # App factory: extensions, blueprints, DB creation, admin seed
│   ├── models.py             # User, StaffProfile, Trek, Booking
│   ├── forms.py               # WTForms (registration, login, trek, profile, search, etc.)
│   ├── decorators.py          # role_required, approved_staff_required
│   ├── routes/
│   │   ├── main.py            # Landing page
│   │   ├── auth.py            # Register / login / logout
│   │   ├── admin.py           # Admin dashboard, trek CRUD, staff & user management, search
│   │   ├── staff.py           # Staff dashboard, trek updates, participant lists
│   │   ├── trekker.py         # Trekker dashboard, browse/search/book treks, history
│   │   └── api.py             # Read-only JSON API resources
│   ├── templates/              # Jinja2 templates (Bootstrap 5 styling)
│   └── static/css/style.css
├── config.py                   # App config (SQLite URI, default admin credentials)
├── run.py                      # Entry point
├── requirements.txt
└── instance/                   # trekking.db is created here at first run (gitignored)
```

## Roles & Functionality

### Admin (pre-seeded, no self-registration)
- Add / edit / remove treks (removal preserves history: a trek with existing
  bookings is closed rather than hard-deleted)
- Approve / reject / blacklist / reinstate Trek Staff registrations
- Assign an approved staff member to a trek
- View all users, staff, and treks; view every booking ever made
- Search treks, staff, and users by name, location, or ID
- Blacklist / reinstate trekker accounts
- Dashboard shows total treks, open treks, total trekkers, total staff, total
  bookings, and pending staff-approval count, plus a no-JavaScript bar chart
  (Bootstrap progress bars) of the most popular treks by bookings

### Trek Staff
- Self-register, then must wait for admin approval before the dashboard
  unlocks (a pending/rejected/blacklisted staff member sees a status message
  instead of trek data)
- Dashboard lists only the treks assigned to them, with live registration
  counts
- Update a trek's available slots and status (Open / Closed / Started /
  Completed) — only for treks assigned to them (enforced server-side, 403
  otherwise). Marking a trek Completed also moves all its active bookings to
  `Completed`, building each trekker's history
- View the participant list for each of their treks
- Edit their own profile (name, contact, password)

### User (Trekker)
- Self-register and log in
- Browse treks with status `Approved` or `Open`; filter by name, location, and
  difficulty
- Book a trek (only possible while it is `Open` and has free slots)
- View booking status and full trekking history (bookings are never deleted —
  cancelling sets status to `Cancelled` rather than removing the record)
- Cancel an active booking (restores one slot to the trek)
- Edit their own profile

## Data Model

- **User** — id, name, email, password_hash, contact, role
  (`admin`/`staff`/`trekker`), account_status (`Active`/`Blacklisted`)
- **StaffProfile** (1:1 with a `staff`-role User) — id, user_id,
  approval_status (`Pending`/`Approved`/`Rejected`)
- **Trek** — id, name, location, difficulty (`Easy`/`Moderate`/`Hard`),
  duration_days, total_slots, available_slots, assigned_staff_id (FK →
  StaffProfile, nullable), status
  (`Pending`/`Approved`/`Open`/`Closed`/`Started`/`Completed`), start_date,
  end_date, description
- **Booking** — id, user_id (FK → User), trek_id (FK → Trek), booking_date,
  status (`Booked`/`Cancelled`/`Completed`)

### Entity relationships

```
User (role=staff) 1───1 StaffProfile 1───* Trek 1───* Booking *───1 User (role=trekker)
```

- One staff profile can be assigned to many treks; each trek has at most one
  assigned staff member.
- One trekker can have many bookings; each booking belongs to exactly one
  trek and one trekker. Bookings are append-only history — cancelling changes
  status instead of deleting the row, and re-booking after a cancellation is
  allowed.

## Key Design Decisions

- **Overbooking prevention:** booking a trek performs an atomic
  `UPDATE treks SET available_slots = available_slots - 1 WHERE id = ? AND
  status = 'Open' AND available_slots > 0`. If zero rows are updated, the
  booking is rejected — this avoids race conditions between two concurrent
  bookings for the last slot.
- **Historical data:** Bookings are never hard-deleted; treks with existing
  bookings are closed instead of removed by the admin, so a trekker's history
  and an admin's audit trail both stay intact.
- **Access control:** every blueprint enforces `login_required` +
  `role_required(...)` via a `before_request` guard. Staff additionally get an
  `approved_staff_required` decorator on trek-management routes, and a trek
  can only be managed by the staff member it is actually assigned to
  (returns 403 otherwise).
- **No JavaScript:** all interactivity (forms, navigation, flash messages,
  charts) is implemented with plain HTML forms, server-side redirects, and CSS,
  per the project's "no JS for core requirements" constraint. Frontend
  validation uses HTML5 (`required`, `type="email"`, etc. rendered by
  WTForms); full validation is repeated server-side in Flask controllers.

## API Resource Endpoints (JSON)

| Method | Endpoint          | Access     | Description                          |
|--------|-------------------|------------|--------------------------------------|
| GET    | `/api/treks`      | Public     | All Approved/Open treks              |
| GET    | `/api/treks/<id>` | Public     | Single trek by ID                    |
| GET    | `/api/users`      | Admin only | All users (id, name, email, role, status) |
| GET    | `/api/bookings`   | Admin only | Every booking record                 |

## Setup & Running Locally

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

The app starts on `http://127.0.0.1:5000/`. On first run it automatically
creates `instance/trekking.db` and seeds a default admin account:

- **Email:** `admin@trekking.com`
- **Password:** `Admin@123`

(Change `DEFAULT_ADMIN_EMAIL` / `DEFAULT_ADMIN_PASSWORD` in `config.py` before
a real deployment.)

### Typical demo flow

1. Log in as the seeded admin and create a trek.
2. Register a new account with role "Trek Staff" (in a different browser /
   incognito session), then log in — the dashboard will show a
   pending-approval message.
3. As admin, approve the staff member (Manage Staff page) and assign them to
   the trek you created.
4. Register a "Trekker" account, browse open treks, and book the one you
   created.
5. As staff, view the participant list and update slots/status; as admin,
   view the booking in the dashboard/bookings list and try the search page.
