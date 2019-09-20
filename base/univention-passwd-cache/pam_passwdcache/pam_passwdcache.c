/*
 * Univention Password Cache
 *  PAM password cache module
 *
 * Copyright 2004-2019 Univention GmbH
 *
 * https://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <https://www.gnu.org/licenses/>.
 */

/* -------------------------------------------------------------------------------- */
/*                                                                                  */
/* pam_passwdcache                                                                  */
/* Ein PAM-Modul   in zusammenarbeit mit nss_passwdcache                            */
/* args: debug  = mit debuginformationen                                            */
/*       master = mit verbindung zum domainmaster                                   */
/*       use_first_pass = benutze vorheriges passwort, sonst fehler erzeugen        */
/*       try_first_pass = benutze vorheriges passwort, sonst passwort selber fragen */
/*                                                                                  */
/* -------------------------------------------------------------------------------- */

#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h>
#include <unistd.h>
#include <syslog.h>
#include <string.h>
#include <time.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <crypt.h>
#include <fcntl.h>
#include <signal.h>

#include <pwd.h>
#include <shadow.h>
#include <grp.h>

#define PAM_SM_AUTH
#include <security/pam_modules.h>

#include "../passwdcache.h"

#define PAM_DEBUG_CMD          "debug"
#define PAM_INSERT_CMD         "insert"
#define PAM_DELETE_CMD         "delete"
#define PAM_MAX_USER_CMD       "max_user="
#define PAM_USE_FIRST_PASS_CMD "use_first_pass"
#define PAM_TRY_FIRST_PASS_CMD "try_first_pass"

#define PAM_DEBUG_ARG          0x0001
#define PAM_INSERT_ARG         0x0002
#define PAM_DELETE_ARG         0x0004
#define PAM_USE_FIRST_PASS_ARG 0x0008
#define PAM_TRY_FIRST_PASS_ARG 0x0010

/* #define DEBUG 1 */

/* -------------------------------------------------------------------------------- */
/*                                                                                  */
/* Vars                                                                             */
/*                                                                                  */
/* -------------------------------------------------------------------------------- */
struct passwdcache_options
{
  int ctrl;
  int max_user;
};

#define LOCK_TIMEOUT 15
static int pwd_lockfd = -1;

/* -------------------------------------------------------------------------------- */
/*                                                                                  */
/* intern Functions                                                                 */
/*                                                                                  */
/* -------------------------------------------------------------------------------- */

/* -------------------------------------------------------------------------------- */
/* for locking                                                                      */
/* -------------------------------------------------------------------------------- */
static int _set_close_on_exec( int fd )
{
  int flags = fcntl( fd, F_GETFD, 0 );
  if( flags == -1 )
    return -1;
  flags |= FD_CLOEXEC;
  return fcntl( fd, F_SETFD, flags );
}

static int _do_lock( int fd )
{
  struct flock fl;

  memset( &fl, 0, sizeof fl );
  fl.l_type   = F_WRLCK;
  fl.l_whence = SEEK_SET;
  return fcntl( fd, F_SETLKW, &fl );
}

static void _alarm_catch( int sig )
{
  /* do nothing */
}

static int _lckpwdf( void )
{
  struct sigaction act, oldact;
  sigset_t set, oldset;

  if( pwd_lockfd != -1 )
    return -1;

  pwd_lockfd = open( PWD_LOCK_FILE, O_CREAT | O_WRONLY, 0600 );
  if( pwd_lockfd == -1 )
    return -1;
  if( _set_close_on_exec( pwd_lockfd ) != -1 )
  {
    memset(&act, 0, sizeof act);
    act.sa_handler = _alarm_catch;
    act.sa_flags = 0;
    sigfillset( &act.sa_mask );
    if( sigaction( SIGALRM, &act, &oldact ) != -1 )
    {
      sigemptyset( &set );
      sigaddset( &set, SIGALRM );
      if( sigprocmask( SIG_UNBLOCK, &set, &oldset ) != -1)
      {
	alarm( LOCK_TIMEOUT );
	if( _do_lock( pwd_lockfd ) != -1)
        {
	  alarm( 0 );
	  sigprocmask( SIG_SETMASK, &oldset, NULL );
	  sigaction( SIGALRM, &oldact, NULL );
	  return 0;
        }
	alarm( 0 );
	sigprocmask( SIG_SETMASK, &oldset, NULL );
      }
      sigaction( SIGALRM, &oldact, NULL );
    }
  }
  close( pwd_lockfd );
  pwd_lockfd = -1;
  return -1;
}

static int _ulckpwdf( void )
{
  unlink( PWD_LOCK_FILE );
  if( pwd_lockfd == -1 )
    return -1;

  if( close( pwd_lockfd ) == -1 )
  {
    pwd_lockfd = -1;
    return -1;
  }
  pwd_lockfd = -1;

  return 0;
}

static int _set_shadow_permissions( const char *filename)
{
	struct group *grp_shadow;
	gid_t grp_id = 0;

	grp_shadow = getgrnam("shadow");
	if ( grp_shadow != NULL ) {
		grp_id = grp_shadow->gr_gid;
	}

	chown( filename, 0, grp_id );
	chmod( filename, 0640 );

	return 0;
}

/* -------------------------------------------------------------------------------- */
/* some syslogging                                                                  */
/* -------------------------------------------------------------------------------- */
static void _pam_log( int err, const char *format, ... )
{
  va_list args;

  va_start( args, format );
  openlog( "PAM-passwdcache", LOG_CONS | LOG_PID, LOG_AUTH );
  vsyslog( err, format, args );
  va_end( args );
  closelog();
}


/* -------------------------------------------------------------------------------- */
/* argument parsing                                                                 */
/* -------------------------------------------------------------------------------- */
static void _pam_parse( struct passwdcache_options *opt, int argc, const char **argv )
{
  #ifdef DEBUG
  /* fprintf( stderr, "Debug: _pam_parse()\n" ); */
  #endif

  opt->ctrl                = 0;
  opt->max_user            = 0;

  /* step through arguments */
  for( ; argc-- > 0; ++argv )
  {
    /* generic options */
    if( !strcmp( *argv, PAM_DEBUG_CMD ) )
    {
      #ifdef DEBUG
      fprintf( stderr, "Debug: _pam_parse(): %s\n", *argv );
      #endif
      opt->ctrl |= PAM_DEBUG_ARG;
    }
    else if( !strncmp( *argv, PAM_INSERT_CMD, sizeof(PAM_INSERT_CMD) ) )
    {
      #ifdef DEBUG
      fprintf( stderr, "Debug: _pam_parse(): %s\n", *argv );
      #endif
      opt->ctrl |= PAM_INSERT_ARG;
    }
    else if( !strncmp( *argv, PAM_DELETE_CMD, sizeof(PAM_DELETE_CMD) ) )
    {
      #ifdef DEBUG
      fprintf( stderr, "Debug: _pam_parse(): %s\n", *argv );
      #endif
      opt->ctrl |= PAM_DELETE_ARG;
    }
    else if( !strncmp( *argv, PAM_MAX_USER_CMD, sizeof(PAM_MAX_USER_CMD)-1 ) )
    {
      #ifdef DEBUG
      fprintf( stderr, "Debug: _pam_parse(): %s\n", *argv );
      #endif
      opt->max_user = atoi( *argv + sizeof(PAM_MAX_USER_CMD) - 1 );
      if( opt->max_user < 0)
        opt->max_user = 0;
    }
    else if( !strncmp( *argv, PAM_USE_FIRST_PASS_CMD, sizeof(PAM_USE_FIRST_PASS_CMD)-1 ) )
    {
      #ifdef DEBUG
      fprintf( stderr, "Debug: _pam_parse(): %s\n", *argv );
      #endif
      opt->ctrl |= PAM_USE_FIRST_PASS_ARG;
    }
    else if( !strncmp( *argv, PAM_TRY_FIRST_PASS_CMD, sizeof(PAM_TRY_FIRST_PASS_CMD)-1 ) )
    {
      #ifdef DEBUG
      fprintf( stderr, "Debug: _pam_parse(): %s\n", *argv );
      #endif
      opt->ctrl |= PAM_TRY_FIRST_PASS_ARG;
    }
    else
    {
      #ifdef DEBUG
      fprintf( stderr, "Debug: unknown option; %s\n", *argv );
      #endif
      _pam_log( LOG_ERR, "pam_parse: unknown option; %s", *argv );
    }
  }
}

/* -------------------------------------------------------------------------------- */
/* crypt the password for shadow                                                    */
/* -------------------------------------------------------------------------------- */
#define bin_to_ascii(c) ((c)>=38?((c)-38+'a'):(c)>=12?((c)-12+'A'):(c)+'.')
static char *_passwdcache_crypt_password( const char *old  )
{
  FILE *rand_file;
  time_t tm;
  char salt[3];

  rand_file = fopen( "/dev/urandom", "r" );
  if( rand_file == NULL )
  {
    time(&tm);
    salt[0] = bin_to_ascii(tm & 0x3f);
    salt[1] = bin_to_ascii((tm >> 6) & 0x3f);
    salt[2] = '\0';
  }
  else
  {
    fgets( salt, sizeof(salt), rand_file );
	salt[0] = bin_to_ascii(salt[0] & 0x3f);
	salt[1] = bin_to_ascii(salt[1] & 0x3f);
    fclose( rand_file );
  }

  return crypt( old, salt );
}

/* -------------------------------------------------------------------------------- */
/* _converse                                                                        */
/* return value:                                                                    */
/* -------------------------------------------------------------------------------- */
static int _converse( pam_handle_t        *pamh     ,
                      int                 nargs     ,
		      struct pam_message  **message ,
		      struct pam_response **response )
{
  int             retval;
  struct pam_conv *conv;

  #ifdef DEBUG
  fprintf( stderr, "Debug: _converse()\n" );
  #endif

  retval = pam_get_item( pamh, PAM_CONV, (const void **) &conv );
  if( retval == PAM_SUCCESS )
  {
    retval = conv->conv( nargs                                ,
                         (const struct pam_message **) message,
			 response                             ,
			 conv->appdata_ptr                     );

    #ifdef DEBUG
    fprintf( stderr, "Debug: _converse() back from function conv()\n" );
    #endif
  }

  return retval;
}


/* -------------------------------------------------------------------------------- */
/*                                                                                  */
/* return value:                                                                    */
/* -------------------------------------------------------------------------------- */
int _make_remark( pam_handle_t *pamh, int type, const char *text )
{
  int retval = PAM_SUCCESS;

  struct pam_message  msg;
  struct pam_message  *pmsg;
  struct pam_response *resp  = NULL;

  msg.msg       = text;
  msg.msg_style = type;
  pmsg = &msg;

  retval = _converse( pamh, 1, &pmsg, &resp );

  if( resp )
  {
    free( resp );
  }

  return retval;
}


/* -------------------------------------------------------------------------------- */
/* get the password for user from cache                                             */
/* return value:                                                                    */
/* -------------------------------------------------------------------------------- */
static struct spwd *_get_cache_spent( struct passwdcache_options *opt     ,
                                      const char                 *username )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: _get_cache_spent(\"%s\")\n", username );
  #endif

  FILE          *ucs_spfile;
  struct spwd   *ucs_spent;
  int           user_found = 0;

  ucs_spfile = fopen( SP_DATAFILE, "r" );
  if( ucs_spfile == NULL )
  {
    #ifdef DEBUG
    fprintf( stderr, "Debug: _get_cache_spent() can not open \"%s\"\n", SP_DATAFILE );
    #endif
    if( opt->ctrl & PAM_DEBUG_ARG )
      _pam_log( LOG_ERR, "can not open \"%s\" for read\n", SP_DATAFILE );
  }
  else
  {
    while( (ucs_spent = fgetspent( ucs_spfile ))!=NULL )
    {
      if( !strcmp( ucs_spent->sp_namp, username ))
      {
	#ifdef DEBUG
	fprintf( stderr, "Debug: _get_cache_spent() user found in \"%s\"\n", SP_DATAFILE );
	#endif
	user_found = 1;
	break;
      }
    }
    fclose( ucs_spfile );
  }

  if( user_found==1 )
  {
    return ucs_spent;
  }

  #ifdef DEBUG
  fprintf( stderr, "Debug: _get_cache_spent() user \"%s\" not found.\n", username );
  #endif

  return NULL;
}


/* -------------------------------------------------------------------------------- */
/* get password                                                                     */
/* return value:                                                                    */
/* -------------------------------------------------------------------------------- */
static int _get_password( struct passwdcache_options *opt  ,
                          pam_handle_t               *pamh ,
			  const char                 **pass )
{
  char                *token = NULL;
  struct pam_message  msg;
  struct pam_message  *pmsg;
  struct pam_response *resp  = NULL;
  int                 retval = PAM_SYSTEM_ERR;

  #ifdef DEBUG
  fprintf( stderr, "Debug: _get_password()\n" );
  #endif

  *pass        = token;

  if( (opt->ctrl & PAM_USE_FIRST_PASS_ARG) || (opt->ctrl & PAM_TRY_FIRST_PASS_ARG) )
  {
    /* look for a password from another pam_modul */

    #ifdef DEBUG
    fprintf( stderr, "Debug: _get_password() try or use first_pass\n" );
    #endif

    retval = pam_get_item( pamh, PAM_AUTHTOK, (const void **) pass);
    if( retval != PAM_SUCCESS )
    {
      #ifdef DEBUG
      fprintf( stderr, "Debug: no prefetched password found\n" );
      #endif
      if( opt->ctrl & PAM_DEBUG_ARG )
        _pam_log( LOG_ERR, "get_password: no prefetched password found" );
      return retval;
    }
    else if( *pass != NULL )
    {	/* we have a password! */
      #ifdef DEBUG
      fprintf( stderr, "Debug: _get_password() try or use first_pass -> found success\n" );
      #endif
      return PAM_SUCCESS;
    }
    else if( opt->ctrl & PAM_USE_FIRST_PASS_ARG )
    {
      #ifdef DEBUG
      fprintf( stderr, "Debug: _get_password() use_first_pass -> error\n" );
      #endif
      return PAM_AUTHTOK_RECOVER_ERR;
    }
  }

  msg.msg       = "Password: ";
  msg.msg_style = PAM_PROMPT_ECHO_OFF;
  pmsg          = &msg;
  retval = _converse( pamh, 1, &pmsg, &resp );

  if( resp != NULL )
  {
    if( retval == PAM_SUCCESS)
    {
      #ifdef DEBUG
      fprintf( stderr, "Debug: _get_password \"%s\"\n", resp[0].resp );
      #endif
      if( resp[0].resp != NULL )
      {
        token = strdup( resp->resp );
      }
    }
    free(resp);
  }
  else
  {
    retval = (retval == PAM_SUCCESS) ? PAM_AUTHTOK_RECOVER_ERR : retval;
  }

  if( retval != PAM_SUCCESS )
  {
    return retval;
  }

  retval = pam_set_item( pamh, PAM_AUTHTOK, token );
  if( token != NULL )
  {
    free(token);
    token = NULL;
  }

  if( retval != PAM_SUCCESS
      ||
      (retval = pam_get_item( pamh, PAM_AUTHTOK,(const void **) pass)) != PAM_SUCCESS)
  {
    *pass = NULL;
    #ifdef DEBUG
    fprintf( stderr, "Debug: _get_password error manipulating password\n" );
    #endif
    if( opt->ctrl & PAM_DEBUG_ARG )
      _pam_log( LOG_CRIT, "error manipulating password" );
  }

  #ifdef DEBUG
  fprintf( stderr, "Debug: _get_password() new password inserted\n" );
  #endif

  return retval;
}

/* -------------------------------------------------------------------------------- */
/* get password                                                                     */
/* return value:                                                                    */
/* -------------------------------------------------------------------------------- */
static int _verify_password( struct passwdcache_options *opt ,
                             pam_handle_t               *pamh,
                             const char                 *name,
                             const char                 *p    )
{
  int           retval;
  struct passwd *pwd       = NULL;
  struct spwd   *spwdent   = NULL;
  char          *salt      = NULL;
  char          *pp        = NULL;

  if( (name == NULL) || (p == NULL) || (strlen(name) == 0) || (strlen(p) == 0) )
  {
    #ifdef DEBUG
    fprintf( stderr, "Debug: _verify_password() missing input\n" );
    #endif
    return PAM_AUTHINFO_UNAVAIL;
  }
  #ifdef DEBUG
  fprintf( stderr, "Debug: _verify_password() name=\"%s\" p=\"%s\" \n", name, p );
  #endif

  pwd     = getpwnam( name );
  /* spwdent = getspnam( name );  old version */
  spwdent = _get_cache_spent( opt, name );
  if( spwdent != NULL )
  {
    if( spwdent->sp_pwdp )
    {
      salt = strdup( spwdent->sp_pwdp );
    }
  }

  if( (pwd == NULL) || (spwdent == NULL) || (salt == NULL) || (strlen(salt) == 0) )
  {
    #ifdef DEBUG
    fprintf( stderr, "Debug: _verify_password() missing stored data\n" );
    #endif
    retval = PAM_AUTHINFO_UNAVAIL;
  }
  else
  {
    pp = crypt( p, salt );
    if( strncmp( pp, salt, strlen(salt) ) == 0)
    {
      #ifdef DEBUG
      fprintf( stderr, "Debug: _verify_password() password is OK\n" );
      #endif
      retval = PAM_SUCCESS;
    }
    else
    {
      #ifdef DEBUG
      fprintf( stderr, "Debug: _verify_password() password is not ok\n" );
      #endif
      retval = PAM_AUTH_ERR;
    }
  }

  if( salt )
  {
    free(salt);
  }

  return retval;
}

/* -------------------------------------------------------------------------------- */
/* get the oldest user from the cache (this is the first entry in cache)            */
/* return value: count of user in cache. an error send count=0                      */
/* -------------------------------------------------------------------------------- */
static int _get_usercount_of_cache( void )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: _get_usercount_of_cache()\n" );
  #endif

  FILE          *ucs_pwfile;
  char          buffer[NSS_BUFLEN_PASSWD];
  int           ucs_user_count = 0;

  ucs_pwfile = fopen( PW_DATAFILE, "r" );
  if( ucs_pwfile == NULL )
  {
    #ifdef DEBUG
    fprintf( stderr, "Debug: _get_usercount_of_cache() can not open \"%s\"\n", PW_DATAFILE );
    #endif
  }
  else
  {
    while( fgets( buffer, sizeof(buffer), ucs_pwfile )!=NULL )
    {
      ++ucs_user_count;
    }
    fclose( ucs_pwfile );
  }

  #ifdef DEBUG
  fprintf( stderr, "Debug: _get_usercount_of_cache() return %d\n", ucs_user_count );
  #endif

  return ucs_user_count;
}


/* -------------------------------------------------------------------------------- */
/* get the oldest user from the cache (this is the first entry in cache)            */
/* return value: pointer to user = ok                                               */
/*               NULL            = error                                            */
/* -------------------------------------------------------------------------------- */
static char *_get_first_user_from_cache( void )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: _get_first_user_from_cache()\n" );
  #endif

  FILE          *ucs_pwfile;
  struct passwd *ucs_pwent;
  char          *ucs_user = NULL;

  ucs_pwfile = fopen( PW_DATAFILE, "r" );
  if( ucs_pwfile == NULL )
  {
    #ifdef DEBUG
    fprintf( stderr, "Debug: _get_first_user_from_cache() can not open \"%s\"\n", PW_DATAFILE );
    #endif
  }
  else
  {
    ucs_pwent = fgetpwent( ucs_pwfile );
    if( ucs_pwent == NULL )
    {
      #ifdef DEBUG
      fprintf( stderr, "Debug: _get_first_user_from_cache() can not read \"%s\"\n", PW_DATAFILE );
      #endif
      fclose( ucs_pwfile );
    }
    else
    {
      ucs_user = ucs_pwent->pw_name;
      fclose( ucs_pwfile );
    }
  }

  #ifdef DEBUG
  fprintf( stderr, "Debug: _get_first_user_from_cache() delivers user \"%s\"\n", ucs_user );
  #endif

  return ucs_user;
}


/* -------------------------------------------------------------------------------- */
/*                                                                                  */
/* -------------------------------------------------------------------------------- */
static int _create_new_grouplist( void )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: _create_new_grouplist()\n" );
  #endif

  FILE          *ucs_pwfile;
  struct passwd *ucs_pwent;
  int           new_group_count = 0;
  __gid_t       *new_group_list = NULL; /* for primary group */

  int           i, j;
  int           found;

  struct group  *grent;
  char          **p = NULL;
  FILE          *new_grfile;
  int           oldmask;

  /* get current userlist of primary and member groups   */
  /* --------------------------------------------------- */
  ucs_pwfile = fopen( PW_DATAFILE, "r" );
  if( ucs_pwfile == NULL )
  {
    #ifdef DEBUG
    fprintf( stderr, "Debug: _create_new_grouplist() can not open \"%s\"\n", PW_DATAFILE );
    #endif
  }
  else
  {
    while( (ucs_pwent = fgetpwent( ucs_pwfile ))!=NULL )
    {
      /* lookup the groups the user currently belongs to */
      {
        gid_t *groupids = NULL;
        int ngroups = 1;
        gid_t *newgroupids = NULL; 
        groupids = (gid_t *) malloc(ngroups * sizeof(gid_t)); 
        if (getgrouplist(ucs_pwent->pw_name, ucs_pwent->pw_gid, groupids, &ngroups) == -1) { 
          newgroupids = (gid_t *) malloc(ngroups * sizeof(gid_t));
          if (newgroupids != NULL) {
            free (groupids);
            groupids = newgroupids;
            getgrouplist (ucs_pwent->pw_name, ucs_pwent->pw_gid, groupids, &ngroups);
          } else {
            ngroups = 1;
          }
        }
        /* extend the list of unique groups */
        for (i = 0; i < ngroups; i++)
        {
          grent = getgrgid(groupids[i]);
          found = 0;
          for( j=0; j<new_group_count; j++ )    // check if the group already is in the new_group_list
          {
            if ( grent->gr_gid == new_group_list[j] )
            {
              found = 1;
              break;
            }
          }
          if( found == 0 )
          {
            ++new_group_count;
            new_group_list = realloc( new_group_list, new_group_count * sizeof(__gid_t) );
            if( new_group_list == NULL )
            {
              #ifdef DEBUG
              fprintf( stderr, "Debug: _create_new_grouplist() realloc() for new_group_list fail\n" );
              #endif
              return PAM_SYSTEM_ERR;
            }
            new_group_list[new_group_count - 1] = grent->gr_gid;
          }
        }
        free(groupids);
      }
    }
    fclose( ucs_pwfile );
  }

  /* write current list of primary and member groups */
  /* --------------------------------------------------- */
  oldmask = umask(077);
  new_grfile = fopen( GR_DATAFILE_TMP, "w" );
  umask(oldmask);
  if( new_grfile == NULL )
  {
    #ifdef DEBUG
    fprintf( stderr, "Debug: _create_new_grouplist() fopen(\"%s\",\"w\") failed\n", GR_DATAFILE_TMP );
    #endif
    return PAM_SYSTEM_ERR;
  }

  for( i=0; i<new_group_count; i++ )
  {
    grent = getgrgid( new_group_list[i] );
    if( grent == NULL )
    {
      #ifdef DEBUG
      fprintf( stderr, "Debug: _create_new_grouplist() getgrgid(%u) fail\n", new_group_list[i] );
      #endif
      return PAM_SYSTEM_ERR;
    }

    if( putgrent( grent, new_grfile ) )
    {
      #ifdef DEBUG
      fprintf( stderr, "Debug: _create_new_grouplist() putgrent() fail\n" );
      #endif
      fclose( new_grfile );
      return PAM_SYSTEM_ERR;
    }
  }

  if( new_group_list != NULL )
  {
    free( new_group_list );
  }

  fclose( new_grfile );

  chown( GR_DATAFILE_TMP, 0, 0 );
  chmod( GR_DATAFILE_TMP, 0644 );
  rename( GR_DATAFILE_TMP, GR_DATAFILE );

  return PAM_SUCCESS;
}

/* -------------------------------------------------------------------------------- */
/* Delete account of user in cache of passwd and shadow                             */
/* -------------------------------------------------------------------------------- */
static int _delete_user_in_cache( const char *user )
{
  struct passwd *pwent;
  FILE          *new_pwfile;
  FILE          *old_pwfile;

  struct spwd   *spent;
  FILE          *new_spfile;
  FILE          *old_spfile;

  int           oldmask;

  #ifdef DEBUG
  fprintf( stderr, "Debug: _delete_user_in_cache(\"%s\")\n", user );
  #endif

  /* cache of passwd */
  oldmask = umask(077);
  new_pwfile = fopen( PW_DATAFILE_TMP, "w" );
  umask(oldmask);
  if( new_pwfile == NULL )
  {
    #ifdef DEBUG
    fprintf( stderr, "Debug: _delete_user_in_cache() can't open %s for writing.\n", PW_DATAFILE_TMP );
    #endif
    return PAM_SYSTEM_ERR;
  }

  old_pwfile = fopen( PW_DATAFILE, "r" );
  if( old_pwfile == NULL )
  {
    #ifdef DEBUG
    fprintf( stderr, "Debug: _delete_user_in_cache() can't open %s for reading.\n", PW_DATAFILE );
    #endif
    fclose( new_pwfile );
    return PAM_SYSTEM_ERR;
  }

  chown( PW_DATAFILE_TMP, 0, 0 );
  chmod( PW_DATAFILE_TMP, 0644 );

  while( (pwent = fgetpwent( old_pwfile ))!=NULL )
  {
    if( strcmp( pwent->pw_name, user ) )
    {
      if( putpwent( pwent, new_pwfile ) )
      {
        #ifdef DEBUG
        fprintf( stderr, "Debug: _delete_user_in_cache() can't write user \"%s\" in %s.\n", pwent->pw_name, PW_DATAFILE_TMP );
        #endif
	fclose( old_pwfile );
	fclose( new_pwfile );
        return PAM_SYSTEM_ERR;
      }
    }
  }
  fclose( old_pwfile );
  if( fclose( new_pwfile ) )
  {
    #ifdef DEBUG
    fprintf( stderr, "Debug: _delete_user_in_cache() error by close %s.\n", PW_DATAFILE_TMP );
    #endif
    return PAM_SYSTEM_ERR;
  }

  /* cache of shadow */
  oldmask = umask(077);
  new_spfile = fopen( SP_DATAFILE_TMP, "w" );
  umask(oldmask);
  if( new_spfile == NULL )
  {
    #ifdef DEBUG
    fprintf( stderr, "Debug: _delete_user_in_cache() can't open %s for writing.\n", SP_DATAFILE_TMP );
    #endif
    return PAM_SYSTEM_ERR;
  }

  old_spfile = fopen( SP_DATAFILE, "r" );
  if( old_spfile == NULL )
  {
    #ifdef DEBUG
    fprintf( stderr, "Debug: _delete_user_in_cache() can't open %s for reading.\n", SP_DATAFILE );
    #endif
    fclose( new_spfile );
    return PAM_SYSTEM_ERR;
  }

  chown( SP_DATAFILE_TMP, 0, 0 );
  chmod( SP_DATAFILE_TMP, 0640 );

  while( (spent = fgetspent( old_spfile ))!=NULL )
  {
    if( strcmp( spent->sp_namp, user ) )
    {
      if( putspent( spent, new_spfile ) )
      {
	fclose( old_spfile );
	fclose( new_spfile );
        return PAM_SYSTEM_ERR;
      }
    }
  }
  fclose( old_spfile );
  if( fclose( new_spfile ) )
  {
    return PAM_AUTH_ERR;
  }

  rename( PW_DATAFILE_TMP, PW_DATAFILE );
  rename( SP_DATAFILE_TMP, SP_DATAFILE );

  _set_shadow_permissions(SP_DATAFILE);

  #ifdef DEBUG
  fprintf( stderr, "Debug: _delete_user_in_cache() user \"%s\" deleted from cache\n", user );
  #endif

  return PAM_SUCCESS;
}

/* -------------------------------------------------------------------------------- */
/* Insert account of user in cache of passwd and shadow.                            */
/* -------------------------------------------------------------------------------- */
static int _insert_new_user( const char *user, char *pw )
{
  FILE          *ucs_pwfile;
  struct passwd *new_pwent;

  FILE          *ucs_spfile;
  struct spwd   *new_spent;

  #ifdef DEBUG
  fprintf( stderr, "Debug: _insert_new_user(\"%s\",\"%s\")\n", user, pw );
  #endif

  /* ------------------------------------------------------------------------------ */
  /* passwd                                                                         */
  /* ------------------------------------------------------------------------------ */
  new_pwent = getpwnam( user );
  if( new_pwent == NULL )
  {
    #ifdef DEBUG
    fprintf( stderr, "Debug: _insert_new_user() getpwnam(\"%s\") failed\n", user );
    #endif
    return PAM_SYSTEM_ERR;
  }

  /* ------------------------------------------------------------------------------ */
  /* shadow                                                                         */
  /* ------------------------------------------------------------------------------ */
  new_spent = getspnam( user );
  if( new_spent == NULL )
  {
    #ifdef DEBUG
    fprintf( stderr, "Debug: _insert_new_user() getspnam(\"%s\") failed\n", user );
    #endif
    return PAM_SYSTEM_ERR;
  }
  new_spent->sp_pwdp = pw;
  
  /* shadow data is not to be cached, thus the entries are overwritten with -1 which
   * putspnam translates to an empty field
   * */
  /* { */
  new_spent->sp_lstchg=-1;
  new_spent->sp_max=-1; 
  new_spent->sp_warn=-1; 
  new_spent->sp_inact=-1; 
  new_spent->sp_expire=-1;
  /* } */

  
  /* ------------------------------------------------------------------------------ */
  /* passwd                                                                         */
  /* ------------------------------------------------------------------------------ */
  ucs_pwfile = fopen( PW_DATAFILE, "a" );
  if( ucs_pwfile == NULL )
  {
    #ifdef DEBUG
    fprintf( stderr, "Debug: _insert_new_user() can not open %s\n", PW_DATAFILE );
    #endif
    return PAM_SYSTEM_ERR;
  }

  if( putpwent( new_pwent, ucs_pwfile ) )
  {
    #ifdef DEBUG
    fprintf( stderr, "Debug: _insert_new_user() putpwent() failed\n" );
    #endif
    fclose( ucs_pwfile );
    return PAM_SYSTEM_ERR;
  }

  fclose( ucs_pwfile );
  chown( PW_DATAFILE, 0, 0 );
  chmod( PW_DATAFILE, 0644 );

  /* ------------------------------------------------------------------------------ */
  /* shadow                                                                         */
  /* ------------------------------------------------------------------------------ */
  ucs_spfile = fopen( SP_DATAFILE, "a" );
  if( ucs_spfile == NULL )
  {
    #ifdef DEBUG
    fprintf( stderr, "Debug: _insert_new_user() can not open %s\n", SP_DATAFILE );
    #endif
    return PAM_SYSTEM_ERR;
  }

  if( putspent( new_spent, ucs_spfile ) )
  {
    #ifdef DEBUG
    fprintf( stderr, "Debug: _insert_new_user() putspent() failed\n" );
    #endif
    fclose( ucs_spfile );
    return PAM_SYSTEM_ERR;
  }

  fclose( ucs_spfile );

  _set_shadow_permissions(SP_DATAFILE);

  return PAM_SUCCESS;
}

/* -------------------------------------------------------------------------------- */
/* check for user in cache                                                          */
/* return value: 0  = user was not found                                            */
/*               1  = user was found                                                */
/* -------------------------------------------------------------------------------- */
static int _check_user_in_cache( const char *user )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: _check_user_in_cache(\"%s\")\n", user );
  #endif

  FILE          *ucs_pwfile;
  struct passwd *ucs_pwent;
  int           user_found = 0;

  ucs_pwfile = fopen( PW_DATAFILE, "r" );
  if( ucs_pwfile == NULL )
  {
    #ifdef DEBUG
    fprintf( stderr, "Debug: _check_user_in_cache() can not open \"%s\"\n", PW_DATAFILE );
    #endif
  }
  else
  {
    while( (ucs_pwent = fgetpwent( ucs_pwfile ))!=NULL )
    {
      if( !strcmp( ucs_pwent->pw_name, user ))
      {
	#ifdef DEBUG
	fprintf( stderr, "Debug: _check_user_in_cache() user \"%s\" found in \"%s\"\n", user, PW_DATAFILE );
	#endif
	user_found = 1;
	break;
      }
    }
    fclose( ucs_pwfile );
  }

  #ifdef DEBUG
  if( user_found==0 )
  {
    fprintf( stderr, "Debug: _check_user_in_cache() user \"%s\" not found in \"%s\"\n", user, PW_DATAFILE );
  }
  #endif

  return user_found;
}


/* -------------------------------------------------------------------------------- */
/*                                                                                  */
/* global Functions                                                                 */
/*                                                                                  */
/* -------------------------------------------------------------------------------- */

/* -------------------------------------------------------------------------------- */
/* function: pam_sm_authenticate    Management group: PAM_SM_AUTH                   */
/* -------------------------------------------------------------------------------- */
PAM_EXTERN int pam_sm_authenticate( pam_handle_t *pamh, int flags, int argc, const char **argv )
{
  int                        count = 1000;
  int                        ret_lck;
  int                        retval;
  const char                 *username;
  const char                 *username_dup = NULL;
  struct passwdcache_options options;
  const char                 *old_pw = NULL;
        char                 *new_pw = NULL;
  char                       *tmp_user;
  char                       *tmp_user_dup;

  #ifdef DEBUG
  fprintf( stderr, "Debug: pam_sm_authenticate()\n" );
  #endif

  _pam_parse( &options, argc, argv );

  /* start with locking */
  while( ((ret_lck = _lckpwdf()) != 0) && (count-- > 0) )
  {
    usleep( 1000 );
  }
  if( ret_lck != 0 )
    return PAM_AUTHTOK_LOCK_BUSY;

  retval = pam_get_user( pamh, &username, NULL );
  if( retval == PAM_SUCCESS )
  {
    username_dup = strdup( username );
    if( username_dup == NULL )
    {
      #ifdef DEBUG
      fprintf( stderr, "Debug: pam_sm_authenticate() strdup() fail\n" );
      #endif
      _ulckpwdf();
      return PAM_SYSTEM_ERR;
    }

    if( options.ctrl & PAM_DELETE_ARG )
    {
      /* we have a user, and want to delete him */
      if( _check_user_in_cache( username_dup ) == 1 )
      {
	/* user found in cache */
	/* delete user in cache */
	#ifdef DEBUG
	fprintf( stderr, "Debug: pam_sm_authenticate() WITH_DELETE delete user \"%s\" in cache\n", username_dup );
	#endif
	if( options.ctrl & PAM_DEBUG_ARG )
          _pam_log( LOG_DEBUG, "auth WITH_DELETE delete user \"%s\" in cache", username_dup );

	_delete_user_in_cache( username_dup );
	_create_new_grouplist();

	retval = PAM_USER_UNKNOWN;
      }
      else
      {
	/* user not found in cache, only retval set to user_unknown */
	#ifdef DEBUG
	fprintf( stderr, "Debug: pam_sm_authenticate() WITH_DELETE user \"%s\" not found in cache\n", username_dup );
	#endif
	if( options.ctrl & PAM_DEBUG_ARG )
          _pam_log( LOG_DEBUG, "auth WITH_DELETE user \"%s\" not found in cache", username_dup );

	retval = PAM_USER_UNKNOWN;
      }
    }
    else
    {
      retval = _get_password( &options, pamh, &old_pw );
      if( old_pw == NULL )
      {
        retval = PAM_SYSTEM_ERR;
      }

      if( retval == PAM_SUCCESS )
      {
        if( !( options.ctrl & PAM_INSERT_ARG ) )
	{
          #ifdef DEBUG
	  fprintf( stderr, "Debug: pam_sm_authenticate() verify password for user \"%s\"\n", username_dup );
	  #endif
          retval = _verify_password( &options, pamh, username, old_pw );
	}

	if( retval == PAM_SUCCESS )
	{
	  new_pw = _passwdcache_crypt_password( (char *) old_pw );
	  if( username_dup == NULL )
	  {
	    retval = PAM_SYSTEM_ERR;
	  }
	  else
	  {
            /* we have a authenticated user */
	    if( options.ctrl & PAM_INSERT_ARG )
	    {
	      /* and we have a master */
	      if( _check_user_in_cache( username_dup ) == 1 )
	      {
		/* user found in cache */
		/* update user in cache */
		#ifdef DEBUG
		fprintf( stderr, "Debug: pam_sm_authenticate() WITH_INSERT update user \"%s\" in cache\n", username_dup );
		#endif
		if( options.ctrl & PAM_DEBUG_ARG )
		  _pam_log( LOG_DEBUG, "auth WITH_INSERT update user \"%s\" in cache", username_dup );

		retval = _delete_user_in_cache( username_dup );
		if( retval == PAM_SUCCESS )
		{
		  retval = _insert_new_user( username_dup, new_pw );
		  if( retval == PAM_SUCCESS )
		  {
		    retval = _create_new_grouplist();
		  }
		}
		else
		{
 		  #ifdef DEBUG
	 	  fprintf( stderr, "Debug: pam_sm_authenticate() WITH_INSERT delete_user \"%s\" fail for update\n", username_dup );
		  #endif
		  if( options.ctrl & PAM_DEBUG_ARG )
		    _pam_log( LOG_DEBUG, "auth WITH_INSERT delete_user \"%s\" fail for update", username_dup );
		}
	      }
	      else
	      {
		/* user not found in cache */
		/* insert user in cache */
		#ifdef DEBUG
		fprintf( stderr, "Debug: pam_sm_authenticate() WITH_INSERT insert user \"%s\" in cache\n", username_dup );
		#endif
		if( options.ctrl & PAM_DEBUG_ARG )
		  _pam_log( LOG_DEBUG, "auth WITH_INSERT insert user \"%s\" in cache", username_dup );

		retval = _insert_new_user( username_dup, new_pw );
		if( retval == PAM_SUCCESS )
		{
		  retval = _create_new_grouplist();
		}
		else
		{
 		  #ifdef DEBUG
	 	  fprintf( stderr, "Debug: pam_sm_authenticate() WITH_INSERT insert_new_user \"%s\" fail\n", username_dup );
		  #endif
		  if( options.ctrl & PAM_DEBUG_ARG )
		    _pam_log( LOG_DEBUG, "auth WITH_INSERT insert_new_user \"%s\" fail", username_dup );
		}
	      }
            }
	  }
	}
      }

      /* we have a username */
      if( (retval != PAM_SUCCESS) && (options.ctrl & PAM_INSERT_ARG) )
      {
        #ifdef DEBUG
	fprintf( stderr, "Debug: pam_sm_authenticate() WITH_INSERT error by user \"%s\"\n", username_dup );
	#endif

	/* error with user auth, if he cached, then delete him */
	if( _check_user_in_cache( username_dup ) == 1 )
	{
	  /* user found in cache */
	  /* delete user in cache */
	  #ifdef DEBUG
	  fprintf( stderr, "Debug: pam_sm_authenticate() WITH_INSERT delete user \"%s\" in cache\n", username_dup );
	  #endif
	  if( options.ctrl & PAM_DEBUG_ARG )
            _pam_log( LOG_DEBUG, "auth WITH_INSERT delete user \"%s\" in cache", username_dup );

	  _delete_user_in_cache( username_dup );
	  _create_new_grouplist();

	  retval = PAM_USER_UNKNOWN;
	}
	else
	{
	  /* user not found in cache, only retval set to user_unknown */
	  #ifdef DEBUG
	  fprintf( stderr, "Debug: pam_sm_authenticate() WITH_INSERT user \"%s\" not found in cache\n", username_dup );
	  #endif
	  if( options.ctrl & PAM_DEBUG_ARG )
            _pam_log( LOG_DEBUG, "auth WITH_INSERT user \"%s\" not found in cache", username_dup );

	  retval = PAM_USER_UNKNOWN;
	}
      }
    }
  }

  /* check of cache limit */
  if( (options.ctrl & PAM_INSERT_ARG) && (options.max_user > 0) )
  {
    while( options.max_user < _get_usercount_of_cache() )
    {
      tmp_user = _get_first_user_from_cache();
      if( tmp_user == NULL )
      {
        if( options.ctrl & PAM_DEBUG_ARG )
	{
          #ifdef DEBUG
	  fprintf( stderr, "Debug: pam_sm_authenticate() _get_first_user_from_cache()==NULL. Not possible ???\n" );
          #endif
          _pam_log( LOG_ERR, "_get_first_user_from_cache()==NULL. Not possible ???" );
	}

        retval = PAM_SYSTEM_ERR;
      }
      else
      {
        if( options.ctrl & PAM_DEBUG_ARG )
	{
          #ifdef DEBUG
	  fprintf( stderr, "Debug: to many user in cache. delete \"%s\"", tmp_user );
          #endif
          _pam_log( LOG_DEBUG, "to many user in cache. delete \"%s\"", tmp_user );
	}

        tmp_user_dup = strdup( tmp_user );
        if( tmp_user_dup == NULL )
	{
          retval = PAM_SYSTEM_ERR;
	}
        else
	{
          retval = _delete_user_in_cache( tmp_user_dup );
	  free( (void *) tmp_user_dup );
          if( retval == PAM_SUCCESS )
	  {
   	    retval = _create_new_grouplist();
	  }
	}
      }
      if( retval != PAM_SUCCESS )
	   break;
    }
  }

  /* end of locking */
  _ulckpwdf();

  #ifdef DEBUG
  fprintf( stderr, "Debug: authentication for %s %s\n", username_dup, retval==PAM_SUCCESS ? "succeeded":"failed" );
  #endif
  if( options.ctrl & PAM_DEBUG_ARG )
    _pam_log( LOG_DEBUG, "authentication for %s %s", username_dup, retval==PAM_SUCCESS ? "succeeded":"failed" );

  if( username_dup != NULL )
  {
    free( (void *) username_dup );
  }

  return retval;
}

/* -------------------------------------------------------------------------------- */
/* function: pam_sm_setcred    Management group: PAM_SM_AUTH                        */
/* -------------------------------------------------------------------------------- */
PAM_EXTERN int pam_sm_setcred( pam_handle_t *pamh, int flags, int argc, const char **argv )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: pam_sm_setcred()\n" );
  #endif

  return PAM_SUCCESS;
}

/* -------------------------------------------------------------------------------- */
/* function: pam_sm_acct_mgmt    Management group: PAM_SM_ACCOUNT                   */
/* -------------------------------------------------------------------------------- */
PAM_EXTERN int pam_sm_acct_mgmt( pam_handle_t *pamh, int flags, int argc, const char **argv )
{
  struct passwdcache_options options;
  const char                 *username;
  struct passwd              *ucs_pwent;
  struct spwd                *ucs_spent;
  time_t                     curdays;

  int retval, daysleft;
  char buf[80];

  #ifdef DEBUG
  fprintf( stderr, "Debug: pam_sm_acct_mgmt()\n" );
  #endif

  _pam_parse( &options, argc, argv );

  retval = pam_get_user( pamh, &username, NULL );
  if( retval != PAM_SUCCESS || username == NULL )
  {
    _pam_log( LOG_ALERT, "could not identify user (from uid=%d)", getuid() );
    return PAM_USER_UNKNOWN;
  }

  ucs_pwent = getpwnam( username );
  if( !ucs_pwent )
  {
    _pam_log( LOG_ALERT, "could not identify user (from getpwnam(%s))", username );
    return PAM_USER_UNKNOWN;
  }

  ucs_spent = _get_cache_spent( &options, username );
  if( !ucs_spent )
    return PAM_AUTHINFO_UNAVAIL;

  curdays = time(NULL) / (60 * 60 * 24);
  if( (curdays > ucs_spent->sp_expire) && (ucs_spent->sp_expire != -1)
	    && (ucs_spent->sp_lstchg != 0))
  {
    _pam_log( LOG_NOTICE, "account %s has expired (account expired)", username );
    _make_remark( pamh, PAM_ERROR_MSG, "Your account has expired; please contact your system administrator" );
    return PAM_ACCT_EXPIRED;
  }

  if( (curdays > (ucs_spent->sp_lstchg + ucs_spent->sp_max + ucs_spent->sp_inact))
	    && (ucs_spent->sp_max != -1) && (ucs_spent->sp_inact != -1)
	    && (ucs_spent->sp_lstchg != 0) )
  {
    _pam_log( LOG_NOTICE, "account %s has expired (failed to change password)", username );
    _make_remark( pamh, PAM_ERROR_MSG, "Your account has expired; please contact your system administrator" );
    return PAM_ACCT_EXPIRED;
  }

  if( ucs_spent->sp_lstchg == 0 )
  {
    _pam_log( LOG_NOTICE, "expired password for user %s (root enforced)", username );
    _make_remark( pamh, PAM_ERROR_MSG, "You are required to change your password immediately (root enforced)" );
    return PAM_NEW_AUTHTOK_REQD;
  }

  if( ((ucs_spent->sp_lstchg + ucs_spent->sp_max) < curdays) && (ucs_spent->sp_max != -1))
  {
    _pam_log( LOG_DEBUG, "expired password for user %s (password aged)", username );
    _make_remark( pamh, PAM_ERROR_MSG, "You are required to change your password immediately (password aged)" );
    return PAM_NEW_AUTHTOK_REQD;
  }
  if( (curdays > (ucs_spent->sp_lstchg + ucs_spent->sp_max - ucs_spent->sp_warn))
	    && (ucs_spent->sp_max != -1) && (ucs_spent->sp_warn != -1))
  {
    daysleft = (ucs_spent->sp_lstchg + ucs_spent->sp_max) - curdays;
    _pam_log( LOG_DEBUG, "password for user %s will expire in %d days", username, daysleft );
    snprintf( buf,
              80,
	      "Warning: your password will expire in %d day%.2s",
              daysleft,
	      daysleft == 1 ? "" : "s");
    _make_remark( pamh, PAM_TEXT_INFO, buf );
  }

  return PAM_SUCCESS;
}
