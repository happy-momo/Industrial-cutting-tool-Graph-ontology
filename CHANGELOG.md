# Changelog / 更新日志

All notable changes to this project should be recorded here. Versions refer to engineering baselines, not production certification.

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
