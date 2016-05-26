if ((gwmi win32_computersystem).partofdomain -eq $true) {
    write-host (gwmi win32_computersystem).domain
    exit 0
}
exit 1
