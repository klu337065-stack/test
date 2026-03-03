#!/usr/bin/env python3
"""OCR invoice recognizer.

Usage:
    python invoice_ocr.py /path/to/invoice.jpg
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable


@dataclass
class InvoiceInfo:
    invoice_type: str | None = None
    invoice_code: str | None = None
    invoice_number: str | None = None
    issue_date: str | None = None
    check_code: str | None = None
    total_amount: str | None = None
    tax_amount: str | None = None
    amount_without_tax: str | None = None
    buyer_name: str | None = None
    seller_name: str | None = None


# --- OCR backends ---
def _ocr_with_paddle(image_path: Path) -> str:
    from paddleocr import PaddleOCR

    ocr = PaddleOCR(use_angle_cls=True, lang="ch")
    result = ocr.ocr(str(image_path), cls=True)
    lines: list[str] = []
    for block in result:
        for row in block:
            lines.append(row[1][0])
    return "\n".join(lines)


def _ocr_with_tesseract(image_path: Path) -> str:
    import cv2
    import pytesseract

    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return pytesseract.image_to_string(binary, lang="chi_sim+eng")


def run_ocr(image_path: Path) -> str:
    backends: list[tuple[str, Callable[[Path], str]]] = [
        ("paddleocr", _ocr_with_paddle),
        ("tesseract", _ocr_with_tesseract),
    ]
    errors: list[str] = []

    for name, fn in backends:
        try:
            text = fn(image_path)
            if text.strip():
                return text
            errors.append(f"{name}: empty output")
        except Exception as exc:  # noqa: BLE001 - fallback sequence
            errors.append(f"{name}: {exc}")
    raise RuntimeError("No OCR backend available. " + " | ".join(errors))


# --- Field extraction ---
def _search(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else None


def parse_invoice_text(text: str) -> InvoiceInfo:
    normalized = text.replace(" ", "")

    info = InvoiceInfo(
        invoice_type=_search(r"(增值税(?:电子)?(?:专用|普通)发票)", normalized),
        invoice_code=_search(r"发票代码[:：]?([0-9]{10,12})", normalized),
        invoice_number=_search(r"发票号码[:：]?([0-9]{8})", normalized),
        issue_date=_search(r"开票日期[:：]?([0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日)", normalized)
        or _search(r"开票日期[:：]?([0-9]{4}-[0-9]{1,2}-[0-9]{1,2})", normalized),
        check_code=_search(r"校验码[:：]?([0-9]{6,20})", normalized),
        total_amount=_search(r"价税合计[^(\n\r)]*[小写]?[¥￥]?([0-9]+\.?[0-9]{0,2})", normalized)
        or _search(r"合计[¥￥]?([0-9]+\.?[0-9]{0,2})", normalized),
        tax_amount=_search(r"税额[¥￥]?([0-9]+\.?[0-9]{0,2})", normalized),
        amount_without_tax=_search(r"金额[¥￥]?([0-9]+\.?[0-9]{0,2})", normalized),
        buyer_name=_search(r"购买方信息[\s\S]{0,50}?名称[:：]?([^\n\r]+)", text)
        or _search(r"名称[:：]?([^\n\r]+)", text),
        seller_name=_search(r"销售方信息[\s\S]{0,50}?名称[:：]?([^\n\r]+)", text),
    )
    return info


def recognize_invoice(image_path: Path) -> InvoiceInfo:
    text = run_ocr(image_path)
    return parse_invoice_text(text)


def main() -> None:
    parser = argparse.ArgumentParser(description="OCR image invoice recognizer")
    parser.add_argument("image", type=Path, help="Invoice image path")
    args = parser.parse_args()

    info = recognize_invoice(args.image)
    for key, value in asdict(info).items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
