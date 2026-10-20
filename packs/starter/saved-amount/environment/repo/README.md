# Application entry points
The dashboard and application have separate responsibilities. `repository` checks
persisted values, `dashboard` chooses the entry route, and `application` resumes
saved or submitted requests. The CLI has no session or database dependency.
