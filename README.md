# Industrial Cutting Tool Ontology

**An ontology-driven, validation-first foundation for cutting-tool knowledge graphs.**

[简体中文](README.zh-CN.md) | **English**

> **Project status:** v1.2 research/engineering baseline. The generators and offline validations are implemented; this is **not a production-ready tooling-recommendation system**, and no live Neo4j deployment or full OWL DL reasoning run is claimed.

# Why This Project Exists

This project is an extension of the Neo4j-based property graph schema I designed during my master's studies.

Back then, my original goal was to develop a standardized schema for property graph models. I wanted to create a unified structure that could organize and manage unstructured, heterogeneous manufacturing tool data from different manufacturers, covering various types of cutting tools, products, materials, and machining processes, all under a consistent set of definitions and constraints.

Most of my work at that time involved collecting data from manufacturers, analyzing data structures, and identifying the relationships between different types of cutting tools, products, materials, and other related entities. By understanding and abstracting these relationships, I hoped to eventually establish a unified schema capable of representing all this information.

To be honest, much of that work was quite tedious.

Day after day, I searched for data, downloaded catalogs, went through technical documents, and organized information piece by piece. It was a process that required a great deal of patience and persistence.

What made it even more challenging was that I wasn't entirely sure what I was working toward. I didn't really know how meaningful my research would turn out to be, or how much practical value it could eventually create.

Looking back now, however, I realize that the most valuable thing I gained from that experience wasn't necessarily the technical outcome itself.

It was the personal growth that came along with it.

That period taught me how to slow down, how to be more patient, and how to remain committed to something I genuinely believed was worth doing, even when the results were uncertain.

And I believe these lessons have become increasingly valuable in today's world.

We live in a time when AI technologies and countless new challenges are constantly transforming the world around us. Everything seems to be moving faster and faster, and the pressure to keep up with that pace only continues to grow.

As individuals, I believe it is becoming increasingly important to develop the ability to reduce the impact of these external pressures on ourselves.

Because thinking matters. And sometimes, slowing down matters just as much.

Thanks to those years of research, I developed a little more resilience and patience. When facing uncertainty, pressure, or unexpected challenges, I now find myself better able to pause, reflect, and approach problems with a calmer and more focused mindset.

I am especially grateful to my academic supervisor.

During my master's studies, he met with me one-on-one every week, patiently guiding me through the details of my research and helping me find the right direction.

But more importantly, he taught me something that has stayed with me ever since.

He once told me:

"Good ideas and great designs don't simply appear in a sudden moment of inspiration. They emerge from countless days and nights of learning, thinking, and accumulating knowledge about technology, industry, and your own research interests. They are shaped by real work, practical experience, and the projects you have been through.

Slow down. Take your time. Think deeply."

These words have stayed with me, and I believe they will continue to guide me throughout my life.

I would also like to take this opportunity to wish my supervisor a wonderful and fulfilling retirement!

The idea of restarting this project came to me quite suddenly.

One day, the research I had put aside since graduate school somehow resurfaced in my mind.

I started thinking that perhaps the work I had done back then still had some value.

And after spending several years working in the industry, I have become increasingly convinced that data standardization and semantic alignment are becoming more important than ever in industrial applications.

This is especially true in the age of AI.

No matter how powerful AI models become, the quality of the underlying data fundamentally determines how well they can perform.

Industrial data, by its very nature, is highly heterogeneous. It comes from different manufacturers, systems, standards, and engineering practices. The same concept may be described in different ways, while similar terms may carry completely different meanings depending on the context.

Without a consistent semantic foundation, integrating, understanding, and effectively utilizing such data becomes extremely difficult.

And that is exactly why I believe we need a standardized way to represent and organize industrial knowledge.

So I decided to revisit my original research, rethink some of the design decisions, and improve the architecture based on what I have learned since then.

This project is the result of that process.

I have chosen to make it open source, hoping that the ideas, designs, and experiences shared here might be useful to others who are working on similar challenges.

Whether you are a student exploring knowledge graphs, a researcher working on industrial knowledge representation, or an engineer trying to make sense of complex manufacturing data, I sincerely hope you can find something valuable in this project.

Thank you for everything. 

## Overview

Industrial cutting-tool catalogs use heterogeneous terminology and structures for inserts, holders, solid tools, tool grades, workpiece materials, machining methods, and recommended cutting parameters. This project establishes a common semantic vocabulary and machine-readable contracts to reduce schema drift across RDF data, JSON interfaces, and a Neo4j property-graph projection.

**What it does**

- Models domain classes and object/data properties in **OWL 2**.
- Maintains example classification vocabularies in **SKOS** rather than treating every taxonomy term as an OWL class.
- Uses a controlled **field registry** to generate JSON Schema, SHACL field constraints, and Neo4j Cypher constraint scripts.
- Runs offline checks for OWL vocabulary alignment, JSON validity, SHACL positive/negative fixtures, documented model identifiers, and projected constraint coverage.
- Records verification results in a machine-readable report.

**Out of scope in this release:** full catalog ingestion, vendor-independent product property verification, engineering-grade cutting recommendations, live-database deployment, and complete OWL DL consistency proofs.

## Architecture and sources of authority

| Layer | Role | Location |
| --- | --- | --- |
| OWL | Semantic definitions, class taxonomy and property meaning | `ontology/cutting-tool.owl` |
| SKOS | Controlled classification vocabulary | `vocabulary/` |
| Field contract | Required fields, types, ranges, patterns, enums | `contract/field-registry.yaml` |
| Mapping | Field/property labels and graph projection conventions | `mappings/ontology-neo4j.yaml` |
| SHACL | Generated RDF data-shape checks | `shapes/generated-shapes.ttl` |
| JSON Schema | Generated JSON object validation | `schemas/` |
| Neo4j | Generated Community uniqueness / Enterprise existence constraints | `neo4j/` |

The OWL ontology is the **semantic authority**, while the registry is the **validation-rule authority**. They are aligned by mapping and cross-layer tests. OWL's open-world semantics must not be mistaken for a closed-world input validator. Neither SHACL nor database constraints fully replace application-level business validation.

## Domain model

The baseline covers 24 modeled entity classes, including:

- **Products:** `Tool`, `Insert`, `Holder`, `SolidTool`, `InsertSpecification`
- **Materials:** `ToolGrade`, `MaterialSubstrate`, `MaterialCoating`, `MaterialGrade`, `Workpiece`
- **Classification:** `ToolType`, `ProcessMethod`, `MaterialClass`, `SubstrateType`
- **Catalogs:** `Manufacturer`, `ProductSeries`, `CatalogCategory`
- **Recommendations and evidence:** `CuttingRecommendation`, `CuttingCondition`, `CuttingParam`, `SourceDocument`, `SourceEvidence`

Example use cases: cross-catalog lookup, tool-grade-to-material matching candidates, verified insert/holder compatibility, constraint-aware cutting-parameter records, and evidence traceability. **Candidate compatibility is not a verified fit, and a record is not operational machining advice.**

## Requirements

- Python 3.10+ (recommended)
- See [`requirements.txt`](requirements.txt) for all Python dependencies.
- A Neo4j server is **not** needed for offline generation and verification. Live database use requires a separately provisioned compatible server and permissions.

## Quick start

From the repository root:

```bash
python -m venv .venv
```

Activate the environment on macOS/Linux:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies and run checks:

```bash
python -m pip install -r requirements.txt
python -m src.generate_constraints
python -m src.verify_consistency
python -m pytest tests/test_regression.py -q
```

> `pytest` is a development/test dependency. If it is not installed, run `python -m pip install pytest` before the final command.

The generator updates `schemas/`, `shapes/generated-shapes.ttl`, and the two `neo4j/*constraints.cypher` files. The verifier writes `reports/verification.json`.

## Using a schema and validating data

You can validate a JSON instance, for example [`examples/Insert.json`](examples/Insert.json), against the generated Insert schema:

```python
import json
from pathlib import Path
from jsonschema import validate

schema = json.loads(Path('schemas/Insert.schema.json').read_text(encoding='utf-8'))
data = json.loads(Path('examples/Insert.json').read_text(encoding='utf-8'))
validate(instance=data, schema=schema)
print('Valid')
```

For RDF integrity checks, refer to `src/verify_consistency.py`, which invokes `pyshacl` with the generated Shacl shapes and the ontology graph. For cross-field recommendation checks, see `src/validator.py`.

## Project layout

```text
ontology/        OWL ontology definition
vocabulary/      SKOS controlled vocabularies
contract/        Field specification and constraint source
mappings/        OWL / data / Neo4j naming and relation mapping
schemas/         Generated JSON Schemas
shapes/          Generated SHACL shapes
neo4j/           Generated Cypher constraint scripts
src/             Constraint generator and validators
examples/        JSON, RDF, and document-anchored identifier fixtures
tests/           Regression and negative test cases
reports/         Verification results
docs/            Design decisions, validation boundaries, and analysis
```

## Current verification baseline

The packaged v1.2 verification run reports **386 successful offline checks and zero failures**, including 8 identifier records selected from the underlying design examples. A SHACL positive case passes and a negative missing-ID case is rejected; two regression tests passed. See [`reports/verification.json`](reports/verification.json) for the exact recorded results. These checks **do not establish product-specification accuracy**. The identifier examples reflect recorded strings, not independently verified manufacturer datasheets.

Not yet verified: actual Neo4j constraint execution, full OWL DL reasoner consistency, live graph queries, complete SHACL-SPARQL relationship rules, vendor-specific machining conditions, or load/performance behavior.

## Maintaining and extending the schema

1. Define or modify semantic classes/properties in `ontology/cutting-tool.owl`.
2. Revise the field obligations in `contract/field-registry.yaml` and name projections in `mappings/ontology-neo4j.yaml`.
3. Run the generator and cross-layer verifier.
4. Add positive and negative fixtures for new fields, classes, and relationships.
5. Review generated diffs before committing; perform supported Neo4j integration tests separately.

**Known semantic pitfall:** the shared `status` property must not acquire multiple `rdfs:domain` statements that imply unrelated classes. This version avoids that error; a future migration may use `toolStatus` and `recommendationStatus`.

**URI policy:** `https://example.org/` is a placeholder namespace. Establish a persistent project-owned namespace before publishing production-linked RDF.

## Data provenance and safety

Examples are development fixtures and symbolic identifiers, **not authenticated product recommendations**. Never infer actual performance, insert/holder fit, speed/feed/depth values, or equipment safety from the example dataset. Production ingestion should retain source publication, revision, page/table evidence, review status, measurement units, and applicability conditions.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for style, testing, review, and issue-reporting guidelines. Please do not add personal, student, university, or confidential company details to documentation, examples, commits, or issue attachments. Use anonymized test fixtures and source data that you are permitted to redistribute.

## Security

See [SECURITY.md](SECURITY.md). Please avoid disclosing secrets, customer data, internal catalog extracts, or operational credentials in public reports.

## Acknowledgment of standards

The project uses W3C OWL 2, SKOS and SHACL conventions, JSON Schema Draft 2020-12, and Neo4j Cypher concepts. These references describe technical interoperability and do not imply endorsement.
