from ..schemas import processor_schema as ps
import uuid


class RMQHelper:
    @staticmethod
    async def handle_txt(cp: ps.CommonParams, data: ps.TxtProcessParams):
        pass

    @staticmethod
    async def handle_json(cp: ps.CommonParams, data: ps.JsonProcessParams):
        pass

    @staticmethod
    async def handle_xml(cp: ps.CommonParams, data: ps.XmlProcessParams):
        pass

    @staticmethod
    async def handle_pdf(cp: ps.CommonParams, data: ps.PdfProcessParams):
        pass

    @staticmethod
    async def handle_md(cp: ps.CommonParams, data: ps.MdProcessParams):
        pass

    @staticmethod
    async def handle_yaml(cp: ps.CommonParams, data: ps.YamlProcessParams):
        pass

    @staticmethod
    async def handle_docx(cp: ps.CommonParams, data: ps.DocxProcessParams):
        pass

    @staticmethod
    async def handle_excel(cp: ps.CommonParams, data: ps.ExcelProcessParams):
        pass

    @staticmethod
    async def handle_code(cp: ps.CommonParams, data: ps.CodeProcessParams):
        pass

    @staticmethod
    async def handle_ppt(cp: ps.CommonParams, data: ps.PptxProcessParams):
        pass

    @staticmethod
    async def handle_html(cp: ps.CommonParams, data: ps.HtmlProcessParams):
        pass

    @staticmethod
    async def handle_csv(cp: ps.CommonParams, data: ps.CSVProcessParams):
        pass

    @staticmethod
    async def handle_image(cp: ps.CommonParams, data: ps.ImageProcessParams):
        pass

    @staticmethod
    async def handle_audio(cp: ps.CommonParams, data: ps.AudioProcessParams):
        pass
