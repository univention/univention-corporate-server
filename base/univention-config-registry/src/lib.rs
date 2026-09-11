#![allow(
    non_upper_case_globals,
    non_camel_case_types,
    non_snake_case,
    dead_code
)]

// SPDX-FileCopyrightText: 2026 Univention GmbH
// SPDX-License-Identifier: AGPL-3.0-only

include!(concat!(env!("OUT_DIR"), "/bindings.rs"));

use std::ffi::{CStr, CString};

pub struct ConfigRegistry;

impl ConfigRegistry {
    pub fn new() -> Self {
        ConfigRegistry
    }

    pub fn get(&self, key: &str) -> Option<String> {
        let ckey = CString::new(key).ok()?;
        unsafe {
            let ptr = univention_config_get_string(ckey.as_ptr());
            if ptr.is_null() {
                return None;
            }
            let val = CStr::from_ptr(ptr).to_string_lossy().into_owned();
            libc::free(ptr as *mut libc::c_void);
            Some(val)
        }
    }

    pub fn get_int(&self, key: &str, default: i32) -> i32 {
        let ckey = match CString::new(key) {
            Ok(k) => k,
            Err(_) => return default,
        };
        let val = unsafe { univention_config_get_int(ckey.as_ptr()) };
        if val == -1 {
            default
        } else {
            val
        }
    }

    pub fn is_true(&self, key: &str, default_value: bool) -> bool {
        let ckey = match CString::new(key) {
            Ok(k) => k,
            Err(_) => return default_value,
        };
        unsafe { univention_config_is_true(ckey.as_ptr(), default_value) }
    }

    pub fn iter_prefix(&self, prefix: &str) -> Vec<(String, String)> {
        let mut results: Vec<(String, String)> = Vec::new();
        let prefix_cstr = match CString::new(prefix) {
            Ok(s) => s,
            Err(_) => return results,
        };

        unsafe extern "C" fn callback(
            key: *const libc::c_char,
            value: *const libc::c_char,
            userdata: *mut libc::c_void,
        ) {
            let results = &mut *(userdata as *mut Vec<(String, String)>);
            let k = std::ffi::CStr::from_ptr(key).to_string_lossy().into_owned();
            let v = std::ffi::CStr::from_ptr(value).to_string_lossy().into_owned();
            results.push((k, v));
        }

        unsafe {
            univention_config_iterate_prefix(
                prefix_cstr.as_ptr(),
                Some(callback),
                &mut results as *mut _ as *mut libc::c_void,
            );
        }

        results
    }
}

impl Default for ConfigRegistry {
    fn default() -> Self {
        ConfigRegistry
    }
}
