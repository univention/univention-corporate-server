// SPDX-FileCopyrightText: 2026 Univention GmbH
// SPDX-License-Identifier: AGPL-3.0-only

extern crate bindgen;

use std::env;
use std::path::PathBuf;

fn find_header() -> PathBuf {
    let candidates = [
        "include/univention/config.h",
        "../include/univention/config.h",
        "/usr/include/univention/config.h",
    ];

    candidates
        .iter()
        .map(PathBuf::from)
        .find(|p| p.exists())
        .expect("univention/config.h not found")
}

fn main() {
    println!("cargo:rustc-link-search=native=/usr/lib/x86_64-linux-gnu");
    println!("cargo:rustc-link-lib=univentionconfig");
    println!("cargo:rerun-if-changed=build.rs");

    let header = find_header();

    let builder = bindgen::Builder::default().header(header.to_str().unwrap());

    let bindings = builder
        // .header("/usr/include/univention/config.h")
        .clang_arg(format!("-Iinclude"))
        .clang_arg(format!("-I/usr/include"))
        .allowlist_function("univention_config.*")
        .parse_callbacks(Box::new(bindgen::CargoCallbacks))
        .generate()
        .expect("Unable to generate UCR bindings");

    let out_path = PathBuf::from(env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out_path.join("bindings.rs"))
        .expect("Couldn't write UCR bindings");
}
