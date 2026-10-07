# -*- coding: utf-8 -*-
"""为 pandoc 生成的 DOCX 文档中的所有表格注入完整边框（内外部）。
用法: python patch_table_borders.py <docx路径> [更多docx路径...]
原理: pandoc 使用内置 Table 样式且该样式无 tblBorders，
      在 document.xml 的每个 w:tblPr 中直接写入单线全边框定义。
幂等: 已含 tblBorders 的表格跳过，可重复执行。
"""
import sys, zipfile, shutil, re, os

BORDERS = ('<w:tblBorders>'
           '<w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
           '<w:left w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
           '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
           '<w:right w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
           '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
           '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
           '</w:tblBorders>')

def patch(path):
    tmp = path + '.tmp.docx'
    patched = 0
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.namelist():
            data = zin.read(item)
            if item == 'word/document.xml':
                xml = data.decode('utf-8')
                parts = re.split(r'(<w:tblPr\b.*?</w:tblPr>)', xml, flags=re.S)
                out = []
                for p in parts:
                    if p.startswith('<w:tblPr'):
                        if '<w:tblBorders' in p:
                            out.append(p)
                        else:
                            # 插入到 tblW/tblLayout/tblCellMar 之后、</w:tblPr> 之前
                            out.append(p.replace('</w:tblPr>', BORDERS + '</w:tblPr>'))
                            patched += 1
                    else:
                        out.append(p)
                data = ''.join(out).encode('utf-8')
            zout.writestr(zin.getinfo(item), data)
    shutil.move(tmp, path)
    print(f'{os.path.basename(path)}: patched {patched} tables -> {path}')

if __name__ == '__main__':
    for f in sys.argv[1:]:
        patch(f)
