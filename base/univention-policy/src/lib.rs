// SPDX-FileCopyrightText: 2026 Univention GmbH
// SPDX-License-Identifier: AGPL-3.0-only

#![allow(
    non_upper_case_globals,
    non_camel_case_types,
    non_snake_case,
    dead_code
)]

include!(concat!(env!("OUT_DIR"), "/bindings.rs"));

use libc::c_char;
use std::collections::HashMap;
use std::ffi::{CStr, CString};
use std::ptr;

use univentionconfig::ConfigRegistry;

// LDAP_SCOPE_* is defined in ldap.h as ((ber_int_t) 0x0000)
// bindgen cannot parse macros with C casts, so we define it manually.
const LDAP_SCOPE_BASE: i32 = 0x0000;
const LDAP_SCOPE_ONELEVEL: i32 = 0x0001;
const LDAP_SCOPE_SUBTREE: i32 = 0x0002;

pub struct LdapError(pub String);

impl std::fmt::Display for LdapError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "LDAP error: {}", self.0)
    }
}

pub struct LdapEntry {
    pub dn: String,
    pub attributes: HashMap<String, Vec<Vec<u8>>>,
}

pub struct LdapConnection {
    lp: *mut univention_ldap_parameters_t,
}

unsafe impl Send for LdapConnection {}

fn read_secret(path: &str) -> Result<String, LdapError> {
    let secret = std::fs::read_to_string(path).map_err(|e| LdapError(format!("Cannot read {}: {}", path, e)))?;
    Ok(secret.trim_end_matches(['\n', '\r']).to_string())
}

unsafe fn set_machine_credentials(
    lp: *mut univention_ldap_parameters_t,
    secret: &str,
    ucr: &ConfigRegistry,
) -> Result<(), LdapError> {
    let hostdn = ucr.get("ldap/hostdn").ok_or_else(|| LdapError("UCR ldap/hostdn unset".to_string()))?;

    let binddn_cstr = CString::new(hostdn).map_err(|e| LdapError(e.to_string()))?;
    let bindpw_cstr = CString::new(secret).map_err(|e| LdapError(e.to_string()))?;

    if !(*lp).binddn.is_null() {
        libc::free((*lp).binddn as *mut libc::c_void);
        (*lp).binddn = ptr::null_mut();
    }
    (*lp).binddn = libc::strdup(binddn_cstr.as_ptr());

    if !(*lp).bindpw.is_null() {
        libc::free((*lp).bindpw as *mut libc::c_void);
        (*lp).bindpw = ptr::null_mut();
    }
    (*lp).bindpw = libc::strdup(bindpw_cstr.as_ptr());

    Ok(())
}

unsafe fn try_connect(
    lp: *mut univention_ldap_parameters_t,
    host: &str,
    port: i32,
    base: &str,
    secret: &str,
    ucr: &ConfigRegistry,
) -> Result<(), LdapError> {
    if !(*lp).host.is_null() {
        libc::free((*lp).host as *mut libc::c_void);
        (*lp).host = ptr::null_mut();
    }
    let host_cstr = CString::new(host).map_err(|e| LdapError(e.to_string()))?;
    (*lp).host = libc::strdup(host_cstr.as_ptr());

    (*lp).port = port;

    if !(*lp).base.is_null() {
        libc::free((*lp).base as *mut libc::c_void);
        (*lp).base = ptr::null_mut();
    }
    let base_cstr = CString::new(base).map_err(|e| LdapError(e.to_string()))?;
    (*lp).base = libc::strdup(base_cstr.as_ptr());

    set_machine_credentials(lp, secret, ucr)?;

    let rc = univention_ldap_open(lp);
    if rc == 0 {
        Ok(())
    } else {
        Err(LdapError(format!("univention_ldap_open failed: {}", rc)))
    }
}

impl LdapConnection {
    pub fn new_machine_connection(ucr: &ConfigRegistry, secret_file: &str) -> Result<Self, LdapError> {
        let secret = read_secret(secret_file)?;

        let base = ucr.get("ldap/base").ok_or_else(|| LdapError("UCR ldap/base unset".to_string()))?;
        let port = ucr.get("ldap/server/port").and_then(|v| v.parse::<i32>().ok()).unwrap_or(7389);
        let master_port = ucr.get("ldap/master/port").and_then(|v| v.parse::<i32>().ok()).unwrap_or(7389);
        let primary = ucr.get("ldap/server/name");
        let additional: Vec<String> = ucr
            .get("ldap/server/addition")
            .unwrap_or_default()
            .split_whitespace()
            .map(|s| s.to_string())
            .collect();
        let mut servers: Vec<String> = Vec::new();
        if let Some(p) = primary {
            servers.push(p);
        }
        servers.extend(additional);

        unsafe {
            let lp = univention_ldap_new();
            if lp.is_null() {
                return Err(LdapError("univention_ldap_new returned NULL".to_string()));
            }

            let mut last_err = LdapError("No LDAP servers configured".to_string());

            for server in &servers {
                match try_connect(lp, server, port, &base, &secret, ucr) {
                    Ok(()) => return Ok(LdapConnection { lp }),
                    Err(e) => {
                        log::warn!("Cannot connect to {}: {}", server, e);
                        last_err = e;
                    }
                }
            }

            if let Some(master) = ucr.get("ldap/master") {
                log::warn!("Falling back to ldap/master: {}", master);
                match try_connect(lp, &master, master_port, &base, &secret, ucr) {
                    Ok(()) => return Ok(LdapConnection { lp }),
                    Err(e) => {
                        last_err = e;
                    }
                }
            }

            univention_ldap_close(lp);
            Err(last_err)
        }
    }

    pub fn base(&self) -> Option<String> {
        unsafe {
            let base = (*self.lp).base;
            if base.is_null() {
                None
            } else {
                Some(CStr::from_ptr(base).to_string_lossy().into_owned())
            }
        }
    }

    pub fn search(&self, filter: &str, attrs: &[&str]) -> Result<Vec<LdapEntry>, LdapError> {
        let base = self.base().unwrap_or_default();
        let base_cstr = CString::new(base).map_err(|e| LdapError(e.to_string()))?;
        let filter_cstr = CString::new(filter).map_err(|e| LdapError(e.to_string()))?;

        let attr_cstrings: Vec<CString> = attrs
            .iter()
            .map(|a| CString::new(*a).map_err(|e| LdapError(e.to_string())))
            .collect::<Result<_, _>>()?;

        let mut attr_ptrs: Vec<*mut c_char> = attr_cstrings
            .iter()
            .map(|cs| cs.as_ptr() as *mut c_char)
            .collect();
        attr_ptrs.push(ptr::null_mut());

        unsafe {
            let ld = (*self.lp).ld;
            if ld.is_null() {
                return Err(LdapError("LDAP handle is NULL".to_string()));
            }

            let mut result: *mut LDAPMessage = ptr::null_mut();
            let rc = ldap_search_ext_s(
                ld,
                base_cstr.as_ptr(),
                LDAP_SCOPE_SUBTREE as i32,
                filter_cstr.as_ptr(),
                attr_ptrs.as_mut_ptr(),
                0,
                ptr::null_mut(),
                ptr::null_mut(),
                ptr::null_mut(),
                0,
                &mut result,
            );

            if rc != LDAP_SUCCESS as i32 {
                if !result.is_null() {
                    ldap_msgfree(result);
                }
                return Err(LdapError(format!("ldap_search_ext_s failed: {}", rc)));
            }

            let mut entries = Vec::new();
            let mut entry = ldap_first_entry(ld, result);
            while !entry.is_null() {
                let dn_ptr = ldap_get_dn(ld, entry);
                let dn = if dn_ptr.is_null() {
                    String::new()
                } else {
                    let s = CStr::from_ptr(dn_ptr).to_string_lossy().into_owned();
                    ldap_memfree(dn_ptr as *mut libc::c_void);
                    s
                };

                let mut attributes: HashMap<String, Vec<Vec<u8>>> = HashMap::new();
                let mut ber: *mut berelement = ptr::null_mut();
                let mut attr_ptr = ldap_first_attribute(ld, entry, &mut ber);
                while !attr_ptr.is_null() {
                    let attr_name = CStr::from_ptr(attr_ptr).to_string_lossy().into_owned();
                    let vals = ldap_get_values_len(ld, entry, attr_ptr);
                    let mut values = Vec::new();
                    if !vals.is_null() {
                        let mut i = 0;
                        loop {
                            let val_ptr = *vals.offset(i);
                            if val_ptr.is_null() {
                                break;
                            }
                            let slice = std::slice::from_raw_parts(
                                (*val_ptr).bv_val as *const u8,
                                (*val_ptr).bv_len as usize,
                            );
                            values.push(slice.to_vec());
                            i += 1;
                        }
                        ldap_value_free_len(vals);
                    }
                    attributes.insert(attr_name, values);
                    ldap_memfree(attr_ptr as *mut libc::c_void);
                    attr_ptr = ldap_next_attribute(ld, entry, ber);
                }
                if !ber.is_null() {
                    ber_free(ber, 0);
                }

                entries.push(LdapEntry { dn, attributes });
                entry = ldap_next_entry(ld, entry);
            }

            if !result.is_null() {
                ldap_msgfree(result);
            }

            Ok(entries)
        }
    }
}

impl Drop for LdapConnection {
    fn drop(&mut self) {
        unsafe {
            if !self.lp.is_null() {
                univention_ldap_close(self.lp);
            }
        }
    }
}

pub fn ldap_filter_escape(s: &str) -> String {
    let mut out = String::with_capacity(s.len());
    for c in s.chars() {
        match c {
            '\\' => out.push_str("\\5c"),
            '*' => out.push_str("\\2a"),
            '(' => out.push_str("\\28"),
            ')' => out.push_str("\\29"),
            '\0' => out.push_str("\\00"),
            other => out.push(other),
        }
    }
    out
}
