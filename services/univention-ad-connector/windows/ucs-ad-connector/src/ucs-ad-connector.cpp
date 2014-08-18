/*
 * Univention AD Connector
 *  this is the password sync service/daemon for the AD side
 * 
 * Copyright 2004-2014 Univention GmbH
 *
 * http://www.univention.de/
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
 * <http://www.gnu.org/licenses/>.
 */

#include <stdio.h>
#include <winsock2.h>
#include <winldap.h>
#include <windows.h>
#include <shlwapi.h>
#include <direct.h>

#include <openssl/ssl.h>
#include <openssl/err.h>

#define SECURITY_WIN32
#include <sspi.h>

#define GET_PASSWORD 'G'
#define SET_PASSWORD 'S'

#define MAX_LINE 4096

/* Error Codes */
#define E_OK								0x00000000

#define E_MALLOC							0x00000001
#define E_PACKET_LENGTH						0x00000101
#define E_PACKET_COMMAND					0x00000102
#define E_PACKET_USER_DATA					0x00000103

#define E_NETWORK_WSASTARTUP				0x00000201
#define E_NETWORK_BIND						0x00000202
#define E_NETWORK_LISTEN					0x00000203

#define E_LDAP_INIT							0x00000301
#define E_LDAP_BIND							0x00000302
#define E_LDAP_SEARCH						0x00000303

#define E_LOGON_PRIVILEGE					0x00000401
#define E_LOGON_WRONG_PASSWORD				0x00000402
#define E_LOGON_ACCESS_DENIED				0x00000403
#define E_LOGON_FAILURE						0x00000404

#define E_IMPERSONATE_LOGGED_ON_USER		0x00000501

/* Was kann dieser Compiler eigentlich? */
/* #define logfile(log_file, args...) fprintf(log_file,  ##args); fflush(log_file)*/
#define logfile(log_file, arg) fprintf(log_file,  (const char *) arg); fflush(log_file)

struct packet
{
	HANDLE *hToken;
	char *userdn;
	char *pwd;
	char cmd;
	char *user_data;
	char *pwd_data;
	FILE *logfile;
};

SSL_CTX* ctx;

SERVICE_STATUS          MyServiceStatus;
SERVICE_STATUS_HANDLE   MyServiceStatusHandle;


LPTSTR p_path;
char path[MAX_PATH];
char path_logfile[MAX_PATH];
char path_copypwd_exe[MAX_PATH];
char path_copypwd_in[MAX_PATH];
char path_copypwd_out[MAX_PATH];
char path_key[MAX_PATH];
char path_cert[MAX_PATH];

char *error_string ( int err )
{
	switch ( err ) {
		case E_OK:
			return "E_OK";
		case E_MALLOC:
			return "E_MALLOC";
		case E_PACKET_LENGTH:
			return "E_PACKET_LENGTH";
		case E_PACKET_COMMAND:
			return "E_PACKET_COMMAND";
		case E_PACKET_USER_DATA:
			return "E_PACKET_USER_DATA";
		case E_NETWORK_WSASTARTUP:
			return "E_NETWORK_WSASTARTUP";
		case E_NETWORK_BIND:
			return "E_NETWORK_BIND";
		case E_NETWORK_LISTEN:
			return "E_NETWORK_LISTEN";
		case E_LDAP_INIT:
			return "E_LDAP_INIT";
		case E_LDAP_BIND:
			return "E_LDAP_BIND";
		case E_LDAP_SEARCH:
			return "E_LDAP_SEARCH";
		case E_LOGON_PRIVILEGE:
			return "E_LOGON_PRIVILEGE";
		case E_LOGON_WRONG_PASSWORD:
			return "E_LOGON_WRONG_PASSWORD";
		case E_LOGON_ACCESS_DENIED:
			return "E_LOGON_ACCESS_DENIED";
		case E_LOGON_FAILURE:
			return "E_LOGON_FAILURE";
		case E_IMPERSONATE_LOGGED_ON_USER:
			return "E_IMPERSONATE_LOGGED_ON_USER";
		default:
			return "Unknown error";
	}
	return "Unknown error";
}


/****************************************************************************
 * split_packet_helper
 *
 * in p ist an der ersten Stelle ein Integer
 * soviele Bytes, wie in dem Integer definiert sind, werden in dest kopiert
 *
 ***************************************************************************/
static int split_packet_helper ( char **p, char **dest )
{
	int len;

	memcpy ( &len, *p, 4 );
	*p+=4;

	if ( len > 8192 ) {
		return E_PACKET_LENGTH;
	}

	if ( (*dest = (char*) malloc ( ( len + 1 ) * sizeof ( char )  )) == NULL ){
		return E_MALLOC;
	}

	memset ( *dest, 0, len+1 );
	memcpy ( *dest, *p, len ) ;
	*p+=len;

	return 0;

}

/****************************************************************************
 * split_packet
 *
 * Bekommt einen Buffer von l_buf Länge wird in die struct packet geschrieben
 * char *userdn
 * char *pwd
 * char cmd
 * char *user_data
 * char *pwd_data
 *
 ***************************************************************************/
int split_packet ( char *buf, int l_buf, struct packet *packet )
{
	char *p;
	int len = 0;
	int rc;

	/* Pointer zum Durchlaufen ... */
	p = buf;

	/* An den ersten 4 Stellen steht ein Integer */
	memcpy( &len, p, 4 );
	p+=4;

	/* Die Länge von den ersten 4 Bytes muss genau so lang sein, wie der
	 * Buffer insgesamt, plus die ersten 4 Bytes */
	if ( l_buf != len+4 ) {
		fprintf ( packet->logfile, "split_packet length error: l_buf=%d, len=%d\n",l_buf,len); fflush ( packet->logfile );
		return E_PACKET_LENGTH;
	}


	/* User DN */
	if ( (rc = split_packet_helper ( &p, &packet->userdn ) ) != E_OK ) {
		if ( rc == E_PACKET_LENGTH ) {
			fprintf ( packet->logfile, ">8192 userdn\n");fflush ( packet->logfile );
		}
		return rc;
	}

	/* User Passwort */
	if ( ( rc = split_packet_helper ( &p, &packet->pwd ) ) != E_OK ) {
		if ( rc == E_PACKET_LENGTH ) {
			fprintf ( packet->logfile, ">8192 pwd\n");fflush ( packet->logfile );
		}
		return rc;
	}

	/* GET_PASSWORD oder SET_PASSWORD */
	packet->cmd = p[0];
	p+=1;

	if ( packet->cmd == GET_PASSWORD ) {
		/* Wenn das Passwort gelese werden soll, dann steht in dem Paket noch die
		 * Information über den Benutzer */
		if ( ( rc = split_packet_helper ( &p, &packet->user_data ) ) != E_OK ) {
			if ( rc == E_PACKET_LENGTH ) {
				fprintf ( packet->logfile, ">8192 user data\n");fflush ( packet->logfile );
			}
			return rc;
		}

	} else if ( packet->cmd == SET_PASSWORD ) {
		/* Wenn wir das Passwort setzen, dann wird die Information des Benutzers
		 * und das Passwort benötigt */
		if ( ( rc = split_packet_helper ( &p, &packet->user_data ) ) != E_OK ) {
			if ( rc == E_PACKET_LENGTH ) {
				fprintf ( packet->logfile, ">8192 user data\n");fflush ( packet->logfile );
			}
			return rc;
		}
		if ( ( rc = split_packet_helper ( &p, &packet->pwd_data ) ) != E_OK ) {
			if ( rc == E_PACKET_LENGTH ) {
				fprintf ( packet->logfile, ">8192 pwd data\n");fflush ( packet->logfile );
			}
			return rc;
		}

	} else {

		return E_PACKET_COMMAND;
	}

	return E_OK;

}

/****************************************************************************
 * create_packet
 *
 * Das Antwortpaket wird aus der Struct packet und dem Error Code erzeugt.
 *
 ***************************************************************************/
int create_packet ( char **buf, int *l_buf, struct packet *packet, unsigned int error_code )
{
	char *p;
	unsigned int len;

	if ( packet->cmd == GET_PASSWORD  && error_code == E_OK ) {

		/* Wenn das Passwort an den Client zurückgeliefert werden soll und
		 * der Error Code in Ordnung ist, dann wird das entsprechene Paket
		 * generiert, Aufbau des Paketes:
		 * 4 Bytes Länge des Paketes minus 4 (quasi sich selbst)
		 * 4 Bytes Error Code
		 * 4 Bytes Länge der folgenden Daten
		 * n Bytes die Passwort Daten
		 */

		*l_buf = 4 + 4 + 4 +strlen(packet->pwd_data);
		*buf = (char*) malloc ( *l_buf * sizeof ( char ) );

		p = *buf;
		len = *l_buf - 4;
		memcpy(p, &len, 4 );
		p+=4;

		len=0;
		memcpy(p, &len, 4);
		p+=4;

		len = strlen ( packet->pwd_data ) ;
		memcpy(p, &len, 4);
		p+=4;

		memcpy ( p, packet->pwd_data, strlen(packet->pwd_data) );
			
	} else  {

		/* Wenn das Passwort gesetzt wurde, oder ein Fehler aufgetreten ist,
		 * geben wir die Länge und den Error Code zurück, jeweils 4 Bytes */

		*l_buf = 4 + 4;
		*buf = (char *) malloc ( *l_buf * sizeof ( char ) );

		p = *buf;
		len = *l_buf - 4;
		memcpy(p, &len, 4 );
		p+=4;

		*p = error_code;
		memcpy ( p, &error_code, 4 );
	}

	return E_OK;
}

/****************************************************************************
 * network_init_ssl
 *
 *
 ***************************************************************************/
SOCKET network_init_ssl( int port, int *error )
{
	SSL_METHOD *meth;
	SOCKET server_socketfd;
	struct sockaddr_in server_address;
	char i;
	int server_l;
	WSADATA wsaData;

	SSL_load_error_strings();
	SSLeay_add_ssl_algorithms();
	meth = SSLv23_server_method();
	ctx = SSL_CTX_new (meth);
	if (!ctx) {
		return -1;
	}

	if (SSL_CTX_use_certificate_file(ctx, path_cert, SSL_FILETYPE_PEM) <= 0) {
		return -1;
	}

	if (SSL_CTX_use_PrivateKey_file(ctx, path_key, SSL_FILETYPE_PEM) <= 0) {
		return -1;
	}

	if (!SSL_CTX_check_private_key(ctx)) {
		return -1;
	}


	if ( (WSAStartup( MAKEWORD(2,2), &wsaData )) != NO_ERROR ) {
		*error = E_NETWORK_WSASTARTUP;
		return -1;
	}

	server_socketfd = socket(AF_INET, SOCK_STREAM, 0);

	i=1;
	setsockopt(server_socketfd,SOL_SOCKET, SO_REUSEADDR, &i, sizeof(i));

	server_address.sin_family = AF_INET;
	memset(&server_address.sin_addr,0,sizeof(server_address.sin_addr));
	server_address.sin_port = htons(port);
	server_l = sizeof(server_address);

	if( (bind(server_socketfd,(struct sockaddr*)&server_address,sizeof(server_address))) == -1) {
		*error = E_NETWORK_BIND;
		return -1;
	}

	if( (listen(server_socketfd, 1)) == -1) {
		*error = E_NETWORK_LISTEN;
		return -1;
	}

	return server_socketfd;
}




int user_logon ( char *username, char *pwd, struct packet packet )
{
	int rc = 0;

	if ( ( ! LogonUser( username, NULL, pwd, LOGON32_LOGON_NETWORK, LOGON32_PROVIDER_DEFAULT, packet.hToken ) ) ) {
		int err = GetLastError ( );
		switch ( err ) {
			case ERROR_PRIVILEGE_NOT_HELD:
				rc = E_LOGON_PRIVILEGE;
				break;
			case ERROR_LOGON_FAILURE:
				rc = E_LOGON_WRONG_PASSWORD;
				break;
			case ERROR_ACCESS_DENIED:
				rc = E_LOGON_ACCESS_DENIED;
				break;
			default:
				rc = E_LOGON_FAILURE;
				break;
			}
	}
	return rc;
}

void thread (LPVOID data)
{
	int res;
	struct packet *packet;
	char *command = NULL;
	FILE *fp;
	char buffer[MAX_LINE+1];
	char *p;
	char filename[MAX_PATH];
	char cmd[MAX_PATH+MAX_PATH];

	packet = (struct packet * ) data;

	if ( (res = ImpersonateLoggedOnUser ( *(packet->hToken) )) == 0 ) {
		ExitThread ( E_IMPERSONATE_LOGGED_ON_USER );
	}

	_chdir(p_path);

	if ( packet->cmd == GET_PASSWORD ) {
		fp = fopen(path_copypwd_in, "w");
		fprintf(fp, "%s", packet->user_data );
		fclose(fp);


		// wsprintf(cmd, "copypwd.exe dump> %s", path_copypwd_out);
		wsprintf(cmd, "PwDump.exe -x localhost> %s", path_copypwd_out);
		//wsprintf(cmd, "\"%s\" dump> %s", path_copypwd_exe, path_copypwd_out);

		fprintf ( packet->logfile, "Starting command: %s\n", cmd);fflush ( packet->logfile );
		system ( cmd );
		fprintf ( packet->logfile, "Exit     command: %s\n", cmd);fflush ( packet->logfile );

		packet->pwd_data = (char*)malloc( ( MAX_LINE + 1 ) * sizeof ( char ) );
		memset ( packet->pwd_data, 0, MAX_LINE + 1 );

		fp = fopen(path_copypwd_out, "r");
		fgets( packet->pwd_data, MAX_LINE, fp );
		fclose ( fp );

	} else if ( packet->cmd == SET_PASSWORD ) {
		fprintf( packet->logfile, "Writing to file [%s]\n", path_copypwd_out);fflush ( packet->logfile );
		fp = fopen(path_copypwd_out, "w");
		fprintf(fp, "%s:%s\n", packet->user_data, packet->pwd_data );
		fclose(fp);
		wsprintf(cmd, "PwDump.exe -i copypwd.in.txt -x localhost");
		fprintf( packet->logfile, "Starting command: %s\n", cmd);fflush ( packet->logfile );
		system(cmd);
		fprintf( packet->logfile, "Exiting command: %s\n", cmd);fflush ( packet->logfile );
	} else {
		fprintf( packet->logfile, "system Unknown command\n");fflush ( packet->logfile );
	}

	if ( command != NULL ) {
		free ( command );
	}

	RevertToSelf();

	ExitThread(0);
}

int worker ( SOCKET socket )
{
	SOCKET client_socket;
	SSL*     ssl;
	int bytesRecv = SOCKET_ERROR;
	char recvbuf[8192];
	struct packet packet;
	HANDLE thd;
	HANDLE *hToken;
	DWORD tid;

	DWORD result;

	char *username;
	int res;

	char filename[MAX_PATH];

	packet.hToken = (PHANDLE)malloc(sizeof(PHANDLE));
	if ( (packet.logfile = fopen( path_logfile, "a+" )) == NULL ) {
		fprintf( stderr, "Failed to open logfile ucs-ad-connector.log\n" );
	}

	while ( 1 ) {
		FILE *fp;
		packet.userdn = NULL;
		packet.pwd = NULL;
		packet.cmd = 0;
		packet.user_data = 0;
		packet.pwd_data = 0;
		fprintf ( packet.logfile, "Waiting for a client to connect...\n" );fflush ( packet.logfile );
		while (1) {
			client_socket = SOCKET_ERROR;
			while ( client_socket == SOCKET_ERROR ) {
				client_socket = accept( socket, NULL, NULL );
				fprintf ( packet.logfile, "accept client connection...\n" );fflush ( packet.logfile );
			}
			fprintf ( packet.logfile, "Client Connected.\n" );fflush ( packet.logfile );
			ssl = SSL_new (ctx);
			//CHK_NULL(ssl);
			SSL_set_fd (ssl, client_socket);
			SSL_accept (ssl);
			//CHK_SSL(err);
			break;
		}
	
	
		memset ( recvbuf, 0, 8192 );
	
		bytesRecv = SSL_read (ssl, recvbuf, sizeof(recvbuf) - 1);

		if ( ( res = split_packet ( recvbuf, bytesRecv, &packet ) ) != E_OK ) {
			fprintf ( packet.logfile, "split_packet error: %s\n", error_string ( res ) );fflush ( packet.logfile );
			goto cleanup;
		}

		fprintf ( packet.logfile, "UserDN  = [%s]\n", packet.userdn );fflush ( packet.logfile );
		/* don't write the password to the logfile */
		/* fprintf ( packet.logfile, "PassDN  = [%s]\n", packet.pwd );fflush ( packet.logfile ); */
		fprintf ( packet.logfile, "Command = [%c]\n", packet.cmd );fflush ( packet.logfile );
		fprintf ( packet.logfile, "User    = [%s]\n", packet.user_data );fflush ( packet.logfile );


		if ( ! packet.user_data ) {
			fprintf ( packet.logfile, "No user_data!!!\n");fflush ( packet.logfile );
			res=E_PACKET_USER_DATA;
			goto cleanup;
		}

		if ( ( res = user_logon ( packet.userdn, packet.pwd, packet ) ) != E_OK ) {
			fprintf ( packet.logfile, "user_logon error: %s\n", error_string ( res ) );fflush ( packet.logfile );
			goto cleanup;
		}
		fprintf ( packet.logfile, "user_logon okay\n");fflush ( packet.logfile );
		

		thd = CreateThread ( NULL, 0, (LPTHREAD_START_ROUTINE)thread, (LPVOID)&packet, 0, &tid );
		WaitForSingleObject(thd, INFINITE);

		GetExitCodeThread ( thd, &result );

		if ( result != E_OK ) {
			fprintf( packet.logfile, "Thread exit with error: %s\n", error_string ( result ) );fflush ( packet.logfile );
			res = result;
			goto cleanup;
		}

		/* create answer for the client */

cleanup:
		if ( client_socket != SOCKET_ERROR ) {
			char *buf = NULL;
			int l_buf;

			create_packet ( &buf, &l_buf, &packet, res );
			fprintf ( packet.logfile, "create packet \n");fflush ( packet.logfile );
			int i;
			for(i=0;i<l_buf; i++) {
				fprintf ( packet.logfile, "%2X ",buf[i]);fflush ( packet.logfile );
			}
			fprintf ( packet.logfile, "\n");fflush ( packet.logfile );

			res = SSL_write ( ssl, buf, l_buf ) ;
			fprintf ( packet.logfile, "send %d\n", res);fflush ( packet.logfile );

			SSL_free (ssl);
			closesocket ( client_socket );

			if ( buf != NULL ) {
				free ( buf );
			}
			//SSL_CTX_free (ctx);
		}

		if ( packet.userdn != NULL ) {
			free ( packet.userdn );
		}
		if ( packet.pwd != NULL ) {
			free ( packet.pwd );
		}
		if ( packet.user_data != NULL ) {
			free ( packet.user_data );
		}
		if ( packet.pwd_data != NULL ) {
			free ( packet.pwd_data );
		}

	}

	return 0;
}

void WINAPI srv_ctrl_handler( DWORD fdwControl)
{
	switch (fdwControl) {
		case SERVICE_CONTROL_PAUSE:
			MyServiceStatus.dwCurrentState = SERVICE_PAUSED;
			break;

		case SERVICE_CONTROL_CONTINUE:
			MyServiceStatus.dwCurrentState = SERVICE_RUNNING;
			break;

		case SERVICE_CONTROL_STOP:
			MyServiceStatus.dwWin32ExitCode = 0;
			MyServiceStatus.dwCurrentState  = SERVICE_STOPPED;
			MyServiceStatus.dwCheckPoint    = 0;
			MyServiceStatus.dwWaitHint      = 0;

			if (!SetServiceStatus (MyServiceStatusHandle,
						&MyServiceStatus))
			{
			 	fprintf(stderr," [MY_SERVICE] SetServiceStatus error %ld\n",
						GetLastError());
			}

			fprintf(stderr," [MY_SERVICE] Leaving MyService \n",0);
			return;

		case SERVICE_CONTROL_INTERROGATE:
			break;

		default:
			fprintf(stderr," [MY_SERVICE] Unrecognized opcode %ld\n", fdwControl);
	}
	if (!SetServiceStatus (MyServiceStatusHandle,  &MyServiceStatus))
	{
		fprintf(stderr," [MY_SERVICE] SetServiceStatus error %ld\n", GetLastError());
	}
	return;
}


void WINAPI service_main ( DWORD argc, LPTSTR *argv)
{
	int res;
	SOCKET socket;
	SC_HANDLE schSCManager;
	SC_HANDLE hService = NULL;
	DWORD status;
	DWORD specificError;

	LPTSTR p_path_logfile;
	LPTSTR p_path_copypwd_exe;
	LPTSTR p_path_copypwd_in;
	LPTSTR p_path_copypwd_out;
	LPTSTR p_path_cert;
	LPTSTR p_path_key;

	schSCManager = OpenSCManager(
						NULL,                    // local machine
						NULL,                    // ServicesActive database
						SC_MANAGER_ALL_ACCESS);  // full access rights
	hService = OpenService(schSCManager, "UCS AD Connector", SERVICE_START);

	MyServiceStatus.dwServiceType        = SERVICE_WIN32;
	MyServiceStatus.dwCurrentState       = SERVICE_START_PENDING;
	MyServiceStatus.dwControlsAccepted   = SERVICE_ACCEPT_STOP;
	MyServiceStatus.dwWin32ExitCode      = 0;
	MyServiceStatus.dwServiceSpecificExitCode = 0;
	MyServiceStatus.dwCheckPoint         = 0;
	MyServiceStatus.dwWaitHint           = 0;

	MyServiceStatusHandle = RegisterServiceCtrlHandler(
			"UCS AD Connector",
			 srv_ctrl_handler);

	if (MyServiceStatusHandle == (SERVICE_STATUS_HANDLE)0)
	{
		printf(" RegisterServiceCtrlHandler failed %d\n", GetLastError());
		return;
	}
	MyServiceStatus.dwCurrentState       = SERVICE_RUNNING;
	MyServiceStatus.dwCheckPoint         = 0;
	MyServiceStatus.dwWaitHint           = 0;

	if (!SetServiceStatus (MyServiceStatusHandle, &MyServiceStatus))
	{
		status = GetLastError();
		printf(" SetServiceStatus failed %d\n", GetLastError());
	}
	p_path=(LPTSTR)malloc(MAX_PATH*sizeof(wchar_t));;
	p_path_logfile=(LPTSTR)malloc(MAX_PATH*sizeof(wchar_t));;
	p_path_copypwd_exe=(LPTSTR)malloc(MAX_PATH*sizeof(wchar_t));;
	p_path_copypwd_in=(LPTSTR)malloc(MAX_PATH*sizeof(wchar_t));;
	p_path_copypwd_out=(LPTSTR)malloc(MAX_PATH*sizeof(wchar_t));;
	p_path_cert=(LPTSTR)malloc(MAX_PATH*sizeof(wchar_t));;
	p_path_key=(LPTSTR)malloc(MAX_PATH*sizeof(wchar_t));;

	memset(p_path, 0, MAX_PATH);
	GetModuleFileName( NULL, p_path, MAX_PATH );
	PathRemoveFileSpec(p_path);

	wsprintf(p_path_logfile, "%s", p_path);
	PathAppend(p_path_logfile, ("ucs-ad-connector.log"));

	wsprintf(p_path_copypwd_exe, "%s", p_path);
	PathAppend(p_path_copypwd_exe, ("copypwd.exe"));

	wsprintf(p_path_copypwd_in, "%s", p_path);
	PathAppend(p_path_copypwd_in, ("copypwd.in.txt"));

	wsprintf(p_path_copypwd_out, "%s", p_path);
	PathAppend(p_path_copypwd_out, ("copypwd.txt"));

	wsprintf(p_path_cert, "%s", p_path);
	PathAppend(p_path_cert, ("cert.pem"));

	wsprintf(p_path_key, "%s", p_path);
	PathAppend(p_path_key, ("private.key"));

	wsprintf(path, "%s", p_path);
	wsprintf(path_logfile, "%s", p_path_logfile);
	wsprintf(path_copypwd_exe, "%s", p_path_copypwd_exe);
	wsprintf(path_copypwd_in, "%s", p_path_copypwd_in);
	wsprintf(path_copypwd_out, "%s", p_path_copypwd_out);
	wsprintf(path_cert, "%s", p_path_cert);
	wsprintf(path_key, "%s", p_path_key);

	free ( p_path_logfile );
	free ( p_path_copypwd_exe );
	free ( p_path_copypwd_in );
	free ( p_path_copypwd_out );
	free ( p_path_key );
	free ( p_path_cert );

	socket = network_init_ssl( 6670, &res );

	if ( socket == -1 ) {
		
		FILE *log_file;

		if ( (log_file = fopen( path_logfile, "a+" )) == NULL ) {
			fprintf( stderr, "Failed to open logfile ucs-ad-connector.log\n" );
		}

		fprintf ( log_file, "Failed to init ssl\n");

		fclose(log_file);

		return;

	}

	worker ( socket );

	return;
}

/****************************************************************************
 * Service Handling
 *
 * 	service_start
 * 	service_stop
 * 	service_install
 * 	service_remove
 *
 ****************************************************************************/

/****************************************************************************
 * Start the Service UCS AD Connector
 ****************************************************************************/
void service_start ( void )
{
	long err;
	
	SERVICE_TABLE_ENTRY   DispatchTable[] =
	{
		{ "UCS AD Connector", service_main      },
		{ NULL,              NULL          }
	};

	if (!StartServiceCtrlDispatcher( DispatchTable))
	{
		err=GetLastError();

		fprintf(stderr, " [UCS AD Connector] StartServiceCtrlDispatcher (%ld)\n", err);

		if ( err == ERROR_FAILED_SERVICE_CONTROLLER_CONNECT ) {
			fprintf ( stderr, "ERROR_FAILED_SERVICE_CONTROLLER_CONNECT\n");
		} else if ( err == ERROR_INVALID_DATA ) {
			fprintf ( stderr, "ERROR_INVALID_DATA\n");
		} else if ( err == ERROR_SERVICE_ALREADY_RUNNING ) {
			fprintf ( stderr, "ERROR_SERVICE_ALREADY_RUNNING\n");
		}
	}
}

/****************************************************************************
 * Install the service
 * 	-> Verwaltung
 * 	-> Dienste
 * 	-> UCS AD Connectot
 ****************************************************************************/
int service_install ( void )
{
	SC_HANDLE schSCManager;
	SC_HANDLE schService;
	TCHAR szPath[MAX_PATH];

	if( !GetModuleFileName( NULL, szPath, MAX_PATH ) )
	{
		printf("GetModuleFileName failed (%d)\n", GetLastError());
		return FALSE;
	}
	/* Open a handle to the SC Manager database. */
	schSCManager = OpenSCManager(
						NULL,                    /* local machine           */
						NULL,                    /* ServicesActive database */
						SC_MANAGER_ALL_ACCESS);  /* full access rights      */

	if (NULL == schSCManager)  {
		fprintf(stderr, "OpenSCManager failed (%d)\n", GetLastError());
		return FALSE;
	}

	schService = CreateService(
			schSCManager,              // SCManager database
			TEXT("UCS AD Connector"),  // name of service
			"UCS AD Connector",           // service name to display
			SERVICE_ALL_ACCESS,        // desired access
			SERVICE_WIN32_OWN_PROCESS, // service type
			SERVICE_DEMAND_START,      // start type
			SERVICE_ERROR_NORMAL,      // error control type
			szPath,                    // path to service's binary
			NULL,                      // no load ordering group
			NULL,                      // no tag identifier
			NULL,                      // no dependencies
			NULL,                      // LocalSystem account
			NULL);                     // no password

	if (schService == NULL)
	{
		printf("CreateService failed (%d)\n", GetLastError());
		return FALSE;
	}
	else
	{
		CloseServiceHandle(schService);
		return TRUE;
	}
}

void service_remove ( void )
{
	SC_HANDLE hSCM = NULL;
	SC_HANDLE hService = NULL;
	BOOL bSuccess = FALSE;

	hSCM = OpenSCManager(NULL, NULL, SC_MANAGER_CONNECT);
	if(!hSCM)
	{
		printf("Error: OpenSCManager");
		return;
	}

	hService = OpenService(hSCM, "UCS AD Connector", DELETE);
	if(!hService)
	{
		printf("Error: OpenService");
		CloseServiceHandle(hSCM);
		return;
	}

	bSuccess = DeleteService(hService);
	if(bSuccess) {
		printf("UCS AD Connector Removed\n");
	} else {
		printf("Error: DeleteService");
	}

	CloseServiceHandle(hService);
	CloseServiceHandle(hSCM);

	return;
}

void service_stop ( void )
{
	printf("Service Stop\n");
}

void usage ( char *cmd )
{
	printf("Usage: %s options\n", cmd);
	printf("Options:\n");
	printf("            -install\n");
	printf("            -remove\n");
	printf("            -start\n");
	printf("            -stop\n");
}

int main ( int argc, char **argv )
{

	if ( argc > 1 ) {
		if(!strcmp(argv[1], ("-install"))) {
			service_install();
		} else if(!strcmp(argv[1], ("-remove"))) {
			service_remove();
		} else if(!strcmp(argv[1], ("-start"))) {
			service_start();
		} else if(!strcmp(argv[1], ("-stop"))) {
			service_stop();
		} else {
			usage(argv[0]);
			return 1;
		}
	} else {
		service_start();
	}

	return 0;
}

