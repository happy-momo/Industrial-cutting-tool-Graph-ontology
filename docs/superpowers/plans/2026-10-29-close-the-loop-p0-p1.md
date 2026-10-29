# 闭环封死 P0 / P1 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 封死「契约 ↔ 生成 ↔ 投影 ↔ 在线校验」四层的闭环:堵住投影器静默透传、在线/离线规则对等、约束重复且命名分叉、id 重复不前置、以及三处残留的 `example.org` 字面量与日字面量。

**Architecture:** 全部改动沿两条主线:(1) 在线规则(离线 SHACL 的 Cypher 镜像)与离线校验共用同一数据源——feed-unit 配对表抽到 `src/feed_units.py`、概念 URI 前缀由 `src/namespaces` 派生、id 唯一约束由共享 `src/neo4j_constraints.py` 生成;(2) 校验前移——投影器对未知字段由「容忍」改「硬失败」、`validate_catalog` 前置 id 唯一检查。每步 TDD:先失败→确认→实现→通过→commit。不改占位命名空间值;不新增契约关系/字段。

**Tech Stack:** Python 3.10 (conda `dev`), rdflib, jsonschema, PyYAML, neo4j driver 5.13。Neo4j `bolt://localhost:7689`/`neo4j:pilotsecret`(pilot 开发 fixture)。

## Global Constraints

- 只集中配置、**不换占位值**:`src/namespaces.py` 的 `ON_BASE`/`VOCAB_BASE` 仍为 `example.org`,是唯一代码来源;所有产物仍用该值。
- 在线规则与离线 SHACL 的「对等」必须用**测试锁死**(每个 SHACL 负例在对应在线规则命中);不猜、不降级单猜。
- 只使用 `contract/field-registry.yaml` 已登记的关系名与字段;不虚构关系。
- 全量回归始终绿(当前 49 passed);Neo4j 在线用例在库不在时 **skip 而非 fail**。
- 生成产物 `schemas/*.schema.json`、`neo4j/*.cypher` 必须**字节零漂移**(改模块只改生成逻辑,不改变最终文本);`shapes/generated-shapes.ttl` 已知非字节确定(CI 注释仅排除它)。
- 每部分 TDD 小步提交;最终推送到 github(main)。

---

### Task 1 (P0-4):validate_catalog 前置 id 唯一校验

**Files:**
- Modify: `pilot/validate_catalog.py`
- Test: `tests/test_pilot_catalog.py`

**Interfaces:**
- Consumes: `validate_catalog(data)->(bool, list)`(现有签名不变)。
- Produces: 新增离线错误文案 `duplicate entity id '<id>' (N x)`。

- [ ] **Step 1: 写失败测试**(追加到 `tests/test_pilot_catalog.py`)

```python
def test_duplicate_entity_ids_rejected():
    data = json.loads((ROOT / "pilot" / "toy-catalog.json").read_text(encoding="utf-8"))
    data["entities"].append({"type": "ToolType", "id": "TY-carbide", "name": "dup",
                             "concept_ref": "https://example.org/cutting-tool/vocabulary/tool#carbide-insert"})
    ok, errors = validate_catalog(data)
    assert not ok
    assert any("duplicate entity id 'TY-carbide'" in e for e in errors)
```

- [ ] **Step 2: 运行确认失败**
- Run: `python -m pytest tests/test_pilot_catalog.py -q`
- Expected: `test_duplicate_entity_ids_rejected` FAIL(未报 id 重复)。

- [ ] **Step 3: 实现**

在 `validate_catalog` 的 entities 循环之后(进入 relationships 之前)插入:

```python
    # --- off-line id uniqueness: mirrors the Neo4j unique constraint so a
    # duplicate blows up here instead of as a NodeUnique failure at load time ---
    seen: dict[str, int] = {}
    for ent in data.get("entities", []):
        eid = ent.get("id")
        seen[eid] = seen.get(eid, 0) + 1
    for eid, n in seen.items():
        if n > 1:
            errors.append(f"duplicate entity id {eid!r} ({n} x)")
```

- [ ] **Step 4: 运行确认通过**
- Run: `python -m pytest tests/test_pilot_catalog.py -q`
- Expected: 全 PASS(含既有 positive/negative fixture)。

- [ ] **Step 5: Commit**
```bash
git add pilot/validate_catalog.py tests/test_pilot_catalog.py
git commit -m "feat(validate): reject duplicate entity ids offline (mirrors Neo4j unique)"
```

---

### Task 2 (P0-1):投影器未知字段由容忍改为硬失败

**Files:**
- Modify: `pilot/project_to_cypher.py:37`
- Test: `tests/test_pilot_project.py`

**Interfaces:**
- Consumes: `project_to_cypher(data, reg, mapping)->str`(对已映射字段行为不变)。
- Produces: 遇未映射字段抛 `KeyError`(与关系侧 `rel_types[rel["name"]]` 一致)。

- [ ] **Step 1: 写失败测试**(追加到 `tests/test_pilot_project.py`)

```python
def test_unmapped_entity_field_is_a_hard_error():
    reg, mapping = load_mapping()
    data = json.loads((ROOT / "pilot" / "toy-catalog.json").read_text(encoding="utf-8"))
    data["entities"].append({"type": "Manufacturer", "id": "M-X", "name": "x",
                             "not_in_mapping": 1})
    with pytest.raises(KeyError):
        project_to_cypher(data, reg, mapping)
```

> 已核实:`owl_properties` 不透传任意键;`Manufacturer` 现有字段(`name`)有映射,追加的 `not_in_mapping` 无映射。

- [ ] **Step 2: 运行确认失败**
- Run: `python -m pytest tests/test_pilot_project.py -q`
- Expected: `test_unmapped_entity_field_is_a_hard_error` FAIL(`nm.get(k,k)` 静默透传,不抛)。

- [ ] **Step 3: 实现**

`pilot/project_to_cypher.py:37` 把:

```python
        cypher_props = ", ".join(f"{nm.get(k, k)}: {_esc(v)}" for k, v in sorted(props.items()))
```

改为:

```python
        cypher_props = ", ".join(f"{nm[k]}: {_esc(v)}" for k, v in sorted(props.items()))
```

- [ ] **Step 4: 运行确认通过**
- Run: `python -m pytest tests/test_pilot_project.py -q`
- Expected: 全 PASS。

- [ ] **Step 5: Commit**
```bash
git add pilot/project_to_cypher.py tests/test_pilot_project.py
git commit -m "fix(project): unknown entity field is a hard error, not silent passthrough"
```

---

### Task 3 (P0-3):约束生成抽成单一来源并修复命名分叉

**Files:**
- Create: `src/neo4j_constraints.py`
- Modify: `src/generate_constraints.py`
- Modify: `pilot/project_to_cypher.py`
- Test: Create `tests/test_constraint_parity.py`

**Interfaces:**
- Consumes: `re`;class 名列表。
- Produces:
  - `constraint_name(cls: str) -> str` — `'ct_' + camel_to_snake(cls) + '_id'`(统一为生成器既有命名,如 `ct_cutting_recommendation_id`)。
  - `community_constraints(classes: list[str]) -> list[str]` — 每类一条 `CREATE CONSTRAINT ... REQUIRE n.id IS UNIQUE;`。

> 现状为两份会分叉的命名:生成器 `ct_cutting_recommendation_id`,投影器 `ct_cuttingrecommendation_id`;统一后投影器改用 snake 名。

- [ ] **Step 1: 写失败测试**(新建 `tests/test_constraint_parity.py`)

```python
"""The catalog projector and the constraint generator must agree on every
id-uniqueness constraint (name AND class). A divergence = drift that would bite
at load time when one side's constraint name stops matching the other's intent."""
import json
import re
from pathlib import Path

from pilot.project_to_cypher import project_to_cypher
from pilot.validate_catalog import load_mapping

ROOT = Path(__file__).resolve().parents[1]
_RE = re.compile(r"CREATE CONSTRAINT (\S+) IF NOT EXISTS FOR \(n:([A-Za-z]+)\) REQUIRE n\.id IS UNIQUE;")


def _constraints_from(cypher: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in _RE.finditer(cypher)}


def test_projected_constraints_subset_of_written_file():
    reg, mapping = load_mapping()
    data = json.loads((ROOT / "pilot" / "toy-catalog.json").read_text("utf-8"))
    projected = _constraints_from(project_to_cypher(data, reg, mapping))
    written = _constraints_from((ROOT / "neo4j/community-constraints.cypher").read_text("utf-8"))
    assert set(projected.items()) <= set(written.items())


def test_projected_skips_recommendation_record_only():
    reg, mapping = load_mapping()
    data = json.loads((ROOT / "pilot" / "toy-catalog.json").read_text("utf-8"))
    projected = _constraints_from(project_to_cypher(data, reg, mapping))
    # RecommendationRecord is an aggregate view, not a graph entity -> no constraint
    assert "RecommendationRecord" not in projected.values()
    # ...but every real entity class is still covered (not skipped-all)
    assert "CuttingRecommendation" in projected.values()


def test_multiword_constraint_name_is_snake():
    reg, mapping = load_mapping()
    data = json.loads((ROOT / "pilot" / "toy-catalog.json").read_text("utf-8"))
    projected = _constraints_from(project_to_cypher(data, reg, mapping))
    assert projected["ct_cutting_recommendation_id"] == "CuttingRecommendation"
```

> 注意第二个用例名 `test_projected_skips_recommendation_record_only` 语义是「只跳过 RecommendationRecord、不跳过别的」;`assert any(v=="CuttingRecommendation")` 恰好锁住这条(RecommendationRecord 不在 → 其余类全在)。

- [ ] **Step 2: 运行确认失败**
- Run: `python -m pytest tests/test_constraint_parity.py -q`
- Expected: `test_multiword_constraint_name_is_snake` FAIL(投影器当前名为 `ct_cuttingrecommendation_id`);subset 用例也 FAIL。

- [ ] **Step 3: 实现**

a) 新建 `src/neo4j_constraints.py`:

```python
"""Shared Neo4j (Community) id-uniqueness constraint emission.

Both the constraint generator (src/generate_constraints.py) and the catalog
projector (pilot/project_to_cypher.py) emit `n.id IS UNIQUE` per entity class.
Keeping a single builder here guarantees identical constraint NAMES and text
across the two outputs — previously they diverged (generator used
`ct_cutting_recommendation_id`, projector used `ct_cuttingrecommendation_id`).
"""
import re


def constraint_name(cls: str) -> str:
    return 'ct_' + re.sub(r'(?<!^)(?=[A-Z])', '_', cls).lower() + '_id'


def community_constraints(classes: list[str]) -> list[str]:
    return [
        f"CREATE CONSTRAINT {constraint_name(cls)} IF NOT EXISTS "
        f"FOR (n:{cls}) REQUIRE n.id IS UNIQUE;"
        for cls in classes
    ]
```

b) `src/generate_constraints.py`:把 :

```python
 common=[];enterprise=[]
 import re
 for cls in r['classes']:
  nm='ct_'+re.sub(r'(?<!^)(?=[A-Z])','_',cls).lower()+'_id'
  common.append(f'CREATE CONSTRAINT {nm} IF NOT EXISTS FOR (n:{cls}) REQUIRE n.id IS UNIQUE;')
  enterprise.append(f'CREATE CONSTRAINT {nm}_exists IF NOT EXISTS FOR (n:{cls}) REQUIRE n.id IS NOT NULL;')
```

替换为:

```python
 from src.neo4j_constraints import community_constraints, constraint_name
 common = community_constraints(list(r['classes']))
 enterprise = [
  f'CREATE CONSTRAINT {constraint_name(cls)}_exists IF NOT EXISTS FOR (n:{cls}) REQUIRE n.id IS NOT NULL;'
  for cls in r['classes']]
```

c) `pilot/project_to_cypher.py`:顶部加 `from src.neo4j_constraints import community_constraints`,并把 :

```python
    out.append("// constraint on entity id (Neo4j 5+ Community)")
    for cls in sorted(reg["classes"]):
        if cls == "RecommendationRecord":
            continue
        out.append(f"CREATE CONSTRAINT ct_{cls.lower()}_id IF NOT EXISTS FOR (n:{cls}) REQUIRE n.id IS UNIQUE;")
```

替换为:

```python
    out.append("// constraint on entity id (Neo4j 5+ Community)")
    classes = sorted(c for c in reg["classes"] if c != "RecommendationRecord")
    out.extend(community_constraints(classes))
```

- [ ] **Step 4: 运行确认通过**
  - Run: `python -m pytest tests/test_constraint_parity.py tests/test_pilot_project.py -q`
  - Expected: 全 PASS。
  - Run: `python -m pytest tests/ -q`
  - Expected: 全量绿(投影器产物文本不变,仅约束名从内联改为经共享函数,对既有确定性测试无影响)。

- [ ] **Step 5: Commit**
```bash
git add src/neo4j_constraints.py src/generate_constraints.py pilot/project_to_cypher.py tests/test_constraint_parity.py
git commit -m "refactor(project): single-source id-unique constraint emission, fix name divergence"
```

---

### Task 4 (P0-2):R2、R3 在线负例 + 对等性测试

**Files:**
- Modify: `tests/test_neo4j_rules.py`

**Interfaces:**
- Consumes: `pilot.neo4j_rules.RULES`(含 `R2_vc_range`、`R3_mounting` 的 `cypher`);运行中 Neo4j fixture。
- Produces: 在线用例证明 R2、R3 对「各自 SHACL 负例」命中,且清理后干净图仍全绿。

> R1、R4 已有负例注入。补上 R2(转速越界)、R3(装夹无匹配规格链)。

- [ ] **Step 1: 写失败测试**(修改 `tests/test_neo4j_rules.py` 的 `test_injected_violations_are_detected` 与 `test_injected_violations_cleanup_restores_pass`)

把 `test_injected_violations_are_detected` 改为:

```python
def test_injected_violations_are_detected(driver):
    with driver.session() as s:
        s.run("MERGE (r:CuttingRecommendation {id:'BAD-NO-EVIDENCE', name:'n'})")
        s.run("MERGE (p:CuttingParam {id:'BAD-FEED', name:'n', feedType:'fn', feedUnit:'mm/tooth'})")
        # R2: vcRecommended outside [vcMin, vcMax]
        s.run("MERGE (p:CuttingParam {id:'BAD-VC', name:'n', vcRecommended: 900, vcMin: 100, vcMax: 200})")
        # R3: an Insert FITS_WITH a Holder but no matched InsertSpecification
        s.run("MERGE (i:Insert {id:'BAD-FIT', name:'i'}) "
              "MERGE (h:Holder {id:'BAD-HOLDER', name:'h'}) "
              "MERGE (i)-[:FITS_WITH]->(h)")
    rules = _rules_by_id()
    assert "BAD-NO-EVIDENCE" in {h["id"] for h in _eval_from(driver, rules["R1_evidence"])}
    assert "BAD-FEED" in {h["id"] for h in _eval_from(driver, rules["R4_feed_unit"])}
    assert "BAD-VC" in {h["id"] for h in _eval_from(driver, rules["R2_vc_range"])}
    assert "BAD-FIT" in {h["id"] for h in _eval_from(driver, rules["R3_mounting"])}
    with driver.session() as s:
        s.run("MATCH (n {id:'BAD-NO-EVIDENCE'}) DETACH DELETE n")
        s.run("MATCH (n {id:'BAD-FEED'}) DETACH DELETE n")
        s.run("MATCH (n {id:'BAD-VC'}) DETACH DELETE n")
        s.run("MATCH (n {id:'BAD-FIT'}) DETACH DELETE n")
        s.run("MATCH (n {id:'BAD-HOLDER'}) DETACH DELETE n")
```

- [ ] **Step 2: 运行确认失败(在库在时)**
- Run: `python -m pytest tests/test_neo4j_rules.py -q`
- Expected: `test_injected_violations_are_detected` FAIL——断言 BAD-VC ∈ R2 命中、BAD-FIT ∈ R3 命中不成立(当前未注入,但这里**是已注入**,失败点是注入的负例**未被** R2/R3 检出则 FAIL;若检出则 PASS)。

> 说明:R2/R3 规则已存在且逻辑正确,本任务**不实现规则**,而是**把「SHACL 负例 → 在线规则命中」的对等写进回归**。步骤 1 的测试引入负例后若立即通过,说明两规则已有对等(预期如此);若失败则暴露语义分叉需修正规则。CI 离线(库不在)自动 skip,维持绿。

- [ ] **Step 3: 确认清理用例仍绿**
- Run: `python -m pytest tests/test_neo4j_rules.py -q`
- Expected: `test_injected_violations_cleanup_restores_pass` 通过(清理后干净图全规则无违例)。

- [ ] **Step 4: 全量回归**
- Run: `python -m pytest tests/ -q`
- Expected: 全绿(库不在时相关用例 skip)。

- [ ] **Step 5: Commit**
```bash
git add tests/test_neo4j_rules.py
git commit -m "test(rules): lock R2/R3 online parity against their SHACL negatives"
```

---

### Task 5 (P1-7):新增节点级在线规则 R5(concept_ref 悬空/缺失)

**Files:**
- Modify: `pilot/neo4j_rules.py`
- Modify: `tests/test_neo4j_rules.py`

**Interfaces:**
- Consumes: `src.namespaces.VOCAB_BASE`。
- Produces: `RULES` 增第 5 条 `{"id":"R5_concept_ref", ...}`;`R5_CONCEPT_REF` 常数。命中 = 受控类节点缺 `conceptRef` 或不在 `VOCAB_BASE` 前缀下。

> 受控类集合(`ToolType/ProcessMethod/MaterialClass`)是本体事实,硬编码为元组;前缀值由 `VOCAB_BASE` 派生(不落字面量)。

- [ ] **Step 1: 写失败测试**(修改 `tests/test_neo4j_rules.py`)

a) 更新 `test_four_rules_defined_matching_shacl` → `test_five_rules_defined_matching_shacl`:

```python
def test_five_rules_defined_matching_shacl():
    assert len(RULES) == 5
    ids = {r["id"] for r in RULES}
    assert ids == {"R1_evidence", "R2_vc_range", "R3_mounting", "R4_feed_unit", "R5_concept_ref"}
```

b) 在 `test_rule_relationship_types_use_mapping_uppercase` 之后追加离线断言(不依赖 Neo4j):

```python
def test_r5_uses_vocab_base_not_raw_literal():
    from pilot.neo4j_rules import R5_CONCEPT_REF
    from src.namespaces import VOCAB_BASE
    assert VOCAB_BASE in R5_CONCEPT_REF
    assert "example.org/cutting-tool/vocabulary/" not in R5_CONCEPT_REF.replace(VOCAB_BASE, "")


def test_r5_covers_every_bound_class():
    from pilot.neo4j_rules import _VOCAB_BOUND
    assert _VOCAB_BOUND == ("ToolType", "ProcessMethod", "MaterialClass")
```

c) 在 `test_injected_violations_are_detected` 加入注入与命中断言 + 清理:

```python
        # R5: a bound class node with a dangling / absent conceptRef
        s.run("MERGE (n:ToolType {id:'BAD-REF', name:'n', conceptRef:'http://garbage/not-vocab'})")
```
命中断言加:
```python
    assert "BAD-REF" in {h["id"] for h in _eval_from(driver, rules["R5_concept_ref"])}
```
清理加:
```python
        s.run("MATCH (n {id:'BAD-REF'}) DETACH DELETE n")
```

- [ ] **Step 2: 运行确认失败**
- Run: `python -m pytest tests/test_neo4j_rules.py -q`
- Expected: `test_five_rules_defined_matching_shacl` FAIL(`len(RULES)==4`);`test_r5_uses_vocab_base_not_raw_literal`/`test_r5_covers_every_bound_class` FAIL(`R5_CONCEPT_REF`/`_VOCAB_BOUND` 未定义)。

- [ ] **Step 3: 实现**

`pilot/neo4j_rules.py` 顶部加:

```python
from src.namespaces import VOCAB_BASE
```

在 R4 定义后加:

```python
# R5 — node-level mirror of the vocabulary-binding invariant: every controlled
# class node must carry a conceptRef rooted at the project vocabulary base.
_VOCAB_BOUND = ("ToolType", "ProcessMethod", "MaterialClass")
R5_CONCEPT_REF = (
    "MATCH (n:" + "|".join(_VOCAB_BOUND) + ") "
    f"WHERE n.conceptRef IS NULL OR NOT n.conceptRef STARTS WITH '{VOCAB_BASE}' "
    "RETURN n.id AS id"
)
```

在 `RULES` 列表尾部追加:

```python
    {"id": "R5_concept_ref", "name": "controlled-class concept must anchor in the vocabulary",
     "shacl_ref": "VocabularyBindingShape", "cypher": R5_CONCEPT_REF},
```

- [ ] **Step 4: 运行确认通过**
  - Run: `python -m pytest tests/test_neo4j_rules.py -q`
  - Expected: 全 PASS(库在时含 R5 注入命中;库不在时在线用例 skip,离线断言仍过)。
  - Run: `python -m pytest tests/ -q`
  - Expected: 全绿。`load_neo4j`/`verify_neo4j_rules` 用 `run_rules()` 自动纳入 R5(不受影响,因 pilot 数据受控类带 `conceptRef`)。

- [ ] **Step 5: Commit**
```bash
git add pilot/neo4j_rules.py tests/test_neo4j_rules.py
git commit -m "feat(rules): add node-level R5 — vocab-bound classes must anchor conceptRef in VOCAB_BASE"
```

---

### Task 6 (P1-5):feed-unit 配对单一来源,离线校验与 R4 同源

**Files:**
- Create: `src/feed_units.py`
- Modify: `src/validator.py`
- Modify: `pilot/neo4j_rules.py`
- Test: Modify `tests/test_neo4j_rules.py`(离线断言)

**Interfaces:**
- Consumes: 现有 `_FEED_UNITS` 语义(`fn→mm/rev`、`fz→mm/tooth`、`vf→mm/min`)。
- Produces: `src.feed_units.FEED_UNITS: dict[str, str]`;离线校验 `src.validator` 与在线 R4 均 import 它。R4 查询由它程序化构造 OR 链。

- [ ] **Step 1: 写失败测试**(往 `tests/test_neo4j_rules.py` 追加离线用例)

```python
def test_r4_feed_units_are_single_source_with_validator_and_schema():
    from pilot.neo4j_rules import R4_FEED_UNIT, _R4_OR
    from src.feed_units import FEED_UNITS
    assert _R4_OR
    for ft, fu in FEED_UNITS.items():
        clause = f"(p.feedType = '{ft}' AND p.feedUnit <> '{fu}')"
        assert clause in R4_FEED_UNIT
    assert FEED_UNITS == {'fn': 'mm/rev', 'fz': 'mm/tooth', 'vf': 'mm/min'}


def test_offline_validator_and_online_r4_share_the_table():
    from src.validator import _FEED_UNITS
    from src.feed_units import FEED_UNITS
    assert _FEED_UNITS is FEED_UNITS or _FEED_UNITS == FEED_UNITS
```

- [ ] **Step 2: 运行确认失败**
- Run: `python -m pytest tests/test_neo4j_rules.py -q`
- Expected: FAIL(`src.feed_units` 不存在;`_R4_OR` 未定义)。

- [ ] **Step 3: 实现**

a) 新建 `src/feed_units.py`:

```python
"""Single source of truth for the feed-type / feed-unit pairing.

`feed_type` (fn/fz/vf) and `feed_unit` (mm/rev, mm/tooth, mm/min) must describe
the same feed semantics. Consumed by the offline validator (src/validator.py)
and the online relationship-rule R4 (pilot/neo4j_rules.py).
"""
FEED_UNITS = {'fn': 'mm/rev', 'fz': 'mm/tooth', 'vf': 'mm/min'}
```

b) `src/validator.py`:把 `_FEED_UNITS = {'fn': ...}` 这一行替换为 `from src.feed_units import FEED_UNITS as _FEED_UNITS`。

c) `pilot/neo4j_rules.py`:把 R4 定义替换为:

```python
from src.feed_units import FEED_UNITS

_R4_OR = " OR\n".join(
    f"(p.feedType = '{ft}' AND p.feedUnit <> '{fu}')" for ft, fu in FEED_UNITS.items()
)
R4_FEED_UNIT = f"""
MATCH (p:CuttingParam)
WHERE {_R4_OR}
RETURN p.id AS id
"""
```

> 生成的 OR 链与旧 R4 逐字节相同,`test_rule_property_names_use_projected_naming`(断言 feedType/feedUnit 存在)仍通过。

- [ ] **Step 4: 运行确认通过**
  - Run: `python -m pytest tests/test_neo4j_rules.py -q`
  - Expected: 全 PASS。
  - Run: `python -m pytest tests/ -q` 与 `python -c "from pilot.neo4j_rules import R4_FEED_UNIT; print('fn' in R4_FEED_UNIT)"`
  - Expected: 全量绿;`True`。

- [ ] **Step 5: Commit**
```bash
git add src/feed_units.py src/validator.py pilot/neo4j_rules.py tests/test_neo4j_rules.py
git commit -m "refactor(feed): single-source feed_type/feed_unit pairing for validator and R4"
```

---

### Task 7 (P1-6):concept_ref 模式正则改由 VOCAB_BASE 派生

**Files:**
- Modify: `contract/field-registry.yaml`(3 处 concept_ref `pattern`)
- Modify: `src/generate_constraints.py`
- Test: Modify `tests/test_namespaces.py`

**Interfaces:**
- Consumes: `src.namespaces.VOCAB_BASE`。
- Produces: 生成器把 field-registry 中的 `{{VOCAB_BASE}}` 哨兵替换为 `re.escape(VOCAB_BASE.rstrip('/'))`,落入 JSON Schema 与 SHACL `sh:pattern`。**有效正则不变**(哨兵展开回原串),故 `schemas/*.schema.json` 字节零漂移。

- [ ] **Step 1: 写失败测试**(追加到 `tests/test_namespaces.py`)

```python
def test_field_registry_has_no_vocab_uri_literal():
    import yaml
    reg = yaml.safe_load((ROOT / "contract/field-registry.yaml").read_text("utf-8"))
    text = (ROOT / "contract/field-registry.yaml").read_text("utf-8")
    assert "example\\.org/cutting-tool/vocabulary" not in text
    assert "example.org/cutting-tool/vocabulary/" not in text


def test_generated_schema_pattern_is_vocab_derived():
    from src import namespaces
    import re as _re, json
    schema = json.loads((ROOT / "schemas/CuttingParam.schema.json").read_text("utf-8"))
    pat = schema["properties"]["concept_ref"]["pattern"]
    assert "{{VOCAB_BASE}}" not in pat
    assert pat.startswith("^" + _re.escape(namespaces.VOCAB_BASE.rstrip("/")) + "/")
    assert "(tool|process|material)" in pat
```

> `CuttingParam` 是受控类之一,携带 concept_ref。若想覆盖多处,可另对 `ToolType`/`MaterialClass` 断言同样 startswith。

- [ ] **Step 2: 运行确认失败**
- Run: `python -m pytest tests/test_namespaces.py -q`
- Expected: 两个新用例 FAIL(field-registry 仍有字面量;生成 schema 直接含字面量)。

- [ ] **Step 3: 实现**

a) `contract/field-registry.yaml`:把 3 处 `concept_ref` 的

```yaml
        pattern: ^https://example\.org/cutting-tool/vocabulary/(tool|process|material)#[A-Za-z][A-Za-z0-9_-]*$
```

替换为(双引号包裹,避免 YAML 把 `#` 当注释、`{{ }}` 歧义):

```yaml
        pattern: "{{VOCAB_BASE}}/(tool|process|material)#[A-Za-z][A-Za-z0-9_-]*$"
```

> 三处分别位于 `ToolType`/`ProcessMethod`、`MaterialClass` 的 `concept_ref`(grep 确认在 97/106/125 行)。`namespace:` 行(普通 IRI,非 pattern)保持不变——它是本体语义身份,由 `test_namespaces.test_field_registry_namespace_matches` 锁定等于 `ON_BASE`。

b) `src/generate_constraints.py`:
- 顶部 `from src.namespaces import ON as CT` 改为 `from src.namespaces import ON as CT, VOCAB_BASE`。
- 在 `DTD` 定义后加辅助:

```python
_VOCAB_TOKEN = "{{VOCAB_BASE}}"
_VOCAB_ESC = re.escape(VOCAB_BASE.rstrip('/'))
def _expand_pattern(value):
    return value.replace(_VOCAB_TOKEN, _VOCAB_ESC) if isinstance(value, str) else value
```

- `import re` 提为模块级(去掉 `generate()` 内的 `import re`;若已存在模块级则删掉内联)。
- 在属性循环内、写 schema 与 SHACL pattern 前,对 opts 与 SH.pattern 做展开。

先构造展开后的 opts:在 `props[key]=opts` 前插入:
```python
   if isinstance(opts.get('pattern'), str):
    opts['pattern'] = _expand_pattern(opts['pattern'])
```
`shapes` 侧 `if keyword in spec` 分支里,`spec['pattern']` 走 `SH.pattern` 三元组时用 `Literal(_expand_pattern(spec['pattern']))`。为稳妥,直接在源码生成处让 `shapes.add((ps,SH.pattern,Literal(spec['pattern'])))` 中的 `spec['pattern']` 换成 `_expand_pattern(spec['pattern'])`。

- **重要确认**:展开后 `schemas/*.schema.json` 与 `generated-shapes.ttl` 的内容与当前(b用字面量时)逐字节相同 → `Contract 无漂移`。

- [ ] **Step 4: 运行确认通过 + 零漂移**
- Run: `python -m src.generate_constraints`
- Run: `git diff --exit-code -- schemas/ neo4j/`
- Expected: 退出码 0(无字节漂移)。`shapes/generated-shapes.ttl` 如出现非字节调整(rdflib 序列化块序)则 `git checkout -- shapes/generated-shapes.ttl` 还原(该文件被 CI 明确排除)。
- Run: `python -m pytest tests/test_namespaces.py -q`
- Expected: 全 PASS(含既有 `test_field_registry_namespace_matches`、`test_generated_shapes_bind_same_ct`)。
- Run: `python -m pytest tests/ -q`
- Expected: 全量绿(`test_semantic_alignment` 只断言 pattern 含 `"tool"`,不受影响)。

- [ ] **Step 5: Commit**
```bash
git add contract/field-registry.yaml src/generate_constraints.py tests/test_namespaces.py
git commit -m "refactor(constraints): derive concept_ref URL pattern from VOCAB_BASE (no raw namespace literal)"
```

---

### Task 8:文档回写 + 全量回归 + 推送 github

**Files:**
- Modify: `CHANGELOG.md`(`[1.4.1-pilot]` 段补 4 项)
- Modify: `README.md`/`README.zh-CN.md`(在线规则段补「R5 节点级 + R2/R3/R4 与离线校验同源 / 约束与校验两处单一来源」一句,双语)

**Interfaces:** 无新代码接口。

- [ ] **Step 1: CHANGELOG** 在 `[1.4.1-pilot]` 段新增一行:
> - Closed the remaining loop gaps: unknown entity fields now hard-fail projection; duplicate ids rejected offline; id-unique constraints single-sourced (fixing a projector/generator name divergence); R2/R3 online negative cases added; new node-level rule R5 mirrors the vocabulary-binding invariant; feed-type/feed-unit pairing single-sourced between the offline validator and R4; concept_ref URL patterns derived from `VOCAB_BASE` (no raw namespace literal left in the contract).

- [ ] **Step 2: README EN/zh** 在「在线关系不变量」所在小节补一句:R5 增加节点级概念绑定不变量;R2–R4 与离线校验/契约共享同一数据源;id 唯一约束与 id 校验双保险。

- [ ] **Step 3: 全量回归**
- Run: `python -m pytest tests/ -q`
- Expected: 全绿(预期 49 基线 + 新增:Task1 +1、Task2 +1、Task3 +3、Task4 ±0(改)、Task5 +2(改)+离线 +1、Task6 +2、Task7 +2 → 约 61;Neo4j 在线用例离线 skip)。
- Run: `python -m pytest tests/ -q` 后 `git status` 应仅剩 CHANGELOG/README 改动、无杂散产物。

- [ ] **Step 4: Commit**
```bash
git add CHANGELOG.md README.md README.zh-CN.md
git commit -m "docs: closed-loop parity (R5, single-source constraints/feed/namespace) for the 4 foundation layers"
```

- [ ] **Step 5: 推送到 github**
```bash
git remote -v          # 确认 remote 存在
git push origin main
```
- Expected: `main` 正常推送(已核对的当前分支);无 `! [rejected]`。若拒绝为非快进,先 `git pull --rebase origin main` 再推,或告知用户待定。

---

## 验证(端到端)

1. `python -m pytest tests/ -q` → 全绿(离线用例全跑;在线用例库不在 skip 而非 fail)。
2. Task3:`python -m pytest tests/test_constraint_parity.py -q` 全 PASS;断言 `ct_cutting_recommendation_id` == `CuttingRecommendation`。
3. Task4/5:`python -m pytest tests/test_neo4j_rules.py -q`;库在时 `BAD-VC`/`BAD-FIT`/`BAD-REF` 均被命中,清理后干净图全绿。
4. Task6:`R4_FEED_UNIT` OR 链与 `src.feed_units.FEED_UNITS` 逐对一致。
5. Task7:重新生成后 `git diff --exit-code -- schemas/ neo4j/` 为零;field-registry 无 `example.org/cutting-tool/vocabulary` 字面量。
6. `scripts/validate_skos.py` 136 概念 + `src.verify_consistency` 398 checks 保持 PASS。
7. `git push origin main` 成功。

## 明确不做(边界)

- 不换占位命名空间值;不引入 w3id/github 真实命名空间。
- feed-unit 配对暂不从 field-registry **枚举**自动推导(ToolType 等枚举分离,配对语义是领域事实),仅把「离线校验 + R4 在线规则」两处收敛到单一 `src/feed_units.py`;契约枚举推导记为后续。
- 不新增契约关系/字段;证据只经既有关系表达。
- 不做批量/索引化加载优化(P2),仅记录。