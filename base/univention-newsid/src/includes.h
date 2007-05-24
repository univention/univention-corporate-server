
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <sys/time.h>
#include <pwd.h>

#define True (1)
#define False (0)
#define SAFE_FREE(x) do { if ((x) != NULL) {free(x); x=NULL;} } while(0)
#define CVAL(buf,pos) (((unsigned char *)(buf))[pos])
#define PVAL(buf,pos) ((unsigned)CVAL(buf,pos))
#define SVAL(buf,pos) (PVAL(buf,pos)|PVAL(buf,(pos)+1)<<8)
#define IVAL(buf,pos) (SVAL(buf,pos)|SVAL(buf,(pos)+2)<<16)
#define IVAL_NC(buf,pos) (*(uint32 *)((char *)(buf) + (pos)))
#define SIVAL(buf,pos,val) IVAL_NC(buf,pos)=((uint32)(val))

#define ZERO_STRUCTP(x) do { if ((x) != NULL) memset((char *)(x), 0, sizeof(*(x))); } while(0)

typedef int BOOL;
typedef unsigned char uint8;
typedef unsigned char uchar;
typedef unsigned short uint16;
typedef unsigned short wchar;
typedef unsigned uint32;

#define MAXSUBAUTHS 15

typedef struct sid_info
{
  uint8  sid_rev_num;             /**< SID revision number */
  uint8  num_auths;               /**< Number of sub-authorities */
  uint8  id_auth[6];              /**< Identifier Authority */
  uint32 sub_auths[MAXSUBAUTHS];
  
} DOM_SID;

#define FSTRING_LEN 256
typedef char fstring[FSTRING_LEN];


/* from memory.c */
void *smb_xmalloc(size_t size);
char *smb_xstrdup(const char *s);
void *memdup(const void *p, size_t size); 

/* from md4.c */
void mdfour(unsigned char *out, const unsigned char *in, int n);

/* from util_pw.c */
struct passwd *getpwnam_alloc(const char *name);
void passwd_free (struct passwd **buf);

/* from genrand.c */
void generate_random_buffer( unsigned char *out, int len, BOOL do_reseed_now);
