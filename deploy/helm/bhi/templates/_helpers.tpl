{{/* Common labels for a service */}}
{{- define "bhi.labels" -}}
app.kubernetes.io/name: {{ .name }}
app.kubernetes.io/part-of: bhi
{{- end -}}

{{/* Build the DATABASE_URL for a service that owns a database.
     .svc.database is the K8s host (DNS-safe key); $pg.db is the real database name. */}}
{{- define "bhi.databaseUrl" -}}
{{- $host := .svc.database -}}
{{- $pg := index .root.Values.postgres $host -}}
postgresql+asyncpg://{{ $pg.user }}:{{ $pg.password }}@{{ $host }}:5432/{{ $pg.db }}
{{- end -}}
