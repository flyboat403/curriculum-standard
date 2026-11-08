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
# 输入前置校验（对齐 Step 3：信息缺失必须先询问用户）
if not (major_code or major_name):
    raise ValueError("缺专业代码/名称，请先询问用户补充后再匹配")

# 方案 A：按专业代码精确匹配（优先）
if major_code:
    matches = [item for item in data if item['major_code'] == major_code]
# 方案 B：按专业名称模糊匹配（次优）
else:
    matches = [item for item in data if major_name in item['major_name']]
# 方案 C：结合教育层次筛选
if education_level:
    matches = [item for item in matches if item['education_level'] == education_level]
# 0命中：禁止后续取 matches[0]，进入 Step 4.3 三选项提示
if not matches:
    raise LookupError("专业教学标准索引0命中 → 按 Step 4.3 提示用户选择")
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

## 选项② 使用专业简介替代专业教学标准（教学标准0命中时）

**优先级（强制）**：专业教学标准（PDF）优先。本节仅在**教学标准索引0命中（缺失）**且用户选择 **2. 使用专业简介替代专业教学标准** 时读取；只要教学标准可用，禁止读取本节。

```python
import json, time, requests
jianjie_index_path = "@path/assets/moe_jianjie_final.json"
with open(jianjie_index_path, 'r', encoding='utf-8') as f:
    jianjie = json.load(f)   # 1349条：major_code/major_name/education_level/md_url

# 输入前置校验（对齐 Step 3：信息缺失必须先询问用户）
if not (major_code or major_name):
    raise ValueError("缺专业代码/名称，请先询问用户补充后再匹配")

# 复用上面"搜索匹配"的同序逻辑：代码精确 → 名称模糊 → 层次筛选
if major_code:
    matches = [m for m in jianjie if m['major_code'] == major_code]
else:
    matches = [m for m in jianjie if major_name in m['major_name']]
if education_level:
    matches = [m for m in matches if m['education_level'] == education_level]
if not matches:
    raise LookupError("简介索引0命中 → 走 references/error-handling.md 故障4")  # 禁止 matches[0]

# 命中后取 md_url —— 简介是 md 纯文本，不是 PDF，不走上面的"下载/解析 PDF"两节
md_url = matches[0]['md_url']
text = None
for _ in range(3):                    # 首发 + 重试2次，对齐下表步骤2与错误处理表
    try:
        resp = requests.get(md_url, timeout=30)
        resp.raise_for_status()       # 404/500 错误页不得当作正文
        resp.encoding = "utf-8"       # 不依赖服务器 charset，防中文乱码
        text = resp.text              # 直接得到文本，无需 fitz/PyMuPDF
        break
    except requests.RequestException:  # 只吞网络类错误，编程错误立即暴露
        time.sleep(2)
if text is None:
    raise IOError("简介md下载失败（已重试2次）→ 走 error-handling.md 故障4")
```

**注意**：1349条记录仅对应 **275个唯一md链接**（同一专业大类共用一份简介md）。取回文本后必须**按 `major_name` 定位该专业所在段落**，仅取该段落文本作为 Phase 1 来源，其余专业内容一律跳过。

| 步骤 | 动作 |
|------|------|
| 1 | 读取 `moe_jianjie_final.json` 并按上序匹配；0命中 → 走故障4（禁止 `matches[0]`） |
| 2 | 用 `md_url` 下载md文档（失败重试2次），直接取 `resp.text` |
| 3 | 按 `major_name` 定位所在段落（md 为纯文本，**无需 fitz**） |
| 4 | 该段落文本 + 人才培养方案 → 交 Phase 1 提取 |
| 5 | 定位不到该专业 → 视同下载失败，走"故障4"并询问用户 |

## 依赖库均为"可选"
`requests`、`fitz`(PyMuPDF)、`pandas`、`pdfplumber`/`PyPDF2` 仅用于 PDF 文本提取与表格处理。其中**专业简介（md）只需 `requests`，不依赖 `fitz`**；`fitz` 仅用于专业教学标准 PDF。若环境缺少某库：
- 下载/解析失败 → 走 references/error-handling.md 的"故障1/故障4"决策树
- 无法解析 → 询问用户提供文本版或截图，禁止静默跳过

## 错误处理
| 错误类型 | 处理方式 |
|----------|----------|
| 索引文件不存在 | 提示用户提供专业教学标准 |
| PDF 下载失败 | 重试 2 次，失败后提示用户手动提供 |
| PDF 解析失败 | 尝试备用解析方案，失败后提示用户 |
| 网络超时 | 提示用户检查网络或手动上传文件 |
| 简介索引不存在 | 提示用户提供专业教学标准文件（选项1），或选择忽略（选项3） |
| 简介md中定位不到该专业 | 重试1次后仍失败 → 走 error-handling.md 故障4，询问用户上传文件或忽略 |