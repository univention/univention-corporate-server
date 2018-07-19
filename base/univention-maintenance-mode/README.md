Univention Maintenance Mode
===========================

How to build:

1. Fire up a UCS 4.3 machine
2. Copy this directory on that machine and login via ssh, change to the directory
3. docker run -v $PWD:/volume -t clux/muslrust cargo build --release
4. Use target/x86_64-unknown-linux-musl/release/maintenance as the binary
