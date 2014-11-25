/*
  Copyright (C) Andrzej Hajda 2009-2013
  Contact: andrzej.hajda@wp.pl
  License: GNU General Public License version 3
*/

#define SVC_INTERACTIVE 1
#define SVC_IGNORE_INTERACTIVE 2
#define SVC_INTERACTIVE_MASK 3
#define SVC_FORCE_UPLOAD 4
#define SVC_OS64BIT 8
#define SVC_OSCHOOSE 16
#define SVC_UNINSTALL 32
#define SVC_SYSTEM 64
#define SVC_PROFILE 128
#define SVC_CONVERT 256

NTSTATUS svc_install(struct tevent_context *ev_ctx, 
                     const char *hostname,
                     const char *service_name, const char *service_filename,
                     unsigned char *svc32_exe, unsigned int svc32_exe_len,
                     unsigned char *svc64_exe, unsigned int svc64_exe_len,
                     struct cli_credentials *credentials,
                     struct loadparm_context *cllp_ctx,
                     int flags);
NTSTATUS svc_uninstall(struct tevent_context *ev_ctx,
                       const char *hostname,
                       const char *service_name, const char *service_filename,
                       struct cli_credentials * credentials,
                       struct loadparm_context *cllp_ctx);

const char **lpcfg_smb_ports(struct loadparm_context *);
const char *lpcfg_socket_options(struct loadparm_context *);
struct gensec_settings *lpcfg_gensec_settings(TALLOC_CTX *, struct loadparm_context *);
struct loadparm_context *loadparm_init_global(bool load_default);
struct resolve_context *lpcfg_resolve_context(struct loadparm_context *lp_ctx);
void lpcfg_smbcli_options(struct loadparm_context *, struct smbcli_options *);
bool lpcfg_set_cmdline(struct loadparm_context *, const char *, const char *);
bool lpcfg_set_option(struct loadparm_context *, const char *);
void lpcfg_smbcli_session_options(struct loadparm_context *,
    struct smbcli_session_options *options);
