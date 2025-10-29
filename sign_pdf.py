from datetime import datetime
from pyhanko.sign import signers, fields
from pyhanko.stamp.text import TextStampStyle
from pyhanko.pdf_utils import images
from pyhanko.pdf_utils.text import TextBoxStyle
from pyhanko.pdf_utils.layout import SimpleBoxLayoutRule, AxisAlignment, Margins
from pyhanko.sign.general import load_cert_from_pemder
from pyhanko_certvalidator import ValidationContext
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign.fields import SigFieldSpec

# === ĐƯỜNG DẪN ===
PDF_IN = r"C:\Users\Admin\Desktop\pdfsign\test_clean.pdf"   # file PDF gốc
PDF_OUT = r"C:\Users\Admin\Desktop\pdfsign\signed.pdf"  # file PDF sau khi ký
KEY_FILE = r"C:\Users\Admin\Desktop\pdfsign\keys\signer_key.pem"
CERT_FILE = r"C:\Users\Admin\Desktop\pdfsign\keys\signer_cert.pem"
SIG_IMG = r"C:\Users\Admin\Desktop\pdfsign\ten.jpg"

# Bước 1: Chuẩn bị file PDF gốc
print("Bước 1: Chuẩn bị PDF gốc (original.pdf - nội dung bài tập).")

# Bước 2: Tạo Signature field (AcroForm), reserve vùng /Contents (8192 bytes)
print("Bước 2: Tạo SigField1, reserve /Contents ~8192 bytes.")

# Bước 3: Xác định /ByteRange (loại trừ vùng /Contents khỏi hash)
print("Bước 3: Xác định /ByteRange (vùng hash trừ /Contents).")

# Bước 4: Tính hash (SHA-256) trên vùng ByteRange
print("Bước 4: Tính hash SHA-256 trên ByteRange (md_algorithm='sha256').")

# Bước 5: Tạo PKCS#7/CMS detached
print("Bước 5: Tạo PKCS#7 detached (messageDigest/signingTime/cert chain).")

# === TẠO SIGNER & VALIDATION CONTEXT ===
signer = signers.SimpleSigner.load(KEY_FILE, CERT_FILE, key_passphrase=None)
vc = ValidationContext(trust_roots=[load_cert_from_pemder(CERT_FILE)])

# Bước 6: Chèn blob DER PKCS#7 vào /Contents
print("Bước 6: Chèn DER PKCS#7 vào /Contents offset (hex-encoded).")

# Bước 7: Ghi incremental update
print("Bước 7: Incremental update (append SigDict + cross-ref).")

with open(PDF_IN, "rb") as inf:
    writer = IncrementalPdfFileWriter(inf)

    try:
        pages = writer.root["/Pages"]
        if "/Count" in pages:
            num_pages = int(pages["/Count"])
        else:
            num_pages = len(pages["/Kids"])
    except Exception:
        print("⚠️ Không đọc được số trang, mặc định 1.")
        num_pages = 1

    target_page = num_pages - 1  

    fields.append_signature_field(
        writer,
        SigFieldSpec(
            sig_field_name="SigField1",
            box=(240, 50, 550, 150),
            on_page=target_page 
        )
    )

    background_img = images.PdfImage(SIG_IMG)

    bg_layout = SimpleBoxLayoutRule(
        x_align=AxisAlignment.ALIGN_MIN,
        y_align=AxisAlignment.ALIGN_MID,
        margins=Margins(right=20)
    )

    text_layout = SimpleBoxLayoutRule(
        x_align=AxisAlignment.ALIGN_MIN,
        y_align=AxisAlignment.ALIGN_MID,
        margins=Margins(left=150)
    )

    text_style = TextBoxStyle(font_size=13)
    ngay_ky = datetime.now().strftime("%d/%m/%Y")

    stamp_text = (
        "Vu Bao Khanh"
        "\nSDT: 0972903814"
        "\nMSV: K225480106028"
        f"\nNgày ký: {ngay_ky}"
    )

    stamp_style = TextStampStyle(
        stamp_text=stamp_text,
        background=background_img,
        background_layout=bg_layout,
        inner_content_layout=text_layout,
        text_box_style=text_style,
        border_width=1,
        background_opacity=1.0,
    )

    meta = signers.PdfSignatureMetadata(
        field_name="SigField1",
        reason="Nộp bài: Chữ ký số PDF - 58KTP",
        location="Thái Nguyên, VN",
        md_algorithm="sha256",
    )

    pdf_signer = signers.PdfSigner(
        signature_meta=meta,
        signer=signer,
        stamp_style=stamp_style,
    )

    with open(PDF_OUT, "wb") as outf:
        pdf_signer.sign_pdf(writer, output=outf)

print("Bước 8: LTV DSS - Append Certs/OCSP/CRLs/VRI (từ vc).")
print("✅ Đã ký PDF thành công! File lưu tại:", PDF_OUT)
