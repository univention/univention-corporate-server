How does the HTTP JSON Interface look like?
===========================================
I will list a few important example how to use this API via JSON requests to perform the basic operations on objects.
For a complete list of all features see [Test cases](test.sh).
The implementation is done via a [Tornado web service](univention-management-console-module-udm).

# Search for all users
$ curl -H 'Accept: application/json' -i http://Administrator:univention@10.200.27.20:8888/udm/users/user/

```http
HTTP/1.1 200 OK
Content-Length: 2013
Etag: "cc54308c33e365b4fb4917d424ab679fb591e883"
Link: </udm/users/user/>; rel="search"; title="Search for user objects"
Link: </udm/users/user/add/>; rel="create-form"; title="Create a user object"
Link: </udm/users/user/edit/>; rel="edit-form"; title="Modify a user object"
Link: </udm/users/user/favicon.ico>; rel="icon"; title="Icon"
Link: </udm/users/user/properties>; rel="udm/relation/properties"; title=""
Link: </udm/users/user/options>; rel="udm/relation/options"; title=""
Link: </udm/users/user/layout>; rel="udm/relation/layout"; title=""
Link: </udm/users/user/templates>; rel="udm/relation/templates"; title=""
Link: </udm/users/user/containers>; rel="udm/relation/containers"; title=""
Link: </udm/users/user/policies>; rel="udm/relation/policies"; title=""
Link: </udm/users/user/report-types>; rel="udm/relation/report-types"; title=""
Allow: GET, POST, OPTIONS
Date: Fri, 29 Mar 2019 03:26:47 GMT
Content-Type: application/json
```

```json
[
    {
        "$childs$": false,
        "$dn$": "uid=Administrator,cn=users,dc=dev,dc=local",
        "$flags$": [],
        "$operations$": [
            "add",
            "edit",
            "remove",
            "search",
            "move",
            "copy"
        ],
        "$url$": "/udm/users/user/uid%3DAdministrator%2Ccn%3Dusers%2Cdc%3Ddev%2Cdc%3Dlocal",
        "labelObjectType": "User",
        "name": "Administrator",
        "objectType": "users/user",
        "path": "local.dev:/users"
    },
	… Further objects here…
]
```

# Create a new user object
curl -XPOST -i -H 'Content-Type: application/json' -H 'Accept: application/json' http://Administrator:univention@10.200.27.20:8888/udm/users/user/ -d
```json
{
    "container": "cn=users,dc=dev,dc=local",
    "$options$": {
        "oxUser": true,
        "pki": false
    },
    "username": "Username",
    "disabled": false,
    "displayName": "Firstname Lastname",
    "firstname": "Firstname",
    "homeSharePath": "Username",
    "lastname": "Lastname",
    "mailForwardCopyToSelf": "0",
    "mailHomeServer": "master20.dev.local",
    "mailUserQuota": "0",
    "objectTemplate": null,
    "objectType": "users/user",
    "overridePWHistory": false,
    "overridePWLength": false,
    "oxAccess": "premium",
    "oxDisplayName": "Firstname Lastname",
    "oxLanguage": "de_DE",
    "oxTimeZone": "Europe/Berlin",
    "password": "univention",
    "primaryGroup": "cn=Domain Users,cn=groups,dc=dev,dc=local",
    "pwdChangeNextLogin": false,
    "shell": "/bin/bash",
    "unixhome": "/home/Username",
    "unlock": false,
}
```
```http
HTTP/1.1 201 Created
Date: Fri, 29 Mar 2019 04:41:34 GMT
Content-Length: 0
Location: /udm/users/user/uid%3DUsername8848%2Ccn%3Dusers%2Cdc%3Ddev%2Cdc%3Dlocal
```

# GET a specific users properties
$ curl -i -H 'Accept: application/json' http://Administrator:univention@10.200.27.20:8888/udm/users/user/uid%3DUsername8848%2Ccn%3Dusers%2Cdc%3Ddev%2Cdc%3Dlocal
```http
HTTP/1.1 200 OK
Content-Length: 1186
Etag: "bc8882463913059c8458916c1ceff764701e3b65"
Link: </udm/users/user/uid%3DUsername8848%2Ccn%3Dusers%2Cdc%3Ddev%2Cdc%3Dlocal>; rel="self"; title=""
Date: Fri, 29 Mar 2019 04:45:39 GMT
Content-Type: application/json
```
```json
{
    "$dn$": "uid=Username8848,cn=users,dc=dev,dc=local",
    "$flags$": [],
    "$labelObjectType$": "User",
    "$operations$": [
        "add",
        "edit",
        "remove",
        "search",
        "move",
        "copy"
    ],
    "$options$": {
        "owncloudEnabled": true,
        "oxUser": false,
        "pki": false
    },
    "$policies$": {},
    "$references$": [],
    "$url$": "/udm/users/user/uid%3DUsername8848%2Ccn%3Dusers%2Cdc%3Ddev%2Cdc%3Dlocal",
    "disabled": "0",
    "displayName": "Firstname Lastname",
    "firstname": "Firstname",
    "gecos": "Firstname Lastname",
    "gidNumber": "5001",
    "groups": [
        "cn=Domain Users,cn=groups,dc=dev,dc=local"
    ],
    "homeSharePath": "Username8848",
    "isOxUser": "Not",
    "lastname": "Lastname",
    "locked": "0",
    "lockedTime": "0",
    "mailForwardCopyToSelf": "0",
    "mailHomeServer": "master20.dev.local",
    "mailUserQuota": "0",
    "owncloudEnabled": "1",
    "oxAccess": "premium",
    "oxDisplayName": "Firstname Lastname",
    "oxDrive": "1",
    "oxLanguage": "de_DE",
    "oxTimeZone": "Europe/Berlin",
    "oxUserQuota": "-1",
    "passwordexpiry": null,
    "primaryGroup": "cn=Domain Users,cn=groups,dc=dev,dc=local",
    "sambaRID": "1419",
    "shell": "/bin/bash",
    "uidNumber": "2242",
    "unixhome": "/home/Username",
    "unlock": "0",
    "unlockTime": "",
    "userexpiry": null,
    "username": "Username8848"
}
```


# PUT: modify a specific user
curl -X PUT -i -H 'Content-Type: application/json' -H 'Accept: application/json' http://Administrator:univention@10.200.27.20:8888/udm/users/user/uid%3DUsername20635%2Ccn%3Dusers%2Cdc%3Ddev%2Cdc%3Dlocal -d
```json
{
    "container": "cn=users,dc=dev,dc=local",
    "$options$": {
        "oxUser": true,
        "pki": false
    },
    "username": "Username",
    "disabled": false,
    "displayName": "Firstname Lastname",
    "firstname": "Firstname",
    "homeSharePath": "Username",
    "lastname": "Lastname",
    "mailForwardCopyToSelf": "0",
    "mailHomeServer": "master20.dev.local",
    "mailUserQuota": "0",
    "objectTemplate": null,
    "objectType": "users/user",
    "overridePWHistory": false,
    "overridePWLength": false,
    "oxAccess": "premium",
    "oxDisplayName": "Firstname Lastname",
    "oxLanguage": "de_DE",
    "oxTimeZone": "Europe/Berlin",
    "password": "univention",
    "primaryGroup": "cn=Domain Users,cn=groups,dc=dev,dc=local",
    "pwdChangeNextLogin": false,
    "shell": "/bin/bash",
    "unixhome": "/home/Username",
    "unlock": false,
}
```
```http
HTTP/1.1 200 OK
Date: Fri, 29 Mar 2019 04:41:34 GMT
Content-Length: 0
Location: /udm/users/user/uid%3DUsername8848%2Ccn%3Dusers%2Cdc%3Ddev%2Cdc%3Dlocal
```



# DELETE: remove a specific user
$ curl -i -X DELETE  -H 'Accept: application/json' http://Administrator:univention@10.200.27.20:8888/udm/users/user/uid%3DUsername20635%2Ccn%3Dusers%2Cdc%3Ddev%2Cdc%3Dlocal
```http
HTTP/1.1 200 OK
Date: Fri, 29 Mar 2019 04:49:47 GMT
Content-Length: 0
```

