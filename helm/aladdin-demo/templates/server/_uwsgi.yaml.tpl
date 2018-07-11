{{/* Config file for uwsgi */}}

# Note: This define name is global, if loading multiple templates with the same name, the last
# one loaded will be used.
{{ define "uwsgi-config" -}}
uwsgi:
  uid: aladdin-user
  gid: aladdin-user
  master: true
  http: :{{ .Values.app.uwsgi.port }}
  processes: {{ .Values.app.uwsgi.processes }}
  wsgi-file: run.py
  callable: app
{{ end }}
