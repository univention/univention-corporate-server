use std::{
    ffi::{c_char, c_int, c_void, CString}, os::raw::c_uint, ptr::{null, null_mut}, str::FromStr
};

use base64::prelude::*;

use sasl2_sys::{
    prelude::{
        sasl_client_params, sasl_client_plug_t, sasl_out_params, sasl_out_params_t, sasl_server_params, sasl_server_plug, sasl_server_plug_t, sasl_utils, sasl_utils_t, SASL_FEAT_ALLOWS_PROXY, SASL_FEAT_WANT_CLIENT_FIRST, SASL_SERVER_PLUG_VERSION
    },
    sasl::{sasl_interact, SASL_CU_AUTHID, SASL_CU_AUTHZID, SASL_OK, SASL_SEC_NOANONYMOUS},
};

struct GlobTest {
    a: u32,
}

unsafe extern "C" fn sasl_mech_new(
    glob_context: *mut c_void,
    sparams: *mut sasl_server_params,
    challenge: *const i8,
    challen: u32,
    conn_context: *mut *mut c_void,
) -> i32 {
    println!("called sasl_mech_new");
    SASL_OK
}

unsafe extern "C" fn sasl_mech_step(
    conn_context: *mut c_void,
    sparams: *mut sasl_server_params,
    client_in: *const c_char,
    client_in_len: u32,
    server_out: *mut *const i8,
    server_out_len: *mut u32,
    oparams: *mut sasl_out_params_t,
) -> i32 {
    unsafe {
        println!("sasl_mech_step");
        let b_slice = std::slice::from_raw_parts(client_in as *const u8, client_in_len as usize);

        println!("{}", std::str::from_utf8_unchecked(b_slice));
        let c_user = (*sparams).canon_user.unwrap();
        let conn = (*(*sparams).utils).conn;
        let user = CString::new("test_user").unwrap();
        c_user(conn, user.as_ptr(), user.count_bytes() as c_uint, SASL_CU_AUTHID, oparams);
        c_user(conn, user.as_ptr(), user.count_bytes() as c_uint, SASL_CU_AUTHZID, oparams);
        (*oparams).doneflag = 1;
        (*oparams).maxoutbuf = 0;
        (*oparams).mech_ssf = 0;
        (*oparams).encode = None;
        (*oparams).decode = None;
        (*oparams).encode_context = null_mut();
        (*oparams).decode_context = null_mut();
    }

    println!("called sasl_mech_step");
    SASL_OK
}
unsafe extern "C" fn sasl_mech_dispose(conn_context: *mut c_void, utils: *const sasl_utils_t) {
    println!("called sasl_mech_dispose");
}
unsafe extern "C" fn sasl_mech_free(conn_context: *mut c_void, utils: *const sasl_utils_t) {
    println!("called sasl_mech_free");
}

pub fn make_sasl_server_plug() -> sasl_server_plug_t {
    let glob_context = Box::new(GlobTest { a: 3 });
    let glob_context_ptr = Box::into_raw(glob_context) as *mut c_void;

    let mech_name: *const i8 = CString::new("OAUTHBEARER_R").unwrap().as_ptr();

    sasl2_sys::saslplug::sasl_server_plug_t {
        mech_name,
        max_ssf: 0,
        security_flags: SASL_SEC_NOANONYMOUS,
        features: SASL_FEAT_WANT_CLIENT_FIRST | SASL_FEAT_ALLOWS_PROXY,
        glob_context: glob_context_ptr,
        mech_new: Some(sasl_mech_new),
        idle: None,
        mech_avail: None,
        mech_dispose: Some(sasl_mech_dispose),
        mech_free: Some(sasl_mech_free),
        mech_step: Some(sasl_mech_step),
        setpass: None,
        spare_fptr2: None,
        user_query: None,
    }
}

#[unsafe(no_mangle)]
pub unsafe extern "C" fn sasl_server_plug_init(
    utils: *const sasl_utils,
    maxvers: i32,
    outvers: *mut i32,
    pluglist: *mut *mut sasl_server_plug,
    plugcount: *mut i32,
) -> i32 {
    println!("called sasl_server_plug_init maxvers is {}", maxvers);
    unsafe {
        *outvers = SASL_SERVER_PLUG_VERSION as i32;
        *pluglist = Box::into_raw(Box::new(make_sasl_server_plug()));
        *plugcount = 1;
    }
    SASL_OK
}
unsafe extern "C" fn sasl_client_mech_step(
    context: *mut c_void,
    c_params: *mut sasl_client_params,
    server_in: *const i8,
    serverinlen: u32,
    prompt_needed: *mut *mut sasl_interact,
    client_out: *mut *const i8,
    client_out_len: *mut u32,
    oparams: *mut sasl_out_params,
) -> i32 {
    println!("Called client mech step");
    unsafe {
        let c_user = (*c_params).canon_user.unwrap();
        let conn = (*(*c_params).utils).conn;
        let user_name = CString::new("test_user").unwrap();
        let user_name_len = user_name.count_bytes();
        c_user(conn, user_name.as_ptr(), user_name_len as c_uint, SASL_CU_AUTHID, oparams);
        c_user(conn, user_name.as_ptr(), user_name_len as c_uint, SASL_CU_AUTHZID, oparams);
    }
    let response = "jwt=eyasdsagewgw";
    let out_string = CString::from_str(response).unwrap();
    unsafe {
        *client_out_len = out_string.count_bytes() as c_uint;
        *client_out = out_string.as_ptr();
    }
    SASL_OK
}
unsafe extern "C" fn sasl_client_mech_new(
    _: *mut c_void,
    _: *mut sasl_client_params,
    _: *mut *mut c_void,
) -> i32 {
    println!("Called sasl_client_mech_new");
    SASL_OK
}
unsafe extern "C" fn sasl_client_mech_dispose(_: *mut c_void, _: *const sasl_utils) {
    println!("sasl client mech dispose called");
}

fn make_sasl_client_plug() -> sasl_client_plug_t {
    let mech_name: *const i8 = CString::new("OAUTHBEARER_R").unwrap().as_ptr();

    sasl_client_plug_t {
        mech_name,
        max_ssf: 0,
        security_flags: SASL_SEC_NOANONYMOUS,
        features: SASL_FEAT_WANT_CLIENT_FIRST | SASL_FEAT_ALLOWS_PROXY,
        required_prompts: null(),
        glob_context: null_mut(),
        mech_new: Some(sasl_client_mech_new),
        mech_step: Some(sasl_client_mech_step),
        mech_dispose: Some(sasl_client_mech_dispose),
        idle: None,
        mech_free: None,
        spare_fptr2: None,
        spare_fptr1: None,
    }
}

#[unsafe(no_mangle)]
pub unsafe extern "C" fn sasl_client_plug_init(
    utils: *const sasl_utils_t,
    maxvers: i32,
    outvers: *mut i32,
    pluglist: *mut *mut sasl_client_plug_t,
    plugcount: *mut i32,
) -> i32 {
    println!("Called sasl_client_plug_init");
    unsafe {
        *outvers = SASL_SERVER_PLUG_VERSION as i32;
        *pluglist = Box::into_raw(Box::new(make_sasl_client_plug()));
        *plugcount = 1;
    }

    SASL_OK
}
