{{/*
Expand the name of the chart.
*/}}
{{- define "kafka.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Kafka cluster name used by Strimzi CRs and bootstrap service.
*/}}
{{- define "kafka.clusterName" -}}
{{- required "clusterName is required" .Values.clusterName -}}
{{- end -}}

{{/*
 labels for resources
*/}}
{{- define "kafka.labels" -}}
strimzi.io/cluster: {{ include "kafka.clusterName" . }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
app.kubernetes.io/name: {{ include "kafka.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
