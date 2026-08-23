# 自动匹配专业教学标准（Phase 0 实现细节）

仅在"用户未提供专业教学标准"且需要自动匹配时读取本文件。

## 读取索引文件
```python
import json
moe_index_path = "@path/assets/moe_pdfs_final.json"
with open(moe_index_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
```

## 搜索匹配
```python
# 方案 A：按专业代码精确匹配（优先）
if major_code:
    matches = [item for item in data if item['major_code'] == major_code]
# 方案 B：按专业名称模糊匹配（次优）
else:
    matches = [item for item in data if major_name in item['major_name']]
# 方案 C：结合教育层次筛选
if education_level:
    matches = [item for item in matches if item['education_level'] == education_level]
```

## 下载 PDF（用户确认后执行）
```python
import requests
response = requests.get(pdf_url, timeout=30)
if response.status_code == 200:
    pdf_content = response.content
    # 保存到临时目录
```

## 解析 PDF
```python
import fitz  # PyMuPDF
doc = fitz.open(stream=pdf_content, filetype="pdf")
text = ""
for page in doc:
    text += page.get_text()
```

## 依赖库均为"可选"
`requests`、`fitz`(PyMuPDF)、`pandas`、`pdfplumber`/`PyPDF2` 仅用于 PDF 文本提取与表格处理。若环境缺少某库：
- 下载/解析失败 → 走 references/error-handling.md 的"故障1/故障4"决策树
- 无法解析 → 询问用户提供文本版或截图，禁止静默跳过

## 错误处理
| 错误类型 | 处理方式 |
|----------|----------|
| 索引文件不存在 | 提示用户提供专业教学标准 |
| PDF 下载失败 | 重试 2 次，失败后提示用户手动提供 |
| PDF 解析失败 | 尝试备用解析方案，失败后提示用户 |
| 网络超时 | 提示用户检查网络或手动上传文件 |