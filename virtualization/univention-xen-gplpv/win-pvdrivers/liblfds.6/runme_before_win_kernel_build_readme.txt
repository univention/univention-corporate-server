The Windows kernel build environment is primitive and has a number
of severe limitations; in particular, all source files must be in
one directory and it is not possible to choose the output binary type
(static or dynamic library) from the build command line; rather,
a string has to be modified in a text file used by the build (!)

To deal with these limitations, it is necessary for a Windows kernel
build to run a batch file prior to building.

There are two batch files, one for static library builds and the other
for dynamic library builds.

They are both idempotent; you can run them as often as you like and
switch between them as often as you want.  It's all fine; whenever
you run one of them, it will take you from whatever state you were
previously in, into the state you want to be in.

Both batch files copy all the sources file into a single directory,
"/src/single_dir_for_windows_kernel/".

The static library batch file will then copy "/sources.static" into
"/src/single_dir_for_windows_kernel/", which will cause a static
library to be built.

The dynamic library batch file will then copy "/sources.dynamic" into
"/src/single_dir_for_windows_kernel/", which will cause a dynamic
library to be built.  It will also copy "src/driver_entry.c" into
"/src/single_dir_for_windows_kernel/", since the linker requires
the DriverEntry function to exist for dynamic libraries, even
though it's not used.


