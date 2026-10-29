# Changelog / 更新日志

All notable changes to this project should be recorded here. Versions refer to engineering baselines, not production certification.

## [1.4.1-pilot] - End-to-end subgraph pilot

Initial end-to-end validation that the architecture carries a real repository pipeline (`standardize → validate → project → load Neo4j → query`) without touching the core `src/` toolchain.

- Added `pilot/`: a self-contained two-fixture subgraph (positive 12 entities / 13 relationships; negative with cross-scheme / dangling `concept_ref` and an absent relation id).
- Added `pilot/validate_catalog.py` — reuses `src.validator.validate_entity` (+ `concept_ref` semantics) and adds relationship definition / id-integrity checks, including subclass-aware source/target matching (an `Insert` entity satisfies a declared `Tool` relation source).
- Added `pilot/project_to_cypher.py` — deterministic, repeatable Cypher (id-uniqueness constraints + node MERGE + relationship MATCH/MERGE), aligned to `mappings/ontology-neo4j.yaml`.
- Added `pilot/run_neo4j.sh` / `load_neo4j.py` / `query_neo4j.py` — Docker Neo4j 5-community on non-conflicting host ports (7475/7689) and driver-based load + representative queries.
- Verified end-to-end: 4 offline tests pass; `LOADED: 12 nodes, 13 relationships` in a live Neo4j; 3/3 representative queries pass (series traversal, grade→material suitability, evidence-backed recommendation chain); idempotent re-load stays 12/13; full baseline regression stays green.
- Landed "relationship invariants to the Neo4j side": added online relationship-rule checks in `pilot/` (`neo4j_rules.py`, `verify_neo4j_rules.py`) mirroring the four SHACL rules in `shapes/relation-shapes.ttl` as violation-detecting Cypher, run on load and via CLI (non-zero exit on violation); verified on the live graph: clean subgraph passes all 4, injected violations are detected, cleanup restores a clean pass.
- Centralized the project namespace into a single source of truth: `src/namespaces.py` (`ON_BASE` / `VOCAB_BASE`) now drives the generator, scripts and tests; the `example.org` placeholder value is retained, and swapping it is a two-line change + regenerate (single swap point, verified no drift by a regression test).
- Completed the document-anchored ingestion sample: `examples/document-anchored-tool-identifiers.json` is now a contract-compliant, near-real sample — non-contract fields (`description`/`verification_status`) are cleaned, and tool records are anchored via a `forTool → supportedBy → fromDocument` provenance chain. It passes the offline validator, projects to deterministic Cypher, and loads idempotently into Neo4j (`tests/test_document_identifiers.py`).
- Resolve turned noise-robust: `resolve_skos` gained a normalization layer (`normalize()` — language-tag strip, NFKC full→half-width folding, a small explicit traditional→simplified table, ASCII case-folding, whitespace collapse) plus an ambiguity-preserving token-containment resolver `resolve_tokens()`. Exact-match stays first and all hits are returned; nothing is guessed.
- Closed the remaining loop gaps in the four foundation layers: unknown entity fields now hard-fail projection (no silent pass-through); duplicate entity ids are rejected off-line; id-uniqueness constraints are single-sourced (`src/neo4j_constraints.py`), fixing a projector/generator name divergence; R2/R3 gained online negative-parity cases; a node-level rule R5 mirrors the vocabulary-binding invariant (controlled-class `conceptRef` must anchor in `VOCAB_BASE`); the feed-type/feed-unit pairing is single-sourced (`src/feed_units.py`) across the off-line validator and R4; and the `concept_ref` URL patterns are now derived from `VOCAB_BASE`, leaving no raw namespace literal in the contract.
- Changes NOT made here (identified, left for a follow-up decision): nothing blocking — namespace value, token-containment breadth (full simplified-traditional conversion), and scale are the remaining engineering tail.

## [1.4] - Vocabulary-enforced semantic alignment

- Closed the gap between the controlled SKOS vocabularies and instance validation: the controlled classes `ToolType` / `ProcessMethod` / `MaterialClass` now require a `concept_ref` field that must point at a real concept in their bound scheme (auto-generated into JSON Schema + SHACL pattern, and enforced by the application validator).
- Added `src/resolve_skos.py`, a vocabulary-aware normalization layer that resolves any canonical label or manufacturer alias ("ISO车削", "整体硬质合金铣刀") back to the stable concept URI, and surfaces cross-scheme/cross-branch ambiguity for human review instead of guessing.
- Added `skos:scopeNote` provenance to every cross-manufacturer alignment decision so normalization is auditable; ambiguous terms are reported (advisory) by `scripts/validate_skos.py`, which now also fails on any unresolved `concept_ref` in examples.
- Extended the regression suite with `tests/test_semantic_alignment.py` (resolver, validator enforcement, generated-schema binding checks).
- Documented the "controlled vocabulary is the value-space" principle and the `resolve_skos` normalization entry point in the READMEs.
- Polished the READMEs and design reports to high-standard OSS shape: badge strip, table of contents, tech-stack and roadmap sections, Mermaid diagrams for the architecture, ontology hierarchy, graph model and normalization flow, and corrected stale version/verification figures. The personal origin narrative was relocated to `docs/origin.md` so the technical docs stay concise.

## [1.3] - Relationship rules and open-source baseline

- Expanded the SKOS controlled vocabularies into the five thesis taxonomy trees (tools, processes, materials, manufacturers, cutting parameters) with `skos:broader` hierarchy and cross-manufacturer `skos:altLabel` aliases.
- Added relationship-level SHACL rules in `shapes/relation-shapes.ttl` (evidence traceability, insert/holder mounting contract, recommended-speed range, feed unit consistency).
- Added `feed_type`/`feed_unit` consistency checks to the application validator (`src/validator.py`).
- Reintroduced the regression test suite under `tests/` with lightweight and RDF/SKOS/SHACL groups, plus a `scripts/validate_skos.py` vocabulary check.
- Added MIT license, `.gitignore` and a GitHub Actions CI workflow (generate → verify → pytest → drift check).
- Documented `RecommendationRecord` as an aggregate view (not an OWL class) to resolve registry/schema source-of-truth confusion.

## [1.2] - Validation and generation baseline

- Added repeatable generation of JSON Schema, SHACL field shapes and Neo4j constraints.
- Added recorded identifier fixtures and offline cross-layer consistency tests.
- Added positive and negative SHACL cases and regression tests.
- Removed an ambiguous shared `status` domain responsible for incorrect RDFS type inference.
- Documented unsupported validation boundaries and deployment prerequisites.
- Expanded bilingual open-source-style documentation without personal or educational information.

## [1.1] - Field contract baseline

- Introduced a centralized field registry, mapped property labels, generated schemas and validation utilities.

## [1.0] - Ontology baseline

- Defined initial OWL vocabulary, SKOS taxonomies, graph mapping, and basic example fixtures.

## 中文说明

- **v1.4：** 打通「SKOS受控词表 ↔ 实例校验」闭环：受控类 ToolType/ProcessMethod/MaterialClass 现必须携带 `concept_ref` 指向其绑定词表的真实概念（自动落入 JSON Schema/SHACL 并由应用校验强制）；新增 `src/resolve_skos.py` 归一化层，将厂商别名（ISO车削、整体硬质合金铣刀）还原为规范概念 URI，并把跨词表/跨分支歧义显式暴露给人工复核而非擅自猜测；为每条跨厂商对齐补 `skos:scopeNote` 溯源；`validate_skos` 新增「未解析 concept_ref 即失败」与「歧义词表项告警」；新增语义对齐回归测试。
- **v1.3：** 将SKOS词表扩展为论文中的五棵分类树并加入跨厂商别名；新增关系级SHACL规则与进给单位一致性校验；补回回归测试与SKOS校验脚本；加入MIT许可证、.gitignore与CI；并明确RecommendationRecord为聚合视图而非OWL类。
- **v1.2：** 增加约束生成器、跨层静态与SHACL测试、文档型号样本、错误推理修复和中英文项目文档。
- **v1.1：** 引入字段约束注册表及Schema校验工具。
- **v1.0：** 建立OWL本体、SKOS术语和初始图谱映射。
