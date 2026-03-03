# test

## 新增能力：OCR 图片识别发票

已新增一个可直接运行的 OCR 发票识别脚本 `invoice_ocr.py`，支持从发票图片中提取以下字段：

- 发票类型（增值税普通/专用/电子发票）
- 发票代码
- 发票号码
- 开票日期
- 校验码
- 价税合计
- 税额
- 不含税金额
- 购买方名称
- 销售方名称

## 识别后端

脚本会按顺序自动尝试以下 OCR 后端：

1. `PaddleOCR`（优先，中文识别效果更好）
2. `pytesseract + OpenCV`（兜底）

如果某个后端不可用，会自动切换到下一个后端。

## 安装

```bash
pip install -r requirements.txt
# 如需更高中文准确率，可额外安装：
# pip install paddleocr
```

> 使用 `pytesseract` 时，系统还需安装 tesseract OCR 引擎，并包含中文语言包 `chi_sim`。

## 使用方法

```bash
python invoice_ocr.py /path/to/invoice.jpg
```

输出示例：

```text
invoice_type: 增值税电子普通发票
invoice_code: 031002300111
invoice_number: 12345678
issue_date: 2026年03月01日
check_code: 12345678901234567890
total_amount: 100.00
tax_amount: 6.00
amount_without_tax: 94.00
buyer_name: 某某科技有限公司
seller_name: 某某服务有限公司
```
