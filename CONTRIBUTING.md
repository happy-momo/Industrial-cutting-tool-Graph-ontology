# Contributing / 贡献指南

## English

Contributions should improve ontology correctness, reproducibility, validation coverage, or documentation. Before opening a change:

1. Describe the model/use case and its intended meaning. Separate an OWL class from a SKOS vocabulary concept.
2. Update `ontology/`, `contract/` and `mappings/` as appropriate. Do not edit generated artifacts without updating their source.
3. Run:

   ```bash
   python -m src.generate_constraints
   python -m src.verify_consistency
   python -m scripts.validate_skos
   python -m pytest tests/ -q
   ```

4. Add positive and negative cases; document limitations or breaking changes in `CHANGELOG.md`.
5. Keep pull requests focused and ensure that samples are anonymized, non-sensitive, and legally redistributable.

There is currently no published governance or maintainer response-time policy. Open a repository issue or pull request if the hosting platform provides that capability. Do not publish secrets, identifying details, university affiliations, or confidential vendor records.

## 简体中文

欢迎贡献本体定义、约束规则、自动化测试、数据映射和说明文档。

1. 首先描述业务语义与使用场景，区分OWL类和SKOS分类概念。
2. 按需同步修改本体、字段注册表及映射文件，不要只修改自动生成文件。
3. 运行上述生成及验证命令，并增加正常/异常测试案例。
4. 对不兼容变更更新`CHANGELOG.md`，在合并前确认生成文件差异。
5. 测试数据应匿名化且具有公开再分发权利，不应出现个人、学校、商业秘密和访问凭据。

目前尚未公开固定的项目治理及响应时效政策。
