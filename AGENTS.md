Namma Clinic Engineering Rules

1. Authoritative workspace:
   D:\project\namma_clinic

2. Branch:
   feature/namma-clinic-demo-data-model

3. Stack:
   PostgreSQL 16
   Django 4.2 / DRF
   React / Vite / TypeScript

4. Local-only application.
   No Docker/cloud deployment unless explicitly requested.

5. Use existing architecture before creating new models/services.

6. Backend is authoritative for:
   RBAC
   facility scope
   business rules
   data validation

7. Use StaffRoleAssignment + RolePermission for authorization.
   Do not use legacy User.role as independent authority.

8. Multiple independent roles are allowed on one StaffProfile.

9. Never create combined roles such as:
   NURSE_COMPOUNDER
   PHARMACY_INVENTORY

10. Maternal/Child functionality is out of scope.

11. No fake/hardcoded business data.

12. InventoryLedger is the inventory source of truth.

13. Pharmacy consumes inventory through the inventory service/ledger.
    Pharmacy must not directly mutate stock.

14. Every implementation must have:
    code tests
    browser/Playwright validation
    database verification

15. For UI workflows:
    enter data through the real UI.
    Do not validate only through direct API calls.

16. If browser behavior differs from code/test expectations:
    investigate the runtime path and fix the root cause.

17. Before implementation:
    inspect current Git/code and reuse existing functionality.

18. Do not duplicate existing models/services.

19. Commit completed implementation.

20. Report:
    commit
    tests
    Playwright result
    DB verification
    remaining issues