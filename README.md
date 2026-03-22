# Curriculum Standard Generator

Generate professional curriculum standards (课程标准) for Chinese vocational education following national standards.

## Features

- Generates complete 10-chapter curriculum standard documents
- Supports Bloom's taxonomy knowledge objectives (4×6 table)
- Three learning scenario templates:
  - 岗课赛证考融合版 (Position-Course-Competition-Certificate-Exam integrated)
  - 标准项目版 (Standard project version)
  - 简化版 (Simplified version)
- Automatic matching with MOE professional teaching standards
- Output in Markdown and DOCX formats

## Usage

```
Use this skill when you need to:
- Create curriculum standards from training plans (人才培养方案)
- Generate learning scenario designs following Chinese vocational education standards
- Convert professional teaching standards to curriculum documents
```

## Required Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| training_plan | PDF/DOCX/MD | ✅ | Training plan document |
| teaching_standard | PDF/DOCX/MD | ❌ | Professional teaching standard (auto-matched if not provided) |
| template_docx | PDF/DOCX/MD | ❌ | Curriculum standard template |

## Directory Structure

```
curriculum-standard/
├── SKILL.md                 # Main skill definition
├── assets/
│   └── moe_pdfs_final.json  # MOE teaching standards index (579 records)
├── examples/
│   └── 课程标准模板.docx    # Default template
└── references/
    └── learning-scenario-templates-new.md  # Learning scenario templates
```

## License

MIT
