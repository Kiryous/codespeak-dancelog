// This is a comment. This line is ignored.
<!-- This is a multiline comment. 
These lines are ignored too. -->

// Feel free to un-comment the example spec below to try CodeSpeak in action:

Dancelog is an internal CRM for a Lindy-Hop dance studio used by admins and teachers to log attended students and payments.

### Tech Stack

- Django
- Tailwind CSS

### Data

- Group
  - schedule: pairs of day of the week + time (e.g., tue, 19:30; thu 20:30)
  - duration: (e.g. 1hr, 90min, etc)
  - start_at: date
  - finished_at: date or null for active groups
  - location: multiline text field for location name and google link, etc
  - prices: One to Many FK to Price
  - teachers: Many to Many FK to User

- Pass
  - price: number
  - group: FK Group
  - lessons_included: int
  - skips_included: int

- User
  - email
  - password

- Student
  - user
  - groups

- StudentVisit
  - student: FK
  - group: FK
  - date: date
  - skipped: bool

- Purchase
  - student: FK
  - pass: FK
  - created_at: date
  - paid_at: date or null
  - payment_method: enum TBC, BOG, Cash
  - cashier: FK Teacher

- Teacher
  - user
  - groups (backlink)

### User stories

- as an admin I want to add a new group
- as a teacher I want to see list of the lessons sorted by the closest date (e.g. 21 Oct 2025, 19:30, Lindy Hop Beginners with Asya&Katya, Melita Dance Studio and so on and so forth for each instance)
- as a teacher I want to mark visited students: from a list of students assigned to this group but also can add new student from other groups or from scratch
- as a teacher/admin I want to add new students
- as a teacher/admin I want to log purchases and see the remaining lessons or outstanding balance for each student

### Notes

Use simple Django auth for teachers and admins, students cannot login at the moment, they are just entities created by admins/teachers. Design: create minimalistic UI inspired by Swiss Typography, not usual lovable/bolt slop with a lot of meaningless gradients, keep it simple and beatiful. 
