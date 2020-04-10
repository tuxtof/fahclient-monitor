# fahclient-monitor

Work in progress - actually POC state - lots of improvement possible

Monitor for Folding@Home clients who send queue-info in InfluxDB

Can be used in different ways:
- as a standalone apps
- as a sidecar for fahclient in container

---

*Configuration Environment variable*

|Name | description|
|---|---|
| INFLUX_HOST | InfluxDB Hostname
| INFLUX_PORT | InfluxDB Port (443)
| INFLUX_USER | InfluxDB  Username
| INFLUX_PASSWORD | InfluxDB Password
| INFLUX_DB | InfluxDB DB Name
| ID | fahclient identifier
| FAHCLIENT_HOST | fahclient target (localhost) 
| FAHCLIENT_PORT | fahclient port (36330)
| LOG | Log Level: debug, info, warning, ...
| INTERVAL | Metric collection interval



SSL is forced for the InfluxDB connection with certificate verification



