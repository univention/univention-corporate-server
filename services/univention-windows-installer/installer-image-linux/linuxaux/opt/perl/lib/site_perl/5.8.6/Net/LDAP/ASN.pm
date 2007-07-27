
package Net::LDAP::ASN;

$VERSION = "0.03";

use Convert::ASN1;

my $asn = Convert::ASN1->new;

sub import {
  my $pkg    = shift;
  my $caller = caller;

  foreach my $macro (@_) {
    my $obj = $asn->find($macro)
      or require Carp and Carp::croak("Unknown macro '$macro'");

    *{"$caller\::$macro"} = \$obj;
  }
}

$asn->prepare(<<LDAP_ASN) or die $asn->error;

    -- We have split LDAPMessage into LDAPResponse and LDAPRequest
    -- The purpose of this is two fold
    -- 1) for encode we don't want the protocolOp
    --    in the hierarchy as it is not really needed
    -- 2) For decode we do want it, this allows Net::LDAP::Message::decode
    --    to be much simpler. Decode will also be faster due to
    --    less elements in the CHOICE

    LDAPRequest ::= SEQUENCE {
	messageID       MessageID,
	  --protocolOp
	CHOICE {
	    bindRequest     BindRequest,
	    unbindRequest   UnbindRequest,
	    searchRequest   SearchRequest,
	    modifyRequest   ModifyRequest,
	    addRequest      AddRequest,
	    delRequest      DelRequest,
	    modDNRequest    ModifyDNRequest,
	    compareRequest  CompareRequest,
	    abandonRequest  AbandonRequest,
	    extendedReq     ExtendedRequest}
	 controls       [0] Controls OPTIONAL }

    LDAPResponse ::= SEQUENCE {
	messageID       MessageID,
	protocolOp     CHOICE {
	    bindResponse    BindResponse,
	    searchResEntry  SearchResultEntry,
	    searchResDone   SearchResultDone,
	    searchResRef    SearchResultReference,
	    modifyResponse  ModifyResponse,
	    addResponse     AddResponse,
	    delResponse     DelResponse,
	    modDNResponse   ModifyDNResponse,
	    compareResponse CompareResponse,
	    extendedResp    ExtendedResponse }
	 controls       [0] Controls OPTIONAL }

    MessageID ::= INTEGER -- (0 .. maxInt)

    -- maxInt INTEGER ::= 2147483647 -- (2^^31 - 1) --

    LDAPString ::= OCTET STRING -- UTF8String ??

    LDAPOID ::= OCTET STRING

    LDAPDN ::= LDAPString

    RelativeLDAPDN ::= LDAPString

    AttributeType ::= LDAPString

    AttributeDescription ::= LDAPString

    AttributeDescriptionList ::= SEQUENCE OF
	AttributeDescription

    AttributeValue ::= OCTET STRING

    AttributeValueAssertion ::= SEQUENCE {
	attributeDesc   AttributeDescription,
	assertionValue  AssertionValue }

    AssertionValue ::= OCTET STRING

    Attribute ::= SEQUENCE {
	type    AttributeDescription,
	vals    SET OF AttributeValue }

    MatchingRuleId ::= LDAPString

    LDAPResult ::= SEQUENCE {
	resultCode      ENUMERATED {
	    success                      (0),
	    operationsError              (1),
	    protocolError                (2),
	    timeLimitExceeded            (3),
	    sizeLimitExceeded            (4),
	    compareFalse                 (5),
	    compareTrue                  (6),
	    authMethodNotSupported       (7),
	    strongAuthRequired           (8),
		-- 9 reserved --
	    referral                     (10),  -- new
	    adminLimitExceeded           (11),  -- new
	    unavailableCriticalExtension (12),  -- new
	    confidentialityRequired      (13),  -- new
	    saslBindInProgress           (14),  -- new
	    noSuchAttribute              (16),
	    undefinedAttributeType       (17),
	    inappropriateMatching        (18),
	    constraintViolation          (19),
	    attributeOrValueExists       (20),
	    invalidAttributeSyntax       (21),
		-- 22-31 unused --
	    noSuchObject                 (32),
	    aliasProblem                 (33),
	    invalidDNSyntax              (34),
		-- 35 reserved for undefined isLeaf --
	    aliasDereferencingProblem    (36),
		-- 37-47 unused --
	    inappropriateAuthentication  (48),
	    invalidCredentials           (49),
	    insufficientAccessRights     (50),
	    busy                         (51),
	    unavailable                  (52),
	    unwillingToPerform           (53),
	    loopDetect                   (54),
		-- 55-63 unused --
	    namingViolation              (64),
	    objectClassViolation         (65),
	    notAllowedOnNonLeaf          (66),
	    notAllowedOnRDN              (67),
	    entryAlreadyExists           (68),
	    objectClassModsProhibited    (69),
		-- 70 reserved for CLDAP --
	    affectsMultipleDSAs          (71), -- new
		-- 72-79 unused --
	    other                        (80)}
		-- 81-90 reserved for APIs --
	matchedDN       LDAPDN,
	errorMessage    LDAPString,
	referral        [3] Referral OPTIONAL }

    Referral ::= SEQUENCE OF LDAPURL

    LDAPURL ::= LDAPString -- limited to characters permitted in URLs

    Controls ::= SEQUENCE OF Control

    -- Names changed here for backwards compat with previous
    -- Net::LDAP    --GMB
    Control ::= SEQUENCE {
	type             LDAPOID,                       -- controlType
	critical         BOOLEAN OPTIONAL, -- DEFAULT FALSE,    -- criticality
	value            OCTET STRING OPTIONAL }        -- controlValue

    BindRequest ::= [APPLICATION 0] SEQUENCE {
	version                 INTEGER, -- (1 .. 127),
	name                    LDAPDN,
	authentication          AuthenticationChoice }

    AuthenticationChoice ::= CHOICE {
	simple                  [0] OCTET STRING,
		     -- 1 and 2 reserved
	sasl                    [3] SaslCredentials }

    SaslCredentials ::= SEQUENCE {
	mechanism               LDAPString,
	credentials             OCTET STRING OPTIONAL }

    BindResponse ::= [APPLICATION 1] SEQUENCE {
	 COMPONENTS OF LDAPResult,
	 serverSaslCreds    [7] OCTET STRING OPTIONAL }

    UnbindRequest ::= [APPLICATION 2] NULL

    SearchRequest ::= [APPLICATION 3] SEQUENCE {
	baseObject      LDAPDN,
	scope           ENUMERATED {
	    baseObject              (0),
	    singleLevel             (1),
	    wholeSubtree            (2) }
	derefAliases    ENUMERATED {
	    neverDerefAliases       (0),
	    derefInSearching        (1),
	    derefFindingBaseObj     (2),
	    derefAlways             (3) }
	sizeLimit       INTEGER , -- (0 .. maxInt),
	timeLimit       INTEGER , -- (0 .. maxInt),
	typesOnly       BOOLEAN,
	filter          Filter,
	attributes      AttributeDescriptionList }

    Filter ::= CHOICE {
	and             [0] SET OF Filter,
	or              [1] SET OF Filter,
	not             [2] Filter,
	equalityMatch   [3] AttributeValueAssertion,
	substrings      [4] SubstringFilter,
	greaterOrEqual  [5] AttributeValueAssertion,
	lessOrEqual     [6] AttributeValueAssertion,
	present         [7] AttributeDescription,
	approxMatch     [8] AttributeValueAssertion,
	extensibleMatch [9] MatchingRuleAssertion }

    SubstringFilter ::= SEQUENCE {
	type            AttributeDescription,
	-- at least one must be present
	substrings      SEQUENCE OF CHOICE {
	    initial [0] LDAPString,
	    any     [1] LDAPString,
	    final   [2] LDAPString } }

    MatchingRuleAssertion ::= SEQUENCE {
	matchingRule    [1] MatchingRuleId OPTIONAL,
	type            [2] AttributeDescription OPTIONAL,
	matchValue      [3] AssertionValue,
	dnAttributes    [4] BOOLEAN OPTIONAL } -- DEFAULT FALSE }

    SearchResultEntry ::= [APPLICATION 4] SEQUENCE {
	objectName      LDAPDN,
	attributes      PartialAttributeList }

    PartialAttributeList ::= SEQUENCE OF SEQUENCE {
	type    AttributeDescription,
	vals    SET OF AttributeValue }

    SearchResultReference ::= [APPLICATION 19] SEQUENCE OF LDAPURL

    SearchResultDone ::= [APPLICATION 5] LDAPResult

    ModifyRequest ::= [APPLICATION 6] SEQUENCE {
	object          LDAPDN,
	modification    SEQUENCE OF SEQUENCE {
	    operation       ENUMERATED {
			add     (0),
			delete  (1),
			replace (2) }
	    modification    AttributeTypeAndValues } }

    AttributeTypeAndValues ::= SEQUENCE {
	type    AttributeDescription,
	vals    SET OF AttributeValue }

    ModifyResponse ::= [APPLICATION 7] LDAPResult

    AddRequest ::= [APPLICATION 8] SEQUENCE {
	objectName      LDAPDN,
	attributes      AttributeList }

    AttributeList ::= SEQUENCE OF SEQUENCE {
	type    AttributeDescription,
	vals    SET OF AttributeValue }

    AddResponse ::= [APPLICATION 9] LDAPResult

    DelRequest ::= [APPLICATION 10] LDAPDN

    DelResponse ::= [APPLICATION 11] LDAPResult

    ModifyDNRequest ::= [APPLICATION 12] SEQUENCE {
	entry           LDAPDN,
	newrdn          RelativeLDAPDN,
	deleteoldrdn    BOOLEAN,
	newSuperior     [0] LDAPDN OPTIONAL }

    ModifyDNResponse ::= [APPLICATION 13] LDAPResult

    CompareRequest ::= [APPLICATION 14] SEQUENCE {
	entry           LDAPDN,
	ava             AttributeValueAssertion }

    CompareResponse ::= [APPLICATION 15] LDAPResult

    AbandonRequest ::= [APPLICATION 16] MessageID

    ExtendedRequest ::= [APPLICATION 23] SEQUENCE {
	requestName      [0] LDAPOID,
	requestValue     [1] OCTET STRING OPTIONAL }

    ExtendedResponse ::= [APPLICATION 24] SEQUENCE {
	COMPONENTS OF LDAPResult,
	responseName     [10] LDAPOID OPTIONAL,
	response         [11] OCTET STRING OPTIONAL }


       VirtualListViewRequest ::= SEQUENCE {
	   beforeCount    INTEGER , --(0 .. maxInt),
	   afterCount     INTEGER , --(0 .. maxInt),
	   CHOICE {
	       byoffset [0] SEQUENCE {
	       offset          INTEGER , --(0 .. maxInt),
	       contentCount    INTEGER } --(0 .. maxInt) }
	       byValue [1] AssertionValue }
	       -- byValue [1] greaterThanOrEqual assertionValue }
	 contextID     OCTET STRING OPTIONAL }

       VirtualListViewResponse ::= SEQUENCE {
	   targetPosition    INTEGER , --(0 .. maxInt),
	   contentCount      INTEGER , --(0 .. maxInt),
	   virtualListViewResult ENUMERATED {
	       success (0),
	       operatonsError (1),
	       unwillingToPerform (53),
	       insufficientAccessRights (50),
	       busy (51),
	       timeLimitExceeded (3),
	       adminLimitExceeded (11),
	       sortControlMissing (60),
	       indexRangeError (61),
	       other (80) }  
	   contextID     OCTET STRING OPTIONAL     }


    LDAPEntry ::= COMPONENTS OF AddRequest

    -- Current parser does not allow a named entity following the ::=
    -- so we use a COMPONENTS OF hack
    SortRequestDummy ::= SEQUENCE {
	order SEQUENCE OF SEQUENCE {
	    type         OCTET STRING,
	    orderingRule [0] OCTET STRING OPTIONAL,
	    reverseOrder [1] BOOLEAN OPTIONAL } }

    SortRequest ::= COMPONENTS OF SortRequestDummy

    SortResult ::= SEQUENCE {
	sortResult  ENUMERATED {
	    success                   (0), -- results are sorted
	    operationsError           (1), -- server internal failure
	    timeLimitExceeded         (3), -- timelimit reached before
					   -- sorting was completed
	    strongAuthRequired        (8), -- refused to return sorted
					   -- results via insecure
					   -- protocol
	    adminLimitExceeded       (11), -- too many matching entries
					   -- for the server to sort
	    noSuchAttribute          (16), -- unrecognized attribute
					   -- type in sort key
	    inappropriateMatching    (18), -- unrecognized or inappro-
					   -- priate matching rule in
					   -- sort key
	    insufficientAccessRights (50), -- refused to return sorted
					   -- results to this client
	    busy                     (51), -- too busy to process
	    unwillingToPerform       (53), -- unable to sort
	    other                    (80) }
    attributeType [0] AttributeDescription OPTIONAL }

    realSearchControlValue ::= SEQUENCE {
	size            INTEGER, --  (0..maxInt),
		      -- requested page size from client
		      -- result set size estimate from server
	cookie          OCTET STRING }

    proxyAuthValue ::= SEQUENCE {
        proxyDN LDAPDN
    }

    ManageDsaIT ::= SEQUENCE {
        dummy INTEGER OPTIONAL   -- it really is unused
    }

    PersistentSearch ::= SEQUENCE {
        changeTypes INTEGER,
        changesOnly BOOLEAN,
        returnECs BOOLEAN
    }

    EntryChangeNotification ::= SEQUENCE {
        changeType ENUMERATED {
            add         (1),
            delete      (2),
            modify      (4),
            modDN       (8)
        }
        previousDN   LDAPDN OPTIONAL,     -- modifyDN ops. only
        changeNumber INTEGER OPTIONAL     -- if supported
    }

LDAP_ASN

1;

