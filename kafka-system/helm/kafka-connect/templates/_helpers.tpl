{{/*
Expand the name of the chart.
*/}}
{{- define "connect.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Kafka Connect cluster name used by Strimzi CRs and REST service.
Service: <clusterName>-connect-api.<namespace>.svc:8083
*/}}
{{- define "connect.clusterName" -}}
{{- required "clusterName is required" .Values.clusterName -}}
{{- end -}}

{{/*
Bootstrap servers for the upstream Kafka cluster.
*/}}
{{- define "connect.bootstrapServers" -}}
{{- $kc := .Values.kafka -}}
{{- printf "%s-kafka-bootstrap.%s.svc:%v" (required "kafkaCluster.name is required" $kc.name) (required "kafkaCluster.namespace is required" $kc.namespace) (default 9092 $kc.bootstrapPort) -}}
{{- end -}}

{{/*
Labels for Kafka Connect resources.
*/}}
{{- define "connect.labels" -}}
strimzi.io/cluster: {{ include "connect.clusterName" . }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
app.kubernetes.io/name: {{ include "connect.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}
