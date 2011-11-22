#pragma warning(disable: 4201)
#include <windows.h>
#include <basetyps.h>
#include <stdlib.h>
#include <wtypes.h>
#include <initguid.h>
#include <stdio.h>
#include <string.h>
#include <winioctl.h>
#include <setupapi.h>
#include <ctype.h>
#include <powrprof.h>
#include <strsafe.h>

#define SERVICE_ID "ShutdownMon"
#define SERVICE_NAME "Xen Shutdown Monitor"

#define OLD_SERVICE_ID "XenShutdownMon"

DEFINE_GUID(GUID_XENBUS_IFACE, 0x14ce175a, 0x3ee2, 0x4fae, 0x92, 0x52, 0x0, 0xdb, 0xd8, 0x4f, 0x1, 0x8e);

enum xsd_sockmsg_type
{
    XS_DEBUG,
    XS_DIRECTORY,
    XS_READ,
    XS_GET_PERMS,
    XS_WATCH,
    XS_UNWATCH,
    XS_TRANSACTION_START,
    XS_TRANSACTION_END,
    XS_INTRODUCE,
    XS_RELEASE,
    XS_GET_DOMAIN_PATH,
    XS_WRITE,
    XS_MKDIR,
    XS_RM,
    XS_SET_PERMS,
    XS_WATCH_EVENT,
    XS_ERROR,
    XS_IS_DOMAIN_INTRODUCED,
    XS_RESUME,
    XS_SET_TARGET
};

struct xsd_sockmsg
{
    ULONG type;  /* XS_??? */
    ULONG req_id;/* Request identifier, echoed in daemon's response.  */
    ULONG tx_id; /* Transaction id (0 if not related to a transaction). */
    ULONG len;   /* Length of data following this. */

    /* Generally followed by nul-terminated string(s). */
};
SERVICE_STATUS service_status; 
SERVICE_STATUS_HANDLE hStatus; 

static void
install_service()
{
  SC_HANDLE manager_handle;
  SC_HANDLE service_handle;
  TCHAR path[MAX_PATH];
  TCHAR command_line[MAX_PATH + 10];

  if(!GetModuleFileName(NULL, path, MAX_PATH))
  {
    printf("Cannot install service (%d)\n", GetLastError());
    return;
  }

  StringCbPrintf(command_line, MAX_PATH + 10, "\"%s\" -s", path);
  manager_handle = OpenSCManager(NULL, NULL, SC_MANAGER_ALL_ACCESS);
 
  if (!manager_handle)
  {
    printf("OpenSCManager failed (%d)\n", GetLastError());
    return;
  }

  service_handle = CreateService( 
    manager_handle, SERVICE_ID, SERVICE_NAME, SERVICE_ALL_ACCESS,
    SERVICE_WIN32_OWN_PROCESS, SERVICE_AUTO_START,
    SERVICE_ERROR_NORMAL, command_line, NULL, NULL, NULL, NULL, NULL);
 
  if (!service_handle) 
  {
    printf("CreateService failed (%d)\n", GetLastError()); 
    CloseServiceHandle(manager_handle);
    return;
  }

  printf("Service installed\n"); 

  CloseServiceHandle(service_handle); 
  CloseServiceHandle(manager_handle);
}

static void
remove_old_service()
{
  SC_HANDLE manager_handle;
  SC_HANDLE service_handle;

  manager_handle = OpenSCManager(NULL, NULL, SC_MANAGER_ALL_ACCESS);
 
  if (!manager_handle)
  {
    printf("OpenSCManager failed (%d)\n", GetLastError());
    return;
  }

  service_handle = OpenService(manager_handle, OLD_SERVICE_ID, DELETE);
 
  if (!service_handle) 
  {
    printf("OpenService failed (%d)\n", GetLastError()); 
    CloseServiceHandle(manager_handle);
    return;
  }

  if (!DeleteService(service_handle))
  {
    printf("DeleteService failed (%d)\n", GetLastError()); 
    CloseServiceHandle(service_handle); 
    CloseServiceHandle(manager_handle);
    return;
  }

  printf("Old Service removed\n"); 

  CloseServiceHandle(service_handle); 
  CloseServiceHandle(manager_handle);
}

static void
remove_service()
{
  SC_HANDLE manager_handle;
  SC_HANDLE service_handle;

  manager_handle = OpenSCManager(NULL, NULL, SC_MANAGER_ALL_ACCESS);
 
  if (!manager_handle)
  {
    printf("OpenSCManager failed (%d)\n", GetLastError());
    return;
  }

  service_handle = OpenService(manager_handle, SERVICE_ID, DELETE);
 
  if (!service_handle) 
  {
    printf("OpenService failed (%d)\n", GetLastError()); 
    CloseServiceHandle(manager_handle);
    return;
  }

  if (!DeleteService(service_handle))
  {
    printf("DeleteService failed (%d)\n", GetLastError()); 
    CloseServiceHandle(service_handle); 
    CloseServiceHandle(manager_handle);
    return;
  }

  printf("Service removed\n"); 

  CloseServiceHandle(service_handle); 
  CloseServiceHandle(manager_handle);
}

static void
do_hibernate()
{
  HANDLE proc_handle = GetCurrentProcess();
  TOKEN_PRIVILEGES *tp;
  HANDLE token_handle;

  printf("proc_handle = %p\n", proc_handle);

  if (!OpenProcessToken(proc_handle, TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, &token_handle))
  {
    printf("OpenProcessToken failed\n");
    return;
  }
  printf("token_handle = %p\n", token_handle);

  tp = malloc(sizeof(TOKEN_PRIVILEGES) + sizeof(LUID_AND_ATTRIBUTES));
  tp->PrivilegeCount = 1;
  if (!LookupPrivilegeValueA(NULL, SE_SHUTDOWN_NAME, &tp->Privileges[0].Luid))
  {
    printf("LookupPrivilegeValue failed\n");
    CloseHandle(token_handle);
    return;
  }

  tp->Privileges[0].Attributes = SE_PRIVILEGE_ENABLED;
  if (!AdjustTokenPrivileges(token_handle, FALSE, tp, 0, NULL, NULL))
  {
    CloseHandle(token_handle);
    return;
  }

  if (!SetSuspendState(TRUE, FALSE, FALSE))
  {
    printf("hibernate failed\n");
  }

  CloseHandle(token_handle);
}

static void
do_shutdown(BOOL bRebootAfterShutdown)
{
  HANDLE proc_handle = GetCurrentProcess();
  TOKEN_PRIVILEGES *tp;
  HANDLE token_handle;

  printf("proc_handle = %p\n", proc_handle);

  if (!OpenProcessToken(proc_handle, TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, &token_handle))
  {
    printf("OpenProcessToken failed\n");
    return;
  }
  printf("token_handle = %p\n", token_handle);

  tp = malloc(sizeof(TOKEN_PRIVILEGES) + sizeof(LUID_AND_ATTRIBUTES));
  tp->PrivilegeCount = 1;
  if (!LookupPrivilegeValueA(NULL, SE_SHUTDOWN_NAME, &tp->Privileges[0].Luid))
  {
    printf("LookupPrivilegeValue failed\n");
    CloseHandle(token_handle);
    return;
  }

  tp->Privileges[0].Attributes = SE_PRIVILEGE_ENABLED;
  if (!AdjustTokenPrivileges(token_handle, FALSE, tp, 0, NULL, NULL))
  {
    CloseHandle(token_handle);
    return;
  }

  if (!InitiateSystemShutdownEx(NULL, NULL, 0, TRUE, bRebootAfterShutdown, SHTDN_REASON_FLAG_PLANNED | SHTDN_REASON_MAJOR_OTHER | SHTDN_REASON_MINOR_OTHER))
  {
    printf("InitiateSystemShutdownEx failed\n");
    // Log a message to the system log here about a failed shutdown
  }
  printf("InitiateSystemShutdownEx succeeded\n");

  CloseHandle(token_handle);
}

static char *
get_xen_interface_path()
{
  HDEVINFO handle;
  SP_DEVICE_INTERFACE_DATA sdid;
  SP_DEVICE_INTERFACE_DETAIL_DATA *sdidd;
  DWORD buf_len;
  char *path;

  handle = SetupDiGetClassDevs(&GUID_XENBUS_IFACE, 0, NULL, DIGCF_PRESENT | DIGCF_DEVICEINTERFACE);
  if (handle == INVALID_HANDLE_VALUE)
  {
    printf("SetupDiGetClassDevs failed\n"); 
    return NULL;
  }
  sdid.cbSize = sizeof(sdid);
  if (!SetupDiEnumDeviceInterfaces(handle, NULL, &GUID_XENBUS_IFACE, 0, &sdid))
  {
    printf("SetupDiEnumDeviceInterfaces failed\n");
    return NULL;
  }
  SetupDiGetDeviceInterfaceDetail(handle, &sdid, NULL, 0, &buf_len, NULL);
  sdidd = malloc(buf_len);
  sdidd->cbSize = sizeof(SP_DEVICE_INTERFACE_DETAIL_DATA);
  if (!SetupDiGetDeviceInterfaceDetail(handle, &sdid, sdidd, buf_len, NULL, NULL))
  {
    printf("SetupDiGetDeviceInterfaceDetail failed\n"); 
    return NULL;
  }
  
  path = malloc(strlen(sdidd->DevicePath) + 1);
  StringCbCopyA(path, strlen(sdidd->DevicePath) + 1, sdidd->DevicePath);
  free(sdidd);
  
  return path;
}

static int
xb_add_watch(HANDLE handle, char *path)
{
  char buf[1024];
  struct xsd_sockmsg *msg;
  DWORD bytes_written;
  DWORD bytes_read;
  char *token = "0";

  msg = (struct xsd_sockmsg *)buf;
  msg->type = XS_WATCH;
  msg->req_id = 0;
  msg->tx_id = 0;
  msg->len = (ULONG)(strlen(path) + 1 + strlen(token) + 1);
  StringCbCopyA(buf + sizeof(*msg), 1024 - sizeof(*msg), path);
  StringCbCopyA(buf + sizeof(*msg) + strlen(path) + 1, 1024 - sizeof(*msg) - strlen(path) - 1, token);

  if (!WriteFile(handle, buf, sizeof(*msg) + msg->len, &bytes_written, NULL))
  {
    printf("write failed\n");
    return 0;
  }
  if (!ReadFile(handle, buf, 1024, &bytes_read, NULL))
  {
    printf("read failed\n");
    return 0;
  }
  printf("bytes_read = %d\n", bytes_read);
  printf("msg->len = %d\n", msg->len);
  buf[sizeof(*msg) + msg->len] = 0;
  printf("msg text = %s\n", buf + sizeof(*msg));

  return 1;
}

static int
xb_wait_event(HANDLE handle)
{
  char buf[1024];
  struct xsd_sockmsg *msg;
  DWORD bytes_read;

printf("wait_event start\n");
  msg = (struct xsd_sockmsg *)buf;
  if (!ReadFile(handle, buf, 1024, &bytes_read, NULL))
  {
    printf("read failed\n");
    return 0;
  }
  printf("bytes_read = %d\n", bytes_read);
  printf("msg->len = %d\n", msg->len);
  buf[sizeof(*msg) + msg->len] = 0;
  printf("msg text = %s\n", buf + sizeof(*msg));
  return 1;
}

static char *
xb_read(HANDLE handle, char *path)
{
  char buf[1024];
  struct xsd_sockmsg *msg;
  char *ret;
  DWORD bytes_written;
  DWORD bytes_read;

printf("read start\n");
  msg = (struct xsd_sockmsg *)buf;
  msg->type = XS_READ;
  msg->req_id = 0;
  msg->tx_id = 0;
  msg->len = (ULONG)(strlen(path) + 1);
  StringCbCopyA(buf + sizeof(*msg), 1024 - sizeof(*msg), path);

  if (!WriteFile(handle, buf, sizeof(*msg) + msg->len, &bytes_written, NULL))
  {
    printf("write failed\n");
    return NULL;
  }

  if (!ReadFile(handle, buf, 1024, &bytes_read, NULL))
  {
    printf("read failed\n");
    return NULL;
  }
  printf("bytes_read = %d\n", bytes_read);
  printf("msg->len = %d\n", msg->len);
  buf[sizeof(*msg) + msg->len] = 0;
  printf("msg text = %s\n", buf + sizeof(*msg));
  ret = malloc(strlen(buf + sizeof(*msg)) + 1);
  StringCbCopyA(ret, 1024 - sizeof(*msg), buf + sizeof(*msg));
  return ret;
}

static void
do_monitoring()
{
  HANDLE handle;
  int state;
  char *path;
  char *buf;

  path = get_xen_interface_path();
  if (path == NULL)
    return;

  handle = CreateFile(path, FILE_GENERIC_READ|FILE_GENERIC_WRITE, 0, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);

  xb_add_watch(handle, "control/shutdown");

  state = 0;
  while(xb_wait_event(handle))
  {
    if (service_status.dwCurrentState != SERVICE_RUNNING)
      return;
    buf = xb_read(handle, "control/shutdown");

    //printf("msg = '%s'\n", msg);
    if (strcmp("poweroff", buf) == 0 || strcmp("halt", buf) == 0)
    {
      do_shutdown(FALSE);
    }
    else if (strcmp("reboot", buf) == 0)
    {
      do_shutdown(TRUE);
    } 
    else if (strcmp("hibernate", buf) == 0)
    {
      do_hibernate();
    } 
  }
}

void control_handler(DWORD request) 
{ 
  switch(request) 
  { 
    case SERVICE_CONTROL_STOP: 
      service_status.dwWin32ExitCode = 0; 
      service_status.dwCurrentState = SERVICE_STOPPED; 
      SetServiceStatus (hStatus, &service_status);
      return; 
 
    case SERVICE_CONTROL_SHUTDOWN: 
      service_status.dwWin32ExitCode = 0; 
      service_status.dwCurrentState = SERVICE_STOPPED; 
      SetServiceStatus (hStatus, &service_status);
      return; 

    default:
      break;
  } 
 
  SetServiceStatus (hStatus, &service_status);

  return; 
}

void service_main(int argc, char *argv[]) 
{ 
  UNREFERENCED_PARAMETER (argc);
  UNREFERENCED_PARAMETER (argv);

  printf("Entering service_main\n"); 

  service_status.dwServiceType = SERVICE_WIN32; 
  service_status.dwCurrentState =  SERVICE_START_PENDING; 
  service_status.dwControlsAccepted = SERVICE_ACCEPT_STOP | SERVICE_ACCEPT_SHUTDOWN;
  service_status.dwWin32ExitCode = 0; 
  service_status.dwServiceSpecificExitCode = 0; 
  service_status.dwCheckPoint = 0; 
  service_status.dwWaitHint = 0; 
 
  hStatus = RegisterServiceCtrlHandler(SERVICE_ID, (LPHANDLER_FUNCTION)control_handler); 
  if (hStatus == (SERVICE_STATUS_HANDLE)0) 
  { 
    printf("RegisterServiceCtrlHandler failed\n"); 
    return; 
  }  

  service_status.dwCurrentState = SERVICE_RUNNING; 
  SetServiceStatus(hStatus, &service_status);

  do_monitoring();

  printf("All done\n"); 

  return; 
}


static void
print_usage(char *name)
{
  printf("Usage:\n");
  printf("  %s <options>\n", name);
  printf("\n");
  printf("Options:\n");
  printf(" -d run in foreground\n");
  printf(" -s run as service\n");
  printf(" -i install service\n");
  printf(" -u uninstall service\n");
  printf(" -o remove the old .NET service\n");
}

int __cdecl
main(
    __in ULONG argc,
    __in_ecount(argc) PCHAR argv[]
)
{
  SERVICE_TABLE_ENTRY service_table[2];

  if (argc == 0)
  {
    print_usage("shutdownmon");
    return 1;
  }
  if (argc != 2 || (argc == 2 && (strlen(argv[1]) != 2 || argv[1][0] != '-')))
  {
    print_usage(argv[0]);
    return 1;
  }

  switch(argv[1][1])
  {
  case 'd':
    service_status.dwCurrentState = SERVICE_RUNNING;
    do_monitoring();
    break;
  case 's':
    service_table[0].lpServiceName = SERVICE_ID;
    service_table[0].lpServiceProc = (LPSERVICE_MAIN_FUNCTION)service_main;

    service_table[1].lpServiceName = NULL;
    service_table[1].lpServiceProc = NULL;

    StartServiceCtrlDispatcher(service_table);
    break;
  case 'i':
    install_service();
    break;
  case 'u':
    remove_service();
    break;
  case 'o':
    remove_old_service();
    break;
  default:
    print_usage(argv[0]);
    return 1;
  }
  return 0;
}

