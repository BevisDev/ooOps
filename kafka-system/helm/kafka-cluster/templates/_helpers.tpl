{{- define "kafka-cluster.name" -}}
{{- default .Chart.Name .Values.cluster.name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "kafka-cluster.labels" -}}
app.kubernetes.io/name: {{ include "kafka-cluster.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
strimzi.io/cluster: {{ .Values.cluster.name }}
{{- end }}

{{- define "kafka-cluster.antiAffinity" -}}
{{- if .Values.ha.podAntiAffinity }}
podAntiAffinity:
  requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchLabels:
          strimzi.io/cluster: {{ .Values.cluster.name }}
          strimzi.io/name: {{ .poolName }}
      topologyKey: kubernetes.io/hostname
{{- end }}
{{- end }}

{{- define "kafka-cluster.topologySpread" -}}
{{- if .Values.ha.topologySpread.enabled }}
topologySpreadConstraints:
  - maxSkew: {{ .Values.ha.topologySpread.maxSkew }}
    topologyKey: {{ .Values.ha.topologySpread.topologyKey }}
    whenUnsatisfiable: {{ .Values.ha.topologySpread.whenUnsatisfiable }}
    labelSelector:
      matchLabels:
        strimzi.io/cluster: {{ .Values.cluster.name }}
        strimzi.io/name: {{ .poolName }}
{{- end }}
{{- end }}