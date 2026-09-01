"""Genera fixtures didácticas binarias; es seguro volver a ejecutarlo."""

from pathlib import Path

from docx import Document
from openpyxl import Workbook
from pptx import Presentation
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

ROOT = Path(__file__).resolve().parents[1] / "examples" / "corpus" / "demo"


def create_docx() -> None:
    path = ROOT / "components" / "orquestador.docx"
    path.parent.mkdir(parents=True, exist_ok=True)
    document = Document()
    document.add_heading("Orquestador de cargas", level=1)
    document.add_paragraph(
        "ORQ_DATAOPS controla las dependencias y reintentos de las ETL nocturnas."
    )
    document.add_heading("Monitorización", level=2)
    document.add_paragraph("Las ejecuciones se consultan en el panel CONTROL_M.")
    document.save(path)


def create_pptx() -> None:
    path = ROOT / "architecture" / "flujo-datos.pptx"
    path.parent.mkdir(parents=True, exist_ok=True)
    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[1])
    slide.shapes.title.text = "Flujo de datos de clientes"
    slide.placeholders[1].text = (
        "CRM Oracle → ETL_CLIENTES_DIARIA → tabla CLIENTE_MAESTRO → reporting"
    )
    presentation.save(path)


def create_xlsx() -> None:
    path = ROOT / "inventory" / "inventario-procesos.xlsx"
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Procesos"
    sheet.append(["Proceso", "Responsable", "SLA"])
    sheet.append(["ETL_CLIENTES_DIARIA", "DataOps", "03:00"])
    sheet.append(["ETL_CONTRATOS_SEMANAL", "Backoffice", "Lunes 06:00"])
    workbook.save(path)


def create_pdf() -> None:
    path = ROOT / "runbooks" / "recuperacion-clientes.pdf"
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_ref = writer._add_object(font)
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})}
    )
    stream = DecodedStreamObject()
    stream.set_data(
        b"BT /F1 12 Tf 72 720 Td (Runbook ETL clientes: reintentar desde "
        b"CONTROL_M tras validar CRM_ORACLE.) Tj ET"
    )
    page[NameObject("/Contents")] = writer._add_object(stream)
    with path.open("wb") as output:
        writer.write(output)


if __name__ == "__main__":
    ROOT.mkdir(parents=True, exist_ok=True)
    create_docx()
    create_pptx()
    create_xlsx()
    create_pdf()
    print(f"Corpus generado en {ROOT}")
