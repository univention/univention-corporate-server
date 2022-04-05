# Univention Management Console

## OAuth 2.0 Authorization in UCS and OIDC Authentication in UMC

### Glossary
#### OIDC / OAuth 2

- **OAuth 2.0**: OAuth 2.0 is an authorization framework for secure resource sharing.

- **OIDC**: OpenID Connect is an identity layer built on top of OAuth 2.0, designed for authentication and identity verification. It introduces identity-related features to OAuth 2.0.

#### Tokens

- **ID-Token**: In OIDC, an ID-Token is a JSON Web Token (JWT) that carries identity information of an authenticated user. Defined in [OIDC Core, Section 2](https://tools.ietf.org/html/rfc6749#section-4.1.2.1).

- **Access Token**: An Access Token is used in OAuth 2.0 to authorize access to protected resources. Defined in [OAuth 2.0, Section 1.4](https://tools.ietf.org/html/rfc6749#section-1.4).

- **Refresh Token**: Used to obtain a new access token after the original access token expires. Provides long-term access to resources and is usually tied to the client's authorization.

- **Bearer Token**: A type of access token that is presented by the client when accessing protected resources. Typically used in the "Bearer" HTTP authentication scheme. Defined in [Bearer Token Usage](https://tools.ietf.org/html/rfc6750).

- **JWT (JSON Web Token)**: A compact, URL-safe means of representing claims to be transferred between two parties. Can be used as access tokens, ID tokens, or in other contexts where data needs to be securely transmitted.

#### Token Information

- **Claim**: A piece of information in a token that describes a user's identity or attributes.

- **AZP (Authorized Party)**: An optional claim in the ID-Token, representing the party to which the ID-Token was issued. Defined in [OIDC Core, Section 5.1](https://tools.ietf.org/html/rfc6749#section-5.1).

- **AUD (Audience)**: The audience for a token, indicating the recipient for which the token is intended. Defined in [OAuth 2.0, Section 2.1](https://tools.ietf.org/html/rfc6749#section-2.1).

#### Roles (Parties and Providers)

- **Resource Owner (RO)**: The user who owns the resource being accessed.

- **Client**: The application requesting access to a user's resources. It is either public or private.

- **User Agent**: The user's client device (e.g., web browser or mobile app) used for user interactions and redirections in the authorization process.

- **Authorization Server**: Responsible for authenticating the user and issuing access tokens. It plays a central role in the OAuth 2.0 and OIDC protocols.

- **Resource Server (RS)**: The resource server hosts protected resources and is capable of accepting and responding to protected resource requests.

- **OpenID Provider (OP)**: In OIDC, the OpenID Provider is the identity provider responsible for authenticating users and issuing ID-Tokens. It is a specialized form of an authorization server. Defined in [OIDC Core, Section 2](https://tools.ietf.org/html/rfc6749#section-4).

- **Relying Party (RP)**: A relying party is an application or service that relies on received tokens to access protected resources or verify user identity. It can be a client application in OAuth 2.0 or OIDC.

#### Authentication Flows and Grant types
OAuth 2.0 defines various flows to enable secure authorization and resource access. A grant is the way how the credentials are exchanged.
The most commonly used ones are:

- **Authorization Code Flow**: Used by confidential clients to obtain an access token by exchanging it with an authorization code.

- **Authorization Code Flow with PKCE**: Enhancement of authorization code flow with Proof Key for Code Exchange to protect against *code* interception attacks [RFC 7636](https://tools.ietf.org/html/rfc7636).

- **Implicit Flow**: Used by public clients to obtain an access token directly (instead of a code). Discouraged for security reasons

- **Client Credentials Flow**: Used by confidential clients to obtain an access token using client credentials.

- **Resource Owner Password Credentials Flow**: Allows a resource owner to provide credentials directly to the client, which then exchanges them against a token.

- **Device (Code) Flow**: Used by devices that do not have a browser to obtain user consent.

- **Refresh Token Flow**: Used by clients to exchange a refresh token with an access token when it has expired without involving the user agent.

##### Authorization Code Flow

- **Authorization Code**: A short-lived code that the client uses to obtain an access token from the authorization server.

- **Client ID**: A unique identifier for the client application, which is registered with the authorization server.

- **Client Secret**: A shared secret key between the client and the authorization server (used by confidential clients).

The Authorization Code Flow is one of the most secure OAuth 2.0 flows and is often used for web and mobile applications. In this flow:

1. The client initiates the authorization request and redirects the user to the authorization server.

2. The user authenticates and consents to the client's request.

3. The authorization server redirects the user back to the client with an authorization code.

4. The client exchanges the authorization code for an access token.

### Meaning of Audience, Authorized Party in ID-Token and Access-Token
An ID Token (OIDC) is intended for a Relying Party ("Client" in OAuth 2) which transfers the identity of the user.
An Access Token (OAuth 2) is intended for a Resource server. In the beginning no structure for access tokens were defined, therefore it was opaque for the client. A relatively new standard (RFC 9068) now defines the structure.

The Audience (aud) in an Access Token should contain an identifier for the resource server (e.g. "ldaps://example.org/").
See [JWT spec](https://datatracker.ietf.org/doc/html/rfc7519#section-4.1.3) and the description of `aud` in [RFC 9068](https://datatracker.ietf.org/doc/html/rfc9068#JWTATLRequest).
An access token is a bearer token and the OAuth standard family doesn't seem to have a concept of the resource server being able or required to check if the client is trusted by the resource server. The latest addition [OAuth 2.0 DPoP](https://www.rfc-editor.org/rfc/rfc9449.html) has some potential for that, but that may be to early to adopt to.

The Audience (aud) in a ID-Token refers to the client/Relying Party (e.g. "https://example.org/univention/oidc/").
See [id\_token specified in OIDC](https://openid.net/specs/openid-connect-core-1_0.html#IDToken), where `aud` refers to the client/RP. That's exactly what the [JWT spec](https://datatracker.ietf.org/doc/html/rfc7519#section-4.1.3) says: `aud` tells who shall evaluate the specific JWT.

Multiple entries in the Audience claim are allowed.

Maybe we need to make use of the [RFC8707 Resource Indicator](https://www.rfc-editor.org/rfc/rfc8707.html) to give a hint to Keycloak what value to put into the `aud` claim of the access token.
A Resource Server must check the Audience in an Access Token and a Relying Party/Client must ignore it.

The Authorized Party (azp) in an Access Token should contain one or more trusted relying parties.
A Relying Party/Client must check if the Authorized Party was issued for itself.
A Resource Server does not need to validate the AZP - but it's also not forbidden to do this. It usually doesn't know the corresponding client/RP.
https://community.auth0.com/t/azp-field-in-the-access-token/46724/4

// Aber in der Tat ist in https://datatracker.ietf.org/doc/html/rfc9068#name-validating-jwt-access-token nicht die Rede von azp sondern von aud.
// Ist ein bisschen verwirrend. https://stackoverflow.com/questions/41231018/openid-connect-standard-authorized-party-azp-contradiction z.B. redet über die ID-Token aber ich stimme zu, das dort ebenfalls verlinkte [doc](https://openid.net/specs/openid-connect-core-1_0.html) lese ich so, dass azp die client\_id enthalten sollte von der RP, die das token angefragt hat. aud hingegen muss auch die client\_id enthalten, kann aber zusätzlich weitere identifier enthalten, und dazu gehört meinem Verständnis nach auch die proteted resource.

#### Keycloak defaults are wrong:
The default access token in Keycloak looks like a mess:
* It doesn't have an `aud` claim at all
* It has an `azp` claim instead, which is non-standard in the OAuth 2.0 world: It's neither part of RFC 7519 nor of RFC 9068 nor RFC 8707. It is in fact only defined in the of the OpenID-Connect core standard and shall mention the client/RP in an *ID token*.
* It doesn't follow RFC 9068 in other aspects either, see https://github.com/keycloak/keycloak/discussions/19419 and https://github.com/keycloak/keycloak/discussions/8646

The Keycloak documentation describes one way to
* [Automatically add audience](https://www.keycloak.org/docs/latest/server_admin/#_audience_resolve) but the description is a bit cryptic. AFAIU the resource server would need to be represented in Keycloak by creating a `bearer-only client` and then the `aud` for the access token should be derived automatically from the associated `scope` claims.
* ^ That mechanism is explicitly referred to in the introduction of [RFC 8707](https://datatracker.ietf.org/doc/html/rfc8707), which suggests a different method, where the client/RP can specify to the IdP which `resource` it intends to access. In our case the UMC could append `&resource=ldaps%3A%2F%2Fexample.com/` to its request to the authorization (and/or token) endpoint of the IdP. In this case `ldaps://example.com` would be an "abstract identifier" that each LDAP-server in that domain identifies with (so to speak).
* But [Keycloak doesn't implement RFC8707 yet](https://github.com/keycloak/keycloak/issues/14355), instead it supports the parameter `&audience=...`
* (Instead of making the scope derivation dance described in [Automatically add audience](https://www.keycloak.org/docs/latest/server_admin/#_audience_resolve) Keycloak also documents how to [add a Hardcoded audience](https://www.keycloak.org/docs/latest/server_admin/#_audience_hardcoded), that the client can request by specifying e.g. `&scope=ldap-service`, but that's just a minor implementation difference internal to Keycloak. The only advantage I see is that one would not need to explicitly create a `bearer-only client` representing the LDAP-servers in Keycloak.)

TODO: when Keycloak supports the official `?audience=…` RFC 8707 we should change the hardcoded aud mapper, so that UMC explicitly requests the permissoins for LDAP access.

### Realization of the security concept

The following roles are taken:
- **Keycloak**: Authorization Server / OpenID Provider
- **UMC**: Relying Party/client (validates ID Token); some kind also additionally takes the role of Resource server.
- **LDAP-server**: Resource Server (validates Access Token)
- **UDM REST API**: Resource Server and Relying Party

UMC implements the Authorization Code Flow with PKCE, provides Logout endpoints for front-channel and back-channel logout, is able to use the refresh-token to renew an access token when the session has expired.
During authentication the ID token is validated by the UMC-server and the access token (in form of a JWT) is given to PAM oauthbearer.
We do this duplicated check to enhance security and make sure both ways are in sync.
The PKCE code challenge method is `S256`.
When creating a LDAP connection as the user the `OAUTHBEARER` SASL module is used and the access token (JWT) is provided as password.
The SASL module validates access tokens, which require to have the `ldap://domainname/` audience and optionally the UMC client id as authorized party.

UMC takes the username from the `uid` claim (not the `preferred_username` claim, as this doesn't preserve the case) as authenticated user.

A oauth-client configuration document suitable for dynamic client registration can be obtained at /univention/oidc/.well-known/openid-configuration.
