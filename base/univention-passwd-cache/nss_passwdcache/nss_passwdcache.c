/*
 * Univention Password Cache
 *  NSS password cache module
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

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/types.h>

#include <pthread.h>

#include <nss.h>    /* for nss* types    */
#include <pwd.h>    /* for struct passwd */
#include <shadow.h> /* for struct spwd   */
#include <grp.h>    /* for struct group  */

#include "../passwdcache.h"

/* -------------------------------------------------------------------------------- */
/*                                                                                  */
/* global Prototypes (nss from glibc required exact this names)                     */
/*                                                                                  */
/* -------------------------------------------------------------------------------- */

/* -------------------------------------------------------------------------------- */
/* passwd                                                                           */
/* -------------------------------------------------------------------------------- */

/* prepares the handle for access to cache of passwd */
enum nss_status _nss_passwdcache_setpwent( int stayopen );

/* close the handle for access to cache of passwd */
enum nss_status _nss_passwdcache_endpwent( void );

/* get password entry of cache */
enum nss_status _nss_passwdcache_getpwent_r( struct passwd *result,
                                             char *buffer,
					     size_t buflen,
					     int *errnop );

/* get password entry of cache for request uid */
enum nss_status _nss_passwdcache_getpwuid_r( uid_t uid,
                                             struct passwd *result,
					     char *buffer,
			                     size_t buflen,
					     int *errnop );

/* get password entry of cache for request username */
enum nss_status _nss_passwdcache_getpwnam_r( const char *name,
                                             struct passwd *result,
					     char *buffer,
			                     size_t buflen,
					     int *errnop );

/* -------------------------------------------------------------------------------- */
/* shadow                                                                           */
/* -------------------------------------------------------------------------------- */

/* prepares the handle for access to cache of shadow */
enum nss_status _nss_passwdcache_setspent( int stayopen );

/* close the handle for access to cache of shadow */
enum nss_status _nss_passwdcache_endspent( void );

/* get shadow entry of cache */
enum nss_status _nss_passwdcache_getspent_r( struct spwd *result,
                                             char *buffer,
					     size_t buflen,
					     int *errnop );

/* get shadow entry of cache for request username */
enum nss_status _nss_passwdcache_getspnam_r( const char *name,
                                             struct spwd *result,
					     char *buffer,
			                     size_t buflen,
					     int *errnop );

/* -------------------------------------------------------------------------------- */
/* group                                                                            */
/* -------------------------------------------------------------------------------- */

/* prepares the handle for access to cache of group */
enum nss_status _nss_passwdcache_setgrent( int stayopen );

/* close the handle for access to cache of group */
enum nss_status _nss_passwdcache_endgrent( void );

/* get group entry of cache */
enum nss_status _nss_passwdcache_getgrent_r( struct group *result,
                                             char *buffer,
					     size_t buflen,
					     int *errnop );

/* get group entry of cache for request gid */
enum nss_status _nss_passwdcache_getgrgid_r( gid_t gid,
                                             struct group *result,
					     char *buffer,
			                     size_t buflen,
					     int *errnop );

/* get group entry of cache for request groupname */
enum nss_status _nss_passwdcache_getgrnam_r( const char *name,
                                             struct group *result,
					     char *buffer,
			                     size_t buflen,
					     int *errnop );


/* -------------------------------------------------------------------------------- */
/*                                                                                  */
/* Vars                                                                             */
/*                                                                                  */
/* -------------------------------------------------------------------------------- */

/* Locks the static variables in this file.  */
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

typedef enum { none, getent, getby } last_use_t;

/* passwd */
static FILE *pw_stream;
static fpos_t pw_position;
static last_use_t pw_last_use;
static int pw_keep_stream;

/* shadow */
static FILE *sp_stream;
static fpos_t sp_position;
static last_use_t sp_last_use;
static int sp_keep_stream;

/* group */
static FILE *gr_stream;
static fpos_t gr_position;
static last_use_t gr_last_use;
static int gr_keep_stream;


/* -------------------------------------------------------------------------------- */
/*                                                                                  */
/* extern Functions                                                                 */
/*                                                                                  */
/* -------------------------------------------------------------------------------- */

/* -------------------------------------------------------------------------------- */
/* passwd                                                                           */
/* -------------------------------------------------------------------------------- */
extern int _nss_files_parse_pwent( char *line,
                                   struct passwd *result,
                                   char *data,
		                   size_t datalen,
		                   int *errnop );

/* -------------------------------------------------------------------------------- */
/* shadow                                                                           */
/* -------------------------------------------------------------------------------- */
extern int _nss_files_parse_spent( char *line,
                                   struct spwd *result,
                                   char *data,
		                   size_t datalen,
		                   int *errnop );

/* -------------------------------------------------------------------------------- */
/* group                                                                            */
/* -------------------------------------------------------------------------------- */
extern int _nss_files_parse_grent( char *line,
                                   struct group *result,
                                   char *data,
		                   size_t datalen,
		                   int *errnop );


/* -------------------------------------------------------------------------------- */
/*                                                                                  */
/* intern Functions                                                                 */
/*                                                                                  */
/* -------------------------------------------------------------------------------- */

/* -------------------------------------------------------------------------------- */
/* passwd                                                                           */
/* -------------------------------------------------------------------------------- */

/* Open database file if not already opened.  */
static enum nss_status internal_setpwent( int stayopen )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: internal_setpwent()\n" );
  #endif

  enum nss_status status = NSS_STATUS_SUCCESS;

  if( pw_stream == NULL )
  {
    pw_stream = fopen( PW_DATAFILE, "r" );

    if( pw_stream == NULL )
      status = errno == EAGAIN ? NSS_STATUS_TRYAGAIN : NSS_STATUS_UNAVAIL;
    else
    {
      int result, flags;

      result = flags = fcntl( fileno( pw_stream ), F_GETFD, 0 );
      if( result >= 0 )
      {
        flags |= FD_CLOEXEC;
        result = fcntl( fileno( pw_stream ), F_SETFD, flags);
      }
     if( result < 0 )
     {
       fclose( pw_stream );
       pw_stream = NULL;
       status = NSS_STATUS_UNAVAIL;
      }
    }
  }
  else
    rewind( pw_stream );

  if( pw_stream != NULL)
    pw_keep_stream |= stayopen;

  return status;
}

/* Close the database file.  */
static void internal_endpwent( void )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: internal_endpwent()\n" );
  #endif

  if( pw_stream != NULL)
  {
    fclose( pw_stream );
    pw_stream = NULL;
  }
}

/* Parsing the database file into `struct passwd' data structures.  */
static enum nss_status internal_getpwent( struct passwd *result,
                                          char *buffer,
					  size_t buflen,
					  int *errnop )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: internal_getpwent()\n" );
  #endif

  char *p;
  int parse_result;

  if( buflen < 2 )
  {
    *errnop = ERANGE;
    return NSS_STATUS_TRYAGAIN;
  }

  do
  {
    buffer[buflen - 1] = '\xff';

    p = fgets_unlocked( buffer, buflen, pw_stream );
    if( p == NULL )
    {
      *errnop = ENOENT;
      return NSS_STATUS_NOTFOUND;
    }
    else if( ( unsigned char ) buffer[buflen - 1] != 0xff)
    {
      *errnop = ERANGE;
      return NSS_STATUS_TRYAGAIN;
    }

    while( isspace(*p) )
      ++p;
  }
  while( *p == '\0' || *p == '#'
	 || !(parse_result = _nss_files_parse_pwent( p, result, buffer, buflen, errnop )));

  return parse_result == -1 ? NSS_STATUS_TRYAGAIN : NSS_STATUS_SUCCESS;
}

/* -------------------------------------------------------------------------------- */
/* shadow                                                                           */
/* -------------------------------------------------------------------------------- */

/* Open database file if not already opened.  */
static enum nss_status internal_setspent( int stayopen )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: internal_setspent()\n" );
  #endif

  enum nss_status status = NSS_STATUS_SUCCESS;

  if( sp_stream == NULL )
  {
    sp_stream = fopen( SP_DATAFILE, "r" );

    if( sp_stream == NULL )
      status = errno == EAGAIN ? NSS_STATUS_TRYAGAIN : NSS_STATUS_UNAVAIL;
    else
    {
      int result, flags;

      result = flags = fcntl( fileno( sp_stream ), F_GETFD, 0 );
      if( result >= 0 )
      {
        flags |= FD_CLOEXEC;
        result = fcntl( fileno( sp_stream ), F_SETFD, flags);
      }
     if( result < 0 )
     {
       fclose( sp_stream );
       sp_stream = NULL;
       status = NSS_STATUS_UNAVAIL;
      }
    }
  }
  else
    rewind( sp_stream );

  if( sp_stream != NULL)
    sp_keep_stream |= stayopen;

  return status;
}

/* Close the database file.  */
static void internal_endspent( void )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: internal_endspent()\n" );
  #endif

  if( sp_stream != NULL)
  {
    fclose( sp_stream );
    sp_stream = NULL;
  }
}

/* Parsing the database file into `struct spwd' data structures.  */
static enum nss_status internal_getspent( struct spwd *result,
                                          char *buffer,
					  size_t buflen,
					  int *errnop )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: internal_getspent()\n" );
  #endif

  char *p;
  int parse_result;

  if( buflen < 2 )
  {
    *errnop = ERANGE;
    return NSS_STATUS_TRYAGAIN;
  }

  do
  {
    buffer[buflen - 1] = '\xff';

    p = fgets_unlocked( buffer, buflen, sp_stream );
    if( p == NULL )
    {
      *errnop = ENOENT;
      return NSS_STATUS_NOTFOUND;
    }
    else if( ( unsigned char ) buffer[buflen - 1] != 0xff)
    {
      *errnop = ERANGE;
      return NSS_STATUS_TRYAGAIN;
    }

    while( isspace(*p) )
      ++p;
  }
  while( *p == '\0' || *p == '#'
	 || !(parse_result = _nss_files_parse_spent( p, result, buffer, buflen, errnop )));

  return parse_result == -1 ? NSS_STATUS_TRYAGAIN : NSS_STATUS_SUCCESS;
}

/* -------------------------------------------------------------------------------- */
/* group                                                                            */
/* -------------------------------------------------------------------------------- */

/* Open database file if not already opened.  */
static enum nss_status internal_setgrent( int stayopen )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: internal_setgrent()\n" );
  #endif

  enum nss_status status = NSS_STATUS_SUCCESS;

  if( gr_stream == NULL )
  {
    gr_stream = fopen( GR_DATAFILE, "r" );

    if( gr_stream == NULL )
      status = errno == EAGAIN ? NSS_STATUS_TRYAGAIN : NSS_STATUS_UNAVAIL;
    else
    {
      int result, flags;

      result = flags = fcntl( fileno( gr_stream ), F_GETFD, 0 );
      if( result >= 0 )
      {
        flags |= FD_CLOEXEC;
        result = fcntl( fileno( gr_stream ), F_SETFD, flags);
      }
     if( result < 0 )
     {
       fclose( gr_stream );
       gr_stream = NULL;
       status = NSS_STATUS_UNAVAIL;
      }
    }
  }
  else
    rewind( gr_stream );

  if( gr_stream != NULL)
    gr_keep_stream |= stayopen;

  return status;
}

/* Close the database file.  */
static void internal_endgrent( void )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: internal_endgrent()\n" );
  #endif

  if( gr_stream != NULL)
  {
    fclose( gr_stream );
    gr_stream = NULL;
  }
}

/* Parsing the database file into `struct group' data structures.  */
static enum nss_status internal_getgrent( struct group *result,
                                          char *buffer,
					  size_t buflen,
					  int *errnop )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: internal_getgrent()\n" );
  #endif

  char *p;
  int parse_result;

  if( buflen < 2 )
  {
    *errnop = ERANGE;
    return NSS_STATUS_TRYAGAIN;
  }

  do
  {
    buffer[buflen - 1] = '\xff';

    p = fgets_unlocked( buffer, buflen, gr_stream );
    if( p == NULL )
    {
      *errnop = ENOENT;
      return NSS_STATUS_NOTFOUND;
    }
    else if( ( unsigned char ) buffer[buflen - 1] != 0xff)
    {
      *errnop = ERANGE;
      return NSS_STATUS_TRYAGAIN;
    }

    while( isspace(*p) )
      ++p;
  }
  while( *p == '\0' || *p == '#'
	 || !(parse_result = _nss_files_parse_grent( p, result, buffer, buflen, errnop )));

  return parse_result == -1 ? NSS_STATUS_TRYAGAIN : NSS_STATUS_SUCCESS;
}


/* -------------------------------------------------------------------------------- */
/*                                                                                  */
/* global Functions                                                                 */
/*                                                                                  */
/* -------------------------------------------------------------------------------- */

/* -------------------------------------------------------------------------------- */
/* passwd                                                                           */
/* -------------------------------------------------------------------------------- */

/* prepares the handle for access to cache of passwd */
enum nss_status _nss_passwdcache_setpwent( int stayopen )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: _nss_passwdcache_setpwent()\n" );
  #endif

  enum nss_status status;

  pthread_mutex_lock( &lock );

  status = internal_setpwent( stayopen );

  if( (status == NSS_STATUS_SUCCESS) && (fgetpos( pw_stream, &pw_position ) < 0) )
  {
    fclose( pw_stream );
    pw_stream = NULL;
    status = NSS_STATUS_UNAVAIL;
  }

  pw_last_use = getent;

  pthread_mutex_unlock( &lock );

  return status;
}

/* close the handle for access to cache of passwd */
enum nss_status _nss_passwdcache_endpwent( void )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: _nss_passwdcache_endpwent()\n" );
  #endif

  pthread_mutex_lock( &lock );

  internal_endpwent();

  pw_keep_stream = 0;

  pthread_mutex_unlock( &lock );

  return NSS_STATUS_SUCCESS;
}

/* get password entry of cache */
enum nss_status _nss_passwdcache_getpwent_r( struct passwd *result,
                                             char *buffer,
					     size_t buflen,
					     int *errnop )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: _nss_passwdcache_getpwent_r()\n" );
  #endif

  enum nss_status status = NSS_STATUS_SUCCESS;

  pthread_mutex_lock( &lock );

  if( pw_stream == NULL )
  {
    status = internal_setpwent(0);

    if( status == NSS_STATUS_SUCCESS && fgetpos( pw_stream, &pw_position ) < 0)
    {
      fclose( pw_stream );
      pw_stream = NULL;
      status = NSS_STATUS_UNAVAIL;
    }
  }

  if( status == NSS_STATUS_SUCCESS )
  {
    if( pw_last_use != getent )
    {
      if( fsetpos( pw_stream, &pw_position ) < 0)
        status = NSS_STATUS_UNAVAIL;
      else
        pw_last_use = getent;
    }

    if( status == NSS_STATUS_SUCCESS )
    {
      status = internal_getpwent( result, buffer, buflen, errnop );

      if( status == NSS_STATUS_SUCCESS )
        fgetpos( pw_stream, &pw_position);
      else
        pw_last_use = none;
    }
  }

  pthread_mutex_unlock( &lock );

  return status;
}


/* get password entry of cache for request uid */
enum nss_status _nss_passwdcache_getpwuid_r( uid_t uid,
                                             struct passwd *result,
					     char *buffer,
			                     size_t buflen,
					     int *errnop )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: _nss_passwdcache_getpwuid_r()\n" );
  #endif

  enum nss_status status;

  pthread_mutex_lock( &lock );

  status = internal_setpwent( pw_keep_stream );

  if( status == NSS_STATUS_SUCCESS)
  {
    pw_last_use = getby;

    while( (status = internal_getpwent( result, buffer, buflen, errnop )) == NSS_STATUS_SUCCESS)
    {
      if( result->pw_uid == uid && result->pw_name[0] != '+' && result->pw_name[0] != '-' )
        break;
    }

    if( !pw_keep_stream )
      internal_endpwent();
  }

  pthread_mutex_unlock( &lock );

  return status;
}

/* get password entry of cache for request username */
enum nss_status _nss_passwdcache_getpwnam_r( const char *name,
                                             struct passwd *result,
					     char *buffer,
			                     size_t buflen,
					     int *errnop )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: _nss_passwdcache_getpwnam_r()\n" );
  #endif

  enum nss_status status;

  pthread_mutex_lock( &lock );

  status = internal_setpwent( pw_keep_stream );

  if( status == NSS_STATUS_SUCCESS)
  {
    pw_last_use = getby;

    while( (status = internal_getpwent( result, buffer, buflen, errnop )) == NSS_STATUS_SUCCESS)
    {
      if( name[0] != '+' && name[0] != '-' && ! strcmp (name, result->pw_name) )
        break;
    }

    if( !pw_keep_stream )
      internal_endpwent();
  }

  pthread_mutex_unlock( &lock );

  return status;
}

/* -------------------------------------------------------------------------------- */
/* shadow                                                                           */
/* -------------------------------------------------------------------------------- */

/* prepares the handle for access to cache of shadow */
enum nss_status _nss_passwdcache_setspent( int stayopen )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: _nss_passwdcache_setspent()\n" );
  #endif

  enum nss_status status;

  pthread_mutex_lock( &lock );

  status = internal_setspent( stayopen );

  if( (status == NSS_STATUS_SUCCESS) && (fgetpos( sp_stream, &sp_position ) < 0) )
  {
    fclose( sp_stream );
    sp_stream = NULL;
    status = NSS_STATUS_UNAVAIL;
  }

  sp_last_use = getent;

  pthread_mutex_unlock( &lock );

  return status;
}

/* close the handle for access to cache of shadow */
enum nss_status _nss_passwdcache_endspent( void )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: _nss_passwdcache_endspent()\n" );
  #endif

  pthread_mutex_lock( &lock );

  internal_endspent();

  sp_keep_stream = 0;

  pthread_mutex_unlock( &lock );

  return NSS_STATUS_SUCCESS;
}

/* get shadow entry of cache */
enum nss_status _nss_passwdcache_getspent_r( struct spwd *result,
                                             char *buffer,
					     size_t buflen,
					     int *errnop )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: _nss_passwdcache_getspent_r()\n" );
  #endif

  /* Return next entry in sp file.  */
  enum nss_status status = NSS_STATUS_SUCCESS;

  pthread_mutex_lock( &lock );

  if( sp_stream == NULL )
  {
    status = internal_setspent(0);

    if( status == NSS_STATUS_SUCCESS && fgetpos( sp_stream, &sp_position ) < 0)
    {
      fclose( sp_stream );
      sp_stream = NULL;
      status = NSS_STATUS_UNAVAIL;
    }
  }

  if( status == NSS_STATUS_SUCCESS )
  {
    if( sp_last_use != getent )
    {
      if( fsetpos( sp_stream, &sp_position ) < 0)
        status = NSS_STATUS_UNAVAIL;
      else
        sp_last_use = getent;
    }

    if( status == NSS_STATUS_SUCCESS )
    {
      status = internal_getspent( result, buffer, buflen, errnop );

      if( status == NSS_STATUS_SUCCESS )
        fgetpos( sp_stream, &sp_position);
      else
        sp_last_use = none;
    }
  }

  pthread_mutex_unlock( &lock );

  return status;
}

/* get shadow entry of cache for request username */
enum nss_status _nss_passwdcache_getspnam_r( const char *name,
                                             struct spwd *result,
					     char *buffer,
			                     size_t buflen,
					     int *errnop )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: _nss_passwdcache_getspnam_r()\n" );
  #endif

  enum nss_status status;

  pthread_mutex_lock( &lock );

  status = internal_setspent( sp_keep_stream );

  if( status == NSS_STATUS_SUCCESS)
  {
    sp_last_use = getby;

    while( (status = internal_getspent( result, buffer, buflen, errnop )) == NSS_STATUS_SUCCESS)
    {
      if( name[0] != '+' && name[0] != '-' && ! strcmp (name, result->sp_namp) )
        break;
    }

    if( !sp_keep_stream )
      internal_endspent();
  }

  pthread_mutex_unlock( &lock );

  return status;
}


/* -------------------------------------------------------------------------------- */
/* group                                                                            */
/* -------------------------------------------------------------------------------- */

/* prepares the handle for access to cache of group */
enum nss_status _nss_passwdcache_setgrent( int stayopen )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: _nss_passwdcache_setgrent()\n" );
  #endif

  enum nss_status status;

  pthread_mutex_lock( &lock );

  status = internal_setgrent( stayopen );

  if( (status == NSS_STATUS_SUCCESS) && (fgetpos( gr_stream, &gr_position ) < 0) )
  {
    fclose( gr_stream );
    gr_stream = NULL;
    status = NSS_STATUS_UNAVAIL;
  }

  gr_last_use = getent;

  pthread_mutex_unlock( &lock );

  return status;
}

/* close the handle for access to cache of group */
enum nss_status _nss_passwdcache_endgrent( void )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: _nss_passwdcache_endgrent()\n" );
  #endif

  pthread_mutex_lock( &lock );

  internal_endgrent();

  gr_keep_stream = 0;

  pthread_mutex_unlock( &lock );

  return NSS_STATUS_SUCCESS;
}

/* get group entry of cache */
enum nss_status _nss_passwdcache_getgrent_r( struct group *result,
                                             char *buffer,
					     size_t buflen,
					     int *errnop )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: _nss_passwdcache_getgrent_r()\n" );
  #endif

  /* Return next entry in gr file.  */
  enum nss_status status = NSS_STATUS_SUCCESS;

  pthread_mutex_lock( &lock );

  if( gr_stream == NULL )
  {
    status = internal_setgrent(0);

    if( status == NSS_STATUS_SUCCESS && fgetpos( gr_stream, &gr_position ) < 0)
    {
      fclose( gr_stream );
      gr_stream = NULL;
      status = NSS_STATUS_UNAVAIL;
    }
  }

  if( status == NSS_STATUS_SUCCESS )
  {
    if( gr_last_use != getent )
    {
      if( fsetpos( gr_stream, &gr_position ) < 0)
        status = NSS_STATUS_UNAVAIL;
      else
        gr_last_use = getent;
    }

    if( status == NSS_STATUS_SUCCESS )
    {
      status = internal_getgrent( result, buffer, buflen, errnop );

      if( status == NSS_STATUS_SUCCESS )
        fgetpos( gr_stream, &gr_position);
      else
        gr_last_use = none;
    }
  }

  pthread_mutex_unlock( &lock );

  return status;
}

/* get group entry of cache for request gid */
enum nss_status _nss_passwdcache_getgrgid_r( gid_t gid,
                                             struct group *result,
					     char *buffer,
			                     size_t buflen,
					     int *errnop )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: _nss_passwdcache_getgrgid_r()\n" );
  #endif

  enum nss_status status;

  pthread_mutex_lock( &lock );

  status = internal_setgrent( gr_keep_stream );

  if( status == NSS_STATUS_SUCCESS)
  {
    gr_last_use = getby;

    while( (status = internal_getgrent( result, buffer, buflen, errnop )) == NSS_STATUS_SUCCESS)
    {
      if( result->gr_gid == gid && result->gr_name[0] != '+' && result->gr_name[0] != '-' )
        break;
    }

    if( !gr_keep_stream )
      internal_endgrent();
  }

  pthread_mutex_unlock( &lock );

  return status;
}

/* get group entry of cache for request groupname */
enum nss_status _nss_passwdcache_getgrnam_r( const char *name,
                                             struct group *result,
					     char *buffer,
			                     size_t buflen,
					     int *errnop )
{
  #ifdef DEBUG
  fprintf( stderr, "Debug: _nss_passwdcache_getgrnam_r()\n" );
  #endif

  enum nss_status status;

  pthread_mutex_lock( &lock );

  status = internal_setgrent( gr_keep_stream );

  if( status == NSS_STATUS_SUCCESS)
  {
    gr_last_use = getby;

    while( (status = internal_getgrent( result, buffer, buflen, errnop )) == NSS_STATUS_SUCCESS)
    {
      if( name[0] != '-' && name[0] != '+' && ! strcmp (name, result->gr_name) )
        break;
    }

    if( !gr_keep_stream )
      internal_endgrent();
  }

  pthread_mutex_unlock( &lock );

  return status;
}
