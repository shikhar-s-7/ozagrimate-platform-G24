# Architecture documentation

| Path | What it is |
|---|---|
| `architecture/workspace.dsl` | The C4 model in Structurizr DSL: every person, software system, container and component, and every relationship. One model, many views. |
| `diagrams/*.puml` | C4-PlantUML source for each diagram in the report, written with exactly the element names, descriptions and relationship labels in `workspace.dsl`. |
| `diagrams/*.png`, `diagrams/*.svg` | The rendered diagrams. Use the SVG in the report where possible, because it stays sharp at any zoom. |

## Diagrams

| Diagram | Source | Owner |
|---|---|---|
| System context | `diagrams/system-context.puml` (to add) | Pranav |
| Container | `diagrams/container.puml` | Shikhar |
| Component: Telemetry Ingestion Service | `diagrams/component-telemetry-ingestion.puml` | Shikhar |
| Component: Alert & Notification Service | `diagrams/component-alert-notification.puml` (to add) | Pranav |
| Component: Farm & Access Service | `diagrams/component-farm-access.puml` | Shikhar |
| Runtime 1: threshold alert, push then SMS | `diagrams/runtime-1-threshold-alert.puml` (to add) | Pranav |
| Runtime 2: farmer grants access, agronomist views alerts | `diagrams/runtime-2-grant-access.puml` (to add) | Pranav |
| Deployment | `diagrams/deployment.puml` (to add) | Pranav |

Component names are the package names in the code: Device Registry is `telemetry_ingestion/device_registry/`, Grant Manager is `farm_access/grant_manager/`, and so on (see the repository README).

## Rendering

The `.puml` files need PlantUML 1.2024 or newer, which bundles the C4-PlantUML library (`!include <C4/...>`), plus Graphviz. Any of these works:

- `java -jar plantuml.jar -tpng -tsvg docs/diagrams/*.puml`
- the PlantUML extension for VS Code;
- the online server at https://www.plantuml.com/plantuml.

To keep all eight diagrams looking the same, start every `.puml` file with the same settings as `container.puml`:

```plantuml
skinparam dpi 150
skinparam wrapWidth 220
skinparam defaultFontName Arial
SHOW_PERSON_OUTLINE()
' ... elements and relationships ...
SHOW_LEGEND(false)
```

`SHOW_LEGEND(false)` keeps the element type, such as «container» or «person», visible inside every box.

`workspace.dsl` opens in Structurizr, for example by pasting it into the DSL editor at https://structurizr.com/dsl. It has commented slots for the system context, Alert & Notification component, dynamic and deployment views.
