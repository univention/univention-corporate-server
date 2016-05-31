name = 'get_domain_name'
description = 'check if system is part of domain and return domain name'
ps = '''
if ((gwmi win32_computersystem).partofdomain -eq $true) {
    write-host (gwmi win32_computersystem).domain
    exit 0
}
exit 1
'''
