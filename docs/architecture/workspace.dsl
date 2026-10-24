workspace "OzAgriMate Platform" "C4 model of the OzAgriMate digital agriculture platform (ISYS3459 Assignment 4)." {

    // One model, many views: every C4 diagram in the report comes from this file,
    // so element names, descriptions and relationship labels match across diagrams.
    // Owners: Shikhar - container view and the Telemetry Ingestion and Farm & Access component views;
    //         Pranav  - system context, Alert & Notification component, two dynamic views, deployment.

    model {
        // ---------- People ----------
        farmer = person "Farmer" "Checks readings and alerts, acts on irrigation advice and shares farm data."
        agronomist = person "Agronomist" "Advises client farms remotely using the data farmers share."
        operationsStaff = person "Operations Staff" "Monitor platform health and capacity and support users."

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
                // Pranav: add the Alert & Notification components here (Alert API, Rule Manager,
                // Threshold Evaluator, Alert Manager, Notification Dispatcher, Delivery Tracker).
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
        // Optional: relationships between people, OzAgriMate and the external systems written here,
        // before the container relationships, replace the labels Structurizr would otherwise imply.

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

        // ---------- Deployment (Pranav) ----------
        // deploymentEnvironment "Production" {
        //     deploymentNode ... { containerInstance telemetryService }
        // }
    }

    views {
        // Pranav: System Context view
        // systemContext ozAgriMate "SystemContext" {
        //     title "System context diagram: OzAgriMate Platform"
        //     include *
        //     autoLayout lr
        // }

        container ozAgriMate "Containers" {
            title "Container diagram: OzAgriMate Platform"
            include *
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

        // Pranav: Alert & Notification component view
        // component alertService "AlertNotificationComponents" {
        //     title "Component diagram: Alert & Notification Service"
        //     include *
        //     autoLayout lr
        // }

        // Pranav: runtime views (each step must match a relationship in the model)
        // dynamic * "Runtime1-ThresholdAlert" "A soil-moisture reading breaches a threshold; push first, SMS if undelivered." { ... }
        // dynamic * "Runtime2-GrantAccess" "A farmer grants an agronomist access, who then views that farm's alerts." { ... }

        // Pranav: deployment view
        // deployment * "Production" "Deployment" { include * autoLayout lr }

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
