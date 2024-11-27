# User Proxy authentication

## Problem description

In Provena, services are deployed in a microservice type architecture. Sometimes, there are privileged operations which only certain 

```mermaid
sequenceDiagram
    participant User
    participant Service A
    participant Service B
    participant Keycloak

    # user login
    Note right of User: login
    User->>Keycloak: login(creds)
    Keycloak-->>User: user token

    # user normal request
    Note right of User: typical request
    User->>Service A: POST /action [user token]
    Service A->>Service A: actions
    Service A-->>User: 200 OK

    # problematic request
    Note over User,Service A: problematic proxy request
    User->>Service A: POST /action [user token]
    Note right of Service A: service account login
    Service A->>Keycloak: login(creds)
    Keycloak-->>Service A: service token
    Service A->>Service B: /special-route [service token]
    Service B->>Service B: checks auth
    Note over Service B: At this point, Service B can't access<br/>the original roles of the User.<br/> For example, what if the user is an admin.
    Service B-->>Service A: 401
    Service A-->>User: 401

```

## Implemented approach

## Technical notes
