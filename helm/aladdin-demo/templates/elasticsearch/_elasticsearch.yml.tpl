{{/* Config file for elasticsearch */}}

{{ define "elasticsearch-config" -}}
# We are only setting up a single node
discovery:
  zen.minimum_master_nodes: 1
# Some xpack plugins that we don't need
xpack:
  security.enabled: false
  ml.enabled: false
  graph.enabled: false
  monitoring.enabled: false
  watcher.enabled: false

# Limit this to every 30 minutes so the logs don't get flooded with cluster info spam
cluster.info.update.interval: "30m"

# Change the path to write data and logs to our peristent volume mounted
path:
  data: stateful/data
  logs: stateful/log

# This allows other pods in the kubernetes cluster to connect to elasticsearch
network.host: 0.0.0.0

{{ end }}
