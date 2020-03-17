/**
 * univention license internal definitions.
 */
#ifndef __UNIVENTION_LICENSE_INTERNAL_H__
#define __UNIVENTION_LICENSE_INTERNAL_H__

#include <string.h>
#include <stdbool.h>
#include <time.h>

#include <openssl/err.h>
#include <openssl/objects.h>
#include <openssl/sha.h>
#include <openssl/rsa.h>
#include <openssl/bio.h>
#include <openssl/pem.h>

#include <univention/debug.h>
#include <univention/config.h>

#include <ldap.h>

#include <univention/license.h>

#define AUTOPTR_FUNC_NAME(type) type##AutoPtrFree
#define DEFINE_AUTOPTR_FUNC(type, func) \
    static inline void AUTOPTR_FUNC_NAME(type)(type **_ptr) \
    { \
        if (*_ptr) \
            (func)(*_ptr); \
        *_ptr = NULL; \
    }
#define AUTOPTR(type) \
    __attribute__((cleanup(AUTOPTR_FUNC_NAME(type)))) type *

DEFINE_AUTOPTR_FUNC(lStrings, univention_licenseStrings_free)
DEFINE_AUTOPTR_FUNC(lObj, univention_licenseObject_free)
DEFINE_AUTOPTR_FUNC(char, free);
DEFINE_AUTOPTR_FUNC(sortElement, free);
DEFINE_AUTOPTR_FUNC(BIO, BIO_free)

#endif
