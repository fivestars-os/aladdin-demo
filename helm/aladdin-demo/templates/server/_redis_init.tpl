{{ define "redis_check" -}}
{{ if .Values.redis.create }}
- name: {{ .Chart.Name }}-redis-check
  image: busybox
  command:
  - 'sh'
  - '-c'
  - 'until nslookup {{ .Chart.Name }}-redis; do echo waiting for redis pod; sleep 2; done;'
{{ end }}
{{ end }}

---

{{ define "redis_populate" -}}
{{ if .Values.redis.create }}
- name: {{ .Chart.Name }}-redis-populate
  image: {{ .Values.deploy.ecr }}{{ .Chart.Name }}:{{ .Values.deploy.imageTag }}
  command:
  - 'python3'
  - 'redis_util/redis_populate.py'
  envFrom:
    - configMapRef:
        name: {{ .Chart.Name }}
{{ end }}
{{ end }}