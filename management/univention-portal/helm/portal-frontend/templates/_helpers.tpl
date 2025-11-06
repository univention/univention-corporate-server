{{- /*
SPDX-FileCopyrightText: 2024 Univention GmbH
SPDX-License-Identifier: AGPL-3.0-only
*/}}


{{- /*
These template definitions are only used in this chart and do not relate to templates defined elsewhere.
*/}}
{{- define "portal-frontend.ingress.tls.secretName" -}}
{{- if .Values.ingress.tls.secretName -}}
{{- tpl .Values.ingress.tls.secretName . -}}
{{- else if .Values.global.nubusDeployment -}}
{{- printf "%s-portal-tls" .Release.Name -}}
{{- else -}}
{{- required ".Values.ingress.tls.secretName must be defined" .Values.ingress.tls.secretName -}}
{{- end -}}
{{- end -}}

{{- define "portalFrontend.branding.css" -}}
{{- if .Values.portalFrontend.branding.css -}}
{{- .Values.portalFrontend.branding.css -}}
{{- else -}}
{{ .Files.Get "branding/custom.css" | b64enc }}
{{- end -}}
{{- end -}}

{{- define "portalFrontend.branding.favicon" -}}
{{- if .Values.portalFrontend.branding.favicon -}}
{{- .Values.portalFrontend.branding.favicon -}}
{{- else -}}
{{ .Files.Get "branding/favicon.ico" | b64enc }}
{{- end -}}
{{- end -}}

{{- define "portalFrontend.branding.logo" -}}
{{- if .Values.portalFrontend.branding.logo -}}
{{- .Values.portalFrontend.branding.logo -}}
{{- else -}}
{{ .Files.Get "branding/logo.svg" | b64enc }}
{{- end -}}
{{- end -}}

{{- define "portalFrontend.branding.backgroundImage" -}}
{{- if .Values.portalFrontend.branding.backgroundImage -}}
{{- .Values.portalFrontend.branding.backgroundImage -}}
{{- else -}}
{{ .Files.Get "branding/portal_background_image.svg" | b64enc }}
{{- end -}}
{{- end -}}
