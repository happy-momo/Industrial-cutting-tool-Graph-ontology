# Industrial Cutting Tool Knowledge Graph: Ontology Design and Engineering Validation

*From heterogeneous vendor catalogs to a verifiable OWL-driven knowledge architecture*

Technical Design Report  |  Version 1.0  |  28 October 2026

# Executive summary

This document consolidates the original user-authored AI Design research, the subsequent node and relationship optimization proposals, and the V1.0–V1.2 ontology project. It emphasizes design rationale, a repeatable modeling method, semantic governance, executable constraints, representative use cases, delivered artifacts, test evidence, and limits of validation. The target architecture separates OWL as the normative semantic model, SKOS as the controlled vocabulary, SHACL as RDF data validation, JSON Schema as exchange contract, and Neo4j as an application-oriented property-graph projection.

| Core dimension | Current status |

| --- | --- |

| Semantic standards | OWL + SKOS |

| 数据质量 / Validation | SHACL + JSON Schema |

| 应用存储 / Graph | Neo4j projection |

| 工程验证 / Tests | 386 PASS; 8 source identifiers; 2 regression tests |

# 1. Background and problem definition

Cutting-tool catalogs contain a mixture of product taxonomies, geometry, substrate and grade data, insert-holder compatibility, machining processes, and recommended cutting conditions. The original study surveyed six manufacturers across domestic, Japanese/Korean and European/American groups. Vendors differ in naming, product hierarchies, tooling series and materials taxonomies. Transcribing any single catalog hierarchy directly into a universal graph risks treating vendor-specific organization as domain truth.

The original Design document established a local-to-global modeling method: collect and classify source information, harmonize concepts, build local graph models for inserts, holders, solid tools, materials and parameters, then integrate them. This remains the methodological foundation of the updated architecture.

The objective is not merely conversion of tables into nodes and edges. It is a traceable, interoperable knowledge model that supports cross-vendor discovery, validated ingestion, compatibility lookup, conditional machining recommendations, source-backed answers and future GraphRAG applications.

# 2. Evolution and architectural decisions

Original model: five catalog-oriented taxonomies and several local property graphs were combined around relations such as contains, machining method, material, compatibility and cutting parameters. It preserved information effectively but overloaded contains with subclass and instance-membership semantics. Vendor directories also mixed classification dimensions.

Property-graph redesign: Tool was separated into Insert, Holder and SolidTool. The material model gained ToolGrade, substrate and coating; the catalog model gained Manufacturer and ProductSeries; recommendations gained context and provenance. Previously broad membership predicates were replaced with business-specific edges.

Semantic-first architecture: Neo4j labels and relationships were explicitly identified as a property-graph schema, not an OWL ontology. OWL classes represent domain entity kinds, while SKOS concepts represent vocabulary terms such as external turning, high-feed milling and ISO material groups.

Executable constraints: OWL retains semantic authority, but field verification is maintained in a contract registry, mapped into JSON Schema, SHACL and Neo4j constraints. OWL’s open-world reasoning must not be confused with closed-world ingestion validation.

# 3. End-to-end design method

1. Analyze source manuals with provenance: manufacturer, catalog version, page/table, extraction evidence, product code and grade identifier. Preserve original terms.

2. Separate information kinds: OWL classes such as Insert and ToolGrade, SKOS-controlled classifications, scalar properties such as dimensions, and reusable entities such as manufacturer, grade and workpiece material.

3. Design local models for tooling, material, machining, catalog and evidence, then align them through stable product identities, grades, processing methods and recommendation contexts. Preserve distinctions made by the source rather than flattening them.

4. Define stable IRIs, OWL class hierarchy, object and datatype properties, domain/range and scoped restrictions; independently maintain SKOS concept schemes and vendor mappings. Domain and range carry entailment semantics, not database-style rejection behaviors.

5. Define executable required/type/enum/range/pattern rules in the contract registry and generate corresponding JSON, SHACL and Neo4j artifacts through curated name mapping.

6. Test real identifiers extracted from the user research and synthetic positive/negative records. Verify cross-layer consistency and investigate semantic side effects rather than patching only the last failing serializer.

# 4. Semantic layers and responsibility boundaries

OWL: defines tool and material identity, subclass structure, grade composition, machining and recommendation semantics. It is the semantics authority, not a mandatory-field gate.

SKOS: defines controlled taxonomies, aliases, broader/narrower terms and source-to-standard catalog mapping. skos:broader is not automatically equivalent to rdfs:subClassOf.

SHACL: validates RDF graphs against data-completeness and shape rules. JSON Schema validates exchange and ingestion payloads. Cross-field formulas, units and conditional cardinalities may require application rules or SHACL-SPARQL.

Neo4j: maps OWL classes to labels, object properties to named relationship types, and adds database-specific uniqueness and indexes. Preserve IRIs and source references during projection. Its constraints cannot replace semantic reasoning or validation.

# 5. Seven business modules and representational choices

Taxonomy: ToolType, ProcessMethod and MaterialClass link standard semantic kinds to managed vocabularies, without an arbitrary three-level limit. Products: Tool identifies a catalog-level product specification; Insert, Holder and SolidTool refine it. Physical inventory items are a separate future type.

Tool materials: ToolGrade preserves vendor grade labels such as GPT6110; MaterialSubstrate and MaterialCoating describe construction, while PVD/CVD are manufacturing/coating processes rather than chemical compounds. Workpiece: MaterialClass, MaterialGrade and Workpiece distinguish classification, grade and a concrete material/state.

Manufacturers: Manufacturer, ProductSeries and CatalogCategory preserve commercial catalog information and enable reviewed mappings to standard terms instead of claiming automatic equivalence.

Recommendations: CuttingRecommendation references tool/series/grade scope, material applicability, ProcessMethod, CuttingCondition and CuttingParam. Feed variants fn, fz and vf and units are integral semantics, not cosmetic attributes.

Provenance: SourceDocument and SourceEvidence attach record version, page and locator. Wildcard identifiers such as CN**1204* designate compatibility specifications, not a concrete Insert individual.

# 6. Competency questions and usage scenarios

Cross-vendor search: starting from normalized tool/machining SKOS categories, retrieve series across multiple manufacturers while preserving their native catalog groupings.

Insert-holder compatibility: return confirmed FITS_WITH evidence first; otherwise compute candidates through InsertSpecification and mark unverified matches as candidates rather than factual compatibility.

Material-specific recommendations: retrieve candidate tooling through grade-to-material applicability, then constrain cuts by material state, process, conditions, parameter range, units and documented source. Broad suitability must never be treated as a precise numerical cutting recommendation.

GraphRAG / agents: map user intent into ontology-aligned queries and return evidence-backed answers. An absent source or unknown machining condition should remain explicitly unknown.

# 7. Engineering deliverables and observed tests

V1.0 established the OWL/SKOS/SHACL/JSON/Neo4j engineering structure. V1.1 added executable field registries. V1.2 implemented a repeatable generator and consistency checks with documentation and examples. The V1.2 archive contains 52 files.

Observed V1.2 offline outcomes: 386 consistency checks passed with zero failures; eight identifiers from the user-provided source text passed structural schema checks; a valid SHACL fixture passed and an invalid fixture was rejected; two regression tests passed. Outputs include 24 JSON class schemas, 706 generated SHACL RDF triples, 24 Neo4j uniqueness statements and 24 Enterprise property-existence statements.

Testing exposed a model defect: a shared status property with multiple RDFS domains could infer that an Insert was also a CuttingRecommendation. The implementation removed the shared domain and scoped status values through class-level validations. The preferred long-term refinement is separate toolStatus and recommendationStatus properties.

Test scope must be stated accurately. Identifier strings were observed in the original user document, but their complete manufacturer datasheet specifications were not independently verified. No actual product geometry or cutting values were inferred. Live Neo4j transaction tests and a dedicated OWL DL reasoner were not run.

# 8. Governance and quality standards

Identity management requires controlled, persistent IRIs and stable entity keys. Per-fact source evidence, catalog versions, assertion status and mapping confidence should be carried through ingestion. The existing example.org namespace is a placeholder and must be replaced before production.

Change management proceeds from semantic review through field-contract update, regeneration of SHACL/JSON/Cypher, regression testing, vetted data ingestion and spot audits. Rule ownership and validation outcomes must be versioned.

Principal risks include shared-domain entailments, nontrivial multi-layer coatings, inconsistent units and hardness scales, workpiece heat-treatment conditions, wildcard compatibility codes, unreviewed cross-vendor equality matches and information loss during source extraction.

# 9. Current status, remaining acceptance criteria and conclusion

The delivered system is a verified offline ontology/schema engineering baseline, not a populated six-vendor production knowledge base. Production sign-off requires audited vendor catalog samples, live Neo4j DDL and Cypher tests, dedicated OWL DL consistency reasoning, richer structural SHACL constraints and business validation of feed, tooling fit and numerical units.

The central contribution is a transferable local-to-global, ontology-driven engineering method: retain the original data-analysis strengths; use OWL for common semantics, SKOS for vocabulary decisions, SHACL and JSON for enforceable quality contracts, Neo4j for operational graph queries, and traceability plus tests across the pipeline.

# Appendix A. Evidence and standards

Project evidence: [I1] User-provided docs; [I2] user-authored node/edge optimization plan and ensuing architecture discussions; [I3] Cutting Tool Ontology V1.2 archive, README, design notes and verification.json (offline report of 386 passing checks).

Standards and implementation references: [S1] W3C OWL 2 Overview, https://www.w3.org/TR/owl2-overview/; [S2] W3C SKOS Reference, https://www.w3.org/TR/skos-reference/; [S3] W3C SHACL, https://www.w3.org/TR/shacl/; [S4] Neo4j Cypher Constraints Documentation, https://neo4j.com/docs/cypher-manual/current/schema/constraints/.
