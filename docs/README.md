# Architecture documentation

| Path | What it is |
|---|---|
| `architecture/workspace.dsl` | The C4 model in Structurizr DSL: every person, software system, container and component, and every relationship. One model, many views. |
| `diagrams/*.puml` | C4-PlantUML source for the PlantUML diagrams, written with exactly the element names, descriptions and relationship labels in `workspace.dsl`. |
| `diagrams/*.mmd` | Mermaid source for the Mermaid diagrams (see the table below). Same elements, technologies and relationships as `workspace.dsl`, with shorter descriptions and labels so they stay readable on an A4 page. |
| `diagrams/*.png`, `diagrams/*.svg` | The rendered diagrams. Use the SVG in the report where possible, because it stays sharp at any zoom; for the Mermaid diagrams use the PNG (see Rendering). |

## Diagrams

| Diagram | Source | Owner |
|---|---|---|
| System context | `diagrams/system-context.puml` | Pranav |
| Container | `diagrams/container.mmd` (Mermaid) | Shikhar |
| Component: Telemetry Ingestion Service | `diagrams/component-telemetry-ingestion.mmd` (Mermaid) | Shikhar |
| Component: Alert & Notification Service | `diagrams/component-alert-notification.puml` | Pranav |
| Component: Farm & Access Service | `diagrams/component-farm-access.mmd` (Mermaid) | Shikhar |
| Runtime 1: threshold alert, push then SMS | `diagrams/runtime-1-threshold-alert.puml` | Pranav |
| Runtime 2: farmer grants access, agronomist views alerts | `diagrams/runtime-2-grant-access.puml` | Pranav |
| Deployment | `diagrams/deployment.puml` | Pranav |

Component names are the package names in the code: Device Registry is `telemetry_ingestion/device_registry/`, Grant Manager is `farm_access/grant_manager/`, and so on (see the repository README).

## Rendering

The `.puml` files need PlantUML 1.2024 or newer, which bundles the C4-PlantUML library (`!include <C4/...>`), plus Graphviz. Any of these works:

- `java -jar plantuml.jar -tpng -tsvg docs/diagrams/*.puml`
- the PlantUML extension for VS Code;
- the online server at https://www.plantuml.com/plantuml.

Large diagrams such as the deployment diagram need `PLANTUML_LIMIT_SIZE=8192`, or PlantUML crops them at 4096 px.

To keep the PlantUML diagrams looking the same, start every `.puml` file with these settings:

```plantuml
skinparam dpi 150
skinparam wrapWidth 220
skinparam defaultFontName Arial
SHOW_PERSON_OUTLINE()
' ... elements and relationships ...
SHOW_LEGEND(false)
```

`SHOW_LEGEND(false)` keeps the element type, such as «container» or «person», visible inside every box.

The `.mmd` diagrams are Mermaid and use Mermaid's ELK layout. Paste one into https://mermaid.live, or render it with mermaid-cli, for example `npx -p @mermaid-js/mermaid-cli mmdc -i docs/diagrams/container.mmd -o docs/diagrams/container.png -s 3`. Use their PNGs in Word: Mermaid's SVG draws the text as HTML, which Word does not display.

`workspace.dsl` opens in Structurizr, for example by pasting it into the DSL editor at https://structurizr.com/dsl. It defines all eight views: system context, containers, the three component views, the two dynamic (runtime) views and the production deployment view. `structurizr-cli validate -workspace docs/architecture/workspace.dsl` checks it.
