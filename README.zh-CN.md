# 工业刀具知识图谱本体

**面向工业刀具的本体驱动、约束优先的知识图谱工程基础。**

**简体中文** | [English](README.md)

> **项目状态：** v1.2 研究与工程验证基线。约束生成器和离线测试已实现，但尚未达到生产级刀具推荐平台要求

# 写在心中的一些感悟

**为什么会有这个项目**

这个项目就是我研究生期间设计的基于Neo4j的属性图模型 schema 基础之上的延申。当时的初衷主要是整理了一套面向属性图模型的schema，希望能够通过这样的一套schema，能够将非结构化的、不同厂家的、多种类型的生产加工刀具信息统一以一个标准属性图的结构和约束管理起来。这个期间的工作大多数是在收集厂商的数据，分析数据结构，寻找各种各样不同的刀具、产品、材料和逻辑关系等要素之间的关联，进而能够在这样的抽象关联基础之上做出一个统一的schema。

这个期间其实工作说白了蛮无聊的，就是搜数据，下载下来看一看，每天整理一些数据内容。这个过程还是很消耗心性的，因为不知道自己做的东西究竟有什么意义，也不知道这个东西究竟能够创造多大的价值。不过回头来看，这段经历带给我的更多是心态上的成长，这个很宝贵！自己拥有了能够让自己稍微慢下来的能力，也拥有了更加坚定的信心去坚持自己认为正确的事情。

尤其是在当前这个社会，被AI技术和各样新的挑战不断冲击情况下，变得越来越快，这个冲下去的动能越来越大。作为个体而言，能够在这样的环境下，尽可能降低环境对自己的冲击和影响就显得格外重要。

因为思考很重要，慢下来的节奏对于人生来讲也很重要。得益于这段时间的工作和经历，我能够稍微有一些心态上的坚韧性，能够在面对外部冲击的情况下，有一些能力去让自己慢下来，去思考，去沉下心面对问题和解决问题。在此特别向我的老师表示感谢，他每周都会和我一对一谈话，指导详细的工作内容和方向。

最重要的，他曾对我说，好的想法和设计并不是灵光一现就能够想出来的，是日日夜夜的对于技术、对于行业、对于自己的研究方向积累的基础之上，叠加着实际的工作经验和项目经验能够得到的，要慢下来，要认真思考。

这段话对我收益终生。

祝愿我的老师退休生活快乐！~

这个项目的始发来源于我突然的想法，尘封的研究生工作从我大脑里给翻了出来。我觉得这份工作稍微有一些些价值。

同样，自己工作了一段时间之后，越发认为在工业领域中，数据的标准化和语义对齐越来越重要，尤其是在AI盛行的今天，高质量的数据从根本上决定了AI的性能。并且，工业领域的数据天然就是异构并且语义混乱的，需要一套标准，所以我把自己的经验和设计稍微优化了一下，开源出来，希望能够帮到每一个看到了、搜索到了这个项目的人。



## 项目简介

不同刀具厂商的产品目录在刀片、刀杆、整体刀具、材料牌号、工件材料、加工方式和切削参数等方面存在命名和结构差异。本项目通过统一语义本体、术语分类和结构化约束，减少RDF、JSON与Neo4j属性图之间的定义漂移。

**主要能力**

- 采用 **OWL 2** 定义领域类、继承关系及对象/数据属性。
- 使用 **SKOS** 管理行业分类与术语，不将所有分类词汇误当作OWL类。
- 基于统一**字段约束注册表**生成JSON Schema、SHACL约束和Neo4j Cypher约束。
- 实施OWL词汇对应关系、JSON合法性、SHACL正反例、型号标识以及生成结果覆盖率的离线测试。
- 输出可复查的机器可读验证报告。

**当前不包含：** 完整厂商目录数据导入、产品规格独立核验、可直接用于加工现场的参数推荐、实际数据库部署以及完整OWL DL一致性证明。

## 架构与规范权威

| 层次 | 主要职责 | 文件位置 |
| --- | --- | --- |
| OWL | 规范实体类型和语义关系 | `ontology/cutting-tool.owl` |
| SKOS | 维护分类体系与标准术语 | `vocabulary/` |
| 字段约束 | 必填规则、数值范围、枚举和数据类型 | `contract/field-registry.yaml` |
| 映射配置 | OWL属性、JSON字段和Neo4j投影映射 | `mappings/ontology-neo4j.yaml` |
| SHACL | 对RDF图数据执行结构和数据质量校验 | `shapes/generated-shapes.ttl` |
| JSON Schema | 数据接口及JSON实例验证 | `schemas/` |
| Neo4j | 唯一性约束和特定版本的存在性约束 | `neo4j/` |

**OWL是语义定义的权威来源；字段注册表是可执行数据校验规则的权威来源。** 两者借助映射和一致性测试保持同步。OWL采用开放世界语义，不能直接替代必填字段校验；SHACL及Neo4j约束也不能取代全部业务规则检查。

## 领域范围与应用场景

系统涵盖24个模型类，包括：

- **刀具产品：** `Tool`、`Insert`、`Holder`、`SolidTool`、`InsertSpecification`
- **刀具与工件材料：** `ToolGrade`、`MaterialSubstrate`、`MaterialCoating`、`MaterialGrade`、`Workpiece`
- **标准分类：** `ToolType`、`ProcessMethod`、`MaterialClass`、`SubstrateType`
- **产品目录：** `Manufacturer`、`ProductSeries`、`CatalogCategory`
- **加工推荐及来源：** `CuttingRecommendation`、`CuttingCondition`、`CuttingParam`、`SourceDocument`、`SourceEvidence`

典型应用包括跨厂商产品检索、刀具牌号和工件材料的候选匹配、已核验的刀片刀杆配合记录、带约束的加工参数管理、数据源追溯以及后续GraphRAG扩展。**候选配合不等于已经确认兼容，示例参数不构成现场加工建议。**

## 环境要求

- Python 3.10及以上版本（建议）
- Python依赖见 [`requirements.txt`](requirements.txt)
- 离线生成和验证**不需要**Neo4j服务器；部署和实际数据库验证需要独立准备适配版本、权限及数据库实例

## 快速开始

在项目根目录执行：

```bash
python -m venv .venv
```

macOS/Linux激活虚拟环境：

```bash
source .venv/bin/activate
```

Windows PowerShell：

```powershell
.venv\Scripts\Activate.ps1
```

安装依赖、生成约束并执行检查：

```bash
python -m pip install -r requirements.txt
python -m src.generate_constraints
python -m src.verify_consistency
python -m pytest tests/test_regression.py -q
```

> `pytest`属于开发/测试依赖。如果环境中尚未安装，先运行`python -m pip install pytest`。

生成器更新`schemas/`、`shapes/generated-shapes.ttl`及`neo4j/`下的约束文件。验证器将结果写入`reports/verification.json`。

## JSON数据校验示例

下面以[`examples/Insert.json`](examples/Insert.json)为例，使用生成的Schema进行验证：

```python
import json
from pathlib import Path
from jsonschema import validate

schema = json.loads(Path('schemas/Insert.schema.json').read_text(encoding='utf-8'))
data = json.loads(Path('examples/Insert.json').read_text(encoding='utf-8'))
validate(instance=data, schema=schema)
print('Valid')
```

RDF及SHACL测试请参考`src/verify_consistency.py`；涉及跨字段规则的辅助校验见`src/validator.py`。

## 项目目录

```text
ontology/        OWL本体
vocabulary/      SKOS受控术语
contract/        字段约束注册表
mappings/        OWL、JSON及Neo4j映射
schemas/         自动生成的JSON Schema
shapes/          自动生成的SHACL约束
neo4j/           自动生成的Cypher约束
src/             生成器与验证程序
examples/        JSON、RDF及文档型号标识样本
tests/           回归测试与无效数据样本
reports/         测试结果
docs/           架构设计与验证分析
```

## 测试结果与验证边界

随附V1.2验证报告记载：**386项离线检查通过、0项失败**；其中包含原设计文档中出现的8个型号/牌号标识。SHACL正向案例通过，缺失ID的反向案例被识别，另有2项回归测试通过。详细信息见[`reports/verification.json`](reports/verification.json)。

这些检查仅证明当前**结构约束与离线测试样本**满足既定条件，**不能证明厂商产品规格真实无误**。标识字段来自已有设计材料，并未独立通过厂家手册核实。

未执行的验收包括：真实Neo4j事务、完整OWL DL推理、数据库查询和性能测试、全部SHACL-SPARQL关系约束，以及真实厂商加工条件核验。

## 二次开发与模型变更流程

1. 在`ontology/cutting-tool.owl`中修改实体类和语义属性。
2. 更新`contract/field-registry.yaml`中的字段校验规则，并同步`mappings/ontology-neo4j.yaml`。
3. 运行约束生成器及跨层一致性测试。
4. 为新增功能提供正向与反向测试数据。
5. 审查生成文件差异；涉及Neo4j时单独执行真实数据库集成测试。

**已知建模风险：** 不要为多业务共用的`status`属性设置会引发错误推理的多个`rdfs:domain`。当前通过移除共享Domain避免问题；未来可考虑迁移至`toolStatus`和`recommendationStatus`。

**URI要求：** 项目中`https://example.org/`为占位命名空间；正式发布带URI的RDF数据前，需要替换为由维护方长期治理的持久化命名空间。

## 数据溯源与安全使用

示例数据用于结构测试，**不代表已经认证的产品推荐**。请勿根据示例推断真实性能、刀具配合、实际切削速度或设备安全性。生产环境数据需要保留资料来源、版本、页码/表格、审核状态、单位以及适用条件。

## 贡献与安全

- 贡献方式、编码规范和测试要求见[CONTRIBUTING.md](CONTRIBUTING.md)。
- 安全报告和保密提示见[SECURITY.md](SECURITY.md)。
- 不要在公开文档、测试案例、提交记录及问题附件中加入个人信息、学校信息、企业内部资料或访问凭据。示例数据应匿名化，并确保具有再分发权限。

## 标准说明

项目参考W3C OWL 2、SKOS、SHACL、JSON Schema Draft 2020-12及Neo4j Cypher相关技术规范。此处仅说明技术兼容方向，不代表标准组织或产品厂商的认可与背书。
