workspace "OzAgriMate Platform" "C4 model of the OzAgriMate digital agriculture platform (ISYS3459 Assignment 4)." {

    // One model, many views: every C4 diagram in the report comes from this file,
    // so element names, descriptions and relationship labels match across diagrams.
    // Owners: Shikhar - container view and the Telemetry Ingestion and Farm & Access component views;
    //         Pranav  - system context, Alert & Notification component, two dynamic views, deployment.

    model {
        // ---------- People ----------
        farmer = person "Farmer" "Checks readings and alerts, acts on irrigation advice and shares farm data."
        agronomist = person "Agronomist" "Advises client farms remotely using the data farmers share."
        operationsStaff = person "Operations Staff" "Monitors platform health and capacity, and supports users."

        // ---------- External software systems ----------
        iotNetwork = softwareSystem "IoT Sensor & Gateway Network" "Farm sensors and edge gateways; gateways buffer readings while offline." "External"
        irrigationControl = softwareSystem "Irrigation Control System" "On-farm irrigation hardware that runs watering schedules." "External"
        weatherProvider = softwareSystem "Weather Data Provider" "Supplies forecasts and climate data." "External"
        smsGateway = softwareSystem "SMS Gateway" "Sends SMS messages to farmers' phones." "External"
        pushService = softwareSystem "Push Notification Service" "Delivers push notifications to phones (APNs, FCM)." "External"
        identityProvider = softwareSystem "Identity Provider" "Signs users in and issues access tokens (OIDC)." "External"
        regulator = softwareSystem "Government & Regulatory Reporting System" "Receives resource-usage reports for compliance checks." "External"
        marketplace = softwareSystem "Agricultural Marketplace" "Third-party marketplace for buying supplies and selling produce." "External"

        // ---------- OzAgriMate and its containers ----------
        ozAgriMate = softwareSystem "OzAgriMate Platform" "Collects farm IoT data, raises alerts and gives AI-assisted irrigation advice." {
            mobileApp = container "Farmer Mobile App" "Shows readings, alerts and advice; works on patchy rural coverage." "React Native" "Mobile App"
            webDashboard = container "Web Dashboard" "Multi-farm views for agronomists; platform health for operations staff." "React" "Web Browser"
            apiGateway = container "API Gateway" "Validates tokens, sets X-User-Id, rate-limits and routes /api/v1 calls." "NGINX"
            telemetryService = container "Telemetry Ingestion Service" "Validates and de-duplicates readings; tracks device health and configuration." "Python, FastAPI" {
                telemetryApi = component "Telemetry API" "Endpoints #1-3: ingest readings, device health, device configuration." "FastAPI router"
                ingestionPipeline = component "Ingestion Pipeline" "Runs each batch through adapters, checks, storage and publishing; holds no state." "Python"
                protocolAdapters = component "Protocol Adapters" "Turn HTTPS JSON and MQTT payloads into one canonical batch." "Python"
                validator = component "Validator" "Checks metric per device type, converts units, rejects impossible values." "Python"
                duplicateFilter = component "Duplicate Filter" "Drops replayed readings by deviceId and sequenceNo." "Python"
                readingStore = component "Reading Store" "Saves accepted readings." "Python repository"
                deviceRegistry = component "Device Registry" "Gateways and devices; offline after 30 minutes; configuration versions." "Python"
                eventPublisher = component "Event Publisher" "Publishes TelemetryReceived, keyed by farmId." "Kafka producer"
            }
            telemetryStore = container "Telemetry Store" "Readings kept for 24 months; devices and their configuration." "TimescaleDB" "Database"
            alertService = container "Alert & Notification Service" "Checks readings against alert rules; notifies by push, then SMS." "Python, FastAPI" {
                alertApi = component "Alert API" "Endpoints #4-6: list a farm's alerts, replace and delete alert rules." "FastAPI router"
                ruleManager = component "Rule Manager" "Thresholds stored as data per crop, region and metric; no redeploy to change." "Python"
                thresholdEvaluator = component "Threshold Evaluator" "Checks each reading in TelemetryReceived against the farm's rules." "Kafka consumer"
                alertManager = component "Alert Manager" "Raises, stores and lists alerts; one open alert per rule and device." "Python"
                farmAccessCache = component "Farm Access Cache" "Local copy of farms and grants; checks who may read a farm's alerts." "Kafka consumer"
                notificationDispatcher = component "Notification Dispatcher" "Sends each alert by push; falls back to SMS after 2 minutes." "Python"
                deliveryTracker = component "Delivery Tracker" "Records every push and SMS attempt; finds unconfirmed pushes." "Python"
            }
            alertDb = container "Alert DB" "Alert rules, alerts and delivery status." "PostgreSQL" "Database"
            accessService = container "Farm & Access Service" "Farms, owners and revocable agronomist access grants." "Python, FastAPI" {
                accessApi = component "Access API" "Endpoints #7-8: grant and revoke an agronomist's access." "FastAPI router"
                grantManager = component "Grant Manager" "Creates and revokes grants; one active grant per agronomist per farm." "Python"
                authorisationChecker = component "Authorisation Checker" "Reads X-User-Id; only a farm's owner may change its grants." "Python"
                farmRegistry = component "Farm Registry" "Farms, their owners and registered agronomists." "Python"
                grantEventPublisher = component "Grant Event Publisher" "Publishes AccessGranted and AccessRevoked, keyed by farmId." "Kafka producer"
            }
            accessDb = container "Farm & Access DB" "Farms, owners, agronomists and access grants." "PostgreSQL" "Database"
            advisoryService = container "Irrigation Advisory Service" "Generates AI irrigation recommendations from readings and forecasts." "Python, FastAPI, ML model"
            advisoryDb = container "Advisory DB" "Recommendations with their inputs and rationale." "PostgreSQL" "Database"
            reportingService = container "Reporting & Compliance Service" "Builds resource-usage reports for farmers and regulators." "Python, FastAPI"
            reportStore = container "Report Store" "Generated reports and regulator exports." "S3-compatible object storage" "Database"
            eventBroker = container "Event Broker" "Carries telemetry, alert, grant and recommendation events between services." "Apache Kafka" "Message Broker"
        }

        // ---------- System-level relationships (Pranav, System Context view) ----------
        // Written before the container relationships, so they replace the labels Structurizr would otherwise imply.
        farmer -> ozAgriMate "Checks readings, alerts and advice; shares farm data with agronomists"
        agronomist -> ozAgriMate "Reviews shared farm data and gives advice"
        operationsStaff -> ozAgriMate "Monitors platform health and devices"
        iotNetwork -> ozAgriMate "Sends sensor readings, replaying buffered data"
        ozAgriMate -> iotNetwork "Pushes device configuration"
        ozAgriMate -> irrigationControl "Sends approved watering schedules"
        ozAgriMate -> weatherProvider "Fetches forecasts on a schedule"
        ozAgriMate -> identityProvider "Validates users' access tokens"
        ozAgriMate -> pushService "Sends push alerts"
        ozAgriMate -> smsGateway "Sends SMS when a push is not delivered"
        pushToFarmer = pushService -> farmer "Delivers push alerts to the farmer's phone"
        ozAgriMate -> regulator "Submits scheduled usage reports"
        ozAgriMate -> marketplace "Links farmers to supplies and produce listings"

        // ---------- Container relationships (container view) ----------
        farmer -> mobileApp "Checks readings, alerts and advice; shares farm data"
        agronomist -> webDashboard "Reviews client farms and gives advice"
        operationsStaff -> webDashboard "Monitors platform health and devices"
        mobileApp -> apiGateway "Makes API calls" "JSON/HTTPS"
        webDashboard -> apiGateway "Makes API calls" "JSON/HTTPS"
        mobileApp -> marketplace "Links to supplies and produce listings" "HTTPS"
        apiGateway -> identityProvider "Validates access tokens" "OIDC/HTTPS"
        apiGateway -> telemetryService "Routes device health and configuration calls" "JSON/HTTPS"
        gatewayToAlerts = apiGateway -> alertService "Routes alert and alert-rule calls" "JSON/HTTPS"
        apiGateway -> accessService "Routes access-grant calls" "JSON/HTTPS"
        apiGateway -> advisoryService "Routes recommendation calls" "JSON/HTTPS"
        apiGateway -> reportingService "Routes report calls" "JSON/HTTPS"
        iotNetwork -> telemetryService "Sends reading batches, replaying buffered data" "MQTT, JSON/HTTPS"
        telemetryService -> iotNetwork "Pushes device configuration" "MQTT"
        telemetryService -> telemetryStore "Reads and writes readings and devices" "SQL"
        telemetryService -> eventBroker "Publishes TelemetryReceived" "Kafka"
        alertService -> eventBroker "Consumes telemetry, grant and recommendation events; publishes AlertRaised" "Kafka"
        alertService -> alertDb "Reads and writes rules, alerts and deliveries" "SQL"
        alertService -> pushService "Sends push alerts" "HTTPS"
        alertService -> smsGateway "Sends SMS when push is not delivered" "HTTPS"
        pushService -> mobileApp "Delivers push notifications" "APNs/FCM"
        smsGateway -> farmer "Texts critical alerts" "SMS"
        accessService -> accessDb "Reads and writes farms and grants" "SQL"
        accessService -> eventBroker "Publishes AccessGranted and AccessRevoked" "Kafka"
        advisoryService -> eventBroker "Consumes telemetry and alert events; publishes RecommendationIssued" "Kafka"
        advisoryService -> advisoryDb "Reads and writes recommendations" "SQL"
        advisoryService -> weatherProvider "Fetches forecasts on a schedule" "JSON/HTTPS"
        advisoryService -> irrigationControl "Sends approved watering schedules" "HTTPS"
        reportingService -> eventBroker "Consumes telemetry and recommendation events" "Kafka"
        reportingService -> reportStore "Stores generated reports" "S3 API"
        reportingService -> regulator "Submits scheduled usage reports" "HTTPS"

        // ---------- Component relationships: Telemetry Ingestion Service ----------
        apiGateway -> telemetryApi "Routes device health and configuration calls (#2, #3)" "JSON/HTTPS"
        iotNetwork -> telemetryApi "Posts reading batches (#1)" "JSON/HTTPS"
        iotNetwork -> ingestionPipeline "Publishes compact reading rows" "MQTT"
        telemetryApi -> ingestionPipeline "Hands over each batch"
        telemetryApi -> deviceRegistry "Reads health; replaces configuration"
        ingestionPipeline -> protocolAdapters "Converts the payload to a canonical batch"
        ingestionPipeline -> deviceRegistry "Checks gateway and devices; records contact"
        ingestionPipeline -> duplicateFilter "Skips readings already accepted"
        ingestionPipeline -> validator "Validates and normalises each reading"
        ingestionPipeline -> readingStore "Saves accepted readings"
        ingestionPipeline -> eventPublisher "Publishes the accepted readings"
        duplicateFilter -> telemetryStore "Checks the deviceId + sequenceNo key" "SQL"
        readingStore -> telemetryStore "Writes readings" "SQL"
        deviceRegistry -> telemetryStore "Reads and writes devices" "SQL"
        deviceRegistry -> iotNetwork "Pushes pending configuration" "MQTT"
        eventPublisher -> eventBroker "Publishes TelemetryReceived (key: farmId)" "Kafka"

        // ---------- Component relationships: Farm & Access Service ----------
        apiGateway -> accessApi "Routes grant calls with the caller's X-User-Id" "JSON/HTTPS"
        accessApi -> grantManager "Creates and revokes grants"
        grantManager -> authorisationChecker "Checks the caller owns the farm"
        grantManager -> farmRegistry "Looks up the farm and agronomist"
        grantManager -> grantEventPublisher "Announces each grant change"
        grantManager -> accessDb "Reads and writes grants" "SQL"
        farmRegistry -> accessDb "Reads farms and agronomists" "SQL"
        grantEventPublisher -> eventBroker "Publishes AccessGranted / AccessRevoked (key: farmId)" "Kafka"

        // ---------- Component relationships: Alert & Notification Service (Pranav) ----------
        apiGateway -> alertApi "Routes alert and alert-rule calls (#4-6) with X-User-Id" "JSON/HTTPS"
        alertApi -> alertManager "Lists a farm's alerts (#4)"
        alertApi -> ruleManager "Replaces and deletes rules (#5, #6)"
        thresholdEvaluator -> eventBroker "Consumes TelemetryReceived" "Kafka"
        farmAccessCache -> eventBroker "Consumes AccessGranted / AccessRevoked" "Kafka"
        alertManager -> eventBroker "Publishes AlertRaised (key: farmId); consumes RecommendationIssued" "Kafka"
        thresholdEvaluator -> ruleManager "Gets the rules for the farm's crop, region and metric"
        thresholdEvaluator -> farmAccessCache "Looks up the farm's crop and region"
        thresholdEvaluator -> alertManager "Raises an alert for each breach"
        thresholdEvaluator -> notificationDispatcher "Dispatches each new alert"
        alertManager -> farmAccessCache "Checks the caller owns the farm or holds a READ_ALERTS grant"
        alertManager -> deliveryTracker "Reads each alert's delivery status"
        notificationDispatcher -> farmAccessCache "Looks up the farm owner's contact"
        notificationDispatcher -> deliveryTracker "Records attempts; asks for overdue pushes"
        notificationDispatcher -> pushService "Sends push alerts" "HTTPS"
        notificationDispatcher -> smsGateway "Sends SMS when a push is not confirmed in 2 minutes" "HTTPS"
        ruleManager -> alertDb "Reads and writes rules" "SQL"
        alertManager -> alertDb "Reads and writes alerts" "SQL"
        deliveryTracker -> alertDb "Reads and writes delivery attempts" "SQL"
        farmAccessCache -> alertDb "Reads and writes farm and grant copies" "SQL"

        // ---------- Deployment (Pranav) ----------
        production = deploymentEnvironment "Production" {
            deploymentNode "Farm site" "One per farm; connectivity drops for hours at a time." "Rural property, 4G or satellite link" {
                deploymentNode "Farm edge gateway" "Collects sensor readings; buffers them on local storage while offline." "Industrial IoT gateway, Linux" {
                    edgeInstance = softwareSystemInstance iotNetwork
                }
            }
            deploymentNode "Farmer's phone" "Receives push alerts and SMS." "iOS or Android" {
                phoneAppInstance = containerInstance mobileApp
            }
            deploymentNode "Agronomist's or staff computer" "Office or field laptop." "Windows or macOS" {
                deploymentNode "Web browser" "Runs the single-page dashboard." "Chrome, Edge or Safari" {
                    dashboardInstance = containerInstance webDashboard
                }
            }
            deploymentNode "Amazon Web Services" "Chosen for an Australian region and managed services." "Public cloud" {
                deploymentNode "ap-southeast-2 (Sydney)" "All data stays onshore (ADR-05, C2); three availability zones." "AWS region in Australia" {
                    loadBalancer = infrastructureNode "Application Load Balancer" "Terminates TLS and spreads app and dashboard calls over the gateway pods." "AWS ALB"
                    deviceLoadBalancer = infrastructureNode "Network Load Balancer" "Terminates TLS and spreads device MQTT (port 8883) and HTTPS connections over the ingestion pods." "AWS NLB"
                    deploymentNode "Kubernetes cluster" "Runs every service as stateless pods; replaces failed pods." "Amazon EKS, nodes in three zones" {
                        deploymentNode "api-gateway pods" "One per availability zone." "NGINX, 3 replicas" "" 3 {
                            gatewayInstance = containerInstance apiGateway
                        }
                        deploymentNode "telemetry-ingestion pods" "Pod autoscaler adds replicas as reading volume grows (ADR-02)." "Python 3.12, Uvicorn; autoscaled 3 to 30" "" 3 {
                            telemetryInstance = containerInstance telemetryService
                        }
                        deploymentNode "alert-notification pods" "One Kafka consumer per replica." "Python 3.12, Uvicorn; 3 replicas" "" 3 {
                            containerInstance alertService
                        }
                        deploymentNode "farm-access pods" "Low, steady load." "Python 3.12, Uvicorn; 2 replicas" "" 2 {
                            containerInstance accessService
                        }
                        deploymentNode "irrigation-advisory pods" "CPU-optimised nodes." "Python 3.12, ML model; 2 replicas" "" 2 {
                            containerInstance advisoryService
                        }
                        deploymentNode "reporting-compliance pods" "Runs scheduled report jobs." "Python 3.12, Uvicorn; 2 replicas" "" 2 {
                            containerInstance reportingService
                        }
                    }
                    deploymentNode "Amazon MSK" "Topics partitioned by farmId, replicated across zones." "Managed Apache Kafka, 3 brokers" {
                        containerInstance eventBroker
                    }
                    deploymentNode "Time-series database" "24-month retention; older data downsampled (ADR-07)." "TimescaleDB, primary and standby" {
                        containerInstance telemetryStore
                    }
                    deploymentNode "Amazon RDS for PostgreSQL" "Database per service (ADR-07); encrypted at rest." "Multi-AZ, one instance per service" {
                        containerInstance alertDb
                        containerInstance accessDb
                        containerInstance advisoryDb
                    }
                    deploymentNode "Amazon S3" "Versioned bucket, encrypted at rest." "Object storage, Sydney" {
                        containerInstance reportStore
                    }
                }
            }
            deploymentNode "External SaaS" "Reached over HTTPS from the cluster." "Third-party providers" {
                softwareSystemInstance identityProvider
                softwareSystemInstance pushService
                softwareSystemInstance smsGateway
                softwareSystemInstance weatherProvider
            }

            edgeInstance -> deviceLoadBalancer "Sends reading batches, replaying buffered data" "MQTT, JSON/HTTPS"
            phoneAppInstance -> loadBalancer "Makes API calls" "JSON/HTTPS"
            dashboardInstance -> loadBalancer "Makes API calls" "JSON/HTTPS"
            loadBalancer -> gatewayInstance "Forwards user API calls" "HTTPS"
            deviceLoadBalancer -> telemetryInstance "Forwards device traffic" "MQTT, HTTPS"
        }
    }

    views {
        systemContext ozAgriMate "SystemContext" {
            title "System context diagram: OzAgriMate Platform"
            include *
            exclude "pushService -> ozAgriMate"
            autoLayout tb
        }

        container ozAgriMate "Containers" {
            title "Container diagram: OzAgriMate Platform"
            include *
            exclude pushToFarmer
            autoLayout tb
        }

        component telemetryService "TelemetryIngestionComponents" {
            title "Component diagram: Telemetry Ingestion Service"
            include *
            autoLayout tb
        }

        component accessService "FarmAccessComponents" {
            title "Component diagram: Farm & Access Service"
            include *
            include alertService
            exclude gatewayToAlerts
            autoLayout tb
        }

        component alertService "AlertNotificationComponents" {
            title "Component diagram: Alert & Notification Service"
            include *
            autoLayout tb
        }

        dynamic alertService "Runtime1-ThresholdAlert" "A low soil-moisture reading triggers an alert; the farmer is notified by push, with SMS fallback after two minutes." {
            title "Runtime diagram 1: low soil moisture raises an alert, sent by push with SMS fallback"
            iotNetwork -> telemetryService "Posts reading batch: DEV-1001 soil moisture 14.2 %"
            telemetryService -> eventBroker "Publishes TelemetryReceived (key: FARM-001)"
            thresholdEvaluator -> eventBroker "Consumes TelemetryReceived"
            thresholdEvaluator -> ruleManager "Gets rules for WHEAT, RIVERINA-NSW, SOIL_MOISTURE"
            thresholdEvaluator -> alertManager "Raises alert: 14.2 % is below the 20 % minimum"
            alertManager -> eventBroker "Publishes AlertRaised (key: FARM-001)"
            thresholdEvaluator -> notificationDispatcher "Dispatches ALERT-003"
            notificationDispatcher -> pushService "Sends push alert"
            notificationDispatcher -> deliveryTracker "Records PUSH SENT; later finds the push unconfirmed after 2 minutes"
            notificationDispatcher -> smsGateway "Sends SMS, retried up to 3 times"
            smsGateway -> farmer "Texts the alert"
            notificationDispatcher -> deliveryTracker "Records SMS DELIVERED"
            autoLayout lr
        }

        dynamic ozAgriMate "Runtime2-GrantAccess" "A farmer grants an agronomist access; the grant event reaches the alert service, which then serves that farm's alerts." {
            title "Runtime diagram 2: a farmer grants an agronomist access, then the agronomist views that farm's alerts"
            farmer -> mobileApp "Shares farm alerts and telemetry with AGR-001"
            mobileApp -> apiGateway "POST /api/v1/farms/FARM-001/access-grants with bearer token"
            apiGateway -> identityProvider "Validates the token: FARMER-001, role farmer"
            apiGateway -> accessService "Routes the call with X-User-Id: FARMER-001"
            accessService -> accessDb "Checks FARMER-001 owns FARM-001; saves GRANT-002"
            accessService -> eventBroker "Publishes AccessGranted (key: FARM-001)"
            alertService -> eventBroker "Consumes AccessGranted"
            alertService -> alertDb "Stores its copy of GRANT-002 (Farm Access Cache)"
            agronomist -> webDashboard "Opens FARM-001's alerts"
            webDashboard -> apiGateway "GET /api/v1/farms/FARM-001/alerts?status=OPEN with bearer token"
            apiGateway -> identityProvider "Validates the token: AGR-001, role agronomist"
            apiGateway -> alertService "Routes the call with X-User-Id: AGR-001"
            alertService -> alertDb "Checks AGR-001 holds READ_ALERTS on FARM-001; reads OPEN alerts"
            autoLayout lr
        }

        deployment ozAgriMate production "Deployment" {
            title "Deployment diagram: OzAgriMate Platform (production)"
            include *
            autoLayout lr
        }

        styles {
            element "Person" {
                shape Person
                background #08427b
                color #ffffff
            }
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "External" {
                background #999999
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
            element "Component" {
                background #85bbf0
                color #000000
            }
            element "Database" {
                shape Cylinder
            }
            element "Message Broker" {
                shape Pipe
            }
            element "Mobile App" {
                shape MobileDevicePortrait
            }
            element "Web Browser" {
                shape WebBrowser
            }
        }
    }
}
