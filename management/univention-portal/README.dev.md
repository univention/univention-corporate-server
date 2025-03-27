# Component moved

The component `univention-portal` is now maintained in a separate dedicated repository,
See `univention/components/univention-portal#737` for the status of the migration.

## Building & CI/CD

Import into repo-ng bildsystem via:

```
repo_admin.py \
    -G git@git.knut.univention.de:univention/components/univention-portal.git \
    -b develop \
    -p univention-portal \
    -P . \
    -r 5.2-0 -s errata5.2-0-or-similar
```

## OIDC Authenticator Overview

* **`OIDCAuthenticator` (`authenticator.py`):** This is the main orchestrator for OIDC logins within the portal. It handles user-facing login/logout requests, manages session cookies, decides when to talk to the OIDC Provider (OP), and uses the other components to perform the necessary steps. It also retrieves user information once authenticated.

* **`oidc` Package:**
    * **`OIDCAuth` (`auth.py`):** This class handles the direct communication with the OIDC Provider (like Keycloak). It knows how to build the correct URLs, exchange codes for tokens, refresh tokens, validate received tokens, and handle logout requests according to the OIDC protocol standards.
    * **Database (`db.py`):** This part manages storing and retrieving session data.
        * `OIDCSession`: A structure holding the user's tokens and related data.
        * `SessionRepository`: Specifically handles saving, finding, updating, and deleting user `OIDCSession` data in the database.
        * `StateRepository`: Temporarily stores information needed during the login redirect process to prevent attacks.
        * `cleanup`: A background task to remove old/expired data from the database.
    * **Schema (`schema.py`):** Defines *what* the database tables look like for storing the session and state information.

### How they fit together (Simplified Login):

1.  `OIDCAuthenticator` gets a login request.
2.  It uses `OIDCAuth` to figure out where to send the user for authentication and stores temporary data via `StateRepository`.
3.  After the user logs in externally, they are redirected back. `OIDCAuthenticator` gets the callback.
4.  It retrieves the temporary data using `StateRepository`.
5.  It uses `OIDCAuth` to exchange the received code for actual user tokens and validates them.
6.  `OIDCAuthenticator` creates a session record (`OIDCSession`) and saves it using `SessionRepository`.
7.  The user gets a session cookie, and the portal now knows who they are.
