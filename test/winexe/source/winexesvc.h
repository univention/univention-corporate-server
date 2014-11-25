/*
  Copyright (C) Andrzej Hajda 2009-2013
  Contact: andrzej.hajda@wp.pl
  License: GNU General Public License version 3
*/

/*
 * Shared by winexe and winexesvc
 */

#define VERSION_MAJOR 1
#define VERSION_MINOR 1

#define VERSION ((VERSION_MAJOR * 100) + VERSION_MINOR)

#define SERVICE_NAME "winexesvc"

#define PIPE_NAME "ahexec"
#define PIPE_NAME_IN "ahexec_stdin%08X"
#define PIPE_NAME_OUT "ahexec_stdout%08X"
#define PIPE_NAME_ERR "ahexec_stderr%08X"

#define CMD_STD_IO_ERR "std_io_err"
#define CMD_RETURN_CODE "return_code"
