// SPDX-FileCopyrightText: 2026 Univention GmbH
// SPDX-License-Identifier: AGPL-3.0-only

extern crate bindgen;

use std::env;
use std::path::PathBuf;

fn find_header() -> PathBuf {
    let candidates = [
        "include/univention/ldap.h",
        "../include/univention/ldap.h",
        "/usr/include/univention/ldap.h",
    ];

    candidates
        .iter()
        .map(PathBuf::from)
        .find(|p| p.exists())
        .expect("univention/ldap.h not found")
}

fn main() {
    println!("cargo:rustc-link-search=native=/usr/lib/x86_64-linux-gnu");
    println!("cargo:rustc-link-lib=univentionpolicy");
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rustc-link-lib=lber");
    println!("cargo:rustc-link-lib=ldap");

    let header = find_header();

    let builder = bindgen::Builder::default().header(header.to_str().unwrap());

    let bindings = builder
        // .header("/usr/include/univention/ldap.h")
        .clang_arg(format!("-Iinclude"))
        .clang_arg(format!("-I/usr/include"))
        .header("/usr/include/ldap.h")
        .allowlist_function("univention_ldap.*")
        .allowlist_type("univention_ldap_parameters_s")
        .allowlist_type("univention_ldap_parameters_t")
        .allowlist_function("ldap_search_ext_s")
        .allowlist_function("ldap_first_entry")
        .allowlist_function("ldap_next_entry")
        .allowlist_function("ldap_get_dn")
        .allowlist_function("ldap_first_attribute")
        .allowlist_function("ldap_next_attribute")
        .allowlist_function("ldap_get_values_len")
        .allowlist_function("ldap_value_free_len")
        .allowlist_function("ldap_msgfree")
        .allowlist_function("ldap_memfree")
        .allowlist_function("ber_free")
        .allowlist_type("LDAPMessage")
        .allowlist_type("berelement")
        .allowlist_type("berval")
        .allowlist_var("LDAP_SUCCESS")
        // .allowlist_var("LDAP_SCOPE_BASE")
        // .allowlist_var("LDAP_SCOPE_ONELEVEL")
        // .allowlist_var("LDAP_SCOPE_SUBTREE")
        // .default_macro_constant_type(bindgen::MacroTypeVariation::Signed)
        .parse_callbacks(Box::new(bindgen::CargoCallbacks))
        .generate()
        .expect("Unable to generate UCR bindings");

    let out_path = PathBuf::from(env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out_path.join("bindings.rs"))
        .expect("Couldn't write UCR bindings");
}
