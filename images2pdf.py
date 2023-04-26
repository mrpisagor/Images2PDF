import imghdr
import os.path
import sys
import tempfile
from PIL import Image
from pypdf import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5
from reportlab.lib.utils import ImageReader
from io import BytesIO
from argparse import ArgumentParser


def list_images(images, recursive=False):
    for image in images:
        if os.path.exists(image):
            if os.path.isfile(image):
                if imghdr.what(image) in ["png", "jpeg", "jpg", "bmp", "gif", "webp", "avif"]:
                    yield image
            if recursive:
                if os.path.isdir(image):
                    yield from list_images([os.path.join(image, i) for i in os.listdir(image)], recursive)
                elif os.path.basename(image) == os.path.curdir or os.path.basename(image) == os.path.pardir:
                    yield from list_images(os.listdir(image), recursive)


def insert_image_page(img_path, ix):
    img = Image.open(img_path)

    exif = img.getexif()

    if exif is not None:
        orientation = exif.get(0x0112)
        if orientation == 3:
            img = img.rotate(180, expand=True)
        elif orientation == 6:
            img = img.rotate(270, expand=True)
        elif orientation == 8:
            img = img.rotate(90, expand=True)

    temp = tempfile.NamedTemporaryFile(suffix=os.path.splitext(img_path)[1], delete=False)
    temp.close()
    img.save(temp.name)
    img.close()

    img_reader = ImageReader(temp.name)

    imgio = BytesIO()
    imgcanvas = canvas.Canvas(imgio, pagesize=A5)
    RATIO = img_reader.getSize()[1] / img_reader.getSize()[0]
    if RATIO >= 1:
        HEIGHT = A5[1] * 5 / 6
        WIDTH = HEIGHT / RATIO
    else:
        WIDTH = A5[0] * 5 / 6
        HEIGHT = WIDTH * RATIO

    imgcanvas.drawImage(img_reader, (A5[0] - WIDTH) / 2, (A5[1] - HEIGHT) / 2, WIDTH, HEIGHT, mask="auto",
                        preserveAspectRatio=True)
    imgcanvas.save()

    os.unlink(temp.name)

    pdf_writer.add_blank_page(*A5)
    page = pdf_writer.get_page(ix)
    page_to_merge = PdfReader(BytesIO(imgio.getvalue())).pages[0]
    page.merge_page(page_to_merge)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-f", "--file", required=True, help="pdf file name")
    parser.add_argument("images", help="images or directory with -r option", nargs="+")
    parser.add_argument("-r", "--recursive", help="If you want to use directory use this option", action="store_true")

    args = parser.parse_args()

    if os.path.splitext(args.file)[1] == ".pdf":
        if not args.recursive and any(map(os.path.isdir, args.images)):
            print("Please use -r option")
            sys.exit(0)
        with open(args.file, "wb") as f:

            pdf_writer = PdfWriter()

            for ix, img_path in enumerate(list_images(args.images, args.recursive)):
                insert_image_page(img_path, ix)

            pdf_writer.write(f)
            pdf_writer.close()
    else:
        print("File name should has .pdf extension")
