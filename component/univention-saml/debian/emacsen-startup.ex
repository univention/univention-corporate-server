;; -*-emacs-lisp-*-
;;
;; Emacs startup file, e.g.  /etc/emacs/site-start.d/50univention-identity-provider.el
;; for the Debian univention-identity-provider package
;;
;; Originally contributed by Nils Naumann <naumann@unileoben.ac.at>
;; Modified by Dirk Eddelbuettel <edd@debian.org>
;; Adapted for dh-make by Jim Van Zandt <jrv@debian.org>

;; The univention-identity-provider package follows the Debian/GNU Linux 'emacsen' policy and
;; byte-compiles its elisp files for each 'emacs flavor' (emacs19,
;; xemacs19, emacs20, xemacs20...).  The compiled code is then
;; installed in a subdirectory of the respective site-lisp directory.
;; We have to add this to the load-path:
(let ((package-dir (concat "/usr/share/"
                           (symbol-name flavor)
                           "/site-lisp/univention-identity-provider")))
;; If package-dir does not exist, the univention-identity-provider package must have
;; removed but not purged, and we should skip the setup.
  (when (file-directory-p package-dir)
    (setq load-path (cons package-dir load-path))
    (autoload 'univention-identity-provider-mode "univention-identity-provider-mode"
      "Major mode for editing univention-identity-provider files." t)
    (add-to-list 'auto-mode-alist '("\\.univention-identity-provider$" . univention-identity-provider-mode))))

