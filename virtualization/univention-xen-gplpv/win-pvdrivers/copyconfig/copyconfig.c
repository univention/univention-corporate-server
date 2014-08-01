#pragma warning(disable: 4201)
#include <basetyps.h>
#include <stdlib.h>
#include <wtypes.h>
#include <initguid.h>
#include <stdio.h>
#include <string.h>
#include <winioctl.h>
#include <ntddndis.h>
#include <strsafe.h>

#define ADAPTER_TYPE_XEN
#define ADAPTER_TYPE_OTHER

#define ARRAY_SIZE(x) (sizeof(x) / sizeof((x)[0]))

typedef struct adapter_details
{
  struct adapter_details *next;
  BYTE mac_address[6];
  CHAR xen_IpConfig_key_name[1024];
  CHAR other_IpConfig_key_name[1024];
} adapter_details_t;

int __cdecl
main(
//    __in ULONG argc,
//    __in_ecount(argc) PCHAR argv[]
)
{
  HKEY key_handle;
  HKEY adapter_key_handle;
  LONG status;
  CHAR adapter_key_name[256];
  BYTE buf[1024];
  DWORD buf_len;
  CHAR *keyptr;
  HANDLE handle;
  CHAR filename[256];
  NDIS_STATISTICS_VALUE oid_req;
  int i;
  adapter_details_t *list_head = NULL, *prev;
  adapter_details_t *adapter;
  CHAR value_name[256];
  DWORD value_name_len;
  DWORD value_type;
  PCHAR value_data;
  DWORD value_data_len;
  DWORD value_data_max_len;
  HKEY src_key_handle;
  HKEY dst_key_handle;
  
  // Enumerate keys in \\Registry\\Machine\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Adapters
  status = RegOpenKey(HKEY_LOCAL_MACHINE, "SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Adapters", &key_handle);
  if (status != ERROR_SUCCESS)
  {
    fprintf(stderr, "Cannot read registry - status = %08x\n", status);
    return 1;
  }
  printf("Enumerating adapters\n");
  buf_len = 39;
  for (i = 0; (status = RegEnumKeyEx(key_handle, i, adapter_key_name, &buf_len, NULL, NULL, NULL, NULL)) != ERROR_NO_MORE_ITEMS; buf_len = 39, i++)
  {
    if (status == ERROR_MORE_DATA)
      continue; /* if the key is longer than a GUID then we aren't interested in it anyway */
    if (status != ERROR_SUCCESS)
      break;
    //printf("buf_len = %d, buf = %s\n", buf_len, buf);
    if (buf_len != 38)
      continue;
    /* check that the name looks like a guid */
    StringCbPrintfA(filename, ARRAY_SIZE(filename), "\\\\.\\%s", adapter_key_name);
    handle = CreateFile(filename, FILE_GENERIC_READ, 0, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (!handle)
      continue;
    oid_req.Oid = OID_802_3_PERMANENT_ADDRESS;
    oid_req.DataLength = 10;
    status = DeviceIoControl(handle, IOCTL_NDIS_QUERY_GLOBAL_STATS, &oid_req, sizeof(NDIS_STATISTICS_VALUE), buf, 256, &buf_len, NULL);
    if (!status || buf_len != 6)
      continue;
    if (buf[0] == 0 && buf[1] == 0 && buf[2] == 0 && buf[3] == 0 && buf[4] == 0 && buf[5] == 0)
      continue;
    printf("Found Adapter:\n MAC = %02x:%02x:%02x:%02x:%02x:%02x\n",
      buf[0], buf[1], buf[2],
      buf[3], buf[4], buf[5]);
    for (adapter = list_head, prev = NULL; adapter != NULL; prev = adapter, adapter = adapter->next)
    {
      if (memcmp(adapter->mac_address, buf, 6) == 0)
        break;
    }
    if (!adapter)
    {
      adapter = malloc(sizeof(adapter_details_t));
      if (prev == NULL)
        list_head = adapter;
      else
        prev->next = adapter;
      adapter->next = NULL;
      memcpy(adapter->mac_address, buf, 6);
      adapter->xen_IpConfig_key_name[0] = 0;
      adapter->other_IpConfig_key_name[0] = 0;
    }

    oid_req.Oid = OID_GEN_VENDOR_DESCRIPTION;
    oid_req.DataLength = 256;
    status = DeviceIoControl(handle, IOCTL_NDIS_QUERY_GLOBAL_STATS, &oid_req, sizeof(NDIS_STATISTICS_VALUE), buf, 256, &buf_len, NULL);
    if (!status)
    {
      printf(" Error opening. Ignoring\n");
      continue;
    }
    printf(" Description = %s\n", buf);
    if (strstr((char *)buf, "Xen"))
    {
      printf(" Type = Xen\n");
      keyptr = adapter->xen_IpConfig_key_name;
    }
    else
    {
      printf(" Type = Other\n");
      keyptr = adapter->other_IpConfig_key_name;
    }
    if (keyptr[0])
    {
      printf(" Multiple Other or multiple Xen adapters exist with the same mac. Ignoring.\n");
      continue;
    }
    buf_len = 1024;
    
    status = RegOpenKey(key_handle, adapter_key_name, &adapter_key_handle);
    if (status != ERROR_SUCCESS)
    {
      printf(" Failed to read registry (%08x). Ignoring.\n", status);
      continue;
    }
    status = RegQueryValueEx(adapter_key_handle, "IpConfig", NULL, NULL, (LPBYTE)keyptr, &buf_len);
    if (status != ERROR_SUCCESS)
    {
      printf(" Failed to read registry (%08x). Ignoring.\n", status);
      continue;
    }
  }

  printf("\nCloning IP Configurations\n");
  for (adapter = list_head; adapter != NULL; adapter = adapter->next)
  {
    printf("Considering MAC = %02x:%02x:%02x:%02x:%02x:%02x\n",
      adapter->mac_address[0], adapter->mac_address[1], adapter->mac_address[2],
      adapter->mac_address[3], adapter->mac_address[4], adapter->mac_address[5]);
    if (adapter->xen_IpConfig_key_name[0])
      printf(" Xen adapter present\n");
    else
      printf(" Xen adapter not present\n");
    if (adapter->other_IpConfig_key_name[0])
      printf(" Other adapter present\n");
    else
      printf(" Other adapter not present\n");
    
    if (adapter->xen_IpConfig_key_name[0] && adapter->other_IpConfig_key_name[0])
    {
      // open HKLM\SYSTEM\Services\%s
      StringCbPrintfA((char *)buf, ARRAY_SIZE(buf), "SYSTEM\\CurrentControlSet\\Services\\%s", adapter->xen_IpConfig_key_name);
      status = RegOpenKey(HKEY_LOCAL_MACHINE, (LPCSTR)buf, &dst_key_handle);
      if (status != ERROR_SUCCESS)
      {
        printf(" Cannot open Xen adapter config key. Skipping.\n");
        continue;
      }
      StringCbPrintfA((char *)buf, ARRAY_SIZE(buf), "SYSTEM\\CurrentControlSet\\Services\\%s", adapter->other_IpConfig_key_name);
      status = RegOpenKey(HKEY_LOCAL_MACHINE, (LPCSTR)buf, &src_key_handle);
      if (status != ERROR_SUCCESS)
      {
        printf(" Cannot open Other adapter config key. Skipping.\n");
        continue;
      }
      value_name_len = 256;
      value_data_max_len = 0;
      value_data = NULL;
      value_data_len = 0;
      while ((status = RegEnumValue(dst_key_handle, 0, value_name, &value_name_len, NULL, &value_type, (LPBYTE)value_data, &value_data_len)) != ERROR_NO_MORE_ITEMS)
      {
        //printf("A status = %08x, value_data_max_len = %d, value_data_len = %d\n", status, value_data_max_len, value_data_len);
        if (value_data_len > value_data_max_len || status == ERROR_MORE_DATA)
        {
          //printf("A Buffer %d too small. Allocating %d bytes\n", value_data_max_len, value_data_len);
          if (value_data != NULL)
            free(value_data);
          value_data_max_len = value_data_len;
          value_data = malloc(value_data_max_len);
        }
        else if (status != ERROR_SUCCESS)
        {
          printf("Failed to read registry %08x\n", status);
          return 1;
        }
        else
        {
          RegDeleteValue(dst_key_handle, value_name);
        }
        value_name_len = 256;
        value_data_len = value_data_max_len;
      }
      i = 0;
      value_name_len = 256;
      value_data_len = value_data_max_len;
      while ((status = RegEnumValue(src_key_handle, i, value_name, &value_name_len, NULL, &value_type, (LPBYTE)value_data, &value_data_len)) != ERROR_NO_MORE_ITEMS)
      {
        //printf("B status = %08x, value_data_max_len = %d, value_data_len = %d\n", status, value_data_max_len, value_data_len);
        if (value_data_len > value_data_max_len || status == ERROR_MORE_DATA)
        {
          //printf("B Buffer %d too small. Allocating %d bytes\n", value_data_max_len, value_data_len);
          if (value_data != NULL)
            free(value_data);
          value_data_max_len = value_data_len;
          value_data = malloc(value_data_max_len);
        }
        else if (status != ERROR_SUCCESS)
        {
          printf("Failed to read registry %08x\n", status);
          return 1;
        }
        else
        {
          RegSetValueEx(dst_key_handle, value_name, 0, value_type, (BYTE *)value_data, value_data_len);
          i++;
        }
        value_name_len = 256;
        value_data_len = value_data_max_len;
      }
      printf(" Copied\n", buf);
    }
  }
  return 0;
  
  // loop through key names that look like GUIDs
  //   get OID_GEN_VENDOR_DESCRIPTION
  //   if description does not contain "RTL8139" then continue to next key name
  //   get OID_802_3_PERMANENT_ADDRESS
  //   get IpConfig path value registry
  //   again loop through key names that look like GUIDs
  //     if description does not contain "xen" then continue to next key name
  //     get IpConfig path value from registry
  //     delete contents of above path
  //     copy contents of RTL8139 IpConfig to Xen IpConfig (use RegCopyTree)
}

