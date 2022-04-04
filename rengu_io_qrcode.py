from io import TextIOBase
from subprocess import PIPE, Popen

from rengu import BASEURL
from rengu.io import RenguOutput, RenguOutputError, with_templating
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


class RenguOutputQrcode(RenguOutput):
    def __init__(self, arg: str, fd: TextIOBase = None):

        super().__init__(arg, fd)

        for x in self.extra:
            if x.startswith("print"):
                if "=" in x:
                    printer = x.split("=", 1)[1]
                    self.fd = Popen(["/usr/bin/lpr", "-P", printer], stdin=PIPE).stdin
                else:
                    self.fd = Popen("/usr/bin/lpr", stdin=PIPE).stdin

    @with_templating
    def __call__(self, obj: dict):

        if "b" not in self.fd.mode:
            self.fd = open(self.fd.name, "wb")

        uid = obj.get("ID")
        if not uid:
            raise RenguOutputError("Invalid Rengu object")

        title = obj.get("Title", "")
        by = obj.get("By", "")
        if isinstance(by, list):
            by = " /  ".join(by)
        if not by:
            by = ""

        c = canvas.Canvas(self.fd)
        c.setPageSize((2.25 * inch, 1.25 * inch))

        qr_code = qr.QrCodeWidget(f"{BASEURL}/{uid}")
        d1 = Drawing(0, 0)
        d1.add(qr_code)
        renderPDF.draw(d1, c, 0, 0)

        d2 = Drawing(1.25, 1.25)
        d2.add(String(0, 0, uid[0:8].lower(), fontSize=10, fontName="Helvetica"))
        d2.add(String(0, -10, title, fontSize=6, fontName="Helvetica"))
        d2.add(String(0, -20, by, fontSize=6, fontName="Helvetica"))

        renderPDF.draw(d1, c, 0, 0)
        renderPDF.draw(d2, c, inch * 1.25, inch)

        c.showPage()

        try:
            c.save()
        except TypeError:
            print("# Aborting QRCode because output stream was not a bytestream")
